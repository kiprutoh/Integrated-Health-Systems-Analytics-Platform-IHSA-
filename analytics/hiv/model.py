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
from analytics import spec_augment as _aug

# spec predictors already represented by the calibrated core (not re-added as extras)
_HANDLED = {"art_coverage", "hiv_testing", "pmtct_coverage", "female_literacy",
            "gender_inequality", "sti_prevalence"}

PANEL = ROOT / "data" / "processed" / "hiv" / "afro_hiv_panel.csv"

# evidence-based effect sizes (documented in docs/)
#   vls: U=U / treatment-as-prevention (Cohen 2011; Rodger 2019); vmmc 60% (Auvert 2005;
#   Bailey 2007; Gray 2007); condom ~80%; prep ~55% (population, adherence-scaled);
#   key populations (UNAIDS 2023); PMTCT Option B+ (>90% vertical, small share of total);
#   harm reduction NSP/OAT for PWID; STI cofactor; female literacy & gender inequality
#   as structural modifiers.
E = dict(vls=0.96, condom=0.80, vmmc=0.60, vmmc_male_share=0.50, prep=0.55,
         sti_per_point=0.06, literacy=0.15, gii=0.40,
         key_pop=0.30, pmtct=0.10, harm_reduction=0.15)


@functools.lru_cache(maxsize=1)
def _panel() -> pd.DataFrame:
    return pd.read_csv(PANEL).sort_values(["country", "year"]).reset_index(drop=True)


def _foi(v: dict) -> float:
    """Relative force of infection (only ratios are meaningful). Each combination-
    prevention and structural factor enters as a multiplicative modifier so that
    scaling any one lever changes incidence (the outcome is sensitive to all 12)."""
    def g(k, d=0.0):
        return float(v.get(k, d))
    i_eff = max(1e-4, g("hiv_prevalence") * (1 - E["vls"] * g("viral_suppression") / 100))
    m_condom = max(0.05, 1 - E["condom"] * g("condom_use") / 100)
    m_vmmc = max(0.05, 1 - E["vmmc"] * E["vmmc_male_share"] * g("vmmc_coverage") / 100)
    m_prep = max(0.05, 1 - E["prep"] * g("prep_coverage") / 100)
    m_kp = max(0.05, 1 - E["key_pop"] * g("key_pop_coverage") / 100)          # UNAIDS
    m_pmtct = max(0.05, 1 - E["pmtct"] * g("pmtct_coverage") / 100)           # Option B+
    m_hr = max(0.05, 1 - E["harm_reduction"] * g("harm_reduction_coverage") / 100)  # NSP/OAT
    m_sti = 1 + E["sti_per_point"] * g("sti_prevalence")
    m_struct = max(0.05, (1 - E["literacy"] * g("female_literacy") / 100)
                   * (1 + E["gii"] * g("gender_inequality")))
    return i_eff * m_condom * m_vmmc * m_prep * m_kp * m_pmtct * m_hr * m_sti * m_struct


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
        LeverSpec("key_pop_coverage", "Key-population service coverage", "%", 0, 100, 1),
        LeverSpec("pmtct_coverage", "PMTCT coverage", "%", 0, 100, 1),
        LeverSpec("harm_reduction_coverage", "Harm reduction (NSP/OAT)", "%", 0, 100, 1),
        LeverSpec("female_literacy", "Female literacy", "%", 0, 100, 1),
        LeverSpec("gender_inequality", "Gender inequality index", "index", 0, 1, 0.01, polarity=+1),
        LeverSpec("sti_prevalence", "STI prevalence", "%", 0, 20, 0.5, polarity=+1),
    ] + _aug.extra_levers("hiv", _HANDLED)
    outcomes = [
        OutcomeSpec("hiv_incidence", "HIV incidence", "per 1,000 uninfected", -1),
    ]

    _cols = ["hiv_prevalence", "viral_suppression", "condom_use", "vmmc_coverage",
             "prep_coverage", "sti_prevalence", "female_literacy", "gender_inequality",
             "pct_know_status", "art_coverage", "hiv_incidence"]
    # evidence-based defaults for predictors not yet in the mined panel
    _defaults = {"key_pop_coverage": 45.0, "pmtct_coverage": 82.0,
                 "harm_reduction_coverage": 25.0, **_aug.extra_defaults("hiv", _HANDLED)}

    def countries(self) -> list[str]:
        return sorted(_panel()["country"].unique().tolist())

    def baseline(self, country: str) -> State:
        sub = _panel()[_panel()["country"] == country].sort_values("year")
        if sub.empty:
            raise ValueError(f"No HIV data for {country}")
        row = sub.iloc[-1]
        vals = {c: float(row[c]) for c in self._cols}
        for k, d in self._defaults.items():
            vals[k] = float(row[k]) if k in row and pd.notna(row[k]) else d
        return State(country, int(row["year"]), vals)

    def simulate(self, state: State) -> Outcome:
        v = state.values
        base = self.baseline(state.country).values
        lam_base = _foi(base)
        lam = _foi(v)
        inc = v["hiv_incidence"] if lam_base <= 0 else base["hiv_incidence"] * lam / lam_base
        inc *= _aug.modifier("hiv", _HANDLED, base, v)      # full-spec secondary determinants
        return Outcome({"hiv_incidence": round(max(0.0, inc), 4)})
