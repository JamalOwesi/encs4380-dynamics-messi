"""ENCS4380 Homework 1, Group Messi — Module 4: Guess the Sensor.

Python implementation for the Pyodide-powered static website.
All sensor mathematics, random challenges, SVG graphs, guessing, reveal,
and session scores are implemented here (not in JavaScript).

First-order step: y(t) = K * (1 - exp(-t/tau))
First-order sine: steady-state y(t) = K*M*sin(omega*t + phase)
                M = 1/sqrt(1+(omega*tau)^2), phase = -atan(omega*tau)
Second-order step (0<zeta<1): normalized unit-step response.
"""
from dataclasses import dataclass
import math
import random
import html


@dataclass(frozen=True)
class Sensor:
    kind: str                    # 'first' or 'second'
    signal: str = 'step'          # 'step' or 'sine'
    K: float = 1.0
    tau: float = 3.0
    omega: float = 1.2
    zeta: float = 0.5
    wn: float = 2.0


def sensor_response(t, sensor):
    """Closed-form output for a unit step, or steady-state unit sine."""
    if sensor.kind == 'first':
        if sensor.signal == 'sine':
            mag = 1.0 / math.sqrt(1 + (sensor.omega * sensor.tau) ** 2)
            phase = -math.atan(sensor.omega * sensor.tau)
            return sensor.K * mag * math.sin(sensor.omega * t + phase)
        return sensor.K * (-math.expm1(-max(t, 0.0) / sensor.tau))
    if sensor.kind == 'second':
        # Random second-order challenges are underdamped (0 < zeta < 1).
        wd = sensor.wn * math.sqrt(1 - sensor.zeta ** 2)
        a = sensor.zeta * sensor.wn
        return 1 - math.exp(-a * max(t, 0.0)) * (
            math.cos(wd * max(t, 0.0)) + (a / wd) * math.sin(wd * max(t, 0.0)))
    raise ValueError('Unknown sensor kind')


def generate_sensor(rng=None, kind=None, signal=None):
    rng = rng or random
    kind = kind or ('first' if rng.random() < .5 else 'second')
    if kind == 'first':
        signal = signal or ('sine' if rng.random() < .4 else 'step')
        return Sensor('first', signal=signal, K=round(rng.uniform(.85, 2.15), 2),
                      tau=round(rng.uniform(.85, 3.25) if signal == 'sine'
                                else rng.uniform(1.6, 5.5), 2),
                      omega=round(rng.uniform(.9, 1.9), 2))
    if kind == 'second':
        return Sensor('second', signal='step',
                      zeta=round(rng.uniform(.28, .73), 2),
                      wn=round(rng.uniform(1.3, 3.6), 2))
    raise ValueError('kind must be first or second')


def observed_curve(sensor, rng=None, samples=260):
    """Produce reproducible-in-round noisy samples; noise is small and unbiased."""
    rng = rng or random
    horizon = 22.0 if sensor.kind == 'first' else 14.0
    clean = [(horizon * i / samples,
              sensor_response(horizon * i / samples, sensor))
             for i in range(samples + 1)]
    size = sensor.K if sensor.kind == 'first' else 1.0
    noisy = [(t, y + size * (rng.random()+rng.random()+rng.random()-1.5)*.014)
             for t, y in clean]
    return horizon, clean, noisy


def parameter_names(sensor):
    return ('K', 'tau') if sensor.kind == 'first' else ('zeta', 'wn')


def relative_errors(sensor, estimates):
    return [abs(estimates[name] - getattr(sensor, name)) / getattr(sensor, name)
            for name in parameter_names(sensor)]


def calculate_score(sensor, estimates):
    """All estimates within 10% -> full 100; smooth partial otherwise."""
    errors = relative_errors(sensor, estimates)
    perfect = all(error <= .1 + 1e-10 for error in errors)
    if perfect:
        return 100, True, errors
    def partial(error):
        return 100 if error <= .1 else 100 * math.exp(-3.2 * (error - .1))
    return round(sum(partial(error) for error in errors) / len(errors)), False, errors


def guess_model(sensor, estimates):
    """Overlay guessed parameters using the same known model family/input."""
    if sensor.kind == 'first':
        return Sensor('first', signal=sensor.signal, K=estimates['K'],
                      tau=estimates['tau'], omega=sensor.omega)
    return Sensor('second', zeta=estimates['zeta'], wn=estimates['wn'])


def get_hint(sensor):
    if sensor.kind == 'second':
        return ('For an underdamped sensor, overshoot Mp = exp(−πζ/√(1−ζ²)). '
                'From the first peak time tp, ωn = π/(tp√(1−ζ²)).')
    if sensor.signal == 'sine':
        return ('Compare the output sine with the visible input sine. If its time lag '
                'is Δt, then |φ| = ωΔt, τ = tan(|φ|)/ω, and K = output amplitude/M.')
    return ('Estimate K from the final height. The time when the noisy output reaches '
            'about 63.2% of this height estimates τ.')


