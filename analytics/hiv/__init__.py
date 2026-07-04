"""HIV analytics package — registers the HIV scenario model on import."""
from analytics.hiv.model import HIVScenarioModel
from scenario_engine.registry import register_model

model = register_model(HIVScenarioModel())

__all__ = ["HIVScenarioModel", "model"]
