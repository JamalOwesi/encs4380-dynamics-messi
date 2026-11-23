"""
My system - our own plant: the Micromouse (Messi) drive motor speed loop.

  u = PWM duty cycle [%] (0-100)    y = wheel speed [rpm] from the encoder
  plant  G(s) = K / (tau s + 1)     K in rpm per % PWM, tau in s

1. Get K and tau from a PWM step test logged with the encoder (paste the log
   into the fit tool; the generated sketch has a STEP_TEST switch for this).
2. Pick the spec: damping 0.6 <= zeta <= 0.8 and a settling time.
3. PI design for a first-order plant:  Ki = wn^2 tau / K,
   Kp = (2 zeta wn tau - 1) / K,  with wn = 4 / (zeta * ts).
4. Simulate the digital loop with the 0-100 % PWM limit, then export code.
"""

import math

import pid_core as pc
import arduino_code
import ui

P = "ms"
DEFAULT_K, DEFAULT_TAU = 3.2, 0.08
_code = ""
_fit = None


def num(i, label, value, step="any", unit=""):
    return ('<label><span class="lab">%s</span><input type="number" id="%s" value="%s" step="%s"> %s</label>'
            % (label, i, value, step, unit))


def controls_html():
    return (
        '<div class="group"><h3>1. Plant model (drive motor)</h3>'
        + num(P + "-K", "K [rpm per % PWM]", DEFAULT_K)
        + num(P + "-tau", "&tau; [s]", DEFAULT_TAU)
        + '<label>Where the numbers come from'
          '<input type="text" id="ms-src" value="" placeholder="e.g. step test 50 % PWM, 21 Nov, left motor"></label>'
        + '<div id="ms-src-warn"></div></div>'
        + '<div class="group"><h3>2. Spec</h3>'
        + ui.slider(P + "-zeta", "Damping &zeta;", 0.4, 1.0, 0.01, 0.7)
        + ui.slider(P + "-tset", "Target settling time t<sub>s</sub>", 0.05, 1.5, 0.01, 0.3, "s")
        + num(P + "-r", "Speed setpoint [rpm]", 200)
        + ui.select(P + "-ts", [("0.005", "T<sub>s</sub> = 5 ms"), ("0.01", "T<sub>s</sub> = 10 ms"),
                                ("0.02", "T<sub>s</sub> = 20 ms"), ("0.05", "T<sub>s</sub> = 50 ms")], "0.005")
        + '</div>'
        + '<div class="group"><h3>3. Gains</h3><div id="ms-gains"></div>'
        + ui.checkbox(P + "-manual", "Set the gains by hand instead", False)
        + '<div id="ms-manual-box">' + num(P + "-kp", "K<sub>p</sub>", 0.35) + num(P + "-ki", "K<sub>i</sub>", 9.0)
        + '</div></div>'
    )


def read_float(i, default):
    try:
        return float(ui.el(i).value)
    except Exception:
        return default


