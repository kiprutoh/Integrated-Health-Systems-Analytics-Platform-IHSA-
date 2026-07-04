"""
HIV scenario model — first concrete implementation of the platform contract.

Wraps the mechanistic 95-95-95 treatment-as-prevention + combination-prevention
transmission model as a `ScenarioModel`, so it runs through the shared engine
exactly like every future domain will. Incidence is projected as the observed
baseline scaled by the relative change in the force of infection, anchored so that
a no-change scenario reproduces the observed value.
"""
from __future__ import annotations

import functools
from pathlib import Path

import pandas as pd

from config.settings import ROOT
from scenario_engine.base import LeverSpec, Outcome, OutcomeSpec, ScenarioModel, State

PANEL = ROOT / "data" / "processed" / "hiv" / "afro_hiv_panel.csv"

# evidence-based effect sizes (documented in docs/)
E = dict(vls=0.96, condom=0.80, vmmc=0.60, vmmc_male_share=0.50, prep=0.55,
         sti_per_point=0.06, literacy=0.15, gii=0.40)


@functools.lru_cache(maxsize=1)
def _panel() -> pd.DataFrame:
    return pd.read_csv(PANEL).sort_values(["country", "year"]).reset_index(drop=True)


def _foi(v: dict) -> float:
    """Relative force of infection (only ratios are meaningful)."""
    i_eff = max(1e-4, v["hiv_prevalence"] * (1 - E["vls"] * v["viral_suppression"] / 100))
    m_condom = max(0.05, 1 - E["condom"] * v["condom_use"] / 100)
    m_vmmc = max(0.05, 1 - E["vmmc"] * E["vmmc_male_share"] * v["vmmc_coverage"] / 100)
    m_prep = max(0.05, 1 - E["prep"] * v["prep_coverage"] / 100)
    m_sti = 1 + E["sti_per_point"] * v["sti_prevalence"]
    m_struct = max(0.05, (1 - E["literacy"] * v["female_literacy"] / 100)
                   * (1 + E["gii"] * v["gender_inequality"]))
    return i_eff * m_condom * m_vmmc * m_prep * m_sti * m_struct


class HIVScenarioModel(ScenarioModel):
    domain = "hiv"
    title = "HIV Scenario Explorer"
    primary_outcome = "hiv_incidence"

    levers = [
        LeverSpec("pct_know_status", "Know status (1st 95)", "%", 0, 100, 1),
        LeverSpec("art_coverage", "ART coverage (2nd 95)", "%", 0, 100, 1),
        LeverSpec("viral_suppression", "Viral suppression (3rd 95)", "%", 0, 100, 1),
        LeverSpec("condom_use", "Condom use", "%", 0, 100, 1),
        LeverSpec("vmmc_coverage", "VMMC coverage", "%", 0, 100, 1),
        LeverSpec("prep_coverage", "PrEP coverage", "%", 0, 30, 0.5),
        LeverSpec("female_literacy", "Female literacy", "%", 0, 100, 1),
        LeverSpec("sti_prevalence", "STI prevalence", "%", 0, 20, 0.5, polarity=+1),
    ]
    outcomes = [
        OutcomeSpec("hiv_incidence", "HIV incidence", "per 1,000 uninfected", -1),
    ]

    _cols = ["hiv_prevalence", "viral_suppression", "condom_use", "vmmc_coverage",
             "prep_coverage", "sti_prevalence", "female_literacy", "gender_inequality",
             "pct_know_status", "art_coverage", "hiv_incidence"]

    def countries(self) -> list[str]:
        return sorted(_panel()["country"].unique().tolist())

    def baseline(self, country: str) -> State:
        sub = _panel()[_panel()["country"] == country].sort_values("year")
        if sub.empty:
            raise ValueError(f"No HIV data for {country}")
        row = sub.iloc[-1]
        return State(country, int(row["year"]), {c: float(row[c]) for c in self._cols})

    def simulate(self, state: State) -> Outcome:
        v = state.values
        # anchor to observed incidence via relative force of infection
        base = self.baseline(state.country).values
        lam_base = _foi(base)
        lam = _foi(v)
        inc = v["hiv_incidence"] if lam_base <= 0 else base["hiv_incidence"] * lam / lam_base
        return Outcome({"hiv_incidence": round(max(0.0, inc), 4)})
