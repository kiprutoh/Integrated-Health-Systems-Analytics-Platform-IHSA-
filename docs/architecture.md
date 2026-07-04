# Architecture

## Layers
1. **config/** — settings (env-driven) and logging.
2. **data/reference + warehouse/** — master data and the medallion warehouse
   (raw → staging → processed → reference → analytics).
3. **etl/** — reusable source clients (retries, caching, pagination, validation,
   metadata versioning). One `BaseETLClient`; concrete clients per source.
4. **scenario_engine/** — the shared modelling workflow. Domain modules implement
   `ScenarioModel`; the engine runs Current State → Intervention → Simulation →
   Forecast → Impact → Sensitivity → Recommendations around any of them.
5. **analytics/<domain>/** — one package per domain (hiv, maternal, uhc, …). Each
   registers a `ScenarioModel` on import.
6. **forecasting/** — shared projection utilities.
7. **reporting/** — exporters (Excel now; Word/PDF/PPTX later).
8. **api/** — FastAPI surface over master data + engine.
9. **streamlit/** — the platform UI shell (registry-driven, so new domains appear
   automatically).

## The extension contract
To add a domain, implement `ScenarioModel` (baseline/apply/simulate + lever specs)
and call `register_model()` in the package `__init__`. No core code changes. The
Streamlit Scenario Explorer and the API pick it up automatically.

## Key design decision
Scenarios are reported as **relative change from an observed baseline**, so a
no-change scenario reproduces reality exactly and projections stay interpretable
even outside the historical data range.
