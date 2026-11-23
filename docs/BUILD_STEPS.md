# How Homework 2 was built, step by step

## A. Plan
1. Read the sheet and list what each module must let the user change and must show (section 2 table), plus the validation checks (2.1), the "My system" page (3) and the GitHub rules (4).
2. Keep Homework 1's approach: Python files run in the browser with Pyodide, the page talks to them through `from js import document`, GitHub Pages, no server.
3. Split the work: one shared solver (`pid_core.py`), one helper file for the page (`ui.py`), one file per module.

## B. The solver (`control/py/pid_core.py`)
4. Write the two plants from Homework 1 as state equations:
   first order `dy/dt = (K·u − y)/τ`; second order `y'' = ωn²(K·u − y) − 2ζωn·y'`.
5. Put the whole loop in one state vector: plant states, sensor state `dym/dt = (y − ym)/τs`, integral `dI/dt = e`, derivative filter state.
6. Controller at each step: `e = r − ym`, `u = Kp·e + Ki·I + Kd·(filtered de/dt)`, then clamp u to the actuator limit.
7. Step it in time with RK4 (and Euler as an option). Stop early if the output blows up.
8. Digital PID: a class that runs the sheet's formula `u[k] = Kp e[k] + Ki Ts Σe + Kd (e[k] − e[k−1])/Ts`, with clamping anti-windup. Hold u for Ts and step the plant on a finer grid in between.
9. Metrics from the simulated response: 10–90 % rise time, overshoot vs final value, 2 % settling time, steady-state error; flag "not settled" and "unstable".
10. Extra tools: characteristic polynomial + Routh test, ultimate gain Ku and period Tu (phase = −180°) for Ziegler–Nichols, PI design formulas, 63.2 % step-test fit, random plant + spec + grading for P4.

## C. Validate before building pages
11. Write `tests/test_pid_core.py`: check 1 (Kp = 9 gives τcl = 0.1 s and 10 % error), check 2 (Kp = Ki = 1 gives ωn = 1, ζ = 1, and y = 1 − e^(−t)), check 3 (random PIs give zero error), plus Routh, sensor, digital and anti-windup tests.
12. Run `python tests/test_pid_core.py` until everything passes. Only then start on the page.

## D. The page
13. `control/index.html`: header, tabs (Overview, P1–P4, My system, Validation), one `<section>` per module with empty divs for controls, plots, metrics and the predict box. Load Plotly and Pyodide from CDNs, fetch the `.py` files into Pyodide's file system, run `main.start()`.
14. `ui.py`: helpers to build sliders/checkboxes as HTML, read values, bind events (one redraw per animation frame), draw Plotly plots, and the reusable "Predict, then check" box.
15. P1: plant + gain sliders, setpoint, limit, solver choice → simulate → plot y and u (with limit lines) → metrics table + hand formulas + Routh result. Block diagram SVG with live labels.
16. P2: same plant/gains plus τs → plot true y and sensor ym together → table of both overshoots → Routh inequality with numbers → overshoot-vs-τs sweep with the oscillation boundary → ZN bonus panel.
17. P3: Ts, gains, limit, anti-windup → digital simulation with the continuous loop as a dashed reference → stair-step u[k] and the integral term → performance-vs-Ts sweep → generated Arduino code + copy button.
18. P4: random plant with a seed, spec card, live response with the spec drawn on the plot, "Check" button that grades each part and keeps attempts/best score, "Reveal" button.
19. My system: K and τ inputs with a source field (warning while they are placeholders), step-test fit tool, ζ/settling-time spec → PI gains from the formulas → digital simulation with PWM 0–100 % → pass/fail checks → Arduino sketch with encoder reading and a STEP_TEST switch.
20. Validation tab: runs the three checks with the solver and shows expected vs measured, PASS/FAIL, and two plots.
21. Styling: reuse Homework 1's `style.css` for everything; `control/control.css` only adds the two-column layout (collapses on phones), tables, code box, diagrams and Plotly fixes.

## E. Test the page
22. Serve the repo locally (`python -m http.server`), open `/control/`, click every tab, move every slider, answer every predict question, press every button; watch the browser console for errors.
23. Check on a phone-width window.
24. Compile-check the generated Arduino code (Arduino IDE "Verify").

## F. Your own system
25. Upload the sketch from "My system" with `STEP_TEST = true`, wheel off the ground, set `COUNTS_PER_REV` and the pins for Messi.
26. Copy the serial log into the fit tool → K and τ → "Use these values" → write the source.
27. Pick ζ (0.6–0.8) and a settling time, check every row is PASS, edit the "Why this spec" paragraph with your numbers, copy the final sketch.

## G. GitHub
28. Home page `index.html` links every module of both homeworks; the Homework 1 page becomes `dynamics.html` with nav links to Home and Control.
29. One issue per module (`GITHUB_ISSUES.md`), assigned to its owner. Each owner commits their own module from their own account.
30. Update the README (`README_HW2_SECTION.md`), including the AI-use note.
31. Push, check the GitHub Pages link, tag the release: `git tag v2.0 && git push origin v2.0`, then create the release on GitHub and post the Pages link on the course page.
