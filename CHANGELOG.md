# Changelog

## [0.1.0] — Enterprise Foundation (Phase A)
### Added
- Full monorepo scaffold per the IHSA charter.
- Config (env-driven settings) and shared logging.
- Master data: 47 WHO AFRO member states, WHO regions, indicator catalogue.
- Warehouse reference layer + medallion directory structure.
- Reusable ETL `BaseETLClient` (retries, caching, pagination, validation, metadata
  versioning) with World Bank + WHO GHO wired and UNAIDS/UNICEF/UNFPA/DHIS2 stubs.
- **Shared scenario engine**: Current State → Intervention → Simulation → Forecast
  → Impact → Sensitivity → Recommendations, driven by a `ScenarioModel` contract.
- Two proof modules on the shared engine: **HIV** (mechanistic 95-95-95 model) and
  **Maternal mortality** (elasticity model).
- Registry-driven Streamlit shell (Home, Country/Dataset/Indicator/Scenario
  Explorer, Settings) and a FastAPI surface.
- Excel reporting; Docker (Streamlit + API + compose); GitHub Actions CI; tests.
