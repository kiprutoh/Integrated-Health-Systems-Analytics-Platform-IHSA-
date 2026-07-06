# Changelog

## [0.3.3] - 2026-07-05
### Added
- UHC registered as a full scenario (Universal Health Coverage Explorer) — 12 domains
  in the UI; financing production function with a separate financial-protection node.
- Definitive methodology (docs/IHSA_Definitive_Methodology.docx): first-principles
  derivations of every method (Bayesian networks; and, where more appropriate,
  Lives Saved Tool cause-deletion, survival decomposition, comparative risk assessment,
  financing production function, composite maturity index, target-gap trajectory,
  additive monotonic bootstrap), a notation table defining every term, Harvard in-text
  citations and a full reference list, and embedded framework diagrams.
- Framework diagrams (scripts/generate_diagrams.py -> docs/figures/): five-layer
  hierarchy DAG, HIV network DAG, and a method-selection map.
- Mathematical derivation comments added to scenario_engine/bayes_engine.py,
  analytics/child_survival/model.py for developer reproducibility.
- Scenario runner derives labels/direction from network metadata (stays in sync).


## [0.3.2] - 2026-07-05
### Added
- All six Bayesian domains (TB, malaria, NCD, SRHR, RHIS, SDG 3) now exposed in the
  UI via a ScenarioModel adapter (analytics/bayesian/) — 11 domains registered.
- Per-country simulated baselines for Bayesian domains (scripts/generate_bayes_panels.py);
  RHIS uses the mined HIS maturity panel.
- Home page restructured into a key-regional-figures dashboard (regional medians per
  domain) with navigation cards into each scenario workspace.
- Expanded methodology document (docs/IHSA_Expanded_Methodology_Scenarios.docx): for
  every domain an Introduction, Predictors-and-evidence-from-literature, and
  Modelling-framework section, each 6+ paragraphs.
- UI outcome-direction handling for positive-index domains (SRHR, RHIS, SDG 3).


## [0.3.1] - 2026-07-05
### Added
- Instantiated Bayesian networks for TB (5.7), Malaria (5.8), NCD (5.9), SRHR (5.10),
  Routine HIS / HIS maturity (5.11) and SDG 3 attainment (5.12) in
  scenario_engine/bayes_networks.py — each with layered parents, structural signs,
  links and a scenario package library (BN.SCENARIO_LIBRARY).
- TB uses a find-treat-cure cascade; malaria multiplicative vector control + flood
  shock; NCD comparative-risk on premature mortality; SRHR a positive coverage index;
  RHIS built from the mined WHO AFRO HIS maturity data (per-country baselines);
  SDG 3 an integrating node over the other outcomes and enablers.
- scripts/run_bayes_scenarios.py runs the full library across all domains.
- tests/test_bayes.py extended to cover all networks (baseline invariance,
  scenario direction, credible intervals, mined-baseline RHIS, TB cascade).


## [0.3.0] - 2026-07-04
### Added / reworked
- Reworked modelling framework as a **Bayesian Health Systems Scenario Engine**
  (scenario_engine/bayes_engine.py, bayes_networks.py): hierarchical DAG over
  layered determinants (shocks -> socioeconomic -> system -> intermediate -> outcome),
  do-operator scenario packages, Monte-Carlo uncertainty propagation, credible
  intervals and P(target).
- **HIS maturity mining** (scripts/mine_his_maturity.py) from the WHO AFRO HISFA
  report -> data/processed/his/afro_his_maturity.csv (38 countries, domain scores,
  maturity bands). HIS maturity wired as an upstream determinant.
- Finalized **Bayesian methodology** doc with full mathematical specification and
  per-domain assumptions: docs/IHSA_Bayesian_Methodology_and_Model_Specification.docx.
- UI/UX rebuilt to match the WHO AFRO maternal explorer: hero + 2x2 metric cards,
  feature cards, numbered steps, CTA banner, two-pane what-if workspace with status-quo
  box, cyan target panel, grouped levers, comparison chart, input-changes table,
  and 2030 trajectory with 95% band.
- API connectors extended (ACLED, EM-DAT, DHIS2, UN Population) per the source plan;
  simulation protocol for indicators without an open API.


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
