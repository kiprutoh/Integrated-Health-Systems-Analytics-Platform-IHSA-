# Changelog

## [0.2.0] - 2026-07-04
### Added
- Child-survival domains: neonatal, child (1-59 months) and under-five mortality
  models using cause-deletion (Lives-Saved-Tool style); U5MR = NMR + child decomposition.
- Robust predictive engine (`analytics/predictive.py`): additive monotone-constrained
  bootstrap model on log(outcome) with prediction intervals and observed-value anchoring.
- Inverse / target-seeking scenario solver (`scenario_engine/inverse.py`).
- Data-mining orchestrator (`scripts/mine_data.py`) across World Bank, WHO GHO,
  UNICEF, UNFPA, UNAIDS with imputation and warehouse landing.
- Redesigned Streamlit UI: dark hero, glassmorphic cards, two-pane forward +
  target-seeking workspace, registry-driven for all domains.
- Finalized methodology: `docs/IHSA_Methodology_and_Model_Specification.docx`
  covering all 13 domains including the three child-survival modules.


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
