<!-- Paste this into the repo README under the Homework 1 section. Fix the owners if your split is different.
     Note: the Homework 1 page moved from index.html to dynamics.html; index.html is now the home page. -->

## Homework 2: Control section (v2.0)

Live: `https://<user>.github.io/<repo>/control/` (linked from the home page `index.html`, and from the Homework 1 page `dynamics.html`).
Every module has its own link: `control/#p1` … `control/#p4`, `control/#my`, `control/#val`. How to run and test each one: see [TESTING.md](TESTING.md).

The Control section adds PID control to the toolkit. Everything still runs in the browser: Python through
Pyodide, plots with Plotly, no server.

| Module | What you can change | What the page shows | Owner | Issue |
|---|---|---|---|---|
| P1 PID playground | plant (Module 1 first order or Module 3 second order), Kp, Ki, Kd, setpoint step, actuator limit, solver | block diagram, output vs setpoint, control signal with its limit, rise time, overshoot, settling time, steady-state error, Routh test | Abdalfatah Dawoud | #5 |
| P2 Slow sensor in the loop | sensor τs, plant, PID gains | true output and sensor reading on one plot, overshoot vs τs sweep, Routh stability limit; bonus Ziegler–Nichols | Jamal Owesi | #6 |
| P3 Digital PID | Ts, gains, actuator limit, anti-windup on/off | stair-step u[k], samples, continuous reference, performance vs Ts, generated Arduino code with a copy button | Ahmad Abuayyash | #7 |
| P4 Tuning challenge | Kp, Ki, Kd, difficulty | hidden random plant from Module 4's `generate_sensor()`, spec, pass/fail per part, score | Hakam | #8 |
| My system | K, τ (or fit them from a step-test log), ζ, settling time, Ts | Messi drive-motor speed loop design, PWM 0–100 % check, Arduino sketch with encoder | everyone | #9 |
| Validation | – | the three checks of section 2.1, computed by our solver | everyone | #9 |

### Files

```
index.html            home page linking both homeworks
dynamics.html         Homework 1 (module1.py … module4.py), unchanged maths
style.css             shared theme (Homework 1's), used by every page
control/
  index.html          page, tabs, block diagrams, Pyodide loader
  control.css         Control-only layout on top of ../style.css
  py/pid_core.py      the solver: plants, continuous PID (RK4/Euler), digital PID, metrics,
                      Routh test, ultimate gain (ZN), PI design, step-test fit, random plants
  py/ui.py            DOM helpers, sliders, Plotly wrapper, "Predict, then check" box
  py/arduino_code.py  turns gains into an Arduino sketch (same algorithm as the simulation)
  py/p1_playground.py py/p2_sensor.py py/p3_digital.py py/p4_challenge.py
  py/my_system.py     py/validation.py   py/main.py
tests/test_hw1_modules.py  python tests/test_hw1_modules.py   (Homework 1 checks 1–6)
tests/test_pid_core.py     python tests/test_pid_core.py      (Homework 2 checks + solver tests)
```

### How the simulation works

The closed loop is one state vector: plant states, sensor state (P2), integral of the error, and a
derivative filter (D = Kd·s/(Tf·s+1), Tf = 5 time steps). It is stepped with RK4 (Euler selectable in
P1), with the actuator limit applied at every step. The digital PID in P3 and "My system" runs the sheet's
formula at each sample, holds u for Ts, and steps the plant on a finer grid in between.

### Validation (section 2.1)

| Check | Expected | Our solver |
|---|---|---|
| P only, Kp = 9 | τcl = 0.1 s, ess = 10 % | τcl = 0.1000 s, ess = 10.000 % |
| PI, Kp = Ki = 1 | ωn = 1 rad/s, ζ = 1 | ωn = 1, ζ = 1; y(t) matches 1 − e^(−t) to 1e−13 |
| any PI | ess = 0 | worst of 10 random PIs < 0.001 % |

### AI use

We used Claude (Anthropic) to help draft the solver, the module pages and the generated Arduino code,
and to write test cases for the validation checks. Every member reviewed and can explain the code of
their own module. <!-- edit to match what you actually did -->

### Release

Final submission: tag `v2.0`.
