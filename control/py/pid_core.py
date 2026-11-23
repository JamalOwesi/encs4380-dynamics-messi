"""
pid_core.py - the simulation engine behind the Control section (Homework 2).

Pure Python on purpose (no numpy): it loads instantly in Pyodide and the
same file runs in CPython for the tests in tests/test_pid_core.py.

What is inside
  * Plant models: FirstOrder  K/(tau s + 1)            (Homework 1, Module 1)
                  SecondOrder K wn^2/(s^2+2 zeta wn s+wn^2) (Homework 1, Module 3)
  * simulate_continuous(): PID + actuator limit + optional slow sensor,
    stepped in time with RK4 (or Euler).            -> modules P1, P2, P4
  * simulate_digital(): the sampled PID u[k] from the homework sheet, held
    constant between samples (zero-order hold).     -> module P3
  * step_metrics(): rise time, overshoot, settling time, steady-state error.
  * Stability tools: closed-loop characteristic polynomial + Routh test,
    ultimate gain for Ziegler-Nichols, PI design formulas, step-test fit.
"""

import math
import random

# --------------------------------------------------------------------------
# Plant models
# --------------------------------------------------------------------------


class FirstOrder:
    """G(s) = K / (tau*s + 1).  State x = [y]."""

    kind = "first"

    def __init__(self, K=1.0, tau=1.0):
        self.K = float(K)
        self.tau = float(tau)

    def n_states(self):
        return 1

    def deriv(self, x, u):
        # tau * dy/dt + y = K * u
        return [(self.K * u - x[0]) / self.tau]

    def output(self, x):
        return x[0]

    def den(self):
        """Denominator polynomial, highest power first: tau s + 1."""
        return [self.tau, 1.0]

    def num(self):
        return [self.K]

    def open_loop_settling(self):
        return 4.0 * self.tau  # 2 % band: about 3.9 tau

    def label(self):
        return "G(s) = %.3g / (%.3g s + 1)" % (self.K, self.tau)


class SecondOrder:
    """G(s) = K wn^2 / (s^2 + 2 zeta wn s + wn^2).  State x = [y, dy/dt]."""

    kind = "second"

    def __init__(self, K=1.0, wn=2.0, zeta=0.3):
        self.K = float(K)
        self.wn = float(wn)
        self.zeta = float(zeta)

    def n_states(self):
        return 2

    def deriv(self, x, u):
        y, v = x
        a = self.wn * self.wn * (self.K * u - y) - 2.0 * self.zeta * self.wn * v
        return [v, a]

    def output(self, x):
        return x[0]

    def den(self):
        return [1.0, 2.0 * self.zeta * self.wn, self.wn * self.wn]

    def num(self):
        return [self.K * self.wn * self.wn]

    def open_loop_settling(self):
        """2 % settling time of the plant alone, measured from a simulated
        unit step, or the 4/(zeta wn) envelope rule if that is longer (the rule
        alone is poor near zeta = 1)."""
        t_end = 12.0 / (min(self.zeta, 1.0) * self.wn) + 6.0 / self.wn
        n = 3000
        dt = t_end / n
        x = [0.0, 0.0]
        ts, ys = [], []
        for k in range(n + 1):
            ts.append(k * dt)
            ys.append(x[0])
            k1 = self.deriv(x, 1.0)
            k2 = self.deriv(_add(x, k1, dt / 2), 1.0)
            k3 = self.deriv(_add(x, k2, dt / 2), 1.0)
            k4 = self.deriv(_add(x, k3, dt), 1.0)
            x = [x[i] + dt / 6.0 * (k1[i] + 2 * k2[i] + 2 * k3[i] + k4[i]) for i in range(2)]
        measured = step_metrics(ts, ys, self.K)["settling"]
        envelope = 4.0 / (min(self.zeta, 1.0) * self.wn)
        return max(measured, envelope)

    def label(self):
        return "G(s) = %.3g*%.3g^2 / (s^2 + 2*%.3g*%.3g s + %.3g^2)" % (
            self.K, self.wn, self.zeta, self.wn, self.wn)