def render():
    global _code
    K = max(1e-6, read_float(P + "-K", DEFAULT_K))
    tau = max(1e-4, read_float(P + "-tau", DEFAULT_TAU))
    zeta = ui.val(P + "-zeta")
    tset = ui.val(P + "-tset")
    r = read_float(P + "-r", 200)
    Ts = float(ui.el(P + "-ts").value)
    manual = ui.is_checked(P + "-manual")
    ui.show(P + "-manual-box", manual)

    src = ui.el(P + "-src").value.strip()
    placeholder = (not src) or (abs(K - DEFAULT_K) < 1e-9 and abs(tau - DEFAULT_TAU) < 1e-9)
    ui.set_html(P + "-src-warn",
                "<p class='warn'>These are placeholder numbers. Run the step test on Messi, fit K and &tau; "
                "below, and write the source here before submitting.</p>" if placeholder else "")

    wn = 4.0 / (zeta * tset)
    Kp_d, Ki_d = pc.pi_design(K, tau, zeta, wn)
    if manual:
        Kp, Ki = read_float(P + "-kp", Kp_d), read_float(P + "-ki", Ki_d)
    else:
        Kp, Ki = Kp_d, Ki_d
    wn_a, zeta_a = pc.pi_first_order(K, tau, Kp, Ki) if (Ki > 0 and Kp > -1.0 / K) else (0, 0)

    design = ("&omega;<sub>n</sub> = 4/(&zeta;t<sub>s</sub>) = <b>%.3g rad/s</b><br>"
              "K<sub>i</sub> = &omega;<sub>n</sub>&sup2;&tau;/K = <b>%.4g</b> &nbsp; "
              "K<sub>p</sub> = (2&zeta;&omega;<sub>n</sub>&tau; &minus; 1)/K = <b>%.4g</b>" % (wn, Ki_d, Kp_d))
    if Kp_d < 0:
        design += ("<p class='warn'>K<sub>p</sub> &lt; 0: this target is slower than the motor already is. "
                   "Pick a shorter settling time.</p>")
    ui.set_html(P + "-gains", design)

    t_end = max(4 * tset, 6 * tau, 0.5)
    d = pc.simulate_digital(pc.FirstOrder(K, tau), max(Kp, 0), max(Ki, 0), 0.0, Ts, r=r, t_end=t_end,
                            u_min=0.0, u_max=100.0, anti_windup=True, fine_steps=3000)
    m = pc.step_metrics(d["t"], d["y"], r)
    t = ui.thin(d["t"])
    ui.plot(P + "-plot-y", [
        ui.line([0, t_end], [r, r], "setpoint", ui.COLORS["r"], "dash", 1.5),
        ui.line(t, ui.thin(d["y"]), "wheel speed", ui.COLORS["y"]),
    ], {"title": {"text": "Simulated speed step (digital PI, T<sub>s</sub> = %g ms)" % (Ts * 1000), "font": {"size": 13}},
        "xaxis": {"title": {"text": "time [s]"}}, "yaxis": {"title": {"text": "rpm"}}})
    ui.plot(P + "-plot-u", [
        ui.line(d["tk"], d["uk"], "PWM [%]", ui.COLORS["u"], shape="hv"),
        ui.hline(0, t_end, 100, "100 %", ui.COLORS["lim"]),
        ui.hline(0, t_end, 0, "0 %", ui.COLORS["lim"]),
    ], {"title": {"text": "PWM command", "font": {"size": 13}}, "height": 220,
        "xaxis": {"title": {"text": "time [s]"}}, "yaxis": {"range": [-5, 110]}})

    u_hi = max(d["uk"])
    u_lo = min(d["uk"][1:]) if len(d["uk"]) > 1 else 0
    reach = r <= 100 * K
    checks = [
        ("0.6 &le; &zeta; &le; 0.8", 0.6 <= zeta_a <= 0.8, "&zeta; = %.3g" % zeta_a),
        ("PWM stays inside 0&ndash;100 %", u_hi < 100 - 1e-6 and u_lo > 1e-6,
         "PWM from %.1f to %.1f %%" % (u_lo, u_hi)),
        ("Setpoint reachable (r &le; 100&middot;K)", reach, "max speed %.0f rpm" % (100 * K)),
        ("Zero steady-state error", m["ess_pct"] is not None and abs(m["ess_pct"]) < 1,
         ui.fmt(m["ess_pct"], "%", 2, "not settled")),
        ("Settling time &le; target", m["settling"] is not None and m["settling"] <= tset * 1.05,
         "%s (target %g s)" % (ui.fmt(m["settling"], "s", 3, "not settled"), tset)),
        ("T<sub>s</sub> &le; rise time / 10", m["rise"] is not None and Ts <= m["rise"] / 10,
         "rise %s" % ui.fmt(m["rise"], "s")),
    ]
    rows = "".join("<tr><th>%s</th><td>%s</td><td>%s</td></tr>" % (n, g, ui.badge(ok)) for n, ok, g in checks)
    ui.set_html(P + "-checks",
                "<table class='ctable'>%s</table><p class='theory'>Overshoot %s. The PI zero at s = &minus;K<sub>i</sub>/K<sub>p</sub> "
                "= %.3g adds overshoot beyond the &zeta; formula, so the simulation is the final word.</p>"
                % (rows, ui.fmt(m["overshoot"], "%"), -Ki / Kp if Kp > 0 else float("nan")))

    _code = arduino_code.generate(max(Kp, 0), max(Ki, 0), 0.0, Ts, 0.0, 100.0, True, r,
                                  mode="encoder", units="rpm")
    ui.el(P + "-code").textContent = _code


# ------------------------------------------------------------- step-test fit
def parse_log(text, step_pwm, step_time):
    """Accepts 't,speed' or the sketch's 't,setpoint,speed,u' log."""
    t, y, u = [], [], []
    for line in text.splitlines():
        parts = [p for p in line.replace(";", ",").replace("\t", ",").replace(" ", ",").split(",") if p]
        try:
            vals = [float(p) for p in parts]
        except ValueError:
            continue  # header or junk line
        if len(vals) >= 4:
            t.append(vals[0]); y.append(vals[2]); u.append(vals[3])
        elif len(vals) >= 2:
            t.append(vals[0]); y.append(vals[1])
    if len(t) < 5:
        raise ValueError("Need at least 5 rows of numbers.")
    if u:
        k0 = next((i for i, v in enumerate(u) if v > 0), 0)
        step = u[k0] if u[k0] > 0 else step_pwm
    else:
        k0 = next((i for i, v in enumerate(t) if v >= step_time), 0)
        step = step_pwm
    t0 = t[k0]
    return [v - t0 for v in t[k0:]], y[k0:], step


