"""Tests for the Bayesian scenario engine."""
from scenario_engine.bayes_engine import scenario_effect
from scenario_engine.bayes_networks import build_hiv, SCENARIO_PACKAGES


def test_baseline_invariance():
    net = build_hiv()
    base = net.summarise("incidence", net.sample(6000))
    assert abs(base["mean"] - 4.0) < 0.3


def test_do_operator_direction():
    net = build_hiv()
    s0 = net.sample(6000)
    s1 = net.sample(6000, interventions={"art_coverage": 0.95})
    assert s1["viral_suppression"].mean() > s0["viral_suppression"].mean()
    assert s1["incidence"].mean() < s0["incidence"].mean()


def test_hiv_acceleration_reduces_incidence():
    net = build_hiv()
    r = scenario_effect(net, "incidence", SCENARIO_PACKAGES["HIV Acceleration"], n=6000)
    assert r["rel_change_pct"] < -5


def test_conflict_shock_raises_incidence():
    net = build_hiv()
    r = scenario_effect(net, "incidence", SCENARIO_PACKAGES["Conflict shock"], n=6000)
    assert r["rel_change_pct"] > 0


def test_credible_interval_present():
    net = build_hiv()
    s = net.summarise("incidence", net.sample(6000), target=2.5)
    assert s["ci_low"] < s["mean"] < s["ci_high"] and 0 <= s["p_target"] <= 1