def make_plant(kind, K=1.0, tau=1.0, wn=2.0, zeta=0.3):
    if kind == "second":
        return SecondOrder(K, wn, zeta)
    return FirstOrder(K, tau)


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------


def clamp(u, u_min, u_max):
    if u_max is not None and u > u_max:
        return u_max
    if u_min is not None and u < u_min:
        return u_min
    return u


def _add(x, k, h):
    return [xi + h * ki for xi, ki in zip(x, k)]


# --------------------------------------------------------------------------
# Continuous-time PID loop (P1, P2, P4)
# --------------------------------------------------------------------------


def simulate_continuous(plant, Kp, Ki, Kd, r=1.0, t_end=10.0, n_steps=3000,
                        tau_s=0.0, u_min=None, u_max=None, anti_windup=False,
                        d_on_measurement=True, method="rk4"):
    """Closed loop:  r -> PID -> limit -> plant -> y -> sensor -> ym -> back.

    The setpoint steps from 0 to r at t = 0. Everything starts at rest.

    State vector X = [plant states..., ym (only if tau_s > 0), I, xf]
      I  = integral of the error
      xf = low-pass copy of the signal being differentiated; the D term is
           Kd * (signal - xf) / Tf, i.e. Kd * s/(Tf s + 1). Tf is a few time
           steps, so it is a "practical" derivative that a solver can handle.
    d_on_measurement=True differentiates -ym instead of e: same effect on
    disturbances, but no spike ("derivative kick") when the setpoint jumps.
    """
    n_p = plant.n_states()
    has_sensor = tau_s > 1e-9
    dt = t_end / float(n_steps)
    Tf = 5.0 * dt
    i_ym = n_p
    i_I = n_p + (1 if has_sensor else 0)
    i_xf = i_I + 1

    def controller(X):
        y = plant.output(X)
        ym = X[i_ym] if has_sensor else y
        e = r - ym
        sig = -ym if d_on_measurement else e
        d_term = Kd * (sig - X[i_xf]) / Tf
        u_raw = Kp * e + Ki * X[i_I] + d_term
        u = clamp(u_raw, u_min, u_max)
        return y, ym, e, sig, u_raw, u

    def f(X):
        y, ym, e, sig, u_raw, u = controller(X)
        dX = plant.deriv(X[:n_p], u)
        if has_sensor:
            dX.append((y - ym) / tau_s)
        # integrator, with optional clamping anti-windup
        dI = e
        if anti_windup and u != u_raw and (u_raw - u) * e > 0:
            dI = 0.0
        dX.append(dI)
        dX.append((sig - X[i_xf]) / Tf)
        return dX

    X = [0.0] * (i_xf + 1)  # xf starts at the pre-step value 0
    ts, ys, yms, us = [], [], [], []
    t = 0.0
    for k in range(n_steps + 1):
        y, ym, e, sig, u_raw, u = controller(X)
        ts.append(t)
        ys.append(y)
        yms.append(ym)
        us.append(u)
        if abs(y) > 1e6 or y != y:  # blew up: stop early
            break
        if method == "euler":
            X = _add(X, f(X), dt)
        else:
            k1 = f(X)
            k2 = f(_add(X, k1, dt / 2))
            k3 = f(_add(X, k2, dt / 2))
            k4 = f(_add(X, k3, dt))
            X = [X[i] + dt / 6.0 * (k1[i] + 2 * k2[i] + 2 * k3[i] + k4[i])
                 for i in range(len(X))]
        t = (k + 1) * dt
    return {"t": ts, "y": ys, "ym": yms, "u": us, "r": r}


# --------------------------------------------------------------------------
# Digital PID (P3): exactly the formula on the homework sheet
# --------------------------------------------------------------------------


