"""Maternal analytics package — registers the maternal scenario model on import."""
from analytics.maternal.model import MaternalScenarioModel
from scenario_engine.registry import register_model

model = register_model(MaternalScenarioModel())

__all__ = ["MaternalScenarioModel", "model"]
