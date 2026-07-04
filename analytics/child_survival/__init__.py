"""Child-survival analytics — registers neonatal, child (1-59mo) and under-5 models."""
from analytics.child_survival.model import ChildModel, NeonatalModel, UnderFiveModel
from scenario_engine.registry import register_model

neonatal = register_model(NeonatalModel())
child = register_model(ChildModel())
under5 = register_model(UnderFiveModel())

__all__ = ["NeonatalModel", "ChildModel", "UnderFiveModel", "neonatal", "child", "under5"]
