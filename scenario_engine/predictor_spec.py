"""
Full predictor specification for the IHSA Bayesian Health Systems Scenario Engine.

Transcribed from the enterprise design document (Scenario_predictor_variables_.docx)
and the WHO AFRO HIS Functionality Assessment (HISFA_Report). This is the single
source of truth for which predictors each domain must include. Every model augments
itself from this spec so the code and the specification cannot drift apart.

Each entry is (name, layer, direction):
    direction "good"  -> higher value improves the outcome
    direction "bad"   -> higher value worsens the outcome
    direction "shock" -> exogenous shock (worsens when active)

Layers follow the five-tier hierarchy: shock, socioeconomic, infrastructure,
system/health_system, governance, reproductive, disease, intermediate.
"""
from __future__ import annotations

# domains whose primary outcome is BENEFICIAL (higher is better)
POSITIVE_OUTCOME = {"uhc", "srhr", "rhis", "sdg3"}

SPEC: dict[str, list[tuple[str, str, str]]] = {
    # ---------------------------------------------------------------- 1. HIV
    "hiv": [
        ("art_coverage", "health_system", "good"), ("hiv_testing", "health_system", "good"),
        ("pmtct_coverage", "health_system", "good"), ("workforce_density", "health_system", "good"),
        ("lab_capacity", "health_system", "good"), ("stockout_rates", "health_system", "bad"),
        ("viral_load_testing", "health_system", "good"), ("chw_density", "health_system", "good"),
        ("contraceptive_prevalence", "reproductive", "good"), ("adolescent_fertility", "reproductive", "bad"),
        ("anc_attendance", "reproductive", "good"), ("facility_delivery", "reproductive", "good"),
        ("skilled_birth_attendance", "reproductive", "good"),
        ("tb_incidence", "disease", "bad"), ("sti_prevalence", "disease", "bad"),
        ("malaria_prevalence", "disease", "bad"), ("hepatitis", "disease", "bad"),
        ("female_literacy", "socioeconomic", "good"), ("income", "socioeconomic", "good"),
        ("urbanization", "socioeconomic", "bad"), ("migration", "socioeconomic", "bad"),
        ("gender_inequality", "socioeconomic", "bad"), ("youth_unemployment", "socioeconomic", "bad"),
        ("internet_connectivity", "infrastructure", "good"), ("facility_density", "infrastructure", "good"),
        ("travel_time", "infrastructure", "bad"), ("electricity", "infrastructure", "good"),
        ("health_expenditure", "governance", "good"), ("reporting_completeness", "governance", "good"),
        ("digital_maturity", "governance", "good"), ("his_maturity", "governance", "good"),
        ("supply_chain", "governance", "good"),
        ("conflict", "shock", "shock"), ("covid", "shock", "shock"), ("floods", "shock", "shock"),
        ("drug_stockouts", "shock", "shock"), ("refugee_influx", "shock", "shock"),
    ],
    # ---------------------------------------------------- 2. Maternal mortality
    "maternal": [
        ("skilled_birth_attendance", "health_system", "good"), ("emergency_obstetric_care", "health_system", "good"),
        ("blood_availability", "health_system", "good"), ("referral_efficiency", "health_system", "good"),
        ("caesarean_rate", "health_system", "good"), ("midwife_density", "health_system", "good"),
        ("health_workforce", "health_system", "good"), ("facility_delivery", "health_system", "good"),
        ("anc4", "reproductive", "good"), ("anc8", "reproductive", "good"),
        ("contraceptive_prevalence", "reproductive", "good"), ("birth_spacing", "reproductive", "good"),
        ("adolescent_fertility", "reproductive", "bad"),
        ("anaemia", "disease", "bad"), ("hiv", "disease", "bad"), ("malaria", "disease", "bad"),
        ("hypertension", "disease", "bad"), ("diabetes", "disease", "bad"),
        ("female_education", "socioeconomic", "good"), ("poverty", "socioeconomic", "bad"),
        ("fertility", "socioeconomic", "bad"), ("gender_inequality", "socioeconomic", "bad"),
        ("rural_population", "socioeconomic", "bad"),
        ("road_access", "infrastructure", "good"), ("travel_time", "infrastructure", "bad"),
        ("ambulances", "infrastructure", "good"), ("facility_density", "infrastructure", "good"),
        ("maternal_death_reviews", "governance", "good"), ("government_expenditure", "governance", "good"),
        ("reporting_completeness", "governance", "good"),
        ("conflict", "shock", "shock"), ("floods", "shock", "shock"),
        ("drug_shortages", "shock", "shock"), ("workforce_strikes", "shock", "shock"),
    ],
    # ------------------------------------------------------- 3. Neonatal mortality
    "neonatal": [
        ("maternal_age", "disease", "bad"), ("prematurity", "disease", "bad"),
        ("low_birth_weight", "disease", "bad"), ("skilled_attendance", "health_system", "good"),
        ("facility_delivery", "health_system", "good"), ("emonc", "health_system", "good"),
        ("newborn_resuscitation", "intermediate", "good"), ("kangaroo_mother_care", "intermediate", "good"),
        ("anc", "reproductive", "good"), ("caesarean_availability", "health_system", "good"),
        ("referral_efficiency", "health_system", "good"), ("electricity", "infrastructure", "good"),
        ("oxygen", "infrastructure", "good"), ("blood_availability", "health_system", "good"),
        ("digital_surveillance", "governance", "good"),
    ],
    # ------------------------------------------------ 4. Child mortality (1-59 mo)
    "child": [
        ("immunization", "intermediate", "good"), ("nutrition", "intermediate", "good"),
        ("vitamin_a", "intermediate", "good"), ("breastfeeding", "intermediate", "good"),
        ("malaria", "disease", "bad"), ("pneumonia", "disease", "bad"), ("diarrhoea", "disease", "bad"),
        ("water", "infrastructure", "good"), ("sanitation", "infrastructure", "good"),
        ("maternal_education", "socioeconomic", "good"), ("facility_readiness", "health_system", "good"),
        ("chw_density", "health_system", "good"), ("travel_time", "infrastructure", "bad"),
    ],
    # ---------------------------------------------------- 5. Under-five mortality
    "under5": [
        ("neonatal_mortality", "intermediate", "bad"), ("child_mortality", "intermediate", "bad"),
        ("nutrition", "intermediate", "good"), ("immunization", "intermediate", "good"),
        ("health_system_readiness", "health_system", "good"), ("disease_burden", "disease", "bad"),
        ("household_poverty", "socioeconomic", "bad"),
        ("conflict", "shock", "shock"), ("floods", "shock", "shock"),
    ],
    # ------------------------------------------------ 6. Universal Health Coverage
    "uhc": [
        ("dpt3", "intermediate", "good"), ("measles", "intermediate", "good"),
        ("full_immunization", "intermediate", "good"), ("zero_dose_children", "intermediate", "bad"),
        ("hpv_vaccine", "intermediate", "good"), ("skilled_birth_attendance", "intermediate", "good"),
        ("institutional_delivery", "intermediate", "good"), ("contraceptive_prevalence", "intermediate", "good"),
        ("anc4", "intermediate", "good"), ("art_coverage", "intermediate", "good"),
        ("cervical_screening", "intermediate", "good"), ("tb_treatment_success", "intermediate", "good"),
        ("itn_use", "intermediate", "good"), ("hypertension_treatment", "intermediate", "good"),
        ("diabetes_treatment", "intermediate", "good"), ("surgical_access", "intermediate", "good"),
        ("care_seeking", "intermediate", "good"), ("nutrition_services", "intermediate", "good"),
        ("service_readiness", "system", "good"), ("essential_equipment", "system", "good"),
        ("diagnostic_services", "system", "good"), ("infection_prevention", "system", "good"),
        ("core_workforce_density", "system", "good"), ("chw_density", "system", "good"),
        ("prepaid_coverage", "financing", "good"), ("out_of_pocket", "financing", "bad"),
        ("gov_health_expenditure", "financing", "good"), ("donor_dependency", "financing", "bad"),
        ("facility_density", "infrastructure", "good"), ("bed_density", "infrastructure", "good"),
        ("electricity", "infrastructure", "good"), ("water_sanitation", "infrastructure", "good"),
        ("lab_capacity", "infrastructure", "good"),
        ("medicine_availability", "system", "good"), ("stockout_rates", "system", "bad"),
        ("his_maturity", "governance", "good"), ("emr_adoption", "governance", "good"),
        ("governance", "governance", "good"), ("policy_implementation", "governance", "good"),
        ("urbanization", "socioeconomic", "good"), ("poverty", "socioeconomic", "bad"),
        ("education", "socioeconomic", "good"), ("vulnerable_populations", "socioeconomic", "bad"),
    ],
    # ----------------------------------------------------------- 7. Tuberculosis
    "tb": [
        ("hiv_prevalence", "disease", "bad"), ("art_coverage", "intermediate", "good"),
        ("nutrition", "socioeconomic", "good"), ("smoking", "socioeconomic", "bad"),
        ("diabetes", "disease", "bad"), ("poverty", "socioeconomic", "bad"),
        ("overcrowding", "socioeconomic", "bad"), ("genexpert", "system", "good"),
        ("laboratory_network", "system", "good"), ("community_screening", "system", "good"),
        ("drug_availability", "system", "good"), ("digital_adherence", "system", "good"),
        ("contact_tracing", "intermediate", "good"), ("tpt", "intermediate", "good"),
        ("his_maturity", "governance", "good"), ("undernutrition", "socioeconomic", "bad"),
    ],
    # --------------------------------------------------------------- 8. Malaria
    "malaria": [
        ("itn", "intermediate", "good"), ("irs", "intermediate", "good"),
        ("act", "intermediate", "good"), ("rdt", "intermediate", "good"),
        ("rainfall", "shock", "bad"), ("temperature", "shock", "bad"), ("floods", "shock", "shock"),
        ("housing", "socioeconomic", "good"), ("travel_time", "infrastructure", "bad"),
        ("surveillance", "system", "good"), ("supply_chain", "system", "good"),
        ("chw_density", "system", "good"), ("chemoprevention", "intermediate", "good"),
        ("vaccine", "intermediate", "good"), ("care_seeking", "intermediate", "good"),
        ("insecticide_resistance", "disease", "bad"),
    ],
    # ------------------------------------------------------------------ 9. NCD
    "ncd": [
        ("obesity", "risk", "bad"), ("smoking", "risk", "bad"), ("alcohol", "risk", "bad"),
        ("inactivity", "risk", "bad"), ("diet", "risk", "bad"), ("salt_diet", "risk", "bad"),
        ("primary_care_readiness", "system", "good"), ("medicine_availability", "system", "good"),
        ("health_insurance", "socioeconomic", "good"), ("screening", "intermediate", "good"),
        ("digital_followup", "system", "good"), ("telemedicine", "system", "good"),
        ("urbanization", "socioeconomic", "bad"), ("htn_control", "intermediate", "good"),
        ("diabetes_control", "intermediate", "good"),
    ],
    # ----------------------------------------------------------------- 10. SRHR
    "srhr": [
        ("family_planning", "intermediate", "good"), ("adolescent_fertility", "intermediate", "bad"),
        ("anc", "intermediate", "good"), ("facility_delivery", "intermediate", "good"),
        ("skilled_attendance", "intermediate", "good"), ("pmtct", "intermediate", "good"),
        ("gender_inequality", "socioeconomic", "bad"), ("education", "socioeconomic", "good"),
        ("gbv_services", "system", "good"), ("youth_services", "system", "good"),
        ("health_workforce", "system", "good"), ("commodity", "system", "good"),
        ("digital_srhr", "system", "good"),
    ],
    # ------------------------------------------------------------- 11. RHIS
    "rhis": [
        ("strategic_planning", "subdomain", "good"), ("policy", "subdomain", "good"),
        ("financing", "subdomain", "good"), ("supervision", "subdomain", "good"),
        ("routine_reporting", "subdomain", "good"), ("dhis2", "subdomain", "good"),
        ("data_quality", "subdomain", "good"), ("crvs", "subdomain", "good"),
        ("interoperability", "subdomain", "good"), ("population_surveys", "subdomain", "good"),
        ("data_analysis", "subdomain", "good"), ("dashboards", "subdomain", "good"),
        ("data_use", "subdomain", "good"),
    ],
    # ------------------------------------------------------ 13. SDG 3 attainment
    "sdg3": [
        ("mmr", "outcome-parent", "bad"), ("u5mr", "outcome-parent", "bad"),
        ("neonatal_mortality", "outcome-parent", "bad"), ("hiv_incidence", "outcome-parent", "bad"),
        ("tb", "outcome-parent", "bad"), ("malaria", "outcome-parent", "bad"),
        ("ncd", "outcome-parent", "bad"), ("uhc", "enabler", "good"),
        ("financial_protection", "enabler", "good"), ("health_expenditure", "enabler", "good"),
        ("digital_health", "enabler", "good"), ("his_maturity", "enabler", "good"),
        ("governance", "enabler", "good"), ("conflict", "shock", "shock"),
    ],
}

# default baseline by direction (probabilities; shocks inactive at baseline)
_DEFAULT_BASE = {"good": 0.55, "bad": 0.30, "shock": 0.0}


def baseline_for(direction: str) -> float:
    return _DEFAULT_BASE.get(direction, 0.5)


def sign_for(domain: str, direction: str) -> int:
    """Sign of a predictor's edge on the outcome VALUE.

    For adverse outcomes (incidence/mortality): 'good' lowers it (-1),
    'bad'/'shock' raise it (+1). For beneficial outcomes (UHC, SRHR, RHIS, SDG3):
    'good' raises it (+1), 'bad'/'shock' lower it (-1).
    """
    positive = domain in POSITIVE_OUTCOME
    if direction == "good":
        return +1 if positive else -1
    return -1 if positive else +1


def domain_predictors(domain: str) -> list[tuple[str, str, str]]:
    return SPEC.get(domain, [])


def counts() -> dict[str, int]:
    return {d: len(v) for d, v in SPEC.items()}
