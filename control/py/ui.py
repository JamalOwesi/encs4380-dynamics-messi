"""
ui.py - small helpers shared by the Control modules.

Same approach as Homework 1: Python talks to the page through `from js import
document`. Controls are built as HTML strings, events are bound with
create_proxy, and plots are drawn with Plotly.
"""

from js import document, window, Object, Plotly
from pyodide.ffi import create_proxy, to_js

COLORS = {               # matched to Homework 1's style.css
    "r": "#7d8aa0",      # setpoint (dashed grey, like chart-ideal)
    "y": "#19c6ff",      # true output (cyan, like chart-output)
    "ym": "#d9a22c",     # sensor reading (gold)
    "u": "#b18cff",      # control signal (violet)
    "lim": "#ff4d63",    # limits (red)
    "ref": "#2fe39a",    # reference / continuous (green)
    "i": "#7ee0c3",      # integral term
}

_keep = []  # keep proxies alive (otherwise Pyodide frees them)


# ---------------------------------------------------------------- DOM access
def el(i):
    return document.getElementById(i)


def val(i):
    return float(el(i).value)


def is_checked(i):
    return bool(el(i).checked)


def radio(name):
    node = document.querySelector('input[name="%s"]:checked' % name)
    return node.value if node else None


def set_html(i, s):
    el(i).innerHTML = s


def show(i, visible=True):
    el(i).style.display = "" if visible else "none"


def set_value(i, v):
    """Set a control's value (slider, checkbox or radio) without firing events."""
    node = el(i)
    if node is None:  # radio group given by name
        for r in document.querySelectorAll('input[name="%s"]' % i):
            r.checked = (r.value == str(v))
        return
    if node.type == "checkbox":
        node.checked = bool(v)
    else:
        node.value = str(v)
    window.syncOutputs()


# ------------------------------------------------------------ control markup
def slider(i, label, mn, mx, step, value, unit=""):
    return ('<label><span class="lab">%s</span><input type="range" id="%s" min="%s" max="%s" step="%s" value="%s">'
            '<span class="val"><output id="%s-out">%s</output>%s</span></label>'
            % (label, i, mn, mx, step, value, i, value, (" " + unit) if unit else ""))


def checkbox(i, label, checked=False):
    return ('<label><input type="checkbox" id="%s"%s><span class="lab">%s</span></label>'
            % (i, " checked" if checked else "", label))


def radios(name, options, selected):
    parts = []
    for value, label in options:
        parts.append('<label><input type="radio" name="%s" value="%s"%s><span class="lab">%s</span></label>'
                     % (name, value, " checked" if value == selected else "", label))
    return '<div class="radios">%s</div>' % "".join(parts)


def select(i, options, selected):
    opts = "".join('<option value="%s"%s>%s</option>' % (v, " selected" if v == selected else "", l)
                   for v, l in options)
    return '<label><select id="%s">%s</select></label>' % (i, opts)


def button(i, label, cls=""):
    """cls: "primary" = Homework 1's red button, anything else = grey 'ghost' button."""
    css = "" if cls == "primary" else "ghost"
    if "small" in cls:
        css += " small"
    return '<button id="%s" class="%s">%s</button>' % (i, css.strip(), label)


def plant_controls(prefix, kind="first", K=1.0, tau=1.0, wn=2.0, zeta=0.3):
    """Plant picker reused by P1-P3: first order (Module 1) or second order (Module 3)."""
    return (
        '<div class="group"><h3>Plant</h3>'
        + radios(prefix + "-plant", [("first", "First order K/(&tau;s+1)"),
                                     ("second", "Second order (Module 3)")], kind)
        + slider(prefix + "-K", "K", 0.1, 5, 0.05, K)
        + '<div id="%s-first">' % prefix
        + slider(prefix + "-tau", "&tau;", 0.05, 5, 0.05, tau, "s")
        + '</div><div id="%s-second">' % prefix
        + slider(prefix + "-wn", "&omega;<sub>n</sub>", 0.5, 10, 0.1, wn, "rad/s")
        + slider(prefix + "-zeta", "&zeta;", 0.05, 2, 0.01, zeta)
        + '</div></div>'
    )


def read_plant(prefix):
    import pid_core as pc
    kind = radio(prefix + "-plant")
    show(prefix + "-first", kind == "first")
    show(prefix + "-second", kind == "second")
    return pc.make_plant(kind, val(prefix + "-K"), val(prefix + "-tau"),
                         val(prefix + "-wn"), val(prefix + "-zeta"))


def gain_controls(prefix, Kp, Ki, Kd, kp_max=50, ki_max=50, kd_max=5):
    return (
        '<div class="group"><h3>PID gains</h3>'
        + slider(prefix + "-kp", "K<sub>p</sub>", 0, kp_max, 0.05, Kp)
        + slider(prefix + "-ki", "K<sub>i</sub>", 0, ki_max, 0.05, Ki)
        + slider(prefix + "-kd", "K<sub>d</sub>", 0, kd_max, 0.01, Kd)
        + '</div>'
    )


def read_gains(prefix):
    return val(prefix + "-kp"), val(prefix + "-ki"), val(prefix + "-kd")


# ------------------------------------------------------------------- events
def on(i, fn, events=("input", "change"), throttle=True):
    """Call fn() when the element (or anything inside it) changes.
    With throttle=True a burst of slider events gives one redraw per frame."""
    state = {"pending": False}

    def run(*_):
        state["pending"] = False
        fn()

    run_p = create_proxy(run)

    def handler(evt):
        if not throttle:
            fn()
            return
        if not state["pending"]:
            state["pending"] = True
            window.requestAnimationFrame(run_p)

    h = create_proxy(handler)
    _keep.extend([run_p, h])
    for ev in events:
        el(i).addEventListener(ev, h)


