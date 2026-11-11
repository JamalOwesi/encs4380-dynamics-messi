"""ENCS4380 — Homework 1, Module 1. Group Messi.

First-order time response, calculated and drawn entirely in Python.
Runs in the browser through Pyodide (no backend) and is importable in CPython
for checking the mathematics without a browser.

Model: tau * dy/dt + y = K*x(t), with y(0)=0 and A=1.
"""

import math

TIME_END = 30.0
AMPLITUDE = 1.0
RESPONSE_GEOM = (760, 315, 66, 26, 20, 42)  # w,h,left,right,top,bottom
ERROR_GEOM = (760, 292, 74, 26, 22, 42)


def step_response(t, gain, tau):
    """Unit-step input x(t)=A, t>=0."""
    return gain * AMPLITUDE * (-math.expm1(-t / tau))


def ramp_response(t, gain, tau):
    """Unit-slope ramp input x(t)=At, t>=0."""
    return gain * AMPLITUDE * (t - tau * (-math.expm1(-t / tau)))


def normalized_transient_error(t, tau):
    """Normalized decaying transient; valid for step and ramp error gap."""
    return math.exp(-t / tau)


def steady_ramp_error(gain, tau):
    return gain * AMPLITUDE * tau


def ramp_error_at(t, gain, tau):
    return steady_ramp_error(gain, tau) * (-math.expm1(-t / tau))


def step_percent(t_multiple):
    """Fraction of final step value at t=t_multiple*tau, in percent."""
    return 100.0 * (-math.expm1(-t_multiple))


def validation_results():
    """Return the two validation results and pass flags (lecture values rounded)."""
    a = step_percent(1)
    b = step_percent(3)
    return ((a, abs(a - 63.2) <= 0.05), (b, abs(b - 95.0) <= 0.05))


def svg_line(x1, y1, x2, y2, css="chart-grid", **attrs):
    extras = " ".join(f'{name.replace("_", "-")}="{value}"' for name, value in attrs.items())
    return (f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
            f'class="{css}" {extras}/>')


def svg_text(x, y, text, css="chart-axis", anchor="middle"):
    return (f'<text x="{x:.2f}" y="{y:.2f}" text-anchor="{anchor}" '
            f'class="{css}">{text}</text>')


def svg_path(fn, count=320):
    parts = []
    for i in range(count + 1):
        t = TIME_END * i / count
        x, y = fn(t)
        if math.isfinite(x) and math.isfinite(y):
            parts.append(f'{"M" if not parts else "L"}{x:.2f},{y:.2f}')
    return " ".join(parts)


