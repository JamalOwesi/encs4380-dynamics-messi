"""Tests for control/py/pid_core.py (run with:  python -m pytest tests/  or
python tests/test_pid_core.py). They repeat the homework's validation checks
with the solver, plus a few sanity checks on the other tools."""

import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "control", "py"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))  # module4.py from Homework 1
import pid_core as pc  # noqa: E402


def test_check1_p_only():
    # K = 1, tau = 1, Kp = 9: tau_cl = 0.1 s, ess = 10 %
    plant = pc.FirstOrder(1, 1)
    for method in ("rk4", "euler"):
        sim = pc.simulate_continuous(plant, 9, 0, 0, t_end=2.0, n_steps=4000, method=method)
        m = pc.step_metrics(sim["t"], sim["y"], 1.0)
        tau_cl = pc.time_constant_from_response(sim["t"], sim["y"])
        assert abs(tau_cl - 0.1) < 2e-3, (method, tau_cl)
        assert abs(m["ess_pct"] - 10.0) < 0.05, (method, m["ess_pct"])
    assert pc.p_only_first_order(1, 1, 9) == (0.1, 0.1)


def test_check2_pi():
    # Kp = 1, Ki = 1: wn = 1 rad/s, zeta = 1
    wn, zeta = pc.pi_first_order(1, 1, 1, 1)
    assert abs(wn - 1) < 1e-12 and abs(zeta - 1) < 1e-12
    # The PI zero cancels the plant pole, so y(t) = 1 - exp(-t) exactly
    sim = pc.simulate_continuous(pc.FirstOrder(1, 1), 1, 1, 0, t_end=8.0, n_steps=4000)
    err = max(abs(y - (1 - math.exp(-t))) for t, y in zip(sim["t"], sim["y"]))
    assert err < 1e-4, err
    # characteristic polynomial s^2 + 2 s + 1
    p = pc.char_poly(pc.FirstOrder(1, 1), 1, 1, 0)
    assert [round(c, 9) for c in p] == [1, 2, 1]


def test_check3_any_pi_zero_error():
    rng = random.Random(1)
    for _ in range(25):
        K, tau = rng.uniform(0.3, 3), rng.uniform(0.2, 3)
        Kp, Ki = rng.uniform(0.1, 10), rng.uniform(0.1, 10)
        plant = pc.FirstOrder(K, tau)
        _, zeta = pc.pi_first_order(K, tau, Kp, Ki)
        wn, _ = pc.pi_first_order(K, tau, Kp, Ki)
        t_end = 12.0 / (zeta * wn) if zeta < 1 else 12.0 * max(tau, 1 / wn) * (2 * zeta)
        sim = pc.simulate_continuous(plant, Kp, Ki, 0, t_end=t_end, n_steps=4000)
        assert abs(1 - sim["y"][-1]) < 1e-3, (K, tau, Kp, Ki, sim["y"][-1])


def test_routh_matches_hand_result():
    # first-order plant + PI + sensor: stable iff (tau+tau_s)(1+K Kp) > tau tau_s K Ki
    plant = pc.FirstOrder(1, 1)
    for tau_s in (0.5, 0.9, 1.1, 1.5):
        stable, _ = pc.routh_stable(pc.char_poly(plant, 3, 8, 0, tau_s))
        assert stable == ((1 + tau_s) * 4 > tau_s * 8), tau_s


def test_slow_sensor_overshoot_grows():
    plant = pc.FirstOrder(1, 1)
    last = -1
    for tau_s in (0.0, 0.2, 0.4, 0.6):
        sim = pc.simulate_continuous(plant, 3, 8, 0, t_end=15, tau_s=tau_s)
        m = pc.step_metrics(sim["t"], sim["y"], 1)
        assert m["overshoot"] > last
        last = m["overshoot"]


def test_ultimate_gain():
    # first-order + perfect sensor never oscillates
    assert pc.ultimate_gain(pc.FirstOrder(1, 1)) == (None, None)
    # first-order plant + first-order sensor + extra lag: use 2nd-order plant
    plant = pc.SecondOrder(1, 2, 0.5)
    Ku, Tu = pc.ultimate_gain(plant, tau_s=0.5)
    stable_below, _ = pc.routh_stable(pc.char_poly(plant, 0.95 * Ku, 0, 0, 0.5))
    stable_above, _ = pc.routh_stable(pc.char_poly(plant, 1.05 * Ku, 0, 0, 0.5))
    assert stable_below and not stable_above


def test_digital_small_ts_matches_continuous():
    plant = pc.FirstOrder(1, 1)
    c = pc.simulate_continuous(plant, 2, 3, 0, t_end=6)
    d = pc.simulate_digital(plant, 2, 3, 0, Ts=0.002, t_end=6, anti_windup=False)
    assert abs(c["y"][-1] - d["y"][-1]) < 1e-3
    mc = pc.step_metrics(c["t"], c["y"], 1)
    md = pc.step_metrics(d["t"], d["y"], 1)
    assert abs(mc["overshoot"] - md["overshoot"]) < 0.5


def test_anti_windup_reduces_overshoot():
    plant = pc.FirstOrder(1, 1)
    kw = dict(t_end=10, u_min=0, u_max=1.5)
    a = pc.simulate_digital(plant, 4, 6, 0, 0.02, anti_windup=False, **kw)
    b = pc.simulate_digital(plant, 4, 6, 0, 0.02, anti_windup=True, **kw)
    oa = pc.step_metrics(a["t"], a["y"], 1)["overshoot"]
    ob = pc.step_metrics(b["t"], b["y"], 1)["overshoot"]
    assert ob < oa


def test_fit_first_order():
    K, tau = 3.2, 0.08
    t = [i * 0.001 for i in range(800)]
    y = [K * 50 * (1 - math.exp(-ti / tau)) for ti in t]
    Kf, tauf = pc.fit_first_order(t, y, 50)
    assert abs(Kf - K) < 0.01 and abs(tauf - tau) < 0.002


def test_p4_uses_module4_generator():
    import module4
    for seed in range(20):
        p = pc.random_plant(seed)
        s = module4.generate_sensor(random.Random(seed), signal="step")
        assert p.kind == s.kind
        if s.kind == "first":
            assert (p.K, p.tau) == (s.K, s.tau)
        else:
            assert (p.wn, p.zeta) == (s.wn, s.zeta)


def test_p4_specs_reachable_examples():
    # a hand-tuned PI meets the normal spec on a first-order and a second-order plant
    for plant, gains in ((pc.FirstOrder(1.5, 3.0), (2.0, 1.2, 0.0)),
                         (pc.SecondOrder(1.0, 2.0, 0.4), (1.0, 1.0, 0.5))):
        spec = pc.make_spec(plant, "normal")
        sim = pc.simulate_continuous(plant, *gains, t_end=spec["t_end"], n_steps=2500,
                                     u_min=-spec["u_max"], u_max=spec["u_max"])
        m = pc.step_metrics(sim["t"], sim["y"], 1)
        parts, score = pc.grade(spec, m, max(abs(v) for v in sim["u"]))
        assert score >= 75, (plant.label(), parts)


def test_pi_design_round_trip():
    Kp, Ki = pc.pi_design(2.0, 0.5, 0.7, 6.0)
    wn, zeta = pc.pi_first_order(2.0, 0.5, Kp, Ki)
    assert abs(wn - 6) < 1e-9 and abs(zeta - 0.7) < 1e-9


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("PASS", name)