# Python-generated SVG: no external charting dependency.
GRAPH = {'w': 760, 'h': 340, 'l': 62, 'r': 22, 't': 26, 'b': 47}
CH_COLORS = {'noise': '#137cb4', 'input': '#6f91a5',
          'guess': '#d1a02c', 'truth': '#10977f'}


def challenge_svg(horizon, clean, noisy, sensor, estimated=None):
    g = GRAPH
    w, h, l, r, top, bottom = (g[k] for k in ('w','h','l','r','t','b'))
    guess_points = [(t, sensor_response(t, estimated)) for t, _ in clean] if estimated else []
    sine_points = ([(t, math.sin(sensor.omega * t)) for t, _ in clean]
                   if sensor.signal == 'sine' else [])
    values = [y for _, y in noisy + clean + guess_points + sine_points]
    extreme = max(max(map(abs, values), default=0), .25)
    minimum = -extreme * 1.2 if sensor.signal == 'sine' else -max(.1, extreme * .12)
    maximum = extreme * 1.2
    X = lambda time: l + (w-l-r) * time / horizon
    Y = lambda value: top + (h-top-bottom) * (maximum-value) / (maximum-minimum)
    path = lambda points: ' '.join(('M' if i==0 else 'L') + f'{X(t):.2f},{Y(v):.2f}'
                                   for i,(t,v) in enumerate(points))
    parts = []
    for i in range(6):
        tm, v = horizon*i/5, minimum+(maximum-minimum)*i/5
        parts.append(f'<line x1="{X(tm):.2f}" x2="{X(tm):.2f}" y1="{top}" y2="{h-bottom}" class="chart-grid"/>')
        parts.append(f'<text x="{X(tm):.2f}" y="{h-bottom+21}" text-anchor="middle" class="chart-axis">{tm:.1f}</text>')
        parts.append(f'<line x1="{l}" x2="{w-r}" y1="{Y(v):.2f}" y2="{Y(v):.2f}" class="chart-grid"/>')
        parts.append(f'<text x="{l-10}" y="{Y(v)+4:.2f}" text-anchor="end" class="chart-axis">{v:.1f}</text>')
    parts.append(f'<text x="{l}" y="14" class="chart-axis-label">SENSOR OUTPUT</text>')
    parts.append(f'<text x="{w-r}" y="{h-5}" text-anchor="end" class="chart-axis-label">TIME (s)</text>')
    if sine_points:
        parts.append(f'<path d="{path(sine_points)}" fill="none" stroke="{CH_COLORS["input"]}" stroke-width="2.3" stroke-dasharray="6 5"/>')
    parts.append(f'<path d="{path(noisy)}" fill="none" stroke="{CH_COLORS["noise"]}" stroke-width="2.3" opacity=".88" stroke-linecap="round" stroke-linejoin="round"/>')
    if estimated:
        parts.append(f'<path d="{path(guess_points)}" fill="none" stroke="{CH_COLORS["guess"]}" stroke-width="2.7" stroke-dasharray="8 5"/>')
        parts.append(f'<path d="{path(clean)}" fill="none" stroke="{CH_COLORS["truth"]}" stroke-width="3.1"/>')
    return ''.join(parts)


class ChallengeSession:
    """Single-page game state. No persistence outside the current browser session."""
    def __init__(self, rng=None):
        self.rng = rng or random.Random()
        self.round_number = 0
        self.rounds_scored = 0
        self.total_score = 0
        self.perfect_rounds = 0
        self.new_round()

    def new_round(self, kind=None, signal=None):
        self.round_number += 1
        self.true_sensor = generate_sensor(self.rng, kind, signal)
        self.horizon, self.clean, self.noisy = observed_curve(self.true_sensor, self.rng)
        self.estimated_sensor = None
        self.submitted = False
        self.last_result = None
        return self.true_sensor

    def submit(self, estimates):
        if self.submitted:
            raise RuntimeError('This round has already been scored')
        keys = parameter_names(self.true_sensor)
        ranges = {'K': (.1, 5), 'tau': (.2, 20), 'zeta': (.05, .95), 'wn': (.3, 10)}
        if not all(k in estimates and math.isfinite(estimates[k]) and
                   ranges[k][0] <= estimates[k] <= ranges[k][1] for k in keys):
            raise ValueError('Enter valid values for all displayed parameters')
        score, perfect, errors = calculate_score(self.true_sensor, estimates)
        self.estimated_sensor = guess_model(self.true_sensor, estimates)
        self.submitted = True
        self.rounds_scored += 1
        self.total_score += score
        self.perfect_rounds += int(perfect)
        self.last_result = (score, perfect, errors)
        return self.last_result

    @property
    def average_score(self):
        return self.total_score/self.rounds_scored if self.rounds_scored else 0


# Pyodide browser wiring, kept out of model calculations so CPython can test them.
_CHALLENGE_PROXIES = []
_CHALLENGE_SESSION = None


