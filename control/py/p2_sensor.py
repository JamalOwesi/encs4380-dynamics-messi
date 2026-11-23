"""
P2 - A slow sensor in the loop.
The controller only sees what the sensor reports. A first-order sensor
1/(tau_s s + 1) in the feedback path adds lag; as tau_s grows the true output
overshoots more and more until the loop oscillates.
Bonus: Ziegler-Nichols tuning from the ultimate gain of plant + sensor.
"""

import pid_core as pc
import ui

P = "p2"
_sweep_key = None


def controls_html():
    return (
        ui.plant_controls(P, "first", K=1, tau=1, wn=2, zeta=0.5)
        + '<div class="group"><h3>Sensor</h3>'
        + ui.slider(P + "-taus", "Sensor &tau;<sub>s</sub>", 0, 2, 0.01, 0.2, "s")
        + '</div>'
        + ui.gain_controls(P, 3, 8, 0, kp_max=30, ki_max=30, kd_max=3)
        + '<div class="group"><h3>Window</h3>'
        + ui.slider(P + "-tend", "Time window", 2, 40, 0.5, 15, "s")
        + '</div>'
    )


def critical_tau_s(plant, Kp, Ki, Kd, hi=10.0):
    """Smallest sensor time constant that makes the loop unstable (Routh)."""
    def stable(ts):
        return pc.routh_stable(pc.char_poly(plant, Kp, Ki, Kd, ts))[0]
    if not stable(1e-6):
        return 0.0
    if stable(hi):
        return None
    lo = 1e-6
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if stable(mid):
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def routh_html(plant, Kp, Ki, Kd, tau_s):
    stable, _ = pc.routh_stable(pc.char_poly(plant, Kp, Ki, Kd, tau_s))
    txt = "Routh test with this sensor: %s." % ui.badge(stable, "stable", "unstable")
    if plant.kind == "first":
        K, tau = plant.K, plant.tau
        left = (tau + tau_s + K * Kd) * (1 + K * Kp)
        right = tau * tau_s * K * Ki
        txt += ("<br>Characteristic equation &tau;&tau;<sub>s</sub>s&sup3; + (&tau;+&tau;<sub>s</sub>+KK<sub>d</sub>)s&sup2; "
                "+ (1+KK<sub>p</sub>)s + KK<sub>i</sub> = 0. Stable when "
                "(&tau;+&tau;<sub>s</sub>+KK<sub>d</sub>)(1+KK<sub>p</sub>) &gt; &tau;&tau;<sub>s</sub>KK<sub>i</sub>: "
                "<b>%.3g</b> %s <b>%.3g</b>." % (left, "&gt;" if left > right else "&le;", right))
    return "<p class='theory'>%s</p>" % txt


def sweep(plant, Kp, Ki, Kd, t_end):
    taus = [0.1 * i for i in range(0, 21)]
    os_true, os_meas = [], []
    for ts in taus:
        s = pc.simulate_continuous(plant, Kp, Ki, Kd, t_end=t_end, n_steps=1200, tau_s=ts)
        mt = pc.step_metrics(s["t"], s["y"], 1)
        mm = pc.step_metrics(s["t"], s["ym"], 1)
        os_true.append(None if mt["unstable"] else min(mt["overshoot"] or 0, 300))
        os_meas.append(None if mm["unstable"] else min(mm["overshoot"] or 0, 300))
    return taus, os_true, os_meas


