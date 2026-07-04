"""
The shared scenario engine.

Runs the charter's end-to-end workflow around ANY registered ScenarioModel:

  Current State -> Intervention -> Simulation -> Forecast
                -> Impact Assessment -> Sensitivity Analysis -> Policy Recommendations

Because the workflow lives here (not in each disease module), every domain gets
forecasting, impact accounting, sensitivity analysis and recommendation scaffolding
for free.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

from config.logging_config import get_logger
from forecasting.base import approach_to_target
from scenario_engine.base import Outcome, ScenarioModel, State
from scenario_engine.registry import get_model

log = get_logger("scenario_engine.engine")


@dataclass
class ScenarioResult:
    domain: str
    country: str
    year: int
    primary_outcome: str
    baseline_state: dict
    scenario_state: dict
    baseline_outcome: dict
    scenario_outcome: dict
    relative_change_pct: dict
    forecast: dict = field(default_factory=dict)
    sensitivity: list = field(default_factory=list)
    recommendations: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


class ScenarioEngine:
    def __init__(self, model: ScenarioModel | None = None, domain: str | None = None):
        if model is None:
            if domain is None:
                raise ValueError("Provide either a model or a domain.")
            model = get_model(domain)
        self.model = model

    # --- individual steps -------------------------------------------------- #
    def _relative_change(self, base: Outcome, scen: Outcome) -> dict:
        out = {}
        for k, b in base.metrics.items():
            s = scen.metrics.get(k, b)
            out[k] = round((s - b) / b * 100, 2) if b else 0.0
        return out

    def _forecast(self, base_state: State, scen_state: State, horizon: int) -> dict:
        """Project the primary outcome as coverage moves toward the scenario."""
        po = self.model.primary_outcome
        base_val = self.model.simulate(base_state).metrics.get(po)
        scen_val = self.model.simulate(scen_state).metrics.get(po)
        if base_val is None or scen_val is None:
            return {}
        proj = approach_to_target(base_val, scen_val, base_state.year, horizon=horizon)
        return {"outcome": po, "years": proj.years, "values": proj.values,
                "method": proj.method}

    def _sensitivity(self, base_state: State, intervention: dict) -> list:
        """One-at-a-time: contribution of each lever to the total change."""
        po = self.model.primary_outcome
        full = self.model.simulate(self.model.apply(base_state, intervention)).metrics.get(po)
        base = self.model.simulate(base_state).metrics.get(po)
        if base is None or full is None or base == 0:
            return []
        rows = []
        for key, target in intervention.items():
            single = self.model.simulate(
                self.model.apply(base_state, {key: target})).metrics.get(po)
            if single is None:
                continue
            rows.append({
                "lever": key,
                "solo_change_pct": round((single - base) / base * 100, 2),
            })
        rows.sort(key=lambda r: r["solo_change_pct"])
        return rows

    def _recommendations(self, sensitivity: list, rel_change: dict) -> list:
        recs = []
        po = self.model.primary_outcome
        total = rel_change.get(po, 0.0)
        if total < 0:
            recs.append(f"Combined package lowers {po} by {abs(total):.0f}% versus baseline.")
        if sensitivity:
            top = sensitivity[0]
            recs.append(f"Highest-leverage single input: '{top['lever']}' "
                        f"({top['solo_change_pct']:.0f}% on its own).")
            weak = [s for s in sensitivity if abs(s["solo_change_pct"]) < 1]
            if weak:
                recs.append("Low marginal effect from: "
                            + ", ".join(s["lever"] for s in weak) + " — reassess cost-effectiveness.")
        recs.append("Illustrative output — validate against national estimates before use.")
        return recs

    # --- public API -------------------------------------------------------- #
    def run(self, country: str, intervention: dict[str, float],
            horizon: int = 6) -> ScenarioResult:
        base_state = self.model.baseline(country)
        scen_state = self.model.apply(base_state, intervention)
        base_out = self.model.simulate(base_state)
        scen_out = self.model.simulate(scen_state)
        rel = self._relative_change(base_out, scen_out)
        sens = self._sensitivity(base_state, intervention)

        result = ScenarioResult(
            domain=self.model.domain,
            country=country,
            year=base_state.year,
            primary_outcome=self.model.primary_outcome,
            baseline_state=base_state.values,
            scenario_state=scen_state.values,
            baseline_outcome=base_out.metrics,
            scenario_outcome=scen_out.metrics,
            relative_change_pct=rel,
            forecast=self._forecast(base_state, scen_state, horizon),
            sensitivity=sens,
            recommendations=self._recommendations(sens, rel),
        )
        log.info("ran %s scenario for %s: %s change %.1f%%", self.model.domain,
                 country, self.model.primary_outcome,
                 rel.get(self.model.primary_outcome, 0.0))
        return result
