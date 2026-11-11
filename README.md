# Dynamic Characteristics Interactive Toolkit

> **Submission stage:** Checkpoint 1 (Tue 3 Nov): Pages live, Module 1 working

**ENCS4380 Interfacing Techniques · Birzeit University · Homework 1 · Group Messi**
Instructor: Dr. Wasel Ghanem

**Live site:** `https://<your-username>.github.io/encs4380-dynamics-<group-name>/`  ← replace with your real link

A static site (GitHub Pages) where all maths and graphs are computed in Python running in the browser through Pyodide. No server, Binder or login is needed.

## Team

| Member | Student ID | Module | GitHub Issue |
|---|---|---|---|
| _name_ | _id_ | 1 · First-order time response | #1 |

## Files

| File | Purpose |
|---|---|
| `index.html` | Landing page linking to the four modules |
| `module1.html` + `module1.py` | Module 1 page and its Python code |
| `style.css` | Shared styling (robotics + samurai theme) |

Each module page loads only its own `.py` file, so each member can work and be graded on their own module.

## Module checklist (from the assignment)


### Module 1 · First-order time response
- [ ] Sliders for K and τ, and a step / ramp input switch
- [ ] 63.2% marker at t = τ and 95% marker at t = 3τ
- [ ] Ramp lag = τ and the steady-state error
- [ ] Error-fraction plot on a log axis with slope −1/τ
- [ ] "Predict, then check" box
- [ ] Validation 1: y(τ) = 0.632 KA and y(3τ) = 0.95 KA (expected, yours, pass/fail)

## Run locally

```
python -m http.server
```

Open `http://localhost:8000`. Opening the HTML by double-click will not work, because the page fetches its `.py` file.

## Screenshots

_Add one screenshot per module here._

## Use of AI tools

_State here what AI coding assistants were used for (required by the assignment). Every member must be able to explain any line of their module in the demo._
