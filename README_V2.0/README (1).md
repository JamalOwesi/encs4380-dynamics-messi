<div align="center">

# 侍 Group Messi Toolkit · 制 Control

**ENCS4380 Interfacing Techniques · Birzeit University · Homework 2: PID Control Toolkit**

An interactive, browser-only toolkit for PID control. Every response is computed live in Python (Pyodide) by our own closed-loop solver.
It runs on GitHub Pages, needs no server, and works on a phone.

### [▶ Open the live toolkit](https://jamalowesi.github.io/encs4380-dynamics-messi/) · [Control section](https://jamalowesi.github.io/encs4380-dynamics-messi/control/) · [Homework 1](https://jamalowesi.github.io/encs4380-dynamics-messi/dynamics.html)

`v2.0` · Homework 2 final release

</div>

---

## Contents

1. [Quick links](#quick-links)
2. [What's new in v2.0](#whats-new-in-v20)
3. [The modules](#the-modules)
4. [My system: Messi's drive motor](#my-system-messis-drive-motor)
5. [How the simulation works](#how-the-simulation-works)
6. [Validation](#validation)
7. [Bonus: Ziegler–Nichols](#bonus-zieglernichols)
8. [Run it and test it](#run-it-and-test-it)
9. [Repository layout](#repository-layout)
10. [Team, issues and ownership](#team-issues-and-ownership)
11. [AI use](#ai-use)
12. [Homework 1 (v1.0)](#homework-1-v10)

---

## Quick links

Every module has its own link, so you can open any of them directly:

| | Module | Link |
|---|---|---|
| 五 | P1 · PID playground | [`control/#p1`](https://jamalowesi.github.io/encs4380-dynamics-messi/control/#p1) |
| 六 | P2 · A slow sensor in the loop | [`control/#p2`](https://jamalowesi.github.io/encs4380-dynamics-messi/control/#p2) |
| 七 | P3 · Digital PID | [`control/#p3`](https://jamalowesi.github.io/encs4380-dynamics-messi/control/#p3) |
| 八 | P4 · Tuning challenge | [`control/#p4`](https://jamalowesi.github.io/encs4380-dynamics-messi/control/#p4) |
| 我 | My system · Messi's motor | [`control/#my`](https://jamalowesi.github.io/encs4380-dynamics-messi/control/#my) |
| 証 | Validation checks | [`control/#val`](https://jamalowesi.github.io/encs4380-dynamics-messi/control/#val) |

---

## What's new in v2.0

- **A home page** (`index.html`) linking every module of both homeworks. The Homework 1 page moved to `dynamics.html`; its maths and styling are unchanged.
- **A Control section** (`control/`) with four PID modules, a "My system" design page and a validation page.
- **Our own solver** (`control/py/pid_core.py`): the closed loop is stepped in time with **RK4** (or **Euler**, selectable in P1). We don't use closed-form answers, because they don't exist for every gain setting, saturation or sensor.
- **Arduino code generation**: the same digital PID algorithm that is simulated is exported as a ready-to-upload sketch.
- **Reuse of Homework 1**: P4's hidden plants come from Module 4's `generate_sensor()`, and the plants are Module 1's first-order and Module 3's second-order models.
- **One look**: the whole site uses Homework 1's `style.css`; `control/control.css` only adds the controls column, tables and plot styling.
- **Automatic tests** for both homeworks in `tests/`.

---

## The modules

The controller in every module:

$$u(t) = K_p\,e(t) + K_i\!\int e\,dt + K_d\,\frac{de}{dt}, \qquad e = r - y_m$$

| Module | What you can change | What the page shows | Owner | Issue |
|---|---|---|---|---|
| **五 P1 · PID playground** | Plant (first order or second order), Kp, Ki, Kd, setpoint step, actuator limit, D on error or on the measurement, solver (RK4/Euler) | Live block diagram, output vs setpoint, control signal with its limit, **rise time, overshoot, settling time, steady-state error**, time at the limit, Routh stability test, the hand formulas next to the simulation | Abdalfatah Dawoud | #5 |
| **六 P2 · Slow sensor** | Sensor time constant τs, plant, PID gains | **True output and sensor reading on one plot**, overshoot of both, the Routh condition with live numbers, an overshoot-vs-τs sweep with the **point where oscillation starts** marked | Jamal Owesi | #6 |
| **七 P3 · Digital PID** | Sampling time Ts, gains, actuator limit, **anti-windup on/off** | The **stair-step u[k]** and the integral term, samples on the output, the continuous loop as a reference, **performance vs Ts**, a sampling-rate check, and the **Arduino code** for the current gains with a copy button | Ahmad Abuayyash | #7 |
| **八 P4 · Tuning challenge** | Kp, Ki, Kd, difficulty | A **hidden random plant** (Module 4's generator), a clear spec drawn on the plot, **pass or fail on each part**, a score out of 100, attempts and best score, a reveal button | Hakam | #8 |
| **我 My system** | K, τ (or fit them from a step-test log), damping ζ, settling time, Ts | Plant model and its source, the justified spec, PI gains from the design formulas, simulated digital loop with PWM 0–100 %, pass/fail checks, the Arduino sketch | everyone | #9 |
| **証 Validation** | – | The three checks from the sheet: expected value, our solver's value, PASS/FAIL, plots | everyone | #9 |

**Spec in P4** (normal difficulty): overshoot ≤ 10 %, 2 % settling time ≤ 0.6 × the plant's open-loop settling time, zero steady-state error (≤ 1 %), and the control signal never hits its limit (6/K). Easy and hard use 0.8× and 0.5×.

### Predict, then check

Every module has a **"Predict, then check"** box: a question, a few answers, and a **Check** button. The button runs the simulator on the exact case and explains the result. Examples:

- *P1:* "You raise Kp from 1 to 9 (P only). What happens to the steady-state error?" → it shrinks from 50 % to 10 % but never reaches zero.
- *P2:* "Which shows the bigger overshoot, the true output or the sensor?" → the true output: the sensor hides the peak.
- *P3:* "The actuator saturates. You switch anti-windup on. The overshoot will…" → drop, from 24 % to 0 %.
- *P4:* "On this hidden plant, if you doubled Kd, what would the overshoot do?" → answered by simulating your own gains.

---

## My system: Messi's drive motor

Our project is the **Micromouse "Messi"**. The plant is one drive motor:

- **Input:** PWM duty cycle u [%] (0–100)
- **Output:** wheel speed y [rpm], from the encoder
- **Model:** $G(s) = \dfrac{K}{\tau s + 1}$

| | Value | Source |
|---|---|---|
| K | **_TODO_** rpm per % PWM | PWM step test logged with the encoder (date, step size, motor) |
| τ | **_TODO_** s | same test, time to 63.2 % of the final speed |

> **How we measured it:** the generated sketch has a `STEP_TEST = true` switch. It applies a PWM step at t = 0.5 s and prints `t,setpoint,speed,u` every Ts. We pasted the Serial Monitor log into the page's **Fit** tool, which gives K = Δspeed/ΔPWM and τ = the time to 63.2 %.

**Spec and why it matters:**

| Requirement | Why, for a micromouse |
|---|---|
| 0.6 ≤ ζ ≤ 0.8 | If one wheel overshoots its speed and the other doesn't, the mouse yaws at every speed change and drifts towards a wall. |
| Settling time ≤ **_TODO_** s | The wheels must follow the speed profile well within one cell-to-cell move. |
| PWM stays inside 0–100 % | A saturated wheel runs open loop, the two wheels stop matching, and the integrator winds up. |
| Zero steady-state error | Both wheels hold the same speed on long straights. |

**Design (PI, pole placement on a first-order plant):**

$$\omega_n = \frac{4}{\zeta\,t_s}, \qquad K_i = \frac{\omega_n^2\,\tau}{K}, \qquad K_p = \frac{2\zeta\omega_n\tau - 1}{K}$$

| Final gains | Kp = **_TODO_** | Ki = **_TODO_** | Ts = **_TODO_** ms |
|---|---|---|---|

The simulated response and the full Arduino sketch (encoder interrupt, fixed-rate loop, anti-windup) are on the [My system page](https://jamalowesi.github.io/encs4380-dynamics-messi/control/#my).

---

## How the simulation works

### Continuous loop (P1, P2, P4)

The whole closed loop is **one state vector**, stepped with **RK4** (default) or **Euler**:

| State | Equation |
|---|---|
| Plant, first order | $\dot y = (K u - y)/\tau$ |
| Plant, second order | $\ddot y = \omega_n^2 (K u - y) - 2\zeta\omega_n \dot y$ |
| Sensor (P2) | $\dot y_m = (y - y_m)/\tau_s$ |
| Integral | $\dot I = e$ (frozen while saturated, if anti-windup is on) |
| Derivative filter | $D = K_d \dfrac{s}{T_f s + 1}$, with $T_f$ = 5 time steps |

At every step: $e = r - y_m$, $u = K_p e + K_i I + D$, then **u is clipped to the actuator limit**.
"D on the measurement" differentiates $-y_m$ instead of $e$: it has the same damping effect, but no spike (derivative kick) when r jumps.

### Digital loop (P3, My system)

Exactly the sheet's formula, run once per sample and **held constant** until the next sample (zero-order hold). The plant keeps evolving on a finer RK4 grid between samples.

$$u[k] = K_p e[k] + K_i T_s \sum_{j=0}^{k} e[j] + K_d \frac{e[k] - e[k-1]}{T_s}$$

**Anti-windup (clamping):** if u is saturated **and** the error would push it further into the limit, the new error is not added to the sum. The generated Arduino `pidUpdate()` is this same algorithm line for line.

### Metrics

| Metric | Definition |
|---|---|
| Rise time | 10 % → 90 % of the final value |
| Overshoot | (peak − final) / final × 100 % |
| Settling time | last time the output leaves a ±2 % band around the final value |
| Steady-state error | r − final value |

If the response hasn't settled inside the time window, the page says so instead of showing a misleading number.

### Stability tools

- **Routh–Hurwitz** on the closed-loop characteristic polynomial, shown live in P1 and P2. For a first-order plant with PID and a sensor:
  $(\tau + \tau_s + K K_d)(1 + K K_p) > \tau\,\tau_s\,K K_i$
- **Ultimate gain** $K_u$ and period $T_u$ from the frequency where the loop phase reaches −180°.

---

## Validation

Plant $K/(\tau s + 1)$ with K = 1, τ = 1 s. All numbers come from our time-stepped solver, not from the formulas.

| # | Check | Expected | Our solver | |
|---|---|---|---|---|
| 1 | P only, Kp = 9 | τcl = 0.1 s, ess = 10 % | τcl = **0.1000 s**, ess = **10.000 %** (Euler gives the same) | ✅ |
| 2 | PI, Kp = Ki = 1 | ωn = 1 rad/s, ζ = 1 | ωn = **1**, ζ = **1** from s² + 2s + 1; 0 % overshoot; y(t) matches 1 − e⁻ᵗ to **5 × 10⁻¹⁴** | ✅ |
| 3 | Any PI controller | ess = 0 | 10 random (Kp, Ki) pairs, worst \|ess\| = **0.0008 %** | ✅ |

Open the [Validation page](https://jamalowesi.github.io/encs4380-dynamics-messi/control/#val) to see these computed live.

---

## Bonus: Ziegler–Nichols

In **P2 → Bonus**, the page finds the P-only gain $K_u$ where the loop (plant + sensor) starts to oscillate, and its period $T_u$. It then applies the classic table:

| Controller | Kp | Ti | Td |
|---|---|---|---|
| P | 0.5 Ku | – | – |
| PI | 0.45 Ku | Tu / 1.2 | – |
| PID | 0.6 Ku | Tu / 2 | Tu / 8 |

with Ki = Kp/Ti and Kd = Kp·Td. "Use" buttons load the gains into the sliders, and "Show the loop at K = Ku" shows the sustained oscillation.
Example: second-order plant (ωn = 2, ζ = 0.5) with τs = 0.2 s gives **Ku ≈ 3.9, Tu ≈ 1.68 s**.

---

## Run it and test it

### Run locally

The pages load `.py` files with `fetch()`, which browsers block for `file://` pages. **Don't double-click `index.html`**; start a local server instead:

```bash
git clone https://github.com/JamalOwesi/encs4380-dynamics-messi.git
cd encs4380-dynamics-messi
python -m http.server 8000
```

Open **http://localhost:8000/**. The first load needs internet (Pyodide and Plotly come from CDNs) and takes 5–15 s.

### Automatic tests (plain Python, no browser)

```bash
python tests/test_hw1_modules.py   # Homework 1: validation checks 1–6, Module 4 scoring
python tests/test_pid_core.py      # Homework 2: PID checks 1–3, Routh, sensor, digital, anti-windup, P4
python -m pytest tests/ -q         # or both at once
```

### Manual tests

[`TESTING.md`](TESTING.md) has, for every module of both homeworks, what to click and the exact numbers you should see, plus a troubleshooting table.

---

## Repository layout

```
index.html              home page: links every module of both homeworks
dynamics.html           Homework 1 page (modules 一–四)
style.css               shared theme, used by every page
module1.py … module4.py Homework 1 Python (module4.py is also used by P4)
control/
  index.html            Control section: tabs, block diagrams, Pyodide loader
  control.css           Control-only layout on top of ../style.css
  py/
    pid_core.py         the solver: plants, RK4/Euler loop, digital PID, metrics,
                        Routh, ultimate gain, PI design, step-test fit, P4 grading
    ui.py               sliders, Plotly wrapper, "Predict, then check" box
    arduino_code.py     generates the Arduino sketch from the current gains
    p1_playground.py  p2_sensor.py  p3_digital.py  p4_challenge.py
    my_system.py        validation.py  main.py
tests/
  test_hw1_modules.py   Homework 1 tests
  test_pid_core.py      Homework 2 tests
docs/                   build steps, issue texts
TESTING.md              how to run and test each module
```

**Tech:** HTML/CSS · Python 3 in the browser via [Pyodide](https://pyodide.org) · [Plotly.js](https://plotly.com/javascript/) for the Control plots · Homework 1 draws its own SVG charts in Python · GitHub Pages.

---

## Team, issues and ownership

| Member | Homework 1 | Homework 2 |
|---|---|---|
| Abdalfatah Dawoud | Module 1 · First-order time response | P1 · PID playground (#5) |
| Jamal Owesi | Module 2 · Frequency response | P2 · Slow sensor (#6) |
| Ahmad Abuayyash | Module 3 · Second-order response | P3 · Digital PID (#7) |
| Hakam | Module 4 · Guess the sensor | P4 · Tuning challenge (#8) |
| Everyone | – | My system + validation (#9) |

Each module has its own GitHub Issue, assigned to its owner, and each member committed their own module.

---

## AI use

AI coding assistants were allowed for this homework. We used **Claude (Anthropic)** to:

- _TODO: edit this list so it matches what you actually did_
- draft the closed-loop solver and the module pages,
- write the Arduino code generator and the test cases for the validation checks,
- restyle the Control section to match Homework 1 and link the two homeworks,
- explain PID behaviour (for example why Kd raises overshoot on a first-order plant with PI).

Every member reviewed, tested and can explain the code and equations of their own module.

---

## Homework 1 (v1.0)

**Dynamic characteristics of sensors** · [open it](https://jamalowesi.github.io/encs4380-dynamics-messi/dynamics.html)

| | Module | What it shows | Validation |
|---|---|---|---|
| 一 | First-order time response | Step and ramp, 63.2 % and 95 % points, ramp lag, log-error plot | 2 / 2 |
| 二 | First-order frequency response | Input vs output sines, amplitude ratio, phase lag, Bode plot, dynamic-error calculator | 4 / 4 |
| 三 | Second-order response | Mass–spring–damper, three damping cases, metrics, poles, state space | 3 / 3 |
| 四 | Guess the sensor | Hidden random sensor with noise, estimate the parameters, score | – |

---

<div align="center">

**武士道 × ROBOTICS** · ENCS4380 · Birzeit University · Group Messi

Releases: `v1.0` Homework 1 · `v2.0` Homework 2

</div>
