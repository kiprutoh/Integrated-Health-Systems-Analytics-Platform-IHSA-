"""
Scenario engine — shared contracts.

This is the platform's core idea from the charter: ONE modelling workflow that every
disease/domain module plugs into, instead of duplicating logic per dashboard.

A domain module implements `ScenarioModel`:

    baseline(country)            -> State        # current observed state
    apply(state, intervention)   -> State        # move the levers
    simulate(state)              -> Outcome      # state -> outcome metrics

The engine (engine.py) then runs the full charter workflow around any such model:

    Current State -> Intervention -> Simulation -> Forecast
                  -> Impact Assessment -> Sensitivity Analysis -> Recommendations
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class LeverSpec:
    """Declares a controllable input for the UI and sensitivity analysis."""
    key: str
    label: str
    unit: str
    min: float
    max: float
    step: float = 1.0
    polarity: int = -1  # -1: raising the lever lowers the (bad) outcome; +1: raises it


@dataclass(frozen=True)
class OutcomeSpec:
    key: str
    label: str
    unit: str
    polarity: int = -1  # -1: lower is better


@dataclass
class State:
    """A country's driver values at a point in time (lever_key -> value)."""
    country: str
    year: int
    values: dict[str, float] = field(default_factory=dict)

    def with_overrides(self, overrides: dict[str, float]) -> "State":
        merged = dict(self.values)
        merged.update({k: v for k, v in overrides.items() if k in merged})
        return State(self.country, self.year, merged)


@dataclass
class Outcome:
    """Outcome metrics produced by simulating a State (outcome_key -> value)."""
    metrics: dict[str, float] = field(default_factory=dict)


class ScenarioModel(ABC):
    """Contract implemented by every domain package (hiv, maternal, uhc, ...)."""

    domain: str = "base"
    title: str = "Base scenario model"
    primary_outcome: str = ""
    levers: list[LeverSpec] = []
    outcomes: list[OutcomeSpec] = []

    @abstractmethod
    def countries(self) -> list[str]:
        ...

    @abstractmethod
    def baseline(self, country: str) -> State:
        ...

    def apply(self, state: State, intervention: dict[str, float]) -> State:
        """Default: overwrite lever values with the intervention targets."""
        return state.with_overrides(intervention)

    @abstractmethod
    def simulate(self, state: State) -> Outcome:
        ...

    # optional metadata for reporting
    def describe(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            "title": self.title,
            "primary_outcome": self.primary_outcome,
            "levers": [l.__dict__ for l in self.levers],
            "outcomes": [o.__dict__ for o in self.outcomes],
        }
