"""ENCS4380 Homework 1 — Group Messi — Module 2 (Python/Pyodide).

First-order frequency response for the normalized transfer function:
    H(s) = 1 / (tau*s + 1), input x(t) = sin(omega*t)

M(omega) = 1 / sqrt(1 + (omega*tau)^2)
phi(omega) = -atan(omega*tau), in radians
Output shown is the steady-state sine y(t) = M sin(omega*t + phi).

No NumPy, Matplotlib, third-party chart library, or backend is required.
Python computes every numeric value and generates SVG markup in the browser.
"""

import math


def freq_amplitude_ratio(omega, tau):
    if tau <= 0 or omega < 0:
        raise ValueError("tau must be positive and omega nonnegative")
    return 1.0 / math.hypot(1.0, omega * tau)


def freq_phase_radians(omega, tau):
    if tau <= 0 or omega < 0:
        raise ValueError("tau must be positive and omega nonnegative")
    return -math.atan(omega * tau)


def freq_phase_lag_degrees(omega, tau):
    return -math.degrees(freq_phase_radians(omega, tau))


def freq_cutoff( tau):
    if tau <= 0:
        raise ValueError("tau must be positive")
    return 1.0 / tau


def freq_dynamic_error(omega, tau):
    """Signed fractional amplitude error δ = M - 1 (≤ 0)."""
    return freq_amplitude_ratio(omega, tau) - 1.0


def freq_bode_magnitude_db(omega, tau):
    if omega <= 0:
        raise ValueError("logarithmic Bode plot requires positive omega")
    return -10 * math.log10(1 + (omega * tau) ** 2)


def freq_maximum_tau(frequency_hz, tolerance_percent):
    """At max frequency f, require M≥1−(tolerance%/100), solve for tau."""
    if frequency_hz <= 0 or not (0 < tolerance_percent < 100):
        raise ValueError("frequency > 0 Hz and 0 < error < 100% required")
    lower_bound = 1 - tolerance_percent / 100.0
    return math.sqrt(1 / (lower_bound ** 2) - 1) / (2 * math.pi * frequency_hz)


def freq_validation_results():
    """Homework validation cases 2 and 3: actual, expected, tolerance, units."""
    m = freq_amplitude_ratio(2.0, 0.2)
    phase = freq_phase_lag_degrees(2.0, 0.2)
    tau_max_ms = 1000 * freq_maximum_tau(100.0, 5.0)
    phase_at_50 = freq_phase_lag_degrees(2 * math.pi * 50, tau_max_ms / 1000)
    return {
        "amplitude": (m, 0.93, 0.005, ""),
        "phase": (phase, 21.8, 0.15, "°"),
        "tau": (tau_max_ms, 0.52, 0.01, " ms"),
        "phase50": (phase_at_50, 9.3, 0.10, "°"),
    }


def freq_line(x1, y1, x2, y2, css="chart-grid", extra=""):
    return (f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
            f'class="{css}" {extra}/>')


def freq_text(x, y, text, css="chart-axis", anchor="middle"):
    return (f'<text x="{x:.2f}" y="{y:.2f}" text-anchor="{anchor}" '
            f'class="{css}">{text}</text>')


def freq_svg_curve(transform, n=300):
    """Return a path string made entirely in Python for a normalized t∈[0,1]."""
    parts = []
    for i in range(n + 1):
        px, py = transform(i / n)
        if math.isfinite(px) and math.isfinite(py):
            parts.append(f'{"M" if not parts else "L"}{px:.2f},{py:.2f}')
    return " ".join(parts)


def freq_draw_sine(omega, tau):
    """SVG plot with three input periods and the steady-state lagged output."""
    w, h, left, right, top, bottom = 760, 315, 67, 22, 19, 46
    width, height = w - left - right, h - top - bottom
    period = 2 * math.pi / omega
    end = 3 * period
    x = lambda t: left + width * t / end
    y = lambda value: top + (1.25 - value) / 2.5 * height
    magnitude = freq_amplitude_ratio(omega, tau)
    phase = freq_phase_radians(omega, tau)
    items = []
    for value in (-1, 0, 1):
        yy = y(value)
        items.append(freq_line(left, yy, w - right, yy, "chart-grid major" if value == 0 else "chart-grid"))
        items.append(freq_text(left - 12, yy + 4, str(value), anchor="end"))
    for tick in range(7):
        t = end * tick / 6
        xx = x(t)
        items.append(freq_line(xx, top, xx, h - bottom))
        items.append(freq_text(xx, h - bottom + 21, f"{t:.1f}" if end > 30 else f"{t:.2f}"))
    items.append(freq_text(left, 13, "AMPLITUDE (units)", "chart-axis-label", "start"))
    ideal = freq_svg_curve(lambda q: (x(q * end), y(math.sin(omega * q * end))))
    sensor = freq_svg_curve(lambda q: (x(q * end), y(magnitude * math.sin(omega * q * end + phase))))
    items.append(f'<path d="{ideal}" class="chart-ideal"/>')
    items.append(f'<path d="{sensor}" class="chart-output"/>')
    return "".join(items)


