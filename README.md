# SensorLab — Dynamic Characteristics Toolkit

**ENCS4380 — Interfacing Techniques**

**Birzeit University**

**Instructor:** Dr. Wasel Ghanem

**Group Name:** Messi

## Group Members

| Name | Assigned Module |
|---|---|
| Ahmad AbuAyyash | Module 1 — First-Order Time Response |
| Jamal Owesi | Module 2 — First-Order Frequency Response |
| Hakam Snouber | Module 3 — Second-Order Response |
| Abd-Alfattah Dawood | Module 4 — Guess the Sensor Challenge |

## Project Overview

SensorLab is an interactive educational website designed to demonstrate the dynamic characteristics of sensors.

Users can change system parameters, observe how sensors respond to different inputs, and understand important engineering concepts through live graphs and calculations.

The project contains four interactive modules. The simulations, calculations, graphs, and interactions are developed using Python running directly in the browser through Pyodide.

HTML and CSS are used for the website structure and design, while a small JavaScript file loads the Python environment.

## Live Website

**GitHub Pages:**

https://jamalowesi.github.io/encs4380-dynamics-messi/

**GitHub Repository:**

https://github.com/JamalOwesi/encs4380-dynamics-messi

**Note:** The new Python version has been prepared locally. The live website will show the updated Python implementation after the new files are uploaded and deployed to GitHub Pages.

## Module 1 — First-Order Time Response

**Status:** Implemented in Python

**Checkpoint 1:** November 3, 2026

Module 1 demonstrates how a first-order sensor responds to step and ramp inputs. Users can adjust the sensor gain and time constant and observe the changes in real time.

### Implemented Features

- Interactive sliders for gain (K) and time constant (τ).
- Step and ramp input selection.
- Live graphs comparing the ideal input and sensor output.
- Response markers at 63.2% (t = τ) and 95% (t = 3τ).
- Ramp time lag and steady-state error calculations.
- Logarithmic error-fraction graph.
- Display of the error decay slope (−1/τ).
- Interactive "Predict, then check" exercise.
- Automatic validation checks.
- Responsive interface for desktop and mobile devices.

### Mathematical Model

The first-order system is described by:

`τ dy/dt + y = Kx`

**Step response:**

`y(t) = KA(1 - exp(-t/τ))`

**Ramp response:**

`y(t) = KA[t - τ(1 - exp(-t/τ))]`

**Steady-state ramp error:**

`e_ss = KAτ`

**Transient error fraction:**

`E(t) = exp(-t/τ)`

Taking the natural logarithm:

`ln(E(t)) = -t/τ`

Therefore, the logarithmic error slope is `-1/τ`.

**Python Source:** `module1.py`

## Module 2 — First-Order Frequency Response

**Status:** Implemented in Python

**Checkpoint 2:** November 9, 2026

Module 2 demonstrates how a first-order sensor responds to sinusoidal inputs at different frequencies.

### Implemented Features

- Interactive sliders for time constant (τ) and angular frequency (ω).
- Input and output sine waves displayed on the same graph.
- Amplitude ratio and phase lag calculations.
- Bode magnitude and phase plots.
- Cutoff frequency at ω = 1/τ.
- Dynamic-error calculator.
- Maximum allowable time-constant calculator.
- Interactive "Predict, then check" exercise.
- Automatic validation checks based on lecture examples.

### Mathematical Model

**Amplitude ratio:**

`M = 1 / sqrt(1 + (ωτ)^2)`

**Phase shift:**

`φ = -atan(ωτ)`

**Dynamic error:**

`δ = M - 1`

**Cutoff angular frequency:**

`ωc = 1/τ`

The module displays how increasing frequency affects the amplitude and phase of the sensor output.

**Python Source:** `module2.py`

## Module 3 — Second-Order Response

**Status:** Implemented in Python

**Checkpoint 2:** November 9, 2026

Module 3 demonstrates the dynamic behavior of second-order systems using a mass-spring-damper model.

### Implemented Features

- Interactive sliders for mass (m), damping (b), and stiffness (k).
- Underdamped, critically damped, and overdamped responses.
- Live second-order step-response graphs.
- Rise time, peak time, overshoot, and settling time calculations.
- System poles displayed in the s-plane.
- State-space matrices A and B.
- Eigenvalue calculations.
- Phase-plane graph displaying displacement and velocity.
- Interactive "Predict, then check" exercise.
- Automatic validation checks.

### Mathematical Model

The mass-spring-damper system is described by:

`m x'' + b x' + kx = F(t)`

**Natural frequency:**

`ωn = sqrt(k/m)`

**Damping ratio:**

`ζ = b / (2 sqrt(mk))`

### State-Space Representation

Using displacement and velocity as state variables:

`x1 = x`

`x2 = dx/dt`

State matrix:

`A = [[0, 1], [-k/m, -b/m]]`

Input matrix:

`B = [[0], [1/m]]`

Output equation:

`y = [1, 0]x`