class DigitalPID:
    """u[k] = Kp e[k] + Ki Ts sum_{j=0..k} e[j] + Kd (e[k] - e[k-1]) / Ts

    Anti-windup (clamping): if the output is saturated and the error would
    push it further into the limit, the new error is NOT added to the sum.
    The generated Arduino code uses this same algorithm line for line.
    """

    def __init__(self, Kp, Ki, Kd, Ts, u_min=None, u_max=None, anti_windup=True):
        self.Kp, self.Ki, self.Kd, self.Ts = Kp, Ki, Kd, Ts
        self.u_min, self.u_max = u_min, u_max
        self.anti_windup = anti_windup
        self.sum_e = 0.0
        self.prev_e = 0.0  # e[-1] = 0

    def _raw(self, e, s):
        return (self.Kp * e + self.Ki * self.Ts * s
                + self.Kd * (e - self.prev_e) / self.Ts)

    def update(self, e):
        s_new = self.sum_e + e
        u = self._raw(e, s_new)
        pushing_up = self.u_max is not None and u > self.u_max and e > 0
        pushing_down = self.u_min is not None and u < self.u_min and e < 0
        if self.anti_windup and (pushing_up or pushing_down):
            s_new = self.sum_e  # freeze the integral
            u = self._raw(e, s_new)
        self.sum_e = s_new
        self.prev_e = e
        return clamp(u, self.u_min, self.u_max)


def simulate_digital(plant, Kp, Ki, Kd, Ts, r=1.0, t_end=10.0, tau_s=0.0,
                     u_min=None, u_max=None, anti_windup=True, fine_steps=3000):
    """Sampled PID with zero-order hold. The plant (and sensor) are still
    continuous, stepped with RK4 on a fine grid between samples."""
    m = max(1, int(math.ceil(Ts / (t_end / float(fine_steps)))))
    dt = Ts / m
    n_p = plant.n_states()
    has_sensor = tau_s > 1e-9
    pid = DigitalPID(Kp, Ki, Kd, Ts, u_min, u_max, anti_windup)

    def f(X, u):
        dX = plant.deriv(X[:n_p], u)
        if has_sensor:
            dX.append((plant.output(X) - X[n_p]) / tau_s)
        return dX

    X = [0.0] * (n_p + (1 if has_sensor else 0))
    ts, ys, yms, us = [], [], [], []
    tk, uk, ymk, ik = [], [], [], []
    t = 0.0
    n_samples = int(t_end / Ts) + 1
    for k in range(n_samples):
        ym = X[n_p] if has_sensor else plant.output(X)
        u = pid.update(r - ym)
        tk.append(k * Ts)
        uk.append(u)
        ymk.append(ym)
        ik.append(Ki * Ts * pid.sum_e)  # the integral part of u[k]
        for j in range(m):
            y = plant.output(X)
            ts.append(t)
            ys.append(y)
            yms.append(X[n_p] if has_sensor else y)
            us.append(u)
            if abs(y) > 1e6 or y != y:
                return {"t": ts, "y": ys, "ym": yms, "u": us, "tk": tk,
                        "uk": uk, "ymk": ymk, "ik": ik, "r": r}
            k1 = f(X, u)
            k2 = f(_add(X, k1, dt / 2), u)
            k3 = f(_add(X, k2, dt / 2), u)
            k4 = f(_add(X, k3, dt), u)
            X = [X[i] + dt / 6.0 * (k1[i] + 2 * k2[i] + 2 * k3[i] + k4[i])
                 for i in range(len(X))]
            t += dt
    return {"t": ts, "y": ys, "ym": yms, "u": us, "tk": tk, "uk": uk,
            "ymk": ymk, "ik": ik, "r": r}


# --------------------------------------------------------------------------
# Step-response metrics
# --------------------------------------------------------------------------


