import pytest
from scenario_engine import ScenarioEngine, list_models, load_builtin_models

load_builtin_models()

def test_domains_registered():
    assert "hiv" in list_models()
    assert "maternal" in list_models()

def test_hiv_baseline_invariance():
    eng = ScenarioEngine(domain="hiv")
    r = eng.run("Kenya", {})
    po = r.primary_outcome
    assert abs(r.baseline_outcome[po] - r.scenario_outcome[po]) < 1e-6

def test_hiv_package_reduces_incidence():
    eng = ScenarioEngine(domain="hiv")
    r = eng.run("Kenya", {"viral_suppression": 95, "condom_use": 80, "vmmc_coverage": 90})
    assert r.relative_change_pct[r.primary_outcome] < 0
    assert r.sensitivity  # non-empty
    assert r.recommendations

def test_maternal_runs_through_same_engine():
    eng = ScenarioEngine(domain="maternal")
    r = eng.run("Nigeria", {"sba": 90})
    assert r.relative_change_pct["mmr"] < 0

def test_unknown_domain_raises():
    with pytest.raises(KeyError):
        ScenarioEngine(domain="does_not_exist")
