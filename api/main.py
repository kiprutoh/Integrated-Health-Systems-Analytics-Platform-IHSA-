"""
IHSA API layer (charter Phase D — minimal v0.1.0 surface).

Exposes master data and the shared scenario engine over HTTP. FastAPI is imported
lazily so the rest of the platform works without it installed; `create_app()` raises
a clear error only if you actually try to build the API without FastAPI.

Run: uvicorn api.main:app --reload
"""
from __future__ import annotations

from config.logging_config import get_logger
from config.settings import settings

log = get_logger("api.main")


def create_app():
    try:
        from fastapi import FastAPI, HTTPException
        from pydantic import BaseModel
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("FastAPI/pydantic required for the API layer. "
                           "Install with: pip install fastapi uvicorn") from exc

    from scenario_engine import ScenarioEngine, get_model, list_models, load_builtin_models
    from warehouse import reference

    load_builtin_models()
    app = FastAPI(title=settings.app_name, version=settings.version)

    class ScenarioRequest(BaseModel):
        country: str
        intervention: dict[str, float] = {}
        horizon: int = 6

    @app.get("/health")
    def health():
        return {"status": "ok", "version": settings.version, "domains": list_models()}

    @app.get("/countries")
    def countries():
        return reference.countries().to_dict(orient="records")

    @app.get("/indicators")
    def indicators(domain: str | None = None):
        df = reference.indicators_for(domain) if domain else reference.indicator_catalogue()
        return df.to_dict(orient="records")

    @app.get("/domains")
    def domains():
        return [get_model(d).describe() for d in list_models()]

    @app.post("/scenario/{domain}")
    def scenario(domain: str, req: ScenarioRequest):
        try:
            engine = ScenarioEngine(domain=domain)
            return engine.run(req.country, req.intervention, req.horizon).to_dict()
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    log.info("API app created (%d domains)", len(list_models()))
    return app


# Only build at import time if FastAPI is present (keeps `import api` cheap/safe).
try:  # pragma: no cover
    import fastapi  # noqa: F401
    app = create_app()
except Exception:  # pragma: no cover
    app = None