def _cross_time(t, y, level):
    """First time y reaches `level` (linear interpolation)."""
    for i in range(1, len(y)):
        if (y[i - 1] - level) * (y[i] - level) <= 0 and y[i] != y[i - 1]:
            frac = (level - y[i - 1]) / (y[i] - y[i - 1])
            return t[i - 1] + frac * (t[i] - t[i - 1])
    return None


def step_metrics(t, y, r, band=0.02):
    """Rise time (10-90 % of final value), percent overshoot (relative to the
    final value), 2 % settling time and steady-state error.

    If the response has not settled inside the window (oscillating or still
    moving) 'settled' is False, settling time and error are None, and the
    overshoot is measured against the setpoint instead.
    """
    out = {"rise": None, "overshoot": None, "settling": None,
           "ess": None, "ess_pct": None, "settled": False, "unstable": False,
           "peak": None, "final": None}
    if not y:
        return out
    t_end = t[-1]
    if abs(y[-1]) > 1e5 or y[-1] != y[-1]:
        out["unstable"] = True
        return out
    y_final = y[-1]
    out["final"] = y_final
    peak = max(y) if r >= 0 else min(y)
    out["peak"] = peak

    # settled?  last point that is outside the band
    ref = abs(y_final) if abs(y_final) > 1e-9 else abs(r)
    tol = band * ref
    last_out = None
    for i in range(len(y) - 1, -1, -1):
        if abs(y[i] - y_final) > tol:
            last_out = i
            break
    if last_out is None:
        settling = 0.0
    else:
        settling = t[min(last_out + 1, len(t) - 1)]
    settled = settling < 0.9 * t_end
    # extra check: the tail must be flat (no slow drift / sustained oscillation)
    tail = y[int(0.9 * len(y)):]
    if tail and (max(tail) - min(tail)) > tol:
        settled = False
    out["settled"] = settled

    base = y_final if settled and abs(y_final) > 1e-9 else r
    if base != 0:
        out["overshoot"] = max(0.0, (peak - base) / abs(base) * 100.0)
        t10 = _cross_time(t, y, 0.1 * base)
        t90 = _cross_time(t, y, 0.9 * base)
        if t10 is not None and t90 is not None:
            out["rise"] = t90 - t10
    if settled:
        out["settling"] = settling
        out["ess"] = r - y_final
        out["ess_pct"] = (r - y_final) / r * 100.0 if r != 0 else None
    return out


def time_constant_from_response(t, y):
    """Time to reach 63.2 % of the final value (first-order loops)."""
    return _cross_time(t, y, 0.632 * y[-1])


# --------------------------------------------------------------------------
# Polynomials, Routh test, frequency response
# --------------------------------------------------------------------------


def poly_mul(a, b):
    out = [0.0] * (len(a) + len(b) - 1)
    for i, ai in enumerate(a):
        for j, bj in enumerate(b):
            out[i + j] += ai * bj
    return out


def poly_add(a, b):
    n = max(len(a), len(b))
    a = [0.0] * (n - len(a)) + list(a)
    b = [0.0] * (n - len(b)) + list(b)
    return [x + y for x, y in zip(a, b)]


def char_poly(plant, Kp, Ki, Kd, tau_s=0.0):
    """1 + C(s) G(s) H(s) = 0 with C = (Kd s^2 + Kp s + Ki)/s, H = 1/(tau_s s+1).
    Returns s*den_G*den_H + num_G*(Kd s^2 + Kp s + Ki), highest power first.
    (The small derivative filter is ignored here.)"""
    den = poly_mul([1.0, 0.0], plant.den())
    num = poly_mul(plant.num(), [Kd, Kp, Ki])
    if tau_s > 1e-9:
        den = poly_mul(den, [tau_s, 1.0])
    p = poly_add(den, num)
    # drop leading zeros
    while len(p) > 1 and abs(p[0]) < 1e-12:
        p = p[1:]
    # a pure P or PD controller leaves a common factor s: remove it
    if Ki == 0 and abs(p[-1]) < 1e-12:
        p = p[:-1]
    return p


