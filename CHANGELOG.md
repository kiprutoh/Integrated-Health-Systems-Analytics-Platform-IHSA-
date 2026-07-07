# Changelog

## [0.3.6] - 2026-07-06
### Added
- Predictor sensitivity screening (scripts/screen_predictors.py): one-at-a-time
  range-sweep of every predictor, effect = normalised outcome swing, threshold 1e-3.
  Writes docs/predictor_screening.csv. Variable Screening Report documents the process.
### Changed
- Do-operator semantics corrected: the scenario engine now intervenes only on levers
  changed from baseline, so mediators are not fixed and upstream predictors keep their
  causal path (analytics/bayesian/model.py). This recovered several wrongly-inert
  predictors (e.g. SRHR commodity, youth services).
- Final variable set: 251 effective adjustable variables, zero inert. Removed as
  redundant/unwired: HIV know-status & ART coverage (act via viral suppression);
  malaria RDT & rainfall; NCD digital follow-up; RHIS population surveys; SRHR facility
  delivery, PMTCT, digital SRHR. SDG 3 constituent outcomes reclassified as
  model-linked inputs (kept as nodes, removed as sliders). See EXCLUDE_LEVERS.
- Definitive methodology updated with a screening note in the predictor section.


## [0.3.5] - 2026-07-06
### Added
- Full enterprise predictor spec encoded as a single source of truth
  (scenario_engine/predictor_spec.py), transcribed from the design document and the
  WHO AFRO HIS assessment. Every model augments itself from it, so code and spec
  cannot drift. Predictors per domain now: HIV 44, maternal 35, neonatal 27,
  child 26, under-5 21, UHC 48, TB 19, malaria 18, NCD 17, RHIS 15, SRHR 14, SDG3 14.
- Bayesian networks augmented with all spec predictors as sign-constrained outcome
  parents (scenario_engine.bayes_networks.augment_from_spec, full_lever_specs).
- Mechanistic models (HIV, maternal, neonatal, child, under-5) augmented with the
  remaining spec predictors as bounded log-linear modifiers, leaving the calibrated
  cores intact (analytics/spec_augment.py).
- Predictor catalogue regenerated (docs/predictor_catalogue.csv, 298 indicators with
  role, direction and evidence basis).
### Changed
- Definitive methodology (docs/IHSA_Definitive_Methodology.docx) now includes the
  Missing-Data Imputation Framework as sub-section 6.2 (MCAR/MAR/MNAR, the three
  stages, proper Bayesian MICE draw, Rubin's rules, self-calibration, Figure 4) and a
  new 7.0 Predictor completeness section with the per-domain predictor table and four
  added references (Little & Rubin 2019; Rubin 1976, 1987; van Buuren 2011).


## [0.3.4] - 2026-07-05
### Added
- Missing-data imputation framework (warehouse/imputation.py): temporal interpolation
  -> Bayesian MICE -> hierarchical shrinkage, multiple imputation with Rubin's-rules
  pooling, plausibility bounds, provenance flagging, held-out validation and
  self-calibrated intervals. Wired into scripts/mine_data.py; demo in
  scripts/impute_demo.py; tests in tests/test_imputation.py (7/7).
- Imputation methodology document (docs/IHSA_Missing_Data_Imputation_Framework.docx)
  with MCAR/MAR/MNAR treatment, full derivations, Harvard citations and Figure 4.
- Every module now carries >= 12 evidence-grounded, outcome-sensitive predictors:
  HIV +key populations/PMTCT/harm reduction/gender inequality (12 levers);
  maternal expanded to 12 (EmONC, blood, facility delivery, PNC, mCPR, workforce,
  anaemia, adolescent fertility); malaria +vaccine/LSM/care-seeking/resistance (14);
  RHIS decomposed into 12 PRISM/HIS sub-domain indicators; UHC +RMNCH/infectious/NCD
  tracer coverage (13).
- Predictor catalogue (docs/predictor_catalogue.csv) documenting each domain's
  indicators, role, direction and evidence basis (163 rows).
### Changed
- mine_data.impute now uses the imputation framework instead of ad-hoc ffill/median.


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