def start_challenge_browser_app():
    from js import document
    from pyodide.ffi import create_proxy

    global _CHALLENGE_SESSION
    session = ChallengeSession()
    _CHALLENGE_SESSION = session

    def node(identifier):
        result = document.getElementById(identifier)
        if result is None:
            raise RuntimeError('Module 4 missing element: ' + identifier)
        return result

    def text(identifier, value):
        node(identifier).textContent = str(value)

    def on(element, event_name, handler):
        proxy = create_proxy(handler)
        _CHALLENGE_PROXIES.append(proxy)
        element.addEventListener(event_name, proxy)

    def update_scoreboard():
        text('ch-round', session.round_number)
        text('ch-played', session.rounds_scored)
        text('ch-total', session.total_score)
        text('ch-average', (f'{session.average_score:.0f} / 100'
                            if session.rounds_scored else '—'))
        text('ch-perfect', session.perfect_rounds)

    def render_graph():
        node('ch-chart').innerHTML = challenge_svg(
            session.horizon, session.clean, session.noisy,
            session.true_sensor, session.estimated_sensor)

    def new_round(event=None):
        if event is not None:
            session.new_round()
        sensor = session.true_sensor
        first = sensor.kind == 'first'
        for field in ('ch-k', 'ch-tau', 'ch-zeta', 'ch-wn'):
            node(field).value = ''
            node(field).disabled = False
        node('ch-fields-first').hidden = not first
        node('ch-fields-second').hidden = first
        node('ch-form').hidden = False
        node('ch-result').hidden = True
        node('ch-hint-text').hidden = True
        node('ch-hint').disabled = False
        node('ch-submit').disabled = False
        node('ch-guess-legend').hidden = True
        node('ch-true-legend').hidden = True
        node('ch-input-legend').hidden = sensor.signal != 'sine'
        text('ch-error','')
        text('ch-kind', ('First-order sine' if sensor.signal=='sine' else 'First-order step')
             if first else 'Second-order step')
        if sensor.signal=='sine':
            text('ch-signal',f'Input: x(t) = sin({sensor.omega:.2f}t), '
                 f'ω = {sensor.omega:.2f} rad/s · steady-state output with noise.')
        else:
            text('ch-signal','Input: unit step at t = 0 · output contains small measurement noise.')
        text('ch-instructions', ('Estimate K and τ from the sine amplitude and phase delay.'
                                 if sensor.signal=='sine' else 'Estimate gain K and time constant τ from the noisy step response.')
             if first else 'Estimate damping ratio ζ and natural frequency ωn from overshoot and peak time.')
        text('ch-caption','The observed curve contains measurement noise. The true model is revealed after you submit a guess.')
        update_scoreboard()
        render_graph()

    def show_hint(event=None):
        if session.submitted:
            return
        text('ch-hint-text',get_hint(session.true_sensor))
        node('ch-hint-text').hidden = False

    def submit(event):
        event.preventDefault()
        if session.submitted:
            return
        sensor = session.true_sensor
        keys = parameter_names(sensor)
        fields={'K':'ch-k','tau':'ch-tau','zeta':'ch-zeta','wn':'ch-wn'}
        estimates={}
        for key in keys:
            try:
                val=str(node(fields[key]).value).strip()
                estimates[key]=float(val) if val else float('nan')
            except (ValueError,TypeError):
                estimates[key]=float('nan')
        try:
            score, perfect, errors = session.submit(estimates)
        except ValueError:
            text('ch-error', ('Enter K between 0.1–5 and τ between 0.2–20 s.'
                              if sensor.kind=='first' else
                              'Enter ζ between 0.05–0.95 and ωn between 0.30–10 rad/s.'))
            return
        text('ch-error','')
        for key in keys:
            node(fields[key]).disabled = True
        node('ch-hint').disabled = True
        node('ch-submit').disabled = True
        node('ch-result').hidden = False
        node('ch-guess-legend').hidden = False
        node('ch-true-legend').hidden = False
        text('ch-score',f'{score} / 100')
        unit_names = {'K':('K',''),'tau':('τ','s'), 'zeta':('ζ',''),'wn':('ωn','rad/s')}
        rows=[]
        for key, error in zip(keys, errors):
            label, unit = unit_names[key]
            true=getattr(sensor,key)
            guessed=estimates[key]
            rows.append('<div><span>'+html.escape(label)+': true / your guess</span>'
                        f'<strong>{true:.2f} / {guessed:.2f} {unit}</strong>'
                        f'<em>{error*100:.1f}% error</em></div>')
        node('ch-reveal').innerHTML=''.join(rows)
        text('ch-feedback',
             'Great estimate! Both parameters were within 10% of their true values.'
             if perfect else 'The green curve is the true response; the gold dashed curve is your estimate. '
                             'Use the differences to improve your next guess.')
        text('ch-caption','The green curve shows the exact model without noise. The gold dashed curve shows your estimated model.')
        update_scoreboard()
        render_graph()

    on(node('ch-new'),'click',new_round)
    on(node('ch-hint'),'click',show_hint)
    on(node('ch-form'),'submit',submit)
    new_round()


if __name__ == '__main__':
    start_challenge_browser_app()
