"""
P1 - PID playground.
Pick a plant (Module 1 first order or Module 3 second order), move Kp, Ki,
Kd and the setpoint step, and watch the output, the control signal with its
limit, and the four step-response numbers.
"""

import pid_core as pc
import ui

P = "p1"


def controls_html():
    return (
        ui.plant_controls(P, "first", K=1, tau=1, wn=2, zeta=0.3)
        + ui.gain_controls(P, 9, 0, 0)
        + '<div class="group"><h3>Step and actuator</h3>'
        + ui.slider(P + "-r", "Setpoint step r", 0.1, 5, 0.1, 1)
        + ui.checkbox(P + "-lim", "Limit the control signal |u| &le; u<sub>max</sub>", True)
        + ui.slider(P + "-umax", "u<sub>max</sub>", 0.5, 100, 0.5, 20)
        + ui.checkbox(P + "-dmeas", "D on the measurement (no kick when r jumps)", True)
        + ui.slider(P + "-tend", "Time window", 1, 30, 0.5, 5, "s")
        + ui.select(P + "-method", [("rk4", "Solver: RK4"), ("euler", "Solver: Euler")], "rk4")
        + '</div>'
    )


def theory_html(plant, Kp, Ki, Kd):
    """Hand formulas for a first-order plant, to compare with the simulation."""
    if plant.kind != "first":
        return ""
    K, tau = plant.K, plant.tau
    if Ki == 0 and Kd == 0 and Kp > 0:
        tcl, ess = pc.p_only_first_order(K, tau, Kp)
        return ("<p class='theory'>Theory (P only): &tau;<sub>cl</sub> = &tau;/(1+KK<sub>p</sub>) = <b>%.3g s</b>, "
                "e<sub>ss</sub> = 1/(1+KK<sub>p</sub>) = <b>%.3g %%</b> of the step.</p>" % (tcl, 100 * ess))
    if Ki > 0 and Kd == 0:
        wn, z = pc.pi_first_order(K, tau, Kp, Ki)
        return ("<p class='theory'>Theory (PI): &omega;<sub>n</sub> = &radic;(KK<sub>i</sub>/&tau;) = <b>%.3g rad/s</b>, "
                "&zeta; = (1+KK<sub>p</sub>)/(2&radic;(&tau;KK<sub>i</sub>)) = <b>%.3g</b>, e<sub>ss</sub> = 0. "
                "(The PI zero adds some overshoot on top of what &zeta; alone predicts.)</p>" % (wn, z))
    return ""


