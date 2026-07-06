"""
Maternal mortality scenario model — second domain on the shared contract.

Transparent log-linear elasticity model: MMR responds to skilled birth attendance,
ANC4, female literacy and fertility. Illustrative only. Demonstrates that a very
different modelling approach still plugs into the same engine as HIV.
"""
from __future__ import annotations

import functools

import pandas as pd

from config.settings import ROOT
from scenario_engine.base import LeverSpec, Outcome, OutcomeSpec, ScenarioModel, State

PANEL = ROOT / "data" / "processed" / "maternal" / "afro_maternal_panel.csv"

# Elasticities = fractional change in MMR per unit change in the predictor (illustrative,
# grounded in the maternal-survival evidence: the continuum of care and the three-delays
# framework; EmONC and blood for the direct obstetric causes; family planning/Adding It Up
# for high-risk pregnancies; anaemia and adolescent fertility as risk factors).
ELAST = dict(
    sba=-0.010,               # skilled birth attendance
    facility_delivery=-0.006,  # institutional delivery
    emonc=-0.012,             # emergency obstetric & newborn care (addresses direct causes)
    blood_availability=-0.004,  # blood for postpartum haemorrhage (leading cause)
    anc4=-0.004,              # antenatal care (4+ contacts)
    postnatal_care=-0.003,    # early postnatal care
    mcpr=-0.006,              # modern contraceptive prevalence (fewer high-risk pregnancies)
    midwife_density=-0.004,   # skilled-workforce density
    female_literacy=-0.006,   # structural (education)
    anaemia=+0.005,           # maternal anaemia (risk)
    adolescent_fertility=+0.0008,  # births per 1,000 women 15-19 (risk)
    fertility=+0.08,          # total fertility rate (risk)
)


@functools.lru_cache(maxsize=1)
def _panel() -> pd.DataFrame:
    return pd.read_csv(PANEL)


class MaternalScenarioModel(ScenarioModel):
    domain = "maternal"
    title = "Maternal Mortality Explorer"
    primary_outcome = "mmr"

    levers = [
        LeverSpec("sba", "Skilled birth attendance", "%", 0, 100, 1),
        LeverSpec("facility_delivery", "Facility delivery", "%", 0, 100, 1),
        LeverSpec("emonc", "Emergency obstetric & newborn care", "%", 0, 100, 1),
        LeverSpec("blood_availability", "Blood availability", "%", 0, 100, 1),
        LeverSpec("anc4", "Antenatal care (4+)", "%", 0, 100, 1),
        LeverSpec("postnatal_care", "Postnatal care", "%", 0, 100, 1),
        LeverSpec("mcpr", "Modern contraceptive prevalence", "%", 0, 100, 1),
        LeverSpec("midwife_density", "Skilled-workforce density", "index", 0, 100, 1),
        LeverSpec("female_literacy", "Female literacy", "%", 0, 100, 1),
        LeverSpec("anaemia", "Maternal anaemia prevalence", "%", 0, 100, 1, polarity=+1),
        LeverSpec("adolescent_fertility", "Adolescent fertility rate", "per 1,000", 0, 200, 1, polarity=+1),
        LeverSpec("fertility", "Total fertility rate", "births", 1.0, 7.0, 0.1, polarity=+1),
    ]
    outcomes = [OutcomeSpec("mmr", "Maternal mortality ratio", "per 100,000 live births", -1)]

    _cols = ["mmr", "sba", "anc4", "female_literacy", "fertility"]
    # evidence-based defaults for predictors not yet in the mined panel (typical AFRO)
    _defaults = {"facility_delivery": 62.0, "emonc": 45.0, "blood_availability": 55.0,
                 "postnatal_care": 55.0, "mcpr": 30.0, "midwife_density": 40.0,
                 "anaemia": 40.0, "adolescent_fertility": 100.0}

    def countries(self) -> list[str]:
        return sorted(_panel()["country"].unique().tolist())

    def baseline(self, country: str) -> State:
        row = _panel()[_panel()["country"] == country]
        if row.empty:
            raise ValueError(f"No maternal data for {country}")
        row = row.iloc[0]
        vals = {c: float(row[c]) for c in self._cols}
        for k, d in self._defaults.items():
            vals[k] = float(row[k]) if k in row and pd.notna(row[k]) else d
        return State(country, int(row["year"]), vals)

    def simulate(self, state: State) -> Outcome:
        base = self.baseline(state.country).values
        v = state.values
        log_mult = 0.0
        for lever, e in ELAST.items():
            log_mult += e * (v.get(lever, base.get(lever, 0.0)) - base.get(lever, 0.0))
        mmr = base["mmr"] * pow(2.718281828, log_mult)
        return Outcome({"mmr": round(max(0.0, mmr), 1)})
