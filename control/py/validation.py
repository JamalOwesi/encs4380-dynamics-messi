"""
Validation - the three checks from section 2.1 of the homework, computed with
our own solver and compared with the hand formulas. Plant K/(tau s + 1),
K = 1, tau = 1 s.
"""

import math
import random

import pid_core as pc
import ui

P = "val"


def render():
    plant = pc.FirstOrder(1, 1)
    rows = []

    # Check 1: P only, Kp = 9
    s1 = pc.simulate_continuous(plant, 9, 0, 0, t_end=2.0, n_steps=4000)
    tau_sim = pc.time_constant_from_response(s1["t"], s1["y"])
    ess_sim = pc.step_metrics(s1["t"], s1["y"], 1)["ess_pct"]
    s1e = pc.simulate_continuous(plant, 9, 0, 0, t_end=2.0, n_steps=4000, method="euler")
    tau_e = pc.time_constant_from_response(s1e["t"], s1e["y"])
    ok1 = abs(tau_sim - 0.1) < 0.002 and abs(ess_sim - 10) < 0.05
    rows.append(("1. P only, K<sub>p</sub> = 9",
                 "&tau;<sub>cl</sub> = 0.1 s, e<sub>ss</sub> = 10 %",
                 "&tau;<sub>cl</sub> = %.4f s (Euler %.4f s), e<sub>ss</sub> = %.3f %%" % (tau_sim, tau_e, ess_sim), ok1))

    # Check 2: PI, Kp = 1, Ki = 1
    wn, zeta = pc.pi_first_order(1, 1, 1, 1)
    poly = pc.char_poly(plant, 1, 1, 0)
    s2 = pc.simulate_continuous(plant, 1, 1, 0, t_end=8.0, n_steps=4000)
    m2 = pc.step_metrics(s2["t"], s2["y"], 1)
    err = max(abs(y - (1 - math.exp(-t))) for t, y in zip(s2["t"], s2["y"]))
    wn_p = math.sqrt(poly[2] / poly[0])
    zeta_p = poly[1] / (2 * wn_p * poly[0])
    ok2 = abs(wn - 1) < 1e-9 and abs(zeta - 1) < 1e-9 and abs(wn_p - 1) < 1e-9 and abs(zeta_p - 1) < 1e-9 \
        and err < 1e-3 and m2["overshoot"] < 0.1
    rows.append(("2. PI, K<sub>p</sub> = 1, K<sub>i</sub> = 1",
                 "&omega;<sub>n</sub> = 1 rad/s, &zeta; = 1",
                 "formula: &omega;<sub>n</sub> = %.4g, &zeta; = %.4g; from s&sup2;+%.3gs+%.3g: &omega;<sub>n</sub> = %.4g, &zeta; = %.4g; "
                 "simulation overshoot %.3f %%, max |y &minus; (1&minus;e<sup>&minus;t</sup>)| = %.1e"
                 % (wn, zeta, poly[1], poly[2], wn_p, zeta_p, m2["overshoot"], err), ok2))

    # Check 3: any PI -> zero steady-state error
    rng = random.Random(7)
    worst = 0.0
    trials = []
    for _ in range(10):
        Kp, Ki = round(rng.uniform(0.2, 10), 2), round(rng.uniform(0.2, 10), 2)
        w, z = pc.pi_first_order(1, 1, Kp, Ki)
        t_end = 10.0 / (min(z, 1.0) * w) * (2 * z if z > 1 else 1) + 2
        s = pc.simulate_continuous(plant, Kp, Ki, 0, t_end=t_end, n_steps=3000)
        e = abs(1 - s["y"][-1]) * 100
        worst = max(worst, e)
        trials.append("(%g, %g): %.2g %%" % (Kp, Ki, e))
    ok3 = worst < 0.1
    rows.append(("3. Any PI controller",
                 "e<sub>ss</sub> = 0 for a step",
                 "10 random (K<sub>p</sub>, K<sub>i</sub>) pairs, worst |e<sub>ss</sub>| = %.2g %%<br><span class='caption'>%s</span>"
                 % (worst, "; ".join(trials)), ok3))

    html = ["<table class='ctable'><tr><th>Check</th><th>Expected</th><th>Our solver</th><th></th></tr>"]
    for name, exp, got, ok in rows:
        html.append("<tr><th>%s</th><td>%s</td><td>%s</td><td>%s</td></tr>" % (name, exp, got, ui.badge(ok)))
    html.append("</table>")
    passed = sum(1 for r in rows if r[3])
    html.append("<p class='score'>%d of 3 checks pass.</p>" % passed)
    ui.set_html(P + "-table", "".join(html))

    ui.plot(P + "-plot1", [
        ui.line(ui.thin(s1["t"]), ui.thin(s1["y"]), "y, K<sub>p</sub> = 9 (RK4)", ui.COLORS["y"]),
        ui.line([0, 2], [0.9, 0.9], "0.9 (10 % error)", ui.COLORS["r"], "dash", 1.5),
        ui.line([0.1, 0.1], [0, 0.9 * 0.632], "τ = 0.1 s", ui.COLORS["lim"], "dot", 1.5),
    ], {"title": {"text": "Check 1", "font": {"size": 13}}, "height": 250, "xaxis": {"title": {"text": "time [s]"}}})
    ui.plot(P + "-plot2", [
        ui.line(ui.thin(s2["t"]), ui.thin(s2["y"]), "y, PI (solver)", ui.COLORS["y"]),
        ui.line(ui.thin(s2["t"]), [1 - math.exp(-t) for t in ui.thin(s2["t"])], "1 − e^(−t)", ui.COLORS["ym"], "dot"),
    ], {"title": {"text": "Check 2", "font": {"size": 13}}, "height": 250, "xaxis": {"title": {"text": "time [s]"}}})


def init():
    ui.on_click(P + "-run", render)
