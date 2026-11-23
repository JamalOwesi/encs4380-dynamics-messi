"""
P3 - Digital PID.
The Arduino only looks at the sensor every Ts seconds and holds u constant
in between (a stair-step). This module runs exactly the sheet's formula
  u[k] = Kp e[k] + Ki Ts sum e[j] + Kd (e[k] - e[k-1]) / Ts
shows how performance falls as Ts grows, shows integrator windup with the
anti-windup switch, and generates the Arduino code for the current gains.
"""

import pid_core as pc
import arduino_code
import ui

P = "p3"
_sweep_key = None
_sweep = None
_code = ""

TS_LIST = [0.01, 0.02, 0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8]


def controls_html():
    return (
        ui.plant_controls(P, "first", K=1, tau=1, wn=2, zeta=0.5)
        + ui.gain_controls(P, 4, 6, 0, kp_max=30, ki_max=30, kd_max=3)
        + '<div class="group"><h3>Sampling and actuator</h3>'
        + ui.slider(P + "-ts", "Sampling time T<sub>s</sub>", 0.005, 0.8, 0.005, 0.05, "s")
        + ui.slider(P + "-umax", "Actuator limit: 0 &le; u &le;", 0.5, 20, 0.1, 1.5)
        + ui.checkbox(P + "-aw", "Anti-windup (clamp the integral while saturated)", False)
        + ui.slider(P + "-tend", "Time window", 2, 30, 0.5, 10, "s")
        + '</div>'
    )


def sweep(plant, Kp, Ki, Kd, umax, aw, t_end):
    os_, st_ = [], []
    for ts in TS_LIST:
        s = pc.simulate_digital(plant, Kp, Ki, Kd, ts, t_end=t_end, u_min=0.0, u_max=umax,
                                anti_windup=aw, fine_steps=1200)
        m = pc.step_metrics(s["t"], s["y"], 1)
        os_.append(None if m["unstable"] else min(m["overshoot"] or 0, 200))
        st_.append(m["settling"])
    return os_, st_


def render():
    global _sweep_key, _sweep, _code
    plant = ui.read_plant(P)
    Kp, Ki, Kd = ui.read_gains(P)
    Ts = ui.val(P + "-ts")
    umax = ui.val(P + "-umax")
    aw = ui.is_checked(P + "-aw")
    t_end = ui.val(P + "-tend")

    d = pc.simulate_digital(plant, Kp, Ki, Kd, Ts, t_end=t_end, u_min=0.0, u_max=umax,
                            anti_windup=aw, fine_steps=3000)
    c = pc.simulate_continuous(plant, Kp, Ki, Kd, t_end=t_end, n_steps=2000, u_min=0.0,
                               u_max=umax, anti_windup=aw, d_on_measurement=False)
    t = ui.thin(d["t"])
    ui.plot(P + "-plot-y", [
        ui.line([0, t_end], [1, 1], "setpoint", ui.COLORS["r"], "dash", 1.5),
        ui.line(ui.thin(c["t"]), ui.thin(c["y"]), "continuous PID (T<sub>s</sub> → 0)", ui.COLORS["ref"], "dot"),
        ui.line(t, ui.thin(d["y"]), "output with digital PID", ui.COLORS["y"]),
        {"x": d["tk"][:400], "y": d["ymk"][:400], "mode": "markers", "type": "scatter",
         "name": "samples", "marker": {"size": 4, "color": ui.COLORS["y"]}},
    ], {"title": {"text": "Output (dots: what the Arduino reads)", "font": {"size": 13}},
        "xaxis": {"title": {"text": "time [s]"}}})
    ui.plot(P + "-plot-u", [
        ui.line(d["tk"], d["uk"], "u[k] (held for T<sub>s</sub>)", ui.COLORS["u"], shape="hv"),
        ui.line(d["tk"], d["ik"], "integral part K<sub>i</sub>T<sub>s</sub>Σe", ui.COLORS["i"], "dot", shape="hv"),
        ui.hline(0, t_end, umax, "limit", ui.COLORS["lim"]),
    ], {"title": {"text": "Stair-step control signal", "font": {"size": 13}},
        "xaxis": {"title": {"text": "time [s]"}}, "height": 240})

    md = pc.step_metrics(d["t"], d["y"], 1)
    mc = pc.step_metrics(c["t"], c["y"], 1)
    rise = mc["rise"]
    if rise:
        ratio = rise / Ts
        if ratio >= 10:
            hint = ui.badge(True, "good") + " T<sub>s</sub> is 1/%.0f of the rise time." % ratio
        elif ratio >= 4:
            hint = '<b class="tag mid">SO-SO</b> only %.1f samples per rise time; aim for 10 or more.' % ratio
        else:
            hint = ui.badge(False, "", "too slow") + " %.1f samples per rise time: the loop is half blind." % ratio
    else:
        hint = ""

    def row(name, key, unit):
        return (name, ui.fmt(md[key], unit, none="not settled") if not md["unstable"] else "<span class='bad'>unstable</span>",
                "continuous: " + ui.fmt(mc[key], unit, none="not settled"))

    ui.set_html(P + "-metrics", ui.metrics_table([
        row("Rise time", "rise", "s"), row("Overshoot", "overshoot", "%"),
        row("Settling time", "settling", "s"), row("Steady-state error", "ess", ""),
        ("Sampling check", hint),
        ("Integral at the end of the window", ui.fmt(d["ik"][-1], ""), "needed at steady state: %.3g" % (1 / plant.K)),
    ]))

    key = (plant.label(), Kp, Ki, Kd, umax, aw, t_end)
    if key != _sweep_key:
        _sweep_key = key
        _sweep = sweep(plant, Kp, Ki, Kd, umax, aw, t_end)
    os_, st_ = _sweep
    ui.plot(P + "-plot-sweep", [
        ui.line(TS_LIST, os_, "overshoot [%]", ui.COLORS["y"], mode="lines+markers"),
        ui.line(TS_LIST, st_, "settling time [s]", ui.COLORS["u"], "dot", mode="lines+markers", yaxis="y2"),
    ], {"title": {"text": "Performance as T<sub>s</sub> grows (same gains)", "font": {"size": 13}},
        "xaxis": {"title": {"text": "T<sub>s</sub> [s]"}},
        "yaxis": {"title": {"text": "overshoot [%]"}},
        "yaxis2": {"title": {"text": "settling [s]"}, "overlaying": "y", "side": "right", "showgrid": False,
                   "tickfont": {"color": "#8693a8"}},
        "shapes": [{"type": "line", "x0": Ts, "x1": Ts, "yref": "paper", "y0": 0, "y1": 1,
                    "line": {"color": "#111827", "dash": "dot"}}],
        "height": 260, "margin": {"r": 50}})

    _code = arduino_code.generate(Kp, Ki, Kd, Ts, 0.0, umax, aw, 1.0)
    ui.el(P + "-code").textContent = _code