def routh_stable(p):
    """Routh-Hurwitz test. Returns (stable, first_column)."""
    p = [c for c in p]
    if p[0] < 0:
        p = [-c for c in p]
    if any(c <= 0 for c in p):
        return False, p
    n = len(p)
    row1 = p[0::2]
    row2 = p[1::2] + [0.0] * (len(row1) - len(p[1::2]))
    rows = [row1, row2]
    for _ in range(n - 2):
        a, b = rows[-2], rows[-1]
        if abs(b[0]) < 1e-9 * max(1.0, abs(a[0])):
            return False, [row[0] for row in rows]  # zero in the first column: on the edge, not stable
        new = []
        for j in range(len(a) - 1):
            bj1 = b[j + 1] if j + 1 < len(b) else 0.0
            new.append((b[0] * a[j + 1] - a[0] * bj1) / b[0])
        new.append(0.0)
        rows.append(new)
    first = [row[0] for row in rows[:n]]
    stable = all(c > 0 for c in first)
    return stable, first


def freq_response(plant, w, tau_s=0.0):
    """G(jw) * H(jw) as a complex number."""
    s = complex(0.0, w)
    G = plant.num()[0] / sum(c * s ** (len(plant.den()) - 1 - i)
                             for i, c in enumerate(plant.den()))
    if tau_s > 1e-9:
        G = G / (tau_s * s + 1.0)
    return G


def ultimate_gain(plant, tau_s=0.0):
    """Ziegler-Nichols: P-only gain Ku at which the loop just oscillates, and
    the period Tu. Found from the frequency where the loop phase is -180 deg.
    Returns (Ku, Tu) or (None, None) if the phase never reaches -180 deg
    (a first-order plant with a perfect sensor can never oscillate)."""

    def phase(w):
        G = freq_response(plant, w, tau_s)
        ph = math.atan2(G.imag, G.real)
        # unwrap: our plants only lag, so keep the phase in (-2pi, 0]
        if ph > 0:
            ph -= 2 * math.pi
        return ph

    lo, hi = 1e-4, 1e5
    if phase(hi) > -math.pi + 1e-6:
        return None, None
    for _ in range(200):
        mid = math.sqrt(lo * hi)
        if phase(mid) > -math.pi:
            lo = mid
        else:
            hi = mid
    w180 = math.sqrt(lo * hi)
    Ku = 1.0 / abs(freq_response(plant, w180, tau_s))
    return Ku, 2 * math.pi / w180


def ziegler_nichols(Ku, Tu):
    """Classic closed-loop Ziegler-Nichols table, as (Kp, Ki, Kd)."""
    rules = {}
    rules["P"] = (0.5 * Ku, 0.0, 0.0)
    kp = 0.45 * Ku
    rules["PI"] = (kp, kp / (Tu / 1.2), 0.0)
    kp = 0.6 * Ku
    rules["PID"] = (kp, kp / (Tu / 2.0), kp * Tu / 8.0)
    return rules


# --------------------------------------------------------------------------
# Design formulas for a first-order plant (validation + "My system")
# --------------------------------------------------------------------------


def p_only_first_order(K, tau, Kp):
    """Closed-loop time constant and steady-state error for P control."""
    return tau / (1 + K * Kp), 1.0 / (1 + K * Kp)


def pi_first_order(K, tau, Kp, Ki):
    """Closed loop s^2 + (1+K Kp)/tau s + K Ki/tau  ->  (wn, zeta)."""
    wn = math.sqrt(K * Ki / tau)
    zeta = (1 + K * Kp) / (2 * math.sqrt(tau * K * Ki))
    return wn, zeta


