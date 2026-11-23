"""Tests for Homework 1 (module1.py - module4.py) in plain Python.

Run:  python tests/test_hw1_modules.py      (or:  python -m pytest tests/)

The modules only import `js` inside their start_*_browser_app() functions, so the
maths can be checked outside the browser. Checks 1-6 are the sheet's validation table.
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import module1  # noqa: E402
import module2  # noqa: E402
import module3  # noqa: E402
import module4  # noqa: E402


# ---------------------------------------------------------------- Module 1
def test_check1_first_order_step():
    (a, ok_a), (b, ok_b) = module1.validation_results()
    assert ok_a and abs(a - 63.2) < 0.05
    assert ok_b and abs(b - 95.0) < 0.05


def test_module1_step_and_ramp():
    K, tau = 2.0, 4.0
    assert abs(module1.step_response(tau, K, tau) - 0.632 * K) < 1e-3
    # ramp: output lags the input by tau, steady-state error = K * tau (for unit ramp)
    assert abs(module1.steady_ramp_error(K, tau) - K * tau) < 1e-9


def test_module1_log_error_slope():
    tau = 3.0
    t1, t2 = 1.0, 4.0
    e1 = module1.normalized_transient_error(t1, tau)
    e2 = module1.normalized_transient_error(t2, tau)
    slope = (math.log(e2) - math.log(e1)) / (t2 - t1)
    assert abs(slope + 1 / tau) < 1e-9


# ---------------------------------------------------------------- Module 2
def test_check2_and_3_frequency():
    for name, (actual, expected, tol, unit) in module2.freq_validation_results().items():
        assert abs(actual - expected) <= tol, (name, actual, expected)


def test_module2_cutoff():
    tau = 0.2
    wc = module2.freq_cutoff(tau)
    assert abs(wc - 5.0) < 1e-12
    assert abs(module2.freq_amplitude_ratio(wc, tau) - 1 / math.sqrt(2)) < 1e-12
    assert abs(module2.freq_phase_lag_degrees(wc, tau) - 45.0) < 1e-9


# ---------------------------------------------------------------- Module 3
def test_check4_5_6_second_order():
    res = module3.second_validation_results()
    assert res["test4"][1] and abs(res["test4"][0] - 16.3) < 0.1
    assert res["test5"][1]
    assert res["test6"][1]


# ---------------------------------------------------------------- Module 4
def test_module4_random_sensors():
    rng = random.Random(0)
    kinds = set()
    for _ in range(200):
        s = module4.generate_sensor(rng)
        kinds.add(s.kind)
        if s.kind == "second":
            assert 0 < s.zeta < 1 and s.wn > 0
        else:
            assert s.K > 0 and s.tau > 0
    assert kinds == {"first", "second"}


def test_module4_scoring():
    s = module4.Sensor("first", K=2.0, tau=3.0)
    assert module4.calculate_score(s, {"K": 2.1, "tau": 2.8})[0] == 100   # within 10 %
    low, perfect, _ = module4.calculate_score(s, {"K": 3.0, "tau": 6.0})
    assert not perfect and low < 100


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("PASS", name)