def draw_time_response(gain, tau, signal):
    """Generate the full SVG contents for the interactive time response plot."""
    width, height, left, right, top, bottom = RESPONSE_GEOM
    ideal = lambda t: gain * AMPLITUDE * (1.0 if signal == "step" else t)
    model = step_response if signal == "step" else ramp_response
    last_input = ideal(TIME_END)
    y_max = (max(1, math.ceil(gain * 1.25 * 2) / 2)
             if signal == "step" else max(5, math.ceil(last_input * 1.12 / 5) * 5))
    x = lambda tm: left + (width - left - right) * tm / TIME_END
    y = lambda val: top + (height - top - bottom) * (1 - val / y_max)
    pieces = []
    # Grid, time ticks, vertical axis values
    for tick in range(7):
        tm = tick * 5
        pieces.append(svg_line(x(tm), top, x(tm), height - bottom))
        pieces.append(svg_text(x(tm), height - bottom + 21, str(tm)))
    for tick in range(6):
        val = y_max * tick / 5
        pieces.append(svg_line(left, y(val), width - right, y(val),
                               "chart-grid major" if tick == 0 else "chart-grid"))
        display_val = str(int(val)) if float(val).is_integer() else f"{val:.1f}"
        pieces.append(svg_text(left - 11, y(val) + 4, display_val, anchor="end"))
    pieces.append(svg_text(left, 12, "OUTPUT (units)", css="chart-axis-label", anchor="start"))
    pieces.append(f'<path d="{svg_path(lambda tm: (x(tm), y(ideal(tm))))}" class="chart-ideal"/>')
    pieces.append(f'<path d="{svg_path(lambda tm: (x(tm), y(model(tm, gain, tau))))}" class="chart-output"/>')

    if signal == "step":
        for tm, label, fill in ((tau, "63.2% · τ", "#1685c5"),
                                (3 * tau, "95.0% · 3τ", "#d9a22c")):
            px, py = x(tm), y(step_response(tm, gain, tau))
            pieces.append(svg_line(px, top, px, height - bottom, "chart-mark"))
            pieces.append(f'<circle cx="{px:.2f}" cy="{py:.2f}" r="6" '
                          f'fill="{fill}" class="chart-marker-circle"/>')
            end = tm > TIME_END - 7
            pieces.append(svg_text(px - 9 if end else px + 9,
                                   py + 21 if py < 43 else py - 13,
                                   label, "chart-marker-label", "end" if end else "start"))
    else:
        # At a given time, compare the ideal ramp with the delayed output.
        tm = 27.0
        px, y_ideal, y_sensor = x(tm), y(ideal(tm)), y(ramp_response(tm, gain, tau))
        pieces.append(svg_line(px, y_ideal, px, y_sensor, "chart-ramp-gap"))
        pieces.append(f'<circle cx="{px:.2f}" cy="{y_sensor:.2f}" r="5" '
                      'fill="#1685c5" stroke="white" stroke-width="2"/>')
        pieces.append(svg_text(px - 8, y_sensor + 19, "lag", "chart-marker-label", "end"))

    return "".join(pieces)


def draw_error_fraction(tau):
    """SVG contents for E(t)=exp(-t/tau) on a log-vertical axis (1 to 1e-4)."""
    width, height, left, right, top, bottom = ERROR_GEOM
    x = lambda tm: left + (width - left - right) * tm / TIME_END
    log_min = math.log(10000)
    y = lambda log_e: top + (height - top - bottom) * (-log_e) / log_min
    pieces = []
    for tick in range(7):
        tm = tick * 5
        pieces.append(svg_line(x(tm), top, x(tm), height - bottom))
        pieces.append(svg_text(x(tm), height - bottom + 22, str(tm)))
    for i in range(5):
        py = top + (height - top - bottom) * i / 4
        pieces.append(svg_line(left, py, width - right, py))
        pieces.append(svg_text(left - 11, py + 4, "1" if i == 0 else f"10⁻{i}", anchor="end"))
    pieces.append(svg_text(left, 12, "ERROR FRACTION (log scale)", "chart-axis-label", "start"))
    # Stop at 10^-4: never fake a flat tail below the visible range.
    max_time = min(TIME_END, tau * log_min)
    pts = []
    for i in range(251):
        tm = max_time * i / 250
        pts.append(f'{"M" if not pts else "L"}{x(tm):.2f},{y(-tm / tau):.2f}')
    pieces.append(f'<path d="{" ".join(pts)}" class="chart-output"/>')
    pieces.append(f'<circle cx="{x(0):.2f}" cy="{y(0):.2f}" r="5" fill="#1685c5"/>')
    return "".join(pieces)