def freq_nice_omega(omega):
    if omega >= 1000:
        return f"{omega:.0f}"
    if omega >= 100:
        return f"{omega:.1f}"
    if omega >= 1:
        return f"{omega:.2f}"
    if omega >= 0.01:
        return f"{omega:.3f}"
    return f"{omega:.4f}"


def freq_draw_bode(tau, omega, kind):
    """Logarithmic angular frequency on x; magnitude or phase on y."""
    if kind not in ("mag", "phase"):
        raise ValueError("kind must be mag or phase")
    w, h, left, right, top, bottom = 560, 295, 72, 20, 26, 54
    width, height = w - left - right, h - top - bottom
    wc = freq_cutoff(tau)
    selected_exp = math.log10(omega / wc)
    low = min(-2, math.floor(2 * selected_exp) / 2 - 0.1)
    high = max(2, math.ceil(2 * selected_exp) / 2 + 0.1)
    x = lambda exponent: left + (exponent - low) / (high - low) * width
    if kind == "mag":
        # Adapt the vertical range so the response stays visible for any slider value.
        minimum = math.floor(freq_bode_magnitude_db(wc * 10**high, tau) / 10) * 10
        minimum = min(-40, minimum)
        y = lambda value: top + (0 - value) / (0 - minimum) * height
        steps = max(4, int(-minimum / 10))
        ticks = [-10 * j for j in range(steps + 1)]
        sample = lambda exponent: freq_bode_magnitude_db(wc * (10**exponent), tau)
    else:
        y = lambda value: top + (0 - value) / 90 * height
        ticks = [0, -30, -60, -90]
        sample = lambda exponent: -freq_phase_lag_degrees(wc * (10**exponent), tau)
    pieces = []
    for value in ticks:
        py = y(value)
        if top - .1 <= py <= h - bottom + .1:
            pieces.append(freq_line(left, py, w - right, py))
            pieces.append(freq_text(left - 11, py + 4, str(value), anchor="end"))
    for exponent in range(math.ceil(low), math.floor(high) + 1):
        px = x(exponent)
        pieces.append(freq_line(px, top, px, h - bottom))
        pieces.append(freq_text(px, h - bottom + 22, freq_nice_omega(wc * 10**exponent)))
    pieces.append(freq_text(left, 13, "GAIN (dB)" if kind == "mag" else "PHASE (°)", "chart-axis-label", "start"))
    pieces.append(freq_text(left + width / 2, h - 8, "ANGULAR FREQUENCY ω (rad/s)", "chart-axis-label"))
    cutoff_x = x(0)
    pieces.append(freq_line(cutoff_x, top, cutoff_x, h - bottom, "chart-mark",
                            'stroke="#c79428" stroke-width="2" stroke-dasharray="5 5"'))
    curve = freq_svg_curve(lambda q: (x(low + (high-low)*q), sample(low + (high-low)*q)))
    pieces.append(f'<path d="{curve}" class="chart-output"/>')
    px, py = x(selected_exp), y(sample(selected_exp))
    pieces.append(f'<circle cx="{px:.2f}" cy="{py:.2f}" r="5" fill="#1685c5" stroke="#fff" stroke-width="2"/>')
    right_aligned = cutoff_x > w - right - 70
    pieces.append(freq_text(cutoff_x - 7 if right_aligned else cutoff_x + 7, top - 7,
                            "ωc", "chart-axis-label", "end" if right_aligned else "start"))
    return "".join(pieces)


