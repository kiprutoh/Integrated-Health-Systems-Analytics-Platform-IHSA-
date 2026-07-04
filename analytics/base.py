"""Analytics package conventions.

Every domain package under analytics/<domain>/ should:
  1. implement a ScenarioModel (scenario_engine.base.ScenarioModel), and
  2. register it in its __init__.py via scenario_engine.registry.register_model.

This module re-exports the contract so domain code can import from one place.
"""
from scenario_engine.base import LeverSpec, Outcome, OutcomeSpec, ScenarioModel, State

__all__ = ["ScenarioModel", "State", "Outcome", "LeverSpec", "OutcomeSpec"]