def on_click(i, fn):
    h = create_proxy(lambda evt: fn())
    _keep.append(h)
    el(i).addEventListener("click", h)


def copy_text(text):
    window.copyToClipboard(text)


# -------------------------------------------------------------------- plots
def _js(obj):
    return to_js(obj, dict_converter=Object.fromEntries)


def _merge(base, extra):
    for k, v in (extra or {}).items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _merge(base[k], v)
        else:
            base[k] = v
    return base


def plot(div, traces, layout=None):
    base = {
        "margin": {"l": 52, "r": 14, "t": 62, "b": 44},
        "title": {"x": 0.01, "xanchor": "left", "y": 0.97, "yanchor": "top",
                  "font": {"size": 11, "family": "Orbitron, sans-serif", "color": "#19c6ff"}},
        "font": {"family": "Rajdhani, system-ui, sans-serif", "size": 13, "color": "#e6ebf2"},
        "legend": {"orientation": "h", "y": 1.02, "yanchor": "bottom", "x": 0, "font": {"color": "#c7d0dd"}},
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0.35)",
        "xaxis": {"gridcolor": "rgba(255,255,255,0.08)", "zeroline": False, "linecolor": "#4b5a70",
                  "tickfont": {"color": "#8693a8"}},
        "yaxis": {"gridcolor": "rgba(255,255,255,0.08)", "zeroline": False, "linecolor": "#4b5a70",
                  "tickfont": {"color": "#8693a8"}},
        "height": 300,
    }
    _merge(base, layout)
    el(div).style.height = "%dpx" % base["height"]
    Plotly.react(div, _js(traces), _js(base),
                 _js({"responsive": True, "displayModeBar": False}))


def line(x, y, name, color, dash="solid", width=2, shape="linear", **extra):
    tr = {"x": x, "y": y, "name": name, "mode": "lines", "type": "scatter",
          "line": {"color": color, "dash": dash, "width": width, "shape": shape}}
    tr.update(extra)
    return tr


def hline(x0, x1, yv, name, color, dash="dash"):
    return line([x0, x1], [yv, yv], name, color, dash, 1.5)


def thin(x, n=1200):
    """Keep at most ~n points per trace (faster plots on phones)."""
    step = max(1, len(x) // n)
    return x[::step]


# ------------------------------------------------------------------ formats
def fmt(v, unit="", digits=3, none="&mdash;"):
    if v is None:
        return none
    return ("%." + str(digits) + "g%s") % (v, (" " + unit) if unit else "")


def metrics_table(rows):
    """rows: list of (name, value_html[, note_html]) -> Homework 1 style metric tiles."""
    out = ['<div class="metrics">']
    for row in rows:
        note = row[2] if len(row) > 2 else ""
        out.append('<div class="metric"><b>%s</b><span class="big">%s</span><small>%s</small></div>'
                   % (row[0], row[1], note))
    out.append("</div>")
    return "".join(out)


def badge(ok, yes="PASS", no="FAIL"):
    return '<b class="%s">%s</b>' % ("test-pass" if ok else "test-fail", yes if ok else no)


# ------------------------------------------------------- "Predict, then check"
class PredictBox:
    """A question, a few answers, and a button that runs the simulator.

    Each question is a dict:
      q        question text (HTML)
      options  list of (value, label)
      setup    dict control-id -> value, applied before the check (optional)
      answer   a value, or a function () -> (value, detail_html) that runs
               the simulator and reports what really happened
      explain  why (HTML)
    """

    def __init__(self, prefix, questions, rerender):
        self.p = prefix
        self.qs = questions
        self.i = 0
        self.rerender = rerender

    def html(self):
        p = self.p
        return ('<section class="card predict"><h3>Predict, then check <span id="%s-pn" class="caption"></span></h3>'
                '<div id="%s-pq"></div><div id="%s-po"></div>'
                '<div class="row">%s %s</div>'
                '<div id="%s-pa" class="prediction-feedback">Choose an answer to test your intuition.</div></section>'
                % (p, p, p, button(p + "-pc", "Check", "primary"), button(p + "-px", "Next question"), p))

    def bind(self):
        on_click(self.p + "-pc", self.check)
        on_click(self.p + "-px", self.next)
        self.load()

    def load(self):
        q = self.qs[self.i]
        p = self.p
        set_html(p + "-pn", "(%d of %d)" % (self.i + 1, len(self.qs)))
        set_html(p + "-pq", "<p>%s</p>" % q["q"])
        set_html(p + "-po", "".join(
            '<label><input type="radio" name="%s-pr" value="%s"><span class="lab">%s</span></label>'
            % (p, v, l) for v, l in q["options"]))
        set_html(p + "-pa", "Choose an answer to test your intuition.")
        el(p + "-pa").className = "prediction-feedback"

    def next(self):
        self.i = (self.i + 1) % len(self.qs)
        self.load()

    def check(self):
        q = self.qs[self.i]
        guess = radio(self.p + "-pr")
        if guess is None:
            set_html(self.p + "-pa", "Pick an answer first, then check it.")
            el(self.p + "-pa").className = "prediction-feedback try-again"
            return
        for cid, v in (q.get("setup") or {}).items():
            set_value(cid, v)
        self.rerender()
        detail = ""
        ans = q["answer"]
        if callable(ans):
            ans, detail = ans()
        right = (guess == ans)
        label = dict(q["options"]).get(ans, ans)
        el(self.p + "-pa").className = "prediction-feedback " + ("success" if right else "try-again")
        set_html(self.p + "-pa",
                 "<p>%s The simulator says: <b>%s</b>. %s</p><p class='explain'>%s</p>"
                 % ("Correct!" if right else "Not quite.", label, detail, q["explain"]))