def render():
    global _sweep_key, _sweep
    plant = ui.read_plant(P)
    Kp, Ki, Kd = ui.read_gains(P)
    tau_s = ui.val(P + "-taus")
    t_end = ui.val(P + "-tend")
    sim = pc.simulate_continuous(plant, Kp, Ki, Kd, t_end=t_end, n_steps=3000, tau_s=tau_s)
    t = ui.thin(sim["t"])
    ui.plot(P + "-plot-y", [
        ui.line([0, t_end], [1, 1], "setpoint", ui.COLORS["r"], "dash", 1.5),
        ui.line(t, ui.thin(sim["y"]), "true output y", ui.COLORS["y"]),
        ui.line(t, ui.thin(sim["ym"]), "what the sensor reports y<sub>m</sub>", ui.COLORS["ym"], "dot"),
    ], {"title": {"text": "True output vs sensor reading", "font": {"size": 13}},
        "xaxis": {"title": {"text": "time [s]"}},
        "yaxis": {"range": [-0.2, 2.6]}})

    mt = pc.step_metrics(sim["t"], sim["y"], 1)
    mm = pc.step_metrics(sim["t"], sim["ym"], 1)

    def cell(m, key, unit):
        if m["unstable"]:
            return "<span class='bad'>unstable</span>"
        return ui.fmt(m[key], unit, none="not settled")

    ui.set_html(P + "-metrics",
                "<table class='ctable'><tr><th></th><th>True y</th><th>Sensor y<sub>m</sub></th></tr>"
                "<tr><th>Overshoot</th><td>%s</td><td>%s</td></tr>"
                "<tr><th>Settling (2 %%)</th><td>%s</td><td>%s</td></tr>"
                "<tr><th>Peak</th><td>%s</td><td>%s</td></tr></table>"
                % (cell(mt, "overshoot", "%"), cell(mm, "overshoot", "%"),
                   cell(mt, "settling", "s"), cell(mm, "settling", "s"),
                   cell(mt, "peak", ""), cell(mm, "peak", ""))
                + routh_html(plant, Kp, Ki, Kd, tau_s))

    # overshoot vs tau_s (recomputed only when the plant or gains change)
    key = (plant.label(), Kp, Ki, Kd, t_end)
    if key != _sweep_key:
        _sweep_key = key
        _sweep = sweep(plant, Kp, Ki, Kd, t_end)
    taus, ot, om = _sweep
    tc = critical_tau_s(plant, Kp, Ki, Kd)
    traces = [ui.line(taus, ot, "true overshoot", ui.COLORS["y"], mode="lines+markers"),
              ui.line(taus, om, "overshoot the sensor shows", ui.COLORS["ym"], "dot", mode="lines+markers")]
    cur_t = mt["overshoot"] if not mt["unstable"] else None
    traces.append({"x": [tau_s], "y": [min(cur_t, 300) if cur_t is not None else 300], "mode": "markers",
                   "type": "scatter", "name": "now", "marker": {"size": 12, "color": "#111827"}})
    shapes = []
    if tc is not None and tc <= 2:
        shapes.append({"type": "line", "x0": tc, "x1": tc, "yref": "paper", "y0": 0, "y1": 1,
                       "line": {"color": ui.COLORS["lim"], "dash": "dash"}})
    ui.plot(P + "-plot-sweep", traces, {
        "title": {"text": "Overshoot as the sensor gets slower" + (
            " (red line: oscillation starts at τ<sub>s</sub> = %.2f s)" % tc if tc is not None and tc <= 2 else ""),
            "font": {"size": 13}},
        "xaxis": {"title": {"text": "sensor τ<sub>s</sub> [s]"}},
        "yaxis": {"title": {"text": "overshoot [%]"}, "range": [0, 160]},
        "shapes": shapes, "height": 260})


# ----------------------------------------------------- Ziegler-Nichols bonus
def zn_find():
    plant = ui.read_plant(P)
    tau_s = ui.val(P + "-taus")
    Ku, Tu = pc.ultimate_gain(plant, tau_s)
    if Ku is None:
        ui.set_html(P + "-zn-out",
                    "<p class='warn'>No ultimate gain: with this plant and sensor the loop phase never reaches "
                    "&minus;180&deg;, so P control alone can never make it oscillate. Pick the second-order "
                    "plant (or add sensor lag to it) and try again.</p>")
        return
    rules = pc.ziegler_nichols(Ku, Tu)
    rows = "".join("<tr><th>%s</th><td>%.3g</td><td>%.3g</td><td>%.3g</td><td>%s</td></tr>"
                   % (k, g[0], g[1], g[2], ui.button(P + "-zn-" + k, "Use", "small"))
                   for k, g in rules.items())
    ui.set_html(P + "-zn-out",
                "<p>Ultimate gain <b>K<sub>u</sub> = %.3g</b>, oscillation period <b>T<sub>u</sub> = %.3g s</b>. "
                "%s</p><table class='ctable'><tr><th>Rule</th><th>K<sub>p</sub></th><th>K<sub>i</sub></th>"
                "<th>K<sub>d</sub></th><th></th></tr>%s</table>"
                "<p class='caption'>Classic table: P: 0.5K<sub>u</sub>; PI: 0.45K<sub>u</sub>, T<sub>i</sub>=T<sub>u</sub>/1.2; "
                "PID: 0.6K<sub>u</sub>, T<sub>i</sub>=T<sub>u</sub>/2, T<sub>d</sub>=T<sub>u</sub>/8; "
                "K<sub>i</sub>=K<sub>p</sub>/T<sub>i</sub>, K<sub>d</sub>=K<sub>p</sub>T<sub>d</sub>. "
                "Expect about 25 %% overshoot: ZN is a starting point, not a final answer.</p>"
                % (Ku, Tu, ui.button(P + "-zn-ku", "Show the loop at K = K<sub>u</sub>", "small"), rows))

    def apply(g):
        ui.set_value(P + "-kp", round(g[0], 2))
        ui.set_value(P + "-ki", round(g[1], 2))
        ui.set_value(P + "-kd", round(g[2], 2))
        render()

    for k, g in rules.items():
        ui.on_click(P + "-zn-" + k, (lambda gg: (lambda: apply(gg)))(g))
    ui.on_click(P + "-zn-ku", lambda: apply((Ku, 0, 0)))