def copy():
    ui.copy_text(_code)
    ui.set_html(P + "-copy-msg", "Copied.")


def _q_ts():
    def ans():
        res = []
        for ts in (0.01, 0.3):
            s = pc.simulate_digital(pc.FirstOrder(1, 1), 4, 6, 0, ts, t_end=10, u_min=0, u_max=20)
            res.append(pc.step_metrics(s["t"], s["y"], 1)["overshoot"])
        return "more", "Overshoot with T<sub>s</sub>=0.01 s: %.0f %%, with T<sub>s</sub>=0.3 s: %.0f %%." % tuple(res)
    return {
        "q": "Same gains (K<sub>p</sub> = 4, K<sub>i</sub> = 6), generous actuator limit. T<sub>s</sub> goes from 0.01 s to 0.3 s. Overshoot will&hellip;",
        "options": [("same", "Stay the same"), ("more", "Grow"), ("less", "Shrink")],
        "setup": {P + "-plant": "first", P + "-K": 1, P + "-tau": 1, P + "-kp": 4, P + "-ki": 6, P + "-kd": 0,
                  P + "-ts": 0.3, P + "-umax": 20, P + "-tend": 10},
        "answer": ans,
        "explain": "Holding u for T<sub>s</sub> acts like a delay of about T<sub>s</sub>/2. Delay in the loop "
                   "means the controller reacts late, just like the slow sensor in P2.",
    }


def _q_aw():
    def ans():
        res = []
        for aw in (False, True):
            s = pc.simulate_digital(pc.FirstOrder(1, 1), 4, 6, 0, 0.05, t_end=10, u_min=0, u_max=1.5, anti_windup=aw)
            res.append(pc.step_metrics(s["t"], s["y"], 1)["overshoot"])
        return "less", "Overshoot without anti-windup: %.0f %%, with it: %.0f %%." % tuple(res)
    return {
        "q": "The actuator saturates at u = 1.5 at the start. You switch anti-windup on. The overshoot will&hellip;",
        "options": [("more", "Grow"), ("less", "Shrink"), ("same", "Not change: anti-windup only matters at the limit")],
        "setup": {P + "-plant": "first", P + "-K": 1, P + "-tau": 1, P + "-kp": 4, P + "-ki": 6, P + "-kd": 0,
                  P + "-ts": 0.05, P + "-umax": 1.5, P + "-aw": True, P + "-tend": 10},
        "answer": ans,
        "explain": "While u is stuck at the limit, the plain integrator keeps adding error it cannot act on. "
                   "That stored-up sum has to be 'unwound' by negative error, which is overshoot. "
                   "Clamping stops the sum from growing while saturated.",
    }


box = None


def init():
    global box
    box = ui.PredictBox(P, [_q_ts(), _q_aw()], render)
    ui.set_html(P + "-controls", controls_html())
    ui.set_html(P + "-predict", box.html())
    ui.on(P + "-controls", render)
    ui.on_click(P + "-copy", copy)
    box.bind()
