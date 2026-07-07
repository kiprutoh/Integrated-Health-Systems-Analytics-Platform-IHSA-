"""
Spec augmentation for the mechanistic scenario models.

The mechanistic models (HIV force-of-infection, maternal elasticity, child-survival
cause-deletion) carry a small, strongly-calibrated core of key drivers. To include
the FULL predictor set from predictor_spec.SPEC without disturbing that calibrated
core, this helper exposes the remaining spec predictors as additional levers and
applies them as a bounded, multiplicative, log-linear modifier on the (adverse)
outcome:

    outcome_scenario = outcome_core * exp( sum_p  s_p * W * (C_p^scen - C_p^base)/100 )

where s_p is the evidence-implied sign (protective -1, risk/shock +1), W is a modest
per-predictor weight (these are secondary determinants), and the total factor is
clipped to a sensible range so the long tail of predictors cannot dominate the
calibrated core.
"""
from __future__ import annotations

import math

from scenario_engine import predictor_spec as SPEC
from scenario_engine.base import LeverSpec

W = 0.40                      # per-predictor log-weight (secondary influence)
CLIP = (0.40, 2.50)           # bound the aggregate modifier

_PRETTY = {
    "chw_density": "Community health workers", "workforce_density": "Health-workforce density",
    "lab_capacity": "Laboratory capacity", "stockout_rates": "Stockout rates",
    "viral_load_testing": "Viral-load testing", "contraceptive_prevalence": "Contraceptive prevalence",
    "adolescent_fertility": "Adolescent fertility", "anc_attendance": "ANC attendance",
    "facility_delivery": "Facility delivery", "skilled_birth_attendance": "Skilled birth attendance",
    "tb_incidence": "TB incidence", "sti_prevalence": "STI prevalence",
    "malaria_prevalence": "Malaria prevalence", "hepatitis": "Hepatitis",
    "income": "Household income", "urbanization": "Urbanization", "migration": "Migration",
    "gender_inequality": "Gender inequality", "youth_unemployment": "Youth unemployment",
    "internet_connectivity": "Internet connectivity", "facility_density": "Facility density",
    "travel_time": "Travel time to care", "electricity": "Electricity access",
    "health_expenditure": "Health expenditure", "reporting_completeness": "Reporting completeness",
    "digital_maturity": "Digital maturity", "his_maturity": "HIS maturity",
    "supply_chain": "Supply-chain efficiency", "conflict": "Conflict", "covid": "COVID disruption",
    "floods": "Floods", "drug_stockouts": "Drug stockouts", "refugee_influx": "Refugee influx",
    "referral_efficiency": "Referral efficiency", "caesarean_rate": "Caesarean section rate",
    "health_workforce": "Health workforce", "anc8": "Antenatal care (8+)", "birth_spacing": "Birth spacing",
    "hiv": "HIV prevalence", "malaria": "Malaria", "hypertension": "Hypertension", "diabetes": "Diabetes",
    "poverty": "Poverty", "fertility": "Total fertility rate", "rural_population": "Rural population",
    "road_access": "Road access", "ambulances": "Ambulance availability",
    "maternal_death_reviews": "Maternal death reviews", "government_expenditure": "Government expenditure",
    "drug_shortages": "Drug shortages", "workforce_strikes": "Workforce strikes",
    "maternal_age": "Maternal age (extremes)", "prematurity": "Prematurity",
    "low_birth_weight": "Low birth weight", "emonc": "EmONC", "anc": "Antenatal care",
    "caesarean_availability": "Caesarean availability", "oxygen": "Medical oxygen",
    "blood_availability": "Blood availability", "digital_surveillance": "Digital surveillance",
    "nutrition": "Nutrition", "pneumonia": "Pneumonia", "diarrhoea": "Diarrhoea",
    "water": "Safe water", "sanitation": "Sanitation", "maternal_education": "Maternal education",
    "facility_readiness": "Facility readiness", "immunization": "Immunization",
    "health_system_readiness": "Health-system readiness", "disease_burden": "Disease burden",
    "household_poverty": "Household poverty",
}


def _label(name: str) -> str:
    return _PRETTY.get(name, name.replace("_", " ").capitalize())


def extra_items(domain: str, handled: set[str]):
    return [(n, layer, d) for (n, layer, d) in SPEC.domain_predictors(domain)
            if n not in handled]


def extra_levers(domain: str, handled: set[str]) -> list[LeverSpec]:
    out = []
    for n, layer, d in extra_items(domain, handled):
        out.append(LeverSpec(n, _label(n), "%", 0, 100, 1, polarity=(-1 if d == "good" else +1)))
    return out


def extra_defaults(domain: str, handled: set[str]) -> dict[str, float]:
    by_dir = {"good": 55.0, "bad": 30.0, "shock": 0.0}
    return {n: by_dir.get(d, 50.0) for n, layer, d in extra_items(domain, handled)}


def modifier(domain: str, handled: set[str], base: dict, scen: dict) -> float:
    """Bounded multiplicative modifier on an adverse outcome from the extra predictors."""
    log = 0.0
    for n, layer, d in extra_items(domain, handled):
        b = base.get(n)
        if b is None:
            continue
        s = SPEC.sign_for(domain, d)              # +1 raises adverse outcome, -1 lowers
        log += s * W * (scen.get(n, b) - b) / 100.0
    return float(min(CLIP[1], max(CLIP[0], math.exp(log))))