def _q_os():
    def ans():
        res = []
        for ts in (0.0, 0.6):
            s = pc.simulate_continuous(pc.FirstOrder(1, 1), 3, 8, 0, t_end=15, tau_s=ts)
            res.append(pc.step_metrics(s["t"], s["y"], 1)["overshoot"])
        return "more", "True overshoot with &tau;<sub>s</sub>=0: %.0f %%, with &tau;<sub>s</sub>=0.6 s: %.0f %%." % tuple(res)
    return {
        "q": "K<sub>p</sub> = 3, K<sub>i</sub> = 8, first-order plant. The sensor gets slower: &tau;<sub>s</sub> from 0 to 0.6 s. "
             "The gains did not change. The overshoot of the true output will be&hellip;",
        "options": [("same", "The same: the gains are the same"), ("more", "Larger"), ("less", "Smaller")],
        "setup": {P + "-plant": "first", P + "-K": 1, P + "-tau": 1, P + "-kp": 3, P + "-ki": 8,
                  P + "-kd": 0, P + "-taus": 0.6, P + "-tend": 15},
        "answer": ans,
        "explain": "The controller reacts to old news. By the time the sensor reports that y reached the "
                   "setpoint, the true y is already past it, so the controller keeps pushing too long.",
    }


def _q_hidden():
    def ans():
        s = pc.simulate_continuous(pc.FirstOrder(1, 1), 3, 8, 0, t_end=15, tau_s=0.6)
        a = pc.step_metrics(s["t"], s["y"], 1)["overshoot"]
        b = pc.step_metrics(s["t"], s["ym"], 1)["overshoot"]
        return "true", "True y: %.0f %%, sensor: %.0f %%." % (a, b)
    return {
        "q": "With &tau;<sub>s</sub> = 0.6 s, which shows the bigger overshoot: the true output or the sensor reading?",
        "options": [("true", "The true output"), ("sensor", "The sensor reading"), ("equal", "They are equal")],
        "setup": {P + "-plant": "first", P + "-K": 1, P + "-tau": 1, P + "-kp": 3, P + "-ki": 8,
                  P + "-kd": 0, P + "-taus": 0.6, P + "-tend": 15},
        "answer": ans,
        "explain": "The sensor is a low-pass filter: it smooths and delays the peaks. Judging the loop "
                   "from the sensor alone makes it look better than it is.",
    }


def _q_osc():
    def ans():
        tc = critical_tau_s(pc.FirstOrder(1, 1), 3, 8, 0)
        return "1", "Routh gives &tau;<sub>s</sub> = %.2f s as the edge of stability." % tc
    return {
        "q": "Same gains (K<sub>p</sub> = 3, K<sub>i</sub> = 8). At about what sensor time constant does the loop start to oscillate for ever?",
        "options": [("0.2", "0.2 s"), ("1", "1 s"), ("5", "5 s"), ("never", "Never")],
        "setup": {P + "-plant": "first", P + "-K": 1, P + "-tau": 1, P + "-kp": 3, P + "-ki": 8,
                  P + "-kd": 0, P + "-taus": 1.0, P + "-tend": 30},
        "answer": ans,
        "explain": "From the Routh condition (&tau;+&tau;<sub>s</sub>)(1+KK<sub>p</sub>) &gt; &tau;&tau;<sub>s</sub>KK<sub>i</sub>: "
                   "(1+&tau;<sub>s</sub>)&middot;4 &gt; 8&tau;<sub>s</sub>, so &tau;<sub>s</sub> &lt; 1 s.",
    }


box = None


def init():
    global box
    box = ui.PredictBox(P, [_q_os(), _q_hidden(), _q_osc()], render)
    ui.set_html(P + "-controls", controls_html())
    ui.set_html(P + "-predict", box.html())
    ui.on(P + "-controls", render)
    ui.on_click(P + "-zn-btn", zn_find)
    box.bind()
