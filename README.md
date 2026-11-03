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

This project is an interactive web toolkit designed to demonstrate the dynamic characteristics of sensors.

Users can change system parameters, observe how sensors respond to different inputs, and understand important concepts through live graphs and calculations.

The toolkit is developed using HTML, CSS, and JavaScript and is hosted using GitHub Pages.

## Live Website

**[Open SensorLab — Group Messi](https://jamalowesi.github.io/encs4380-dynamics-messi/)**

**GitHub Repository:**

https://github.com/JamalOwesi/encs4380-dynamics-messi

## Checkpoint 1 — November 3, 2026

### Module 1: First-Order Time Response

**Status:** Implemented

Module 1 demonstrates how a first-order sensor responds to step and ramp inputs. Users can adjust the sensor gain and time constant and observe the changes in real time.

### Implemented Features

- Interactive sliders for gain (K) and time constant (τ).
- Step and ramp input selection.
- Live graphs showing the ideal input and sensor output.
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

`y(t) = KA(1 - e^(-t/τ))`

**Ramp response:**

`y(t) = KA[t - τ(1 - e^(-t/τ))]`

**Steady-state ramp error:**

`e_ss = KAτ`

**Transient error fraction:**

`E(t) = e^(-t/τ)`

Taking the natural logarithm:

`ln(E(t)) = -t/τ`

Therefore, the logarithmic error slope is `-1/τ`.

### Validation Results

The following values are checked automatically in Module 1:

| Test | Expected Value | Calculated Value | Result |
|---|---|---|---|
| Step response at t = τ | 63.2% | 63.21% | PASS |
| Step response at t = 3τ | 95.0% | 95.02% | PASS |

The values agree with the expected first-order response from the course lecture.

## Upcoming Modules

### Module 2: First-Order Frequency Response

**Deadline:** November 9, 2026

**Status:** Planned

This module will demonstrate how a first-order sensor responds to sinusoidal inputs at different frequencies.

Planned features include:

- Adjustable time constant and frequency.
- Input and output sine-wave graphs.
- Amplitude ratio and phase lag calculations.
- Bode plot with cutoff frequency.
- Dynamic-error calculator.
- Prediction exercise and validation checks.

### Module 3: Second-Order Response

**Deadline:** November 9, 2026

**Status:** Planned

This module will simulate second-order systems using a mass-spring-damper model.

Planned features include:

- Adjustable damping ratio and natural frequency.
- Underdamped, critically damped, and overdamped responses.
- Rise time, peak time, overshoot, and settling time.
- System poles in the s-plane.
- State-space matrices and eigenvalues.
- Phase-plane trajectory.
- Prediction exercise and validation checks.

### Module 4: Guess the Sensor Challenge

**Deadline:** November 12, 2026

**Status:** Planned

This module will provide an interactive challenge where users estimate unknown sensor parameters from response curves.

Planned features include:

- Random first-order and second-order sensors.
- Noisy response curves.
- Parameter estimation by users.
- Comparison of estimated and actual responses.
- Accuracy-based scoring.
- New sensor and hint buttons.
- Running session score.

## Project Screenshot

![SensorLab Screenshot](assets/preview.png)

## Technologies Used

- **HTML5:** Website structure.
- **CSS3:** Layout, styling, and responsive design.
- **JavaScript:** Mathematical calculations, graphs, sliders, and interactions.
- **Git and GitHub:** Version control and team collaboration.
- **GitHub Pages:** Website hosting.

The website uses a simple Argentina-inspired sky-blue, white, and gold color scheme.

## Running the Project Locally

1. Download or clone the repository.
2. Open the project folder.
3. Open `index.html` in a web browser.
4. Use the sliders and controls to explore the simulations.

No additional software installation or server is required.

## GitHub Collaboration

The project is maintained in a shared public GitHub repository.

Each module has a corresponding GitHub Issue for task organization and assignment.

All group members are expected to contribute to the project through their own GitHub commits.

**[View GitHub Issues](https://github.com/JamalOwesi/encs4380-dynamics-messi/issues)**

The course instructor is invited as a repository collaborator.

## Project Timeline

| Date | Milestone |
|---|---|
| November 3, 2026 | Checkpoint 1 — Module 1 and live GitHub Pages |
| November 9, 2026 | Checkpoint 2 — Modules 2 and 3 |
| November 12, 2026 | Final submission — All four modules and release v1.0 |
| November 15–16, 2026 | Group demonstration |

## AI Assistance

Our group worked on the Dynamic Characteristics Toolkit with assistance from ChatGPT in developing the website, improving the interface, implementing the simulations, and preparing the documentation. The group is responsible for reviewing, testing, and understanding the implementation.
