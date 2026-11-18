"""ENCS4380 HW2 numerical simulation engine, written in Python for Pyodide.

A browser loads this file with Pyodide. The UI (js/app.js) only renders results
and handles DOM events; all numerical integration, PID calculations, validation live here.

First-order plant: dy/dt = (K*u-y)/tau
Second-order plant: d2y/dt2 = wn^2*(K*u-y)-2*zeta*wn*dy/dt
Sensor: dym/dt = (y-ym)/sensorTau
Continuous UI uses derivative on measurement to avoid setpoint kick.
Digital PID follows the HW2 positional formula, derivative on sampled error.
"""
from __future__ import annotations
import json
import math


def clamp(x, low, high):
    return min(high, max(low, x))


def config(options):
    o = dict(options or {})
    p = {"kind": "first", "K": 1, "tau": 1, "zeta": 0.5, "wn": 3}
    p.update(o.get("plant") or {})
    c = {
        "plant": p, "kp": 2, "ki": 1, "kd": 0, "reference": 1,
        "sensorTau": 0, "uMin": 0, "uMax": 100, "duration": 15,
        "dt": 0.005, "mode": "continuous", "sampleTime": 0.05,
        "antiWindup": True,
    }
    c.update({k: v for k, v in o.items() if k != "plant"})
    if not p["K"] > 0:
        raise ValueError("Plant gain K must be positive")
    if p["kind"] == "first" and not p["tau"] > 0:
        raise ValueError("Plant τ must be positive")
    if p["kind"] == "second" and not (p["wn"] > 0 and p["zeta"] >= 0):
        raise ValueError("ωn must be positive and ζ nonnegative")
    if not c["uMin"] < c["uMax"]:
        raise ValueError("Control limits must be ordered")
    if c["mode"] == "digital" and not c["sampleTime"] > 0:
        raise ValueError("Sample time must be positive")
    for name in ("kp", "ki", "kd"):
        val = c[name]
        c[name] = max(0.0, val if math.isfinite(val) else 0.0)
    c["reference"] = c["reference"] if math.isfinite(c["reference"]) else 0.0
    c["duration"] = clamp(c["duration"], 0.5, 45)
    c["dt"] = clamp(c["dt"], 0.0002, 0.03)
    c["sensorTau"] = max(0, c["sensorTau"])
    return c


def derivative(s, u, p, sensor_tau):
    y, v, sensor = s
    if p["kind"] == "second":
        dy = v
        dv = p["wn"]**2 * (p["K"] * u - y) - 2 * p["zeta"] * p["wn"] * v
    else:
        dy = (p["K"] * u - y) / p["tau"]
        dv = 0
    d_sensor = (y - sensor) / sensor_tau if sensor_tau > 0 else 0
    return dy, dv, d_sensor


def rk4(s, u, h, p, sensor_tau):
    k1 = derivative(s, u, p, sensor_tau)
    k2 = derivative(tuple(s[i] + h / 2 * k1[i] for i in range(3)), u, p, sensor_tau)
    k3 = derivative(tuple(s[i] + h / 2 * k2[i] for i in range(3)), u, p, sensor_tau)
    k4 = derivative(tuple(s[i] + h * k3[i] for i in range(3)), u, p, sensor_tau)
    out = tuple(s[i] + h * (k1[i]+2*k2[i]+2*k3[i]+k4[i])/6 for i in range(3))
    if sensor_tau <= 0:
        return out[0], out[1], out[0]
    return out


def pid_step(c, error, prev_error, measurement, prev_measurement, integral, h):
    # Digital control: derivative on error exactly as in HW2 equation.
    # Continuous playground: derivative on measurement for no setpoint kick.
    d = (c["kd"] * (error-prev_error)/h if c["mode"] == "digital"
         else -c["kd"] * (measurement-prev_measurement)/h)
    next_integral = integral + c["ki"] * h * error
    raw_candidate = c["kp"] * error + next_integral + d
    pushing_high = raw_candidate > c["uMax"] and error > 0
    pushing_low = raw_candidate < c["uMin"] and error < 0
    if c["antiWindup"] and (pushing_high or pushing_low):
        next_integral = integral
    raw = c["kp"] * error + next_integral + d
    return clamp(raw, c["uMin"], c["uMax"]), next_integral, raw