The module updates the system matrices, eigenvalues, and response graphs when the parameters change.

**Python Source:** `module3.py`

## Module 4 — Guess the Sensor Challenge

**Status:** Implemented in Python

**Final Submission:** November 12, 2026

Module 4 is an interactive challenge where users analyze an unknown sensor response and estimate its parameters.

### Implemented Features

- Random first-order and second-order sensor models.
- First-order step and sine response challenges.
- Second-order step response challenges.
- Response curves with simulated measurement noise.
- Hidden sensor parameters.
- Parameter estimation by users.
- Reveal of actual parameters after submitting a guess.
- Comparison of estimated and actual response curves.
- Accuracy-based scoring system.
- "New Sensor" button to generate another challenge.
- Hint button to help users estimate parameters.
- Running session score and average results.

### Scoring System

The challenge awards a maximum score of 100 points for each round.

Users receive full marks when all their estimated parameters are within 10% of the actual sensor values.

Less accurate estimates receive partial credit based on their relative error.

The session maintains the total score and average performance across multiple rounds.

**Python Source:** `module4.py`

## Validation Results

The Python calculations were checked against the expected values from the course lecture.

| Test | Expected Value | Calculated Value | Result |
|---|---|---|---|
| Module 1: Step at t = τ | 63.2% | 63.212% | PASS |
| Module 1: Step at t = 3τ | 95.0% | 95.021% | PASS |
| Module 2: Amplitude ratio | 0.93 | 0.9285 | PASS |
| Module 2: Phase lag | 21.8° | 21.801° | PASS |
| Module 2: Maximum τ at 100 Hz | 0.52 ms | 0.523 ms | PASS |
| Module 2: Phase lag at 50 Hz | 9.3° | 9.33° | PASS |
| Module 3: Overshoot at ζ = 0.5 | 16.3% | 16.30% | PASS |
| Module 3: Overshoot at ζ = 1 | 0% | 0% | PASS |
| Module 3: Eigenvalues for m = 1, b = 2, k = 4 | −1 ± j1.732 | −1 ± j1.732 | PASS |

These results confirm that the numerical calculations agree with the expected lecture values.

The complete Python/Pyodide website still requires final browser testing before submission.

## Project Screenshots

![Python Module 1 Screenshot](assets/python-module1-desktop-preview.png)

Additional screenshots can be added after the final testing of the four modules.

## Technologies Used

- **Python:** Mathematical calculations, sensor simulations, graphs, and interactions.
- **Pyodide:** Executes Python directly inside the web browser.
- **HTML5:** Website structure.
- **CSS3:** Layout, styling, and responsive design.
- **JavaScript:** Loads the Pyodide environment and Python modules.
- **Git and GitHub:** Version control and collaboration.
- **GitHub Pages:** Static website hosting.

The website uses a simple Argentina-inspired sky-blue, white, and gold color scheme.

## Project Structure

The project is organized into separate Python files for each module.

| File | Description |
|---|---|
| `index.html` | Main website |
| `module1.py` | First-order time response |
| `module2.py` | First-order frequency response |
| `module3.py` | Second-order response |
| `module4.py` | Guess the Sensor Challenge |
| `assets/boot.js` | Python runtime initialization |
| `assets/styles.css` | Main website styling |
| `assets/frequency.css` | Module 2 styling |
| `assets/second-order.css` | Module 3 styling |
| `assets/challenge.css` | Module 4 styling |
| `README.md` | Project documentation |

## Running the Project Locally

1. Download or clone the project repository.
2. Extract the project files if downloaded as a ZIP.
3. Open the folder containing `index.html` and the Python files.
4. Open `index.html` using Chrome or Microsoft Edge.
5. Make sure the computer is connected to the internet because Pyodide loads from an external CDN.
6. Confirm that the Python engine is ready.
7. Explore the four modules using the interactive controls.

A Python backend server is not required to run the published website.

## GitHub Collaboration

The project is maintained in a shared public GitHub repository.

Each module has a corresponding GitHub Issue for task organization and assignment.

Group members are responsible for contributing to their assigned modules and maintaining their work through GitHub commits.

**GitHub Issues:**

https://github.com/JamalOwesi/encs4380-dynamics-messi/issues

The instructor, Dr. Wasel Ghanem, has been invited as a repository collaborator.

## Project Timeline

| Date | Milestone |
|---|---|
| November 3, 2026 | Checkpoint 1 — Module 1 |
| November 9, 2026 | Checkpoint 2 — Modules 2 and 3 |
| November 12, 2026 | Final submission — All four modules and release v1.0 |
| November 15–16, 2026 | Group demonstration |

## AI Assistance

ChatGPT assisted the group with the Python conversion, interface development, and documentation. The group is responsible for reviewing, testing, understanding, and explaining the implementation and results.

## Final Submission

Before the final submission, the group will verify that all four modules are functioning correctly on GitHub Pages, review the validation results, and update the project documentation if necessary.

The final submission requires a GitHub release tagged `v1.0` and the live website link on the course page.
