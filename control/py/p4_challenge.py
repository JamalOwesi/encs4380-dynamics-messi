"""
P4 - Tuning challenge.
A hidden random plant (the same idea as Homework 1 Module 4, 'Guess the
sensor') and a spec. Tune Kp, Ki, Kd, then press "Check against the spec":
each part of the spec is marked pass or fail and you get a score.
"""

import random

import pid_core as pc
import ui

P = "p4"
state = {"plant": None, "spec": None, "seed": None, "attempts": 0, "best": 0, "revealed": False}


def controls_html():
    return (
        '<div class="group"><h3>Challenge</h3>'
        + ui.select(P + "-level", [("easy", "Easy spec"), ("normal", "Normal spec"), ("hard", "Hard spec")], "normal")
        + '<div class="row">' + ui.button(P + "-new", "New hidden plant", "primary")
        + ui.button(P + "-reveal", "Reveal the plant") + '</div>'
        + '<div id="p4-spec"></div></div>'
        + ui.gain_controls(P, 1, 0, 0, kp_max=20, ki_max=20, kd_max=5)
        + '<div class="row">' + ui.button(P + "-check", "Check against the spec", "primary") + '</div>'
    )


def new_plant(seed=None):
    if seed is None:
        seed = random.randrange(1, 10 ** 6)
    state["seed"] = seed
    state["plant"] = pc.random_plant(seed)
    state["spec"] = pc.make_spec(state["plant"], ui.el(P + "-level").value)
    state["attempts"] = 0
    state["best"] = 0
    state["revealed"] = False
    for cid, v in ((P + "-kp", 1), (P + "-ki", 0), (P + "-kd", 0)):
        ui.set_value(cid, v)
    ui.set_html(P + "-result", "<p class='caption'>Tune the gains, then press <b>Check against the spec</b>.</p>")
    ui.set_html(P + "-plant-info", "Plant #%d is hidden." % seed)
    show_spec()
    render()


def show_spec():
    s = state["spec"]
    ui.set_html(P + "-spec",
                "<ul class='spec'><li>Overshoot &le; <b>%g %%</b></li>"
                "<li>Settling time (2 %%) &le; <b>%g s</b></li>"
                "<li>Zero steady-state error (within %g %%)</li>"
                "<li>Control signal never hits its limit <b>|u| &lt; %g</b></li></ul>"
                % (s["overshoot"], s["settling"], s["ess_pct"], s["u_max"]))


def run():
    plant, spec = state["plant"], state["spec"]
    Kp, Ki, Kd = ui.read_gains(P)
    return pc.simulate_continuous(plant, Kp, Ki, Kd, t_end=spec["t_end"], n_steps=2500,
                                  u_min=-spec["u_max"], u_max=spec["u_max"])


def render():
    if state["plant"] is None:
        return
    spec = state["spec"]
    sim = run()
    t_end = spec["t_end"]
    t = ui.thin(sim["t"])
    shapes = [
        {"type": "rect", "x0": 0, "x1": t_end, "y0": 0.98, "y1": 1.02, "fillcolor": "rgba(22,163,74,0.12)",
         "line": {"width": 0}},
        {"type": "line", "x0": spec["settling"], "x1": spec["settling"], "yref": "paper", "y0": 0, "y1": 1,
         "line": {"color": ui.COLORS["ref"], "dash": "dash"}},
    ]
    ui.plot(P + "-plot-y", [
        ui.line([0, t_end], [1, 1], "setpoint", ui.COLORS["r"], "dash", 1.5),
        ui.line([0, t_end], [1 + spec["overshoot"] / 100] * 2, "overshoot limit", ui.COLORS["lim"], "dot", 1.5),
        ui.line(t, ui.thin(sim["y"]), "output", ui.COLORS["y"]),
    ], {"title": {"text": "Hidden plant: green band = ±2 %, dashed line = settling deadline", "font": {"size": 13}},
        "xaxis": {"title": {"text": "time [s]"}}, "shapes": shapes})
    ui.plot(P + "-plot-u", [
        ui.line(t, ui.thin(sim["u"]), "u", ui.COLORS["u"]),
        ui.hline(0, t_end, spec["u_max"], "limit", ui.COLORS["lim"]),
        ui.hline(0, t_end, -spec["u_max"], "", ui.COLORS["lim"]),
    ], {"title": {"text": "Control signal", "font": {"size": 13}}, "height": 200,
        "xaxis": {"title": {"text": "time [s]"}}, "showlegend": False})


