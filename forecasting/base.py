"""Shared forecasting utilities (charter Phase C 'Forecast' step).

Deliberately simple and transparent for v0.1.0: linear trend, CAGR, and a
logistic-style approach-to-target. Domain modules can supply their own richer
forecasters later; the engine only needs a callable that projects a value forward.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Projection:
    years: list[int]
    values: list[float]
    method: str


def approach_to_target(current: float, target: float, start_year: int,
                       horizon: int = 6, speed: float = 0.35) -> Projection:
    """Geometric approach from `current` toward `target` (e.g. scaling coverage)."""
    years, values, v = [], [], current
    for k in range(horizon + 1):
        years.append(start_year + k)
        values.append(round(v, 4))
        v = v + speed * (target - v)
    return Projection(years, values, "approach_to_target")


def cagr_project(current: float, annual_rate: float, start_year: int,
                 horizon: int = 6) -> Projection:
    years, values = [], []
    for k in range(horizon + 1):
        years.append(start_year + k)
        values.append(round(current * ((1 + annual_rate) ** k), 4))
    return Projection(years, values, "cagr")


def linear_project(current: float, annual_delta: float, start_year: int,
                   horizon: int = 6) -> Projection:
    years = [start_year + k for k in range(horizon + 1)]
    values = [round(current + annual_delta * k, 4) for k in range(horizon + 1)]
    return Projection(years, values, "linear")