def simulate(options=None):
    c = config(options)
    state = (0.0, 0.0, 0.0)
    integral = prev_error = prev_measurement = u = 0.0
    t, y, sensors, controls, references, raw_values = [], [], [], [], [], []
    tau_scale = c["plant"]["tau"] if c["plant"]["kind"] == "first" else 1 / c["plant"]["wn"]
    h_base = min(c["dt"], tau_scale/12, c["sensorTau"]/12 if c["sensorTau"] > 0 else 1)

    def save(time, raw):
        t.append(time)
        y.append(state[0])
        sensors.append(state[2] if c["sensorTau"] > 0 else state[0])
        controls.append(u)
        references.append(c["reference"])
        raw_values.append(raw)

    if c["mode"] == "digital":
        time = 0.0
        while time < c["duration"]-1e-10:
            window = min(c["sampleTime"], c["duration"]-time)
            measurement = state[2] if c["sensorTau"] > 0 else state[0]
            e = c["reference"] - measurement
            u, integral, raw = pid_step(c, e, prev_error, measurement, prev_measurement, integral, c["sampleTime"])
            prev_error = e
            n = max(1, math.ceil(window/h_base))
            h = window/n
            save(time, raw)
            stride = max(1, n//10)
            diverged = False
            for j in range(n):
                state = rk4(state, u, h, c["plant"], c["sensorTau"])
                time += h
                if (j+1) % stride == 0 and j < n-1:
                    save(time, raw)
                if abs(state[0]) > 1e7 or not math.isfinite(state[0]):
                    diverged = True
                    break
            if diverged:
                break
        if math.isfinite(state[0]):
            save(min(c["duration"], time), u)
    else:
        steps = math.ceil(c["duration"]/h_base)
        h = c["duration"]/steps
        for i in range(steps+1):
            time = i*h
            measurement = state[2] if c["sensorTau"] > 0 else state[0]
            e = c["reference"] - measurement
            u, integral, raw = pid_step(c, e, prev_error, measurement, prev_measurement, integral, h)
            prev_measurement = measurement
            save(time, raw)
            if i < steps:
                state = rk4(state, u, h, c["plant"], c["sensorTau"])
            if abs(state[0]) > 1e7 or not math.isfinite(state[0]):
                break
    metrics = measure({"t": t, "y": y, "control": controls}, c["reference"], c["uMax"])
    return {"t": t, "y": y, "sensor": sensors, "control": controls,
            "reference": references, "raw": raw_values, "metrics": metrics, "config": c}


def interpolate_crossing(times, values, level):
    for i in range(1, len(values)):
        if values[i-1] < level <= values[i]:
            delta = values[i]-values[i-1]
            return times[i-1] + ((level-values[i-1])/delta if delta else 0) * (times[i]-times[i-1])
    return None


def measure(trace, target, u_max=100):
    t, y, control = trace["t"], trace["y"], trace["control"]
    n = len(y)
    if n < 3:
        return dict(riseTime=None, overshoot=None, settlingTime=None, steadyError=None, iae=None, peakU=None, unstable=True)
    tail = max(4, n//25)
    final_y = sum(y[-tail:])/tail
    max_y, min_y, peak_u = max(y), min(y), max(control)
    amplitude = abs(final_y-y[0])
    direction = 1 if final_y >= y[0] else -1
    oriented = [direction*(v-y[0]) for v in y]
    t10 = interpolate_crossing(t, oriented, .1*amplitude)
    t90 = interpolate_crossing(t, oriented, .9*amplitude)
    rise_time = t90-t10 if t10 is not None and t90 is not None else None
    overshoot = 100 * max(0, (max_y-final_y) if direction == 1 else (final_y-min_y)) / amplitude if amplitude >= 1e-7 else None
    band = .02 * max(abs(final_y), .01*abs(target), 1e-6)
    last_bad = -1
    for i, value in enumerate(y):
        if abs(value-final_y) > band:
            last_bad = i
    settling_time = None if last_bad >= n-1 else 0 if last_bad < 0 else t[last_bad+1]
    iae = sum(.5*(abs(target-y[i])+abs(target-y[i-1]))*(t[i]-t[i-1]) for i in range(1,n))
    steady_error = 100*(target-final_y)/max(abs(target),1e-9)
    unstable = not math.isfinite(final_y) or abs(final_y) > 1e5 or abs(steady_error)>10000
    return dict(riseTime=rise_time, overshoot=overshoot, settlingTime=settling_time,
                steadyError=steady_error, iae=iae, peakU=peak_u, finalY=final_y,
                maxY=max_y, unstable=unstable,
                actuatorSaturated=any(v>=u_max-1e-8 for v in control))


def damping_for_pi(K, tau, kp, ki):
    if not (K > 0 and tau > 0 and ki > 0):
        return None
    wn = math.sqrt(K * ki/tau)
    return {"wn": wn, "zeta": (1+K*kp)/(2*tau*wn)}


def validation():
    common = {"plant": {"kind": "first", "K": 1, "tau": 1}, "reference": 1,
              "uMin": 0, "uMax": 100, "dt": .001, "duration": 16}
    p = simulate({**common, "kp": 9, "ki": 0, "kd": 0})
    p_tau = interpolate_crossing(p["t"],p["y"],.9*(1-math.exp(-1)))
    error = p["metrics"]["steadyError"]
    pi = simulate({**common, "kp": 1, "ki": 1, "kd": 0})
    poles = damping_for_pi(1,1,1,1)
    alt = simulate({**common, "kp":2,"ki":1,"kd":0,"duration":22})
    def status(name, expected, actual, passed):
        return {"name": name,"expected": expected,"actual": actual,"pass":bool(passed)}
    return [
        status("P only: Kp=9, closed-loop τ", "0.100 s", f"{p_tau:.4f} s" if p_tau is not None else "—", p_tau is not None and abs(p_tau-.1)<.004),
        status("P only: Kp=9, step steady-state error", "10.0%",f"{error:.3f}%",abs(error-10)<.1),
        status("PI: Kp=1, Ki=1, ωn and ζ", "1.000 rad/s, 1.000",
               f"{poles['wn']:.3f} rad/s, {poles['zeta']:.3f}; OS={pi['metrics']['overshoot']:.2f}%",
               abs(poles["wn"]-1)<.001 and abs(poles["zeta"]-1)<.001 and pi["metrics"]["overshoot"]<.5),
        status("PI: zero step steady-state error", "≈ 0%",f"{alt['metrics']['steadyError']:.4f}%",abs(alt["metrics"]["steadyError"])<.1),
    ]



def bridge_dispatch(action, payload):
    """Python/JavaScript JSON bridge for Checkpoint 1."""
    args = json.loads(payload)
    if action == "simulate":
        value = simulate(args)
    elif action == "validation":
        value = validation()
    else:
        raise ValueError("Unknown checkpoint action: " + action)
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