def check():
    sim = run()
    m = pc.step_metrics(sim["t"], sim["y"], 1)
    u_peak = max(abs(v) for v in sim["u"])
    parts, score = pc.grade(state["spec"], m, u_peak)
    state["attempts"] += 1
    state["best"] = max(state["best"], score)
    rows = "".join("<tr><th>%s</th><td>%s</td><td>%s</td></tr>" % (name, got, ui.badge(ok)) for name, ok, got in parts)
    msg = "All four parts pass. Well tuned!" if score == 100 else "Fix the failing parts and check again."
    ui.set_html(P + "-result",
                "<table class='ctable'><tr><th>Spec</th><th>You got</th><th></th></tr>%s</table>"
                "<p class='score'>Score <b>%d / 100</b> &nbsp; attempt %d &nbsp; best %d</p><p>%s</p>"
                % (rows, score, state["attempts"], state["best"], msg))


def reveal():
    p = state["plant"]
    state["revealed"] = True
    ui.set_html(P + "-plant-info", "Plant #%d: <code>%s</code>" % (state["seed"], p.label()))


def _relative_q(gain_id, gain_name):
    """Question about the user's own gains on the hidden plant."""
    def ans():
        plant, spec = state["plant"], state["spec"]
        g = list(ui.read_gains(P))
        idx = {"kp": 0, "ki": 1, "kd": 2}[gain_id]
        base = g[idx]
        out = []
        for factor in (1, 2):
            gg = list(g)
            gg[idx] = base * factor if base > 0 else (0.5 if factor == 2 else 0)
            s = pc.simulate_continuous(plant, gg[0], gg[1], gg[2], t_end=spec["t_end"], n_steps=1500,
                                       u_min=-spec["u_max"], u_max=spec["u_max"])
            out.append(pc.step_metrics(s["t"], s["y"], 1)["overshoot"] or 0)
        verdict = "up" if out[1] > out[0] + 0.5 else ("down" if out[1] < out[0] - 0.5 else "same")
        return verdict, "Now %.1f %%, after doubling %s: %.1f %%. (Your sliders were not changed.)" % (out[0], gain_name, out[1])
    rule = {"kp": "A larger K<sub>p</sub> usually pushes harder and overshoots more.",
            "ki": "A larger K<sub>i</sub> removes the error faster but almost always adds overshoot.",
            "kd": "A larger K<sub>d</sub> usually adds damping and lowers overshoot, until noise or the actuator limit gets in the way."}[gain_id]
    return {
        "q": "On this hidden plant, with your current gains: if you doubled %s, what would the overshoot do?" % gain_name,
        "options": [("up", "Go up"), ("down", "Go down"), ("same", "Barely change")],
        "answer": ans,
        "explain": "Rule of thumb: " + rule + " Rules of thumb can fail on a particular plant, which is why you check.",
    }


box = None


def init():
    global box
    box = ui.PredictBox(P, [_relative_q("ki", "K<sub>i</sub>"), _relative_q("kd", "K<sub>d</sub>"),
                            _relative_q("kp", "K<sub>p</sub>")], lambda: None)
    ui.set_html(P + "-controls", controls_html())
    ui.set_html(P + "-predict", box.html())
    ui.on(P + "-controls", render, events=("input",))
    ui.on_click(P + "-new", lambda: new_plant())
    ui.on_click(P + "-reveal", reveal)
    ui.on_click(P + "-check", check)
    ui.on(P + "-level", lambda: new_plant(state["seed"]), events=("change",), throttle=False)
    box.bind()
    new_plant()
