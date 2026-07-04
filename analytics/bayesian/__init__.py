"""Bayesian domain analytics — registers TB, malaria, NCD, SRHR, RHIS, SDG3."""
from analytics.bayesian.model import register_bayesian_models

_models = register_bayesian_models()
__all__ = ["register_bayesian_models"]