def start_frequency_browser_app():
    """Attach Python callbacks to DOM elements via Pyodide JS interop."""
    from js import document
    from pyodide.ffi import create_proxy

    # Store Python proxies for the lifetime of the page.
    callbacks = []

    def el(node_id):
        return document.getElementById(node_id)

    def set_label(node_id, value):
        el(node_id).textContent = str(value)

    def on(node, event_name, callback):
        proxy = create_proxy(callback)
        callbacks.append(proxy)
        node.addEventListener(event_name, proxy)

    def render(event=None):
        tau = float(el("freq-tau").value)
        omega = float(el("freq-omega").value)
        magnitude = freq_amplitude_ratio(omega, tau)
        lag = freq_phase_lag_degrees(omega, tau)
        set_label("freq-tau-value", f"{tau:.2f} s")
        set_label("freq-omega-value", f"{omega:.1f} rad/s")
        set_label("freq-magnitude", f"{magnitude:.3f}")
        set_label("freq-phase", f"{lag:.1f}°")
        set_label("freq-cutoff", f"{freq_cutoff(tau):.2f}")
        set_label("freq-error", f"−{abs(freq_dynamic_error(omega, tau))*100:.1f}%")
        el("frequency-sine-chart").innerHTML = freq_draw_sine(omega, tau)
        el("bode-magnitude-chart").innerHTML = freq_draw_bode(tau, omega, "mag")
        el("bode-phase-chart").innerHTML = freq_draw_bode(tau, omega, "phase")

    def calculate(event=None):
        try:
            f = float(el("calc-frequency").value)
            allowed = float(el("calc-tolerance").value)
            at_frequency = float(el("calc-phase-at").value)
            if at_frequency < 0:
                raise ValueError("phase frequency must be nonnegative")
            tau_max = freq_maximum_tau(f, allowed)
            tau_ms = tau_max * 1000
            set_label("calc-tau-max", f"{tau_ms:.2f} ms" if tau_ms >= 1 else f"{tau_ms:.3f} ms")
            set_label("calc-phase-result", f"{freq_phase_lag_degrees(2*math.pi*at_frequency,tau_max):.2f}°")
        except (ValueError, TypeError):
            set_label("calc-tau-max", "Invalid input")
            set_label("calc-phase-result", "—")

    def validate():
        passed = 0
        for name, (value, expected, tolerance, unit) in freq_validation_results().items():
            digits = 4 if name == "amplitude" else 3 if name == "tau" else 2
            set_label("fv-" + name, f"{value:.{digits}f}{unit}")
            success = abs(value - expected) <= tolerance
            status = el("fv-" + name + "-status")
            status.textContent = "PASS" if success else "FAIL"
            status.className = "test-pass" if success else "test-fail"
            passed += int(success)
        set_label("freq-validation-status", f"{passed} / 4 PASS")

    def reset(event=None):
        el("freq-tau").value = "0.20"
        el("freq-omega").value = "2.0"
        for radio in document.querySelectorAll('input[name="freq-prediction"]'):
            radio.checked = False
        feedback = el("freq-predict-feedback")
        feedback.className = "prediction-feedback"
        feedback.textContent = "Select an answer to test your prediction."
        render()

    def check_prediction(event=None):
        selected = document.querySelector('input[name="freq-prediction"]:checked')
        feedback = el("freq-predict-feedback")
        if selected is None:
            feedback.className = "prediction-feedback try-again"
            feedback.textContent = "Choose a prediction first."
            return
        omega = float(el("freq-omega").value)
        # Move to a known lower value when already at max so a positive change is possible.
        if omega >= 39.9:
            omega = 20
        el("freq-omega").value = str(min(40.0, max(omega + 0.2, omega * 2)))
        render()
        if selected.value == "lower":
            feedback.className = "prediction-feedback success"
            feedback.textContent = ("✓ Correct. Increasing ω reduces output amplitude "
                                    "and increases the phase lag.")
        else:
            feedback.className = "prediction-feedback try-again"
            feedback.textContent = ("Try again. Higher input frequency means "
                                    "more attenuation and greater phase lag.")

    for node_id in ("freq-tau", "freq-omega"):
        on(el(node_id), "input", render)
    for node_id in ("calc-frequency", "calc-tolerance", "calc-phase-at"):
        on(el(node_id), "input", calculate)
    on(el("freq-reset"), "click", reset)
    on(el("freq-example"), "click", reset)
    on(el("freq-predict-check"), "click", check_prediction)
    validate()
    calculate()
    render()
    for node_id in ("freq-tau", "freq-omega", "freq-reset", "freq-example",
                    "calc-frequency", "calc-tolerance", "calc-phase-at", "freq-predict-check"):
        el(node_id).disabled = False


if __name__ == "__main__":
    start_frequency_browser_app()