def fit():
    global _fit
    try:
        t, y, step = parse_log(ui.el(P + "-log").value, read_float(P + "-step", 50), read_float(P + "-steptime", 0.5))
        K, tau = pc.fit_first_order(t, y, step)
        if tau is None:
            raise ValueError("The speed never reached 63 % of its final value.")
    except Exception as exc:
        ui.set_html(P + "-fit-out", "<p class='warn'>Could not fit: %s</p>" % exc)
        return
    _fit = (K, tau)
    model = [y[0] + K * step * (1 - math.exp(-ti / tau)) for ti in t]
    ui.set_html(P + "-fit-out",
                "<p>Fitted <b>K = %.4g rpm/%%</b>, <b>&tau; = %.4g s</b> from a %.4g %% step (63.2 %% method). %s</p>"
                % (K, tau, step, ui.button(P + "-use", "Use these values", "primary")))
    ui.on_click(P + "-use", use_fit)
    ui.plot(P + "-plot-fit", [
        {"x": t, "y": y, "mode": "markers", "type": "scatter", "name": "measured",
         "marker": {"size": 4, "color": ui.COLORS["y"]}},
        ui.line(t, model, "fitted K/(τs+1)", ui.COLORS["ym"]),
    ], {"title": {"text": "Step test vs fitted model", "font": {"size": 13}}, "height": 240,
        "xaxis": {"title": {"text": "time after the step [s]"}}})


def use_fit():
    if _fit:
        ui.el(P + "-K").value = "%.4g" % _fit[0]
        ui.el(P + "-tau").value = "%.4g" % _fit[1]
        if not ui.el(P + "-src").value.strip():
            ui.el(P + "-src").value = "Encoder step test, fitted with the 63.2 % method"
        render()


def example_log():
    """Synthetic log so the fit tool can be tried before the real test.
    Clearly NOT a measurement: replace it with Messi's serial log."""
    import random
    rng = random.Random(4)
    lines = ["t,setpoint,speed,u"]
    for k in range(0, 100):
        tk = k * 0.01
        u = 50.0 if tk >= 0.5 else 0.0
        y = 0.0 if tk < 0.5 else 3.0 * 50 * (1 - math.exp(-(tk - 0.5) / 0.07))
        lines.append("%.3f,0,%.1f,%.1f" % (tk, y + rng.gauss(0, 2.0) if tk >= 0.5 else 0.0, u))
    ui.el(P + "-log").value = "\n".join(lines)


def copy():
    ui.copy_text(_code)
    ui.set_html(P + "-copy-msg", "Copied.")


def _q_zeta():
    def ans():
        res = []
        for z in (0.6, 0.8):
            Kp, Ki = pc.pi_design(DEFAULT_K, DEFAULT_TAU, z, 4 / (z * 0.3))
            d = pc.simulate_digital(pc.FirstOrder(DEFAULT_K, DEFAULT_TAU), Kp, Ki, 0, 0.01, r=200, t_end=1.2,
                                    u_min=0, u_max=100)
            res.append(pc.step_metrics(d["t"], d["y"], 200)["overshoot"])
        return "06", "Overshoot with &zeta; = 0.6: %.1f %%, with &zeta; = 0.8: %.1f %%." % tuple(res)
    return {
        "q": "Same settling-time target (0.3 s). Which design overshoots more: &zeta; = 0.6 or &zeta; = 0.8?",
        "options": [("06", "&zeta; = 0.6"), ("08", "&zeta; = 0.8"), ("same", "The same")],
        "setup": {P + "-zeta": 0.6, P + "-tset": 0.3, P + "-manual": False},
        "answer": ans,
        "explain": "Less damping means more swing. For the wheels that means a speed overshoot that "
                   "the other wheel does not share, so the mouse turns a little at every speed change.",
    }


box = None


def init():
    global box
    box = ui.PredictBox(P, [_q_zeta()], render)
    ui.set_html(P + "-controls", controls_html())
    ui.set_html(P + "-predict", box.html())
    ui.on(P + "-controls", render)
    ui.on_click(P + "-fit", fit)
    ui.on_click(P + "-example", example_log)
    ui.on_click(P + "-copy", copy)
    box.bind()
