"""
Inverse (target-seeking) scenario solver.

Forward scenarios ask "if I move these levers, what happens to the outcome?".
The inverse solver asks the maternal-app question in reverse: "what coverage would
I need to reach this target outcome?". It scales the chosen protective levers
proportionally from baseline toward their maxima and bisects on the scaling factor
t in [0, 1] until the modelled outcome meets the target (or t saturates).

Domain-agnostic: works for any registered ScenarioModel.
"""
from __future__ import annotations

from dataclasses import dataclass

from scenario_engine.base import ScenarioModel, State


@dataclass
class InverseResult:
    country: str
    target: float
    achieved: float
    feasible: bool
    effort_fraction: float          # t in [0,1] of the way to max coverage
    lever_settings: dict


def _outcome(model: ScenarioModel, state: State) -> float:
    return model.simulate(state).metrics[model.primary_outcome]


def solve_for_target(model: ScenarioModel, country: str, target: float,
                     lever_keys: list[str] | None = None,
                     iterations: int = 40) -> InverseResult:
    base = model.baseline(country)
    levers = {l.key: l for l in model.levers}
    keys = lever_keys or [k for k, l in levers.items() if l.polarity <= 0]  # protective levers

    def state_at(t: float) -> State:
        ov = {}
        for k in keys:
            l = levers[k]
            cur = base.values.get(k, l.min)
            ov[k] = cur + t * (l.max - cur)   # move toward max coverage
        return base.with_overrides(ov)

    best = _outcome(model, base)
    # if target already met at baseline
    if best <= target:
        return InverseResult(country, target, round(best, 3), True, 0.0, dict(base.values))

    full = _outcome(model, state_at(1.0))
    if full > target:  # even full effort cannot reach it
        st = state_at(1.0)
        return InverseResult(country, target, round(full, 3), False, 1.0,
                             {k: round(st.values[k], 1) for k in keys})

    lo, hi = 0.0, 1.0
    for _ in range(iterations):
        mid = (lo + hi) / 2
        if _outcome(model, state_at(mid)) <= target:
            hi = mid
        else:
            lo = mid
    st = state_at(hi)
    return InverseResult(country, target, round(_outcome(model, st), 3), True,
                         round(hi, 3), {k: round(st.values[k], 1) for k in keys})
