# Integrated Health Systems Analytics Platform (IHSA)

**Enterprise v0.1.0 · WHO AFRO · modular, extensible, cloud-native**

IHSA is a decision-support **platform** — not a collection of dashboards — for
health-systems monitoring, forecasting and scenario modelling across the WHO
African Region. It is built so every disease/domain module shares the same
foundations: master data, ETL, a data warehouse, and **one scenario engine**.

It is designed to answer questions like:

- What happens to **UHC** if government health expenditure increases by 10%?
- How would **HIV incidence** change if ART coverage reached 95%?
- Which districts are likely to **miss SDG 3** targets by 2030?
- Which investments produce the greatest reduction in **maternal mortality**?

## Why a platform

The scenario workflow lives in one shared engine:

```
Current State → Intervention → Simulation → Forecast
             → Impact Assessment → Sensitivity Analysis → Policy Recommendations
```

A domain module only implements a small `ScenarioModel` contract (baseline, apply,
simulate, plus lever/outcome specs) and registers itself. The Streamlit UI and the
API then expose it automatically — no core changes. Two modules ship in v0.1.0 to
prove the pattern: **HIV** (mechanistic 95-95-95 transmission model) and **maternal
mortality** (elasticity model).

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python scripts/seed_master_data.py       # 47 AFRO countries + indicator catalogue
python scripts/generate_hiv_panel.py     # illustrative HIV panel (offline)

streamlit run app.py                      # UI at http://localhost:8501
# optional API:
uvicorn api.main:app --reload             # http://localhost:8000/health
```

Or with Docker:

```bash
docker compose -f docker/docker-compose.yml up --build
```

## Repository layout (charter-aligned)

```
config/            settings + logging
data/reference/    master data (countries, regions, indicator catalogue)
data/processed/    domain panels (hiv, maternal, …)
warehouse/         medallion layers (raw/staging/processed/reference/analytics)
etl/               reusable source clients (World Bank, WHO GHO, UNAIDS, …)
scenario_engine/   shared ScenarioModel contract + engine + registry
forecasting/       shared projection utilities
analytics/<domain> one package per domain; registers a ScenarioModel
reporting/         exporters (Excel now; Word/PDF/PPTX later)
api/               FastAPI surface over master data + engine
streamlit/         platform UI shell (registry-driven)
authentication/ gis/ database/  Phase D placeholders
docker/ .github/   containers + CI
tests/ docs/ scripts/ notebooks/
```

## Add a new domain

See `docs/modules.md`. In short: implement `ScenarioModel`, register it, drop data
in `data/processed/<domain>/`, add tests. The UI/API require no changes.

## Testing

```bash
pytest -q            # full suite (CI runs this)
python scripts/selftest.py   # dependency-light smoke test
```

## Roadmap

`v0.1.0` foundation → `v0.2.0` real data/ETL → `v0.3.0` UHC → `v0.4.0` scenario
engine hardening → `v1.0.0` first enterprise release (auth, reporting, GIS,
monitoring). See `docs/roadmap.md`.

## Disclaimer

Committed data are **illustrative** (synthetic-but-plausible) so the platform runs
offline. Replace with real WHO/World Bank/UNAIDS/DHS data via the ETL layer before
any operational use. Scenario outputs are decision-support illustrations, not
official estimates.