def pi_design(K, tau, zeta, wn):
    """Inverse of pi_first_order: pick zeta and wn, get Kp and Ki."""
    Ki = wn * wn * tau / K
    Kp = (2 * zeta * wn * tau - 1.0) / K
    return Kp, Ki


def fit_first_order(t, y, u_step):
    """Fit K and tau from a step test (63.2 % method).
    K   = final value / step size
    tau = time to reach 63.2 % of the final value (after the step at t[0])."""
    n = len(y)
    tail = y[int(0.9 * n):] or y[-1:]
    y_final = sum(tail) / len(tail)
    y0 = y[0]
    K = (y_final - y0) / u_step
    t63 = _cross_time(t, y, y0 + 0.632 * (y_final - y0))
    tau = (t63 - t[0]) if t63 is not None else None
    return K, tau


# --------------------------------------------------------------------------
# Random plants and specs for the tuning challenge (P4)
# --------------------------------------------------------------------------


def random_plant(seed=None):
    """A hidden plant for the tuning challenge, drawn by the SAME generator as
    Homework 1 Module 4 ('Guess the sensor'): module4.generate_sensor().
    First order -> K/(tau s + 1); second order -> wn^2/(s^2 + 2 zeta wn s + wn^2).
    If module4.py is not available (e.g. a test run without it) we fall back
    to similar random ranges here."""
    rng = random.Random(seed)
    try:
        import module4
    except ImportError:
        module4 = None
    if module4 is not None:
        s = module4.generate_sensor(rng, signal="step")
        if s.kind == "first":
            return FirstOrder(K=s.K, tau=s.tau)
        return SecondOrder(K=1.0, wn=s.wn, zeta=s.zeta)
    if rng.random() < 0.5:
        return FirstOrder(K=round(rng.uniform(0.85, 2.15), 2),
                          tau=round(rng.uniform(1.6, 5.5), 2))
    return SecondOrder(K=1.0, wn=round(rng.uniform(1.3, 3.6), 2),
                       zeta=round(rng.uniform(0.28, 0.73), 2))


def make_spec(plant, level="normal"):
    """Overshoot <= 10 %, settling time <= a fraction of the open-loop
    settling time, zero steady-state error, and the control signal must stay
    inside the actuator limit."""
    frac = {"easy": 0.8, "normal": 0.6, "hard": 0.5}.get(level, 0.6)
    ts_ol = plant.open_loop_settling()
    return {
        "overshoot": 10.0,
        "settling": round(max(0.1, frac * ts_ol), 2),
        "ess_pct": 1.0,
        "u_max": round(6.0 / plant.K, 2),  # 6x what is needed at steady state
        "t_end": round(max(3.0 * ts_ol, 4.0), 1),
    }


def grade(spec, metrics, u_peak):
    """Pass/fail on each part of the spec and a score out of 100."""
    m = metrics
    parts = []
    ok = m["settled"] and m["overshoot"] is not None and m["overshoot"] <= spec["overshoot"]
    parts.append(("Overshoot <= %g %%" % spec["overshoot"], ok,
                  "%.1f %%" % m["overshoot"] if m["overshoot"] is not None else "n/a"))
    ok = m["settling"] is not None and m["settling"] <= spec["settling"]
    parts.append(("Settling time (2 %%) <= %g s" % spec["settling"], ok,
                  "%.2f s" % m["settling"] if m["settling"] is not None else "not settled"))
    ok = m["ess_pct"] is not None and abs(m["ess_pct"]) <= spec["ess_pct"]
    parts.append(("Steady-state error = 0 (|e| <= %g %%)" % spec["ess_pct"], ok,
                  "%.2f %%" % m["ess_pct"] if m["ess_pct"] is not None else "not settled"))
    ok = u_peak < spec["u_max"] - 1e-6
    parts.append(("Control signal never hits its limit (%g)" % spec["u_max"], ok,
                  "peak %.2f" % u_peak))
    score = 25 * sum(1 for p in parts if p[1])
    return parts, score
