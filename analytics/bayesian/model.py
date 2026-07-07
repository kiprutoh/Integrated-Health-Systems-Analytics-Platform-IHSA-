"""
Bayesian → ScenarioModel adapter.

Wraps each domain BayesianNetwork (TB, malaria, NCD, SRHR, RHIS, SDG 3) in the
platform's ScenarioModel contract so the registry-driven UI, engine and API expose
them exactly like the mechanistic models. Levers are the network's policy nodes
(probability nodes shown as %, HIS domain scores shown 0–100). simulate() runs the
Monte-Carlo posterior-predictive propagation and returns the outcome mean plus a
95% credible interval.
"""
from __future__ import annotations

import functools

import pandas as pd

from config.settings import ROOT
from scenario_engine import bayes_networks as BN
from scenario_engine.base import LeverSpec, Outcome, OutcomeSpec, ScenarioModel, State
from scenario_engine.registry import register_model
from warehouse import reference

PANELS = ROOT / "data" / "processed" / "bayes"
N_SAMPLES = 1500


@functools.lru_cache(maxsize=8)
def _panel(dom: str) -> pd.DataFrame | None:
    path = PANELS / f"{dom}_baselines.csv"
    return pd.read_csv(path) if path.exists() else None


class BayesianScenarioModel(ScenarioModel):
    def __init__(self, domain: str):
        self.domain = domain
        self.title = BN.TITLES[domain]
        self._outcome_node = BN.OUTCOME[domain]
        label, unit, better = BN.OUTCOME_META[domain]
        self.primary_outcome = self._outcome_node
        self.outcomes = [OutcomeSpec(self._outcome_node, label, unit, -1 if better == "down" else +1)]
        self._better = better
        self._lever_meta = BN.full_lever_specs(domain)
        self.levers = [
            LeverSpec(k, lbl, "%" if kind == "prob" else "score", 0, 100, 1,
                      polarity=-1 if improves else +1)
            for (k, lbl, kind, improves) in self._lever_meta]
        self._kind = {k: kind for (k, _l, kind, _i) in self._lever_meta}

    # ---- countries ----
    def countries(self) -> list[str]:
        if self.domain == "rhis":
            df = _panel_rhis()
            return sorted(df["country"].tolist()) if df is not None else reference.countries()["country"].tolist()
        p = _panel(self.domain)
        return sorted(p["country"].tolist()) if p is not None else reference.countries()["country"].tolist()

    # ---- baseline (slider units) ----
    def _country_baseline(self, country: str) -> dict:
        if self.domain == "rhis":
            return BN.default_baselines("rhis", country)
        p = _panel(self.domain)
        if p is not None and country in set(p["country"]):
            row = p[p["country"] == country].iloc[0].to_dict()
            base = BN.default_baselines(self.domain)
            base.update({k: row[k] for k in base if k in row and pd.notna(row[k])})
            return base
        return BN.default_baselines(self.domain)

    def baseline(self, country: str) -> State:
        node_base = self._country_baseline(country)
        vals = {}
        for k, _lbl, kind, _i in self._lever_meta:
            v = node_base.get(k, 0.0)
            vals[k] = round(v * 100, 1) if kind == "prob" else round(v, 1)
        return State(country, 2023, vals)

    # ---- simulate ----
    def _build_net(self, country: str):
        base = self._country_baseline(country)
        return (BN.build_rhis(country, baseline=base) if self.domain == "rhis"
                else BN.BUILDERS[self.domain](base))

    def simulate(self, state: State) -> Outcome:
        net = self._build_net(state.country)
        base = self.baseline(state.country).values
        # do-operator semantics: intervene ONLY on levers the caller actually changed
        # from baseline. Levers left at baseline are NOT fixed, so mediators (e.g. a
        # coverage node driven by upstream levers) remain free to respond — otherwise
        # fixing a mediator would sever the causal path from its own parents.
        interventions = {}
        for k, _lbl, kind, _i in self._lever_meta:
            if k in state.values and abs(state.values[k] - base.get(k, state.values[k])) > 1e-9:
                interventions[k] = state.values[k] / 100 if kind == "prob" else state.values[k]
        samples = net.sample(N_SAMPLES, interventions=interventions or None, seed=11)
        s = net.summarise(self._outcome_node, samples)
        return Outcome({self._outcome_node: round(s["mean"], 3),
                        f"{self._outcome_node}_ci_low": round(s["ci_low"], 3),
                        f"{self._outcome_node}_ci_high": round(s["ci_high"], 3)})


@functools.lru_cache(maxsize=1)
def _panel_rhis():
    path = ROOT / "data" / "processed" / "his" / "afro_his_maturity.csv"
    return pd.read_csv(path) if path.exists() else None


def register_bayesian_models():
    models = {}
    for dom in ("uhc", "tb", "malaria", "ncd", "srhr", "rhis", "sdg3"):
        models[dom] = register_model(BayesianScenarioModel(dom))
    return models


__all__ = ["BayesianScenarioModel", "register_bayesian_models"]
