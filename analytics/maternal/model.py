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

# elasticities (fractional change in MMR per unit change), illustrative
ELAST = dict(sba=-0.010, anc4=-0.004, female_literacy=-0.006, fertility=+0.08)


@functools.lru_cache(maxsize=1)
def _panel() -> pd.DataFrame:
    return pd.read_csv(PANEL)


class MaternalScenarioModel(ScenarioModel):
    domain = "maternal"
    title = "Maternal Mortality Explorer"
    primary_outcome = "mmr"

    levers = [
        LeverSpec("sba", "Skilled birth attendance", "%", 0, 100, 1),
        LeverSpec("anc4", "Antenatal care (4+)", "%", 0, 100, 1),
        LeverSpec("female_literacy", "Female literacy", "%", 0, 100, 1),
        LeverSpec("fertility", "Total fertility rate", "births", 1.0, 7.0, 0.1, polarity=+1),
    ]
    outcomes = [OutcomeSpec("mmr", "Maternal mortality ratio", "per 100,000 live births", -1)]

    _cols = ["mmr", "sba", "anc4", "female_literacy", "fertility"]

    def countries(self) -> list[str]:
        return sorted(_panel()["country"].unique().tolist())

    def baseline(self, country: str) -> State:
        row = _panel()[_panel()["country"] == country]
        if row.empty:
            raise ValueError(f"No maternal data for {country}")
        row = row.iloc[0]
        return State(country, int(row["year"]), {c: float(row[c]) for c in self._cols})

    def simulate(self, state: State) -> Outcome:
        base = self.baseline(state.country).values
        v = state.values
        log_mult = 0.0
        for lever, e in ELAST.items():
            log_mult += e * (v[lever] - base[lever])
        mmr = base["mmr"] * pow(2.718281828, log_mult)
        return Outcome({"mmr": round(max(0.0, mmr), 1)})