def render():
    plant = ui.read_plant(P)
    Kp, Ki, Kd = ui.read_gains(P)
    r = ui.val(P + "-r")
    limited = ui.is_checked(P + "-lim")
    ui.show(P + "-umax-row", limited)
    umax = ui.val(P + "-umax") if limited else None
    umin = -umax if limited else None
    t_end = ui.val(P + "-tend")
    sim = pc.simulate_continuous(plant, Kp, Ki, Kd, r=r, t_end=t_end, n_steps=3000,
                                 u_min=umin, u_max=umax,
                                 d_on_measurement=ui.is_checked(P + "-dmeas"),
                                 method=ui.el(P + "-method").value)
    t, y, u = sim["t"], sim["y"], sim["u"]
    m = pc.step_metrics(t, y, r)

    # block diagram labels
    ui.set_html(P + "-bd-c", "K<tspan baseline-shift='sub' font-size='9'>p</tspan>=%.3g  K<tspan baseline-shift='sub' font-size='9'>i</tspan>=%.3g  K<tspan baseline-shift='sub' font-size='9'>d</tspan>=%.3g" % (Kp, Ki, Kd))
    ui.set_html(P + "-bd-g", "K/(&#964;s+1)" if plant.kind == "first" else "K&#969;n&#178;/(s&#178;+2&#950;&#969;n s+&#969;n&#178;)")
    ui.set_html(P + "-bd-lim", ("&#177;%g" % umax) if limited else "no limit")

    tt, yy, uu = ui.thin(t), ui.thin(y), ui.thin(u)
    ui.plot(P + "-plot-y", [
        ui.line([0, t_end], [r, r], "setpoint r", ui.COLORS["r"], "dash", 1.5),
        ui.line(tt, yy, "output y", ui.COLORS["y"]),
    ], {"title": {"text": "Output against setpoint", "font": {"size": 13}},
        "xaxis": {"title": {"text": "time [s]"}}})
    traces = [ui.line(tt, uu, "control signal u", ui.COLORS["u"])]
    if limited:
        traces += [ui.hline(0, t_end, umax, "limit", ui.COLORS["lim"]),
                   ui.hline(0, t_end, umin, "", ui.COLORS["lim"])]
        traces[-1]["showlegend"] = False
    ui.plot(P + "-plot-u", traces,
            {"title": {"text": "Control signal u", "font": {"size": 13}},
             "xaxis": {"title": {"text": "time [s]"}}, "height": 230})

    sat = 0
    if limited:
        sat = 100.0 * sum(1 for v in u if abs(v) >= umax - 1e-9) / len(u)
    stable, _ = pc.routh_stable(pc.char_poly(plant, Kp, Ki, Kd))
    if m["unstable"]:
        rows = [("Response", "<span class='bad'>unstable &mdash; it blew up</span>")]
    else:
        rows = [
            ("Rise time (10&ndash;90 %)", ui.fmt(m["rise"], "s")),
            ("Overshoot", ui.fmt(m["overshoot"], "%"),
             "" if m["settled"] else "vs the setpoint (not settled)"),
            ("Settling time (2 %)", ui.fmt(m["settling"], "s", none="not settled in the window")),
            ("Steady-state error", ui.fmt(m["ess"], "", none="&mdash;"),
             ui.fmt(m["ess_pct"], "% of r", 3, "") if m["ess_pct"] is not None else ""),
            ("Peak |u|", ui.fmt(max(abs(v) for v in u), "")),
            ("Time spent at the limit", "%.0f %%" % sat if limited else "no limit"),
        ]
    rows.append(("Routh test (linear loop)", ui.badge(stable, "stable", "unstable")))
    ui.set_html(P + "-metrics", ui.metrics_table(rows) + theory_html(plant, Kp, Ki, Kd))


# ------------------------------------------------------------ predict box
def _q_kp_ess():
    def ans():
        out = []
        for kp in (1, 9):
            s = pc.simulate_continuous(pc.FirstOrder(1, 1), kp, 0, 0, t_end=5)
            out.append(pc.step_metrics(s["t"], s["y"], 1)["ess_pct"])
        return "smaller", "Error with K<sub>p</sub>=1: %.1f %%, with K<sub>p</sub>=9: %.1f %%." % tuple(out)
    return {
        "q": "First-order plant, K = 1, &tau; = 1 s, P only. You raise K<sub>p</sub> from 1 to 9. "
             "What happens to the steady-state error?",
        "options": [("bigger", "It grows"), ("smaller", "It shrinks but stays above zero"),
                    ("zero", "It becomes exactly zero")],
        "setup": {P + "-plant": "first", P + "-K": 1, P + "-tau": 1, P + "-kp": 9,
                  P + "-ki": 0, P + "-kd": 0, P + "-tend": 5, P + "-umax": 20},
        "answer": ans,
        "explain": "With P only, the controller needs an error to make any output: u = K<sub>p</sub>e. "
                   "The error settles at 1/(1+KK<sub>p</sub>), so 50 % becomes 10 %, but never 0.",
    }


