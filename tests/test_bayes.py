"""Tests for the Bayesian scenario engine and all domain networks."""
try:
    import pytest
except ModuleNotFoundError:  # offline: minimal shim so tests run standalone
    class _Mark:
        def parametrize(self, argnames, argvalues):
            def deco(fn):
                fn._params = argvalues
                return fn
            return deco
    class _PT:
        mark = _Mark()
    pytest = _PT()
from scenario_engine.bayes_engine import scenario_effect
from scenario_engine import bayes_networks as BN


def _net(dom):
    return BN.BUILDERS[dom]("Kenya") if dom == "rhis" else BN.BUILDERS[dom]()


def test_all_networks_baseline_invariance():
    for dom, build in BN.BUILDERS.items():
        net = _net(dom); oc = BN.OUTCOME[dom]
        a = net.summarise(oc, net.sample(4000))["mean"]
        b = net.summarise(oc, net.sample(4000, interventions={}))["mean"]
        assert abs(a - b) < 1e-9, dom


def test_every_domain_has_scenarios():
    for dom in BN.BUILDERS:
        assert dom in BN.SCENARIO_LIBRARY and len(BN.SCENARIO_LIBRARY[dom]) >= 2


def test_credible_intervals_present():
    for dom, build in BN.BUILDERS.items():
        net = _net(dom); s = net.summarise(BN.OUTCOME[dom], net.sample(4000))
        assert s["ci_low"] - 1e-6 <= s["mean"] <= s["ci_high"] + 1e-6, dom


@pytest.mark.parametrize("dom,pkg,direction", [
    ("tb", "Find-Treat-Cure", "down"),
    ("malaria", "Vector-control scale-up", "down"),
    ("ncd", "HEARTS hypertension", "down"),
    ("srhr", "FP scale-up", "up"),          # positive index: higher is better
    ("rhis", "Governance strengthening", "up"),
    ("sdg3", "UHC investment", "up"),
])
def test_scenario_direction(dom, pkg, direction):
    net = _net(dom)
    r = scenario_effect(net, BN.OUTCOME[dom], BN.SCENARIO_LIBRARY[dom][pkg], n=5000)
    assert (r["rel_change_pct"] < -2) if direction == "down" else (r["rel_change_pct"] > 2)


def test_rhis_uses_mined_baseline():
    net = BN.build_rhis("Kenya")
    assert 40 < net.summarise("his_maturity_index", net.sample(3000))["mean"] < 70


def test_tb_cascade_do_operator():
    tb = BN.build_tb()
    s0 = tb.sample(4000); s1 = tb.sample(4000, interventions={"genexpert": 0.95})
    assert s1["case_detection"].mean() > s0["case_detection"].mean()
    assert s1["incidence"].mean() < s0["incidence"].mean()
