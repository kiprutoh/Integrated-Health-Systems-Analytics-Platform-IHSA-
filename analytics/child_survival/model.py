"""
Child-survival scenario models — cause-deletion (Lives-Saved-Tool style).

Three registered models share one illustrative panel and a common reduced-form
cause-deletion engine:

  * NeonatalModel    -> neonatal mortality rate (NMR, per 1,000 live births)
  * ChildModel       -> child mortality 1-59 months (per 1,000 live births)
  * UnderFiveModel   -> under-five mortality rate (U5MR, per 1,000 live births)

Each intervention has an "impact per unit coverage" parameter folding cause share
x effectiveness x affected-fraction into one transparent, monotone coefficient.
Raising coverage from C0 to C1 reduces the relevant mortality by a factor
(1 - impact x max(0, C1-C0)); interventions combine multiplicatively. Everything
is anchored to the observed rate, so a no-change scenario reproduces it exactly.

U5MR is decomposed additively per 1,000 live births:
    U5MR = NMR + PNMR ,  PNMR = (U5MR - NMR)   [post-neonatal 1-59 mo deaths]
so the under-five model recombines the neonatal and child segments coherently.
"""
from __future__ import annotations

import functools

import pandas as pd

from config.settings import ROOT
from scenario_engine.base import LeverSpec, Outcome, OutcomeSpec, ScenarioModel, State

PANEL = ROOT / "data" / "processed" / "child_survival" / "afro_child_survival_panel.csv"

# impact per unit (fractional) coverage gain — illustrative LiST-style coefficients
NEONATAL_IMPACT = {
    "sba": 0.20, "neonatal_resuscitation": 0.10, "kangaroo_mother_care": 0.12,
    "neonatal_sepsis_mgmt": 0.12, "pnc": 0.08,
}
CHILD_IMPACT = {
    "dtp3": 0.10, "measles": 0.08, "pcv": 0.10, "rota": 0.08,
    "ors_zinc": 0.12, "careseeking_pneumonia": 0.10, "itn_use": 0.10,
    "vitamin_a": 0.08, "exclusive_bf": 0.10,
}


@functools.lru_cache(maxsize=1)
def _panel() -> pd.DataFrame:
    return pd.read_csv(PANEL)


def _reduction_factor(base: dict, scen: dict, impact: dict) -> float:
    f = 1.0
    for lever, imp in impact.items():
        dc = (scen.get(lever, base[lever]) - base[lever]) / 100.0
        if dc > 0:
            f *= (1.0 - imp * dc)
    return max(0.05, f)


def _labels(keys):
    pretty = {
        "sba": "Skilled birth attendance", "neonatal_resuscitation": "Newborn resuscitation",
        "kangaroo_mother_care": "Kangaroo mother care", "neonatal_sepsis_mgmt": "Neonatal sepsis management",
        "pnc": "Postnatal care", "dtp3": "DTP3 immunisation", "measles": "Measles immunisation",
        "pcv": "PCV (pneumococcal)", "rota": "Rotavirus vaccine", "ors_zinc": "ORS + zinc (diarrhoea)",
        "careseeking_pneumonia": "Pneumonia careseeking", "itn_use": "ITN use (malaria)",
        "vitamin_a": "Vitamin A", "exclusive_bf": "Exclusive breastfeeding",
    }
    return [LeverSpec(k, pretty.get(k, k), "%", 0, 100, 1) for k in keys]


class _ChildSurvivalBase(ScenarioModel):
    _cols = (["nmr", "u5mr"] + list(NEONATAL_IMPACT) + list(CHILD_IMPACT))

    def countries(self) -> list[str]:
        return sorted(_panel()["country"].unique().tolist())

    def baseline(self, country: str) -> State:
        sub = _panel()[_panel()["country"] == country]
        if sub.empty:
            raise ValueError(f"No child-survival data for {country}")
        row = sub.iloc[0]
        return State(country, int(row["year"]),
                     {c: float(row[c]) for c in self._cols if c in row})


class NeonatalModel(_ChildSurvivalBase):
    domain = "neonatal"
    title = "Neonatal Mortality Explorer"
    primary_outcome = "nmr"
    levers = _labels(NEONATAL_IMPACT)
    outcomes = [OutcomeSpec("nmr", "Neonatal mortality rate", "per 1,000 live births", -1)]

    def simulate(self, state: State) -> Outcome:
        base = self.baseline(state.country).values
        f = _reduction_factor(base, state.values, NEONATAL_IMPACT)
        return Outcome({"nmr": round(base["nmr"] * f, 2)})


class ChildModel(_ChildSurvivalBase):
    domain = "child"
    title = "Child Mortality Explorer (1–59 months)"
    primary_outcome = "child_mortality"
    levers = _labels(CHILD_IMPACT)
    outcomes = [OutcomeSpec("child_mortality", "Child mortality (1–59 months)",
                            "per 1,000 live births", -1)]

    def simulate(self, state: State) -> Outcome:
        base = self.baseline(state.country).values
        pnmr = max(0.0, base["u5mr"] - base["nmr"])
        f = _reduction_factor(base, state.values, CHILD_IMPACT)
        return Outcome({"child_mortality": round(pnmr * f, 2)})


class UnderFiveModel(_ChildSurvivalBase):
    domain = "under5"
    title = "Under-Five Mortality Explorer"
    primary_outcome = "u5mr"
    levers = _labels(list(NEONATAL_IMPACT) + list(CHILD_IMPACT))
    outcomes = [OutcomeSpec("u5mr", "Under-five mortality rate", "per 1,000 live births", -1)]

    def simulate(self, state: State) -> Outcome:
        base = self.baseline(state.country).values
        nmr_scen = base["nmr"] * _reduction_factor(base, state.values, NEONATAL_IMPACT)
        pnmr = max(0.0, base["u5mr"] - base["nmr"])
        pnmr_scen = pnmr * _reduction_factor(base, state.values, CHILD_IMPACT)
        return Outcome({"u5mr": round(nmr_scen + pnmr_scen, 2)})
