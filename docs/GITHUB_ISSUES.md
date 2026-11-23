# GitHub issues for Homework 2 (one per module)

Create each with `gh issue create --title "..." --body-file - --assignee <github-user>` or in the web UI.

---
### P1 – PID playground
Build the PID playground (`control/py/p1_playground.py`).
- [ ] Plant picker: first order (Module 1) / second order (Module 3)
- [ ] Kp, Ki, Kd and setpoint sliders
- [ ] Block diagram with live gain labels
- [ ] Output vs setpoint plot, control signal plot with the limit
- [ ] Live rise time, overshoot, settling time, steady-state error
- [ ] "Predict, then check" questions
- [ ] Checkpoint (Thu 19 Nov): working on the live link

### P2 – A slow sensor in the loop
Build `control/py/p2_sensor.py`.
- [ ] First-order sensor τs in the feedback path
- [ ] True output and sensor reading on the same plot
- [ ] Overshoot vs τs sweep, Routh stability limit marked
- [ ] Bonus: Ziegler–Nichols (Ku, Tu, rules, "Use" buttons)
- [ ] "Predict, then check" questions
- [ ] Checkpoint (Thu 19 Nov): working on the live link

### P3 – Digital PID
Build `control/py/p3_digital.py` and `control/py/arduino_code.py`.
- [ ] u[k] = Kp e[k] + Ki Ts Σe + Kd (e[k] − e[k−1]) / Ts with zero-order hold
- [ ] Ts slider, stair-step plot, performance vs Ts plot
- [ ] Anti-windup switch (clamping) and actuator limit
- [ ] Generated Arduino code + copy button; same algorithm as the simulation
- [ ] "Predict, then check" questions

### P4 – Tuning challenge
Build `control/py/p4_challenge.py`.
- [ ] Hidden random plant (reuse Module 4's generator)
- [ ] Spec: overshoot ≤ 10 %, settling time limit, zero ess, u never hits its limit
- [ ] Pass/fail per part, score, attempts, reveal button
- [ ] "Predict, then check" questions

### My system + validation
`control/py/my_system.py`, `control/py/validation.py`, `tests/`.
- [ ] Step test on Messi's drive motor (STEP_TEST = true), fit K and τ, cite the source
- [ ] Spec 0.6 ≤ ζ ≤ 0.8, PWM 0–100 %, justify it on the page
- [ ] Final gains, simulated response, Arduino sketch
- [ ] Validation checks 1–3 pass on the page and in `tests/`
- [ ] README updated, release v2.0