def start_browser_app():
    """Connect Python to browser controls. Only runs under Pyodide."""
    from js import document
    from pyodide.ffi import create_proxy

    listeners = []  # Keep references alive; otherwise Pyodide event proxies get collected.

    def element(element_id):
        return document.getElementById(element_id)

    def change_text(element_id, value):
        element(element_id).textContent = str(value)

    def attach(dom_node, event_name, handler):
        proxy = create_proxy(handler)
        listeners.append(proxy)
        dom_node.addEventListener(event_name, proxy)

    def current_values():
        gain = float(element("gain").value)
        tau = float(element("tau").value)
        signal = "ramp" if bool(element("input-ramp").checked) else "step"
        return gain, tau, signal

    def render(event=None):
        gain, tau, signal = current_values()
        change_text("gain-readout", f"{gain:.1f}")
        change_text("tau-readout", f"{tau:.1f} s")
        change_text("response-subtitle", f"· {signal} input")
        element("response-chart").innerHTML = draw_time_response(gain, tau, signal)
        element("error-chart").innerHTML = draw_error_fraction(tau)
        change_text("slope-readout", f"Slope = −{1 / tau:.3f} s⁻¹")
        if signal == "step":
            change_text("metric-one-title", "AT t = τ")
            change_text("metric-one", f"{step_percent(1):.1f}%")
            change_text("metric-one-detail", "of the final step value")
            change_text("metric-two-title", "AT t = 3τ")
            change_text("metric-two", f"{step_percent(3):.1f}%")
            change_text("metric-two-detail", "of the final step value")
            change_text("metric-three-title", "FINAL VALUE")
            change_text("metric-three", f"{gain * AMPLITUDE:.2f}")
            change_text("metric-three-detail", "K × step amplitude")
            change_text("response-caption", "At τ: 63.2% of KA. At 3τ: 95.0% of KA.")
        else:
            change_text("metric-one-title", "RAMP TIME LAG")
            change_text("metric-one", f"{tau:.1f} s")
            change_text("metric-one-detail", "approaches τ at steady state")
            change_text("metric-two-title", "STEADY-STATE ERROR")
            change_text("metric-two", f"{steady_ramp_error(gain, tau):.2f}")
            change_text("metric-two-detail", "vertical error = KAτ")
            change_text("metric-three-title", "ERROR AT 30 s")
            change_text("metric-three", f"{ramp_error_at(TIME_END, gain, tau):.2f}")
            change_text("metric-three-detail", "Kx(30) − y(30)")
            change_text("response-caption", "The ideal ramp is KAt. The steady-state time lag approaches τ.")
        (r1, pass1), (r2, pass2) = validation_results()
        change_text("test-one-result", f"{r1:.2f}% of KA")
        change_text("test-two-result", f"{r2:.2f}% of KA")
        for ident, passed in (("one", pass1), ("two", pass2)):
            node = element(f"test-{ident}-status")
            node.textContent = "PASS" if passed else "FAIL"
            node.className = "test-pass" if passed else "test-fail"
        change_text("validation-status", f"{int(pass1) + int(pass2)} / 2 PASSED")

    def reset(event=None):
        element("gain").value = "1"
        element("tau").value = "4"
        element("input-step").checked = True
        for item in document.querySelectorAll('input[name="prediction"]'):
            item.checked = False
        feedback = element("prediction-feedback")
        feedback.className = "prediction-feedback"
        feedback.textContent = "Choose an answer to test your intuition."
        render()

    def check_prediction(event=None):
        choice = document.querySelector('input[name="prediction"]:checked')
        feedback = element("prediction-feedback")
        if choice is None:
            feedback.className = "prediction-feedback try-again"
            feedback.textContent = "Choose an answer first."
            return
        old_tau = float(element("tau").value)
        # At the upper limit, first move down so the test can demonstrate an increase.
        if old_tau > 6.5:
            element("tau").value = "6.0"
            old_tau = 6.0
        element("tau").value = str(min(8.0, round(old_tau + 1.5, 1)))
        render()
        if choice.value == "slower":
            feedback.className = "prediction-feedback success"
            feedback.textContent = ("✓ Correct! Increasing τ slows the sensor. "
                                    "For a step, the final value KA stays the same.")
        else:
            feedback.className = "prediction-feedback try-again"
            feedback.textContent = ("The correct answer is 'more slowly'. "
                                    "A larger τ changes response speed, not the final step value.")

    attach(element("gain"), "input", render)
    attach(element("tau"), "input", render)
    attach(element("input-step"), "change", render)
    attach(element("input-ramp"), "change", render)
    attach(element("reset"), "click", reset)
    attach(element("check-prediction"), "click", check_prediction)
    for selector in ('gain', 'tau', 'input-step', 'input-ramp', 'reset', 'check-prediction'):
        element(selector).disabled = False
    render()


if __name__ == "__main__":
    start_browser_app()
