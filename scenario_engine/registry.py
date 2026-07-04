"""Registry of scenario models so new domains plug in without touching the core."""
from __future__ import annotations

from config.logging_config import get_logger
from scenario_engine.base import ScenarioModel

log = get_logger("scenario_engine.registry")

_REGISTRY: dict[str, ScenarioModel] = {}


def register_model(model: ScenarioModel) -> ScenarioModel:
    if not model.domain or model.domain == "base":
        raise ValueError("ScenarioModel must set a unique `domain`.")
    _REGISTRY[model.domain] = model
    log.info("registered scenario model: %s", model.domain)
    return model


def get_model(domain: str) -> ScenarioModel:
    if domain not in _REGISTRY:
        raise KeyError(f"No scenario model registered for domain '{domain}'. "
                       f"Available: {sorted(_REGISTRY)}")
    return _REGISTRY[domain]


def list_models() -> list[str]:
    return sorted(_REGISTRY)


def load_builtin_models() -> None:
    """Import domain packages that register themselves. Safe to call repeatedly."""
    import importlib
    for domain in ("hiv", "maternal"):
        try:
            importlib.import_module(f"analytics.{domain}")
        except Exception as exc:  # pragma: no cover
            log.warning("could not load analytics.%s: %s", domain, exc)
