"""Tests for child-survival modules, inverse solver, and predictive model."""
import numpy as np
import pandas as pd
from scenario_engine import ScenarioEngine, get_model, load_builtin_models
from scenario_engine.inverse import solve_for_target
from analytics.predictive import PredictiveModel

load_builtin_models()


def test_child_domains_registered():
    for d in ("neonatal", "child", "under5"):
        assert get_model(d) is not None


def test_baseline_invariance_child():
    for d in ("neonatal", "child", "under5"):
        eng = ScenarioEngine(domain=d)
        r = eng.run("Nigeria", {})
        po = r.primary_outcome
        assert abs(r.relative_change_pct[po]) < 1e-6


def test_u5mr_decomposition_coherent():
    b5 = ScenarioEngine(domain="under5").run("Nigeria", {}).baseline_outcome["u5mr"]
    bn = ScenarioEngine(domain="neonatal").run("Nigeria", {}).baseline_outcome["nmr"]
    bc = ScenarioEngine(domain="child").run("Nigeria", {}).baseline_outcome["child_mortality"]
    assert abs(b5 - (bn + bc)) < 0.1


def test_protective_levers_reduce_mortality():
    eng = ScenarioEngine(domain="under5")
    base = eng.model.baseline("Nigeria")
    # move each lever in its beneficial direction (raise protective, lower risk/shock)
    ov = {}
    for l in eng.model.levers:
        cur = base.values.get(l.key, 0)
        ov[l.key] = min(95, cur + 20) if l.polarity <= 0 else max(0, cur - 20)
    r = eng.run("Nigeria", ov)
    assert r.scenario_outcome["u5mr"] < r.baseline_outcome["u5mr"]


def test_inverse_reports_feasibility():
    m = get_model("under5")
    base = m.baseline("Nigeria").values["u5mr"]
    # trivially reachable target (baseline itself) => feasible, zero effort
    r = solve_for_target(m, "Nigeria", base)
    assert r.feasible and r.effort_fraction == 0.0


def test_predictive_monotone_and_interval():
    df = pd.read_csv("data/processed/hiv/afro_hiv_panel.csv")
    feats = ["viral_suppression", "condom_use", "vmmc_coverage", "sti_prevalence", "hiv_prevalence"]
    signs = {"viral_suppression": -1, "condom_use": -1, "vmmc_coverage": -1,
             "sti_prevalence": 1, "hiv_prevalence": 1}
    pm = PredictiveModel(feats, signs).fit(df[feats].to_numpy(float),
                                           df["hiv_incidence"].to_numpy(float), n_boot=40)
    assert (pm.coef >= 0).all()
    row = {c: float(df.iloc[-1][c]) for c in feats}
    lo, med, hi = pm.predict_interval(row)
    assert lo <= med <= hi