def _q_ki():
    def ans():
        s = pc.simulate_continuous(pc.FirstOrder(1, 1), 9, 20, 0, t_end=5, u_min=-20, u_max=20)
        m = pc.step_metrics(s["t"], s["y"], 1)
        return "zero_os", "Error now %.2f %%, overshoot %.1f %%." % (m["ess_pct"], m["overshoot"])
    return {
        "q": "Keep K<sub>p</sub> = 9 and add K<sub>i</sub> = 20. What do you expect?",
        "options": [("same", "Same 10 % error, no change"),
                    ("zero_os", "Zero error, but some overshoot appears"),
                    ("zero_fast", "Zero error and no overshoot")],
        "setup": {P + "-plant": "first", P + "-K": 1, P + "-tau": 1, P + "-kp": 9,
                  P + "-ki": 20, P + "-kd": 0, P + "-tend": 5, P + "-umax": 20},
        "answer": ans,
        "explain": "The integral keeps growing while any error is left, so the error must end at zero. "
                   "The price is a second-order loop that can overshoot (here &zeta; &asymp; 0.71).",
    }


def _q_kd():
    def ans():
        res = []
        for kd in (0, 0.3):
            s = pc.simulate_continuous(pc.SecondOrder(1, 2, 0.3), 5, 3, kd, t_end=10, u_min=-20, u_max=20)
            res.append(pc.step_metrics(s["t"], s["y"], 1)["overshoot"])
        return ("less" if res[1] < res[0] else "more",
                "Overshoot with K<sub>d</sub>=0: %.0f %%, with K<sub>d</sub>=0.3: %.0f %%." % tuple(res))
    return {
        "q": "Second-order plant (&omega;<sub>n</sub> = 2, &zeta; = 0.3) with K<sub>p</sub> = 5, K<sub>i</sub> = 3. "
             "You add K<sub>d</sub> = 0.3. The overshoot will be&hellip;",
        "options": [("more", "Larger"), ("less", "Smaller"), ("same", "About the same")],
        "setup": {P + "-plant": "second", P + "-K": 1, P + "-wn": 2, P + "-zeta": 0.3, P + "-kp": 5,
                  P + "-ki": 3, P + "-kd": 0.3, P + "-tend": 10, P + "-umax": 20},
        "answer": ans,
        "explain": "The D term pushes against the speed of the output. It acts like extra damping, "
                   "so the swing past the setpoint gets smaller.",
    }


def _q_limit():
    def ans():
        res = []
        for um in (100, 2):
            s = pc.simulate_continuous(pc.FirstOrder(1, 1), 20, 0, 0, t_end=3, u_min=-um, u_max=um)
            res.append(pc.step_metrics(s["t"], s["y"], 1)["rise"])
        return "slower", "Rise time with u<sub>max</sub>=100: %.3f s, with u<sub>max</sub>=2: %.3f s." % tuple(res)
    return {
        "q": "P only, K<sub>p</sub> = 20. You lower u<sub>max</sub> from 100 to 2. The rise time will&hellip;",
        "options": [("same", "Stay the same: the gain did not change"), ("slower", "Get longer"),
                    ("faster", "Get shorter")],
        "setup": {P + "-plant": "first", P + "-K": 1, P + "-tau": 1, P + "-kp": 20, P + "-ki": 0,
                  P + "-kd": 0, P + "-lim": True, P + "-umax": 2, P + "-tend": 3},
        "answer": ans,
        "explain": "A big gain asks for a big push, but the actuator cannot deliver more than its limit. "
                   "While u sits on the limit the loop is open, and the plant rises at its own pace.",
    }


box = None


def init():
    global box
    box = ui.PredictBox(P, [_q_kp_ess(), _q_ki(), _q_kd(), _q_limit()], render)
    ui.set_html(P + "-controls", controls_html())
    # wrap the u_max slider so it can be hidden when the limit is off
    node = ui.el(P + "-umax").parentElement
    node.id = P + "-umax-row"
    ui.set_html(P + "-predict", box.html())
    ui.on(P + "-controls", render)
    box.bind()
