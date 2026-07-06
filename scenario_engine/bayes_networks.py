"""
Domain Bayesian networks and the multi-domain scenario library.

Each build_* function returns a BayesianNetwork over the layered determinants of
one domain (shocks -> socioeconomic -> system -> intermediate -> outcome), using
the predictors catalogued in the methodology.

Sign convention (structural): sign = +1 means increasing the parent increases this
node on its link scale; sign = -1 means it decreases it. Coefficients are
non-negative magnitudes; direction is carried by `sign`. Coefficients/baselines are
illustrative or elicited and are replaced by fitted posteriors when data are mined.
"""
from __future__ import annotations

from pathlib import Path

from config.settings import ROOT
from scenario_engine.bayes_engine import BayesianNetwork, Edge, Node


# ----------------------------------------------------------------- 5.1 HIV
def build_hiv(baseline: dict | None = None) -> BayesianNetwork:
    b = {"incidence": 4.0, "viral_suppression": 0.75, "art_coverage": 0.78,
         "hiv_testing": 0.80, "supply_chain": 0.75, "his_maturity": 0.55,
         "condom_use": 0.45, "sti_prevalence": 0.10, "female_literacy": 0.65, "conflict": 0.0}
    if baseline:
        b.update(baseline)
    n = BayesianNetwork("hiv")
    n.add(Node("female_literacy", "socioeconomic", "prob", b["female_literacy"], lo=0, hi=1))
    n.add(Node("conflict", "shock", "continuous", b["conflict"], lo=0, hi=1))
    n.add(Node("his_maturity", "system", "continuous", b["his_maturity"], lo=0, hi=1))
    n.add(Node("condom_use", "intermediate", "prob", b["condom_use"], lo=0, hi=1))
    n.add(Node("sti_prevalence", "disease", "prob", b["sti_prevalence"], lo=0, hi=1))
    n.add(Node("supply_chain", "system", "prob", b["supply_chain"], lo=0.05, hi=1, link="logit",
               parents=[Edge("his_maturity", 0.9, 0.12, +1, b["his_maturity"]),
                        Edge("conflict", 1.2, 0.20, -1, 0.0)]))
    n.add(Node("hiv_testing", "system", "prob", b["hiv_testing"], lo=0.05, hi=1, link="logit",
               parents=[Edge("his_maturity", 0.8, 0.12, +1, b["his_maturity"])]))
    n.add(Node("art_coverage", "intermediate", "prob", b["art_coverage"], lo=0.05, hi=0.99, link="logit",
               parents=[Edge("hiv_testing", 1.4, 0.18, +1, b["hiv_testing"]),
                        Edge("supply_chain", 0.9, 0.14, +1, b["supply_chain"])]))
    n.add(Node("viral_suppression", "intermediate", "prob", b["viral_suppression"], lo=0.05, hi=0.99,
               link="logit", parents=[Edge("art_coverage", 2.2, 0.25, +1, b["art_coverage"]),
                                      Edge("supply_chain", 0.6, 0.12, +1, b["supply_chain"])]))
    n.add(Node("incidence", "outcome", "rate", b["incidence"], lo=0.01, hi=50, noise_sd=0.05, link="log",
               parents=[Edge("viral_suppression", 2.4, 0.28, -1, b["viral_suppression"]),
                        Edge("condom_use", 0.6, 0.12, -1, b["condom_use"]),
                        Edge("sti_prevalence", 0.9, 0.16, +1, b["sti_prevalence"]),
                        Edge("female_literacy", 0.4, 0.10, -1, b["female_literacy"])]))
    return n


# --------------------------------------------------------- 5.7 Tuberculosis
def build_tb(baseline: dict | None = None) -> BayesianNetwork:
    b = {"incidence": 200.0, "case_detection": 0.65, "treatment_success": 0.85, "tpt": 0.40,
         "genexpert": 0.60, "community_screening": 0.50, "drug_availability": 0.80,
         "digital_adherence": 0.40, "hiv_prevalence": 0.10, "art_coverage": 0.75,
         "undernutrition": 0.20, "his_maturity": 0.55, "conflict": 0.0}
    if baseline:
        b.update(baseline)
    n = BayesianNetwork("tb")
    for k, layer in [("genexpert", "system"), ("community_screening", "system"),
                     ("drug_availability", "system"), ("digital_adherence", "system"),
                     ("tpt", "intermediate"), ("hiv_prevalence", "disease"),
                     ("art_coverage", "intermediate"), ("undernutrition", "socioeconomic"),
                     ("his_maturity", "system")]:
        n.add(Node(k, layer, "prob", b[k], lo=0, hi=1))
    n.add(Node("conflict", "shock", "continuous", b["conflict"], lo=0, hi=1))
    n.add(Node("case_detection", "intermediate", "prob", b["case_detection"], lo=0.05, hi=0.99, link="logit",
               parents=[Edge("genexpert", 1.0, 0.14, +1, b["genexpert"]),
                        Edge("community_screening", 0.8, 0.12, +1, b["community_screening"]),
                        Edge("his_maturity", 0.4, 0.08, +1, b["his_maturity"])]))
    n.add(Node("treatment_success", "intermediate", "prob", b["treatment_success"], lo=0.05, hi=0.99,
               link="logit", parents=[Edge("drug_availability", 1.2, 0.16, +1, b["drug_availability"]),
                                      Edge("digital_adherence", 0.6, 0.10, +1, b["digital_adherence"])]))
    n.add(Node("incidence", "outcome", "rate", b["incidence"], lo=1, hi=1500, noise_sd=0.05, link="log",
               parents=[Edge("case_detection", 1.2, 0.16, -1, b["case_detection"]),
                        Edge("treatment_success", 1.0, 0.14, -1, b["treatment_success"]),
                        Edge("tpt", 0.6, 0.12, -1, b["tpt"]),
                        Edge("hiv_prevalence", 0.8, 0.15, +1, b["hiv_prevalence"]),
                        Edge("art_coverage", 0.4, 0.10, -1, b["art_coverage"]),
                        Edge("undernutrition", 0.5, 0.12, +1, b["undernutrition"])]))
    return n


# ---------------------------------------------------------------- 5.8 Malaria
def build_malaria(baseline: dict | None = None) -> BayesianNetwork:
    b = {"incidence": 220.0, "itn": 0.55, "irs": 0.20, "act": 0.60, "chemoprevention": 0.30,
         "rdt": 0.60, "housing": 0.40, "supply_chain": 0.70, "his_maturity": 0.55,
         "floods": 0.0, "rainfall": 0.5,
         # added evidence-grounded predictors
         "vaccine": 0.10, "larval_source_mgmt": 0.15, "care_seeking": 0.55,
         "insecticide_resistance": 0.35}
    if baseline:
        b.update(baseline)
    n = BayesianNetwork("malaria")
    for k, layer in [("itn", "intermediate"), ("irs", "intermediate"), ("act", "intermediate"),
                     ("chemoprevention", "intermediate"), ("rdt", "intermediate"),
                     ("vaccine", "intermediate"), ("larval_source_mgmt", "intermediate"),
                     ("care_seeking", "intermediate"), ("insecticide_resistance", "risk"),
                     ("housing", "socioeconomic"), ("his_maturity", "system"), ("rainfall", "shock")]:
        n.add(Node(k, layer, "prob", b[k], lo=0, hi=1))
    n.add(Node("floods", "shock", "continuous", b["floods"], lo=0, hi=1))
    n.add(Node("supply_chain", "system", "prob", b["supply_chain"], lo=0.05, hi=1, link="logit",
               parents=[Edge("his_maturity", 0.9, 0.12, +1, b["his_maturity"]),
                        Edge("floods", 0.7, 0.15, -1, 0.0)]))
    n.add(Node("incidence", "outcome", "rate", b["incidence"], lo=1, hi=1200, noise_sd=0.05, link="log",
               parents=[Edge("itn", 1.4, 0.18, -1, b["itn"]),               # Lengeler 2004
                        Edge("irs", 0.9, 0.14, -1, b["irs"]),
                        Edge("chemoprevention", 1.0, 0.15, -1, b["chemoprevention"]),  # SMC/IPTp
                        Edge("act", 0.5, 0.10, -1, b["act"]),
                        Edge("vaccine", 0.5, 0.12, -1, b["vaccine"]),        # RTS,S / R21
                        Edge("larval_source_mgmt", 0.4, 0.10, -1, b["larval_source_mgmt"]),  # LSM
                        Edge("care_seeking", 0.4, 0.10, -1, b["care_seeking"]),
                        Edge("supply_chain", 0.7, 0.12, -1, b["supply_chain"]),
                        Edge("housing", 0.4, 0.10, -1, b["housing"]),        # Tusting 2015
                        Edge("insecticide_resistance", 0.5, 0.12, +1, b["insecticide_resistance"]),
                        Edge("floods", 0.45, 0.10, +1, 0.0)]))
    return n


# ------------------------------------------------------------------ 5.9 NCD
def build_ncd(baseline: dict | None = None) -> BayesianNetwork:
    b = {"premature_mortality": 0.20, "tobacco": 0.15, "alcohol": 0.10, "inactivity": 0.25,
         "salt_diet": 0.40, "obesity": 0.15, "htn_control": 0.20, "diabetes_control": 0.25,
         "screening": 0.30, "primary_care_readiness": 0.55, "medicine_availability": 0.60,
         "digital_followup": 0.30, "urbanization": 0.45, "insurance": 0.20}
    if baseline:
        b.update(baseline)
    n = BayesianNetwork("ncd")
    for k, layer in [("tobacco", "risk"), ("alcohol", "risk"), ("inactivity", "risk"),
                     ("salt_diet", "risk"), ("obesity", "risk"), ("htn_control", "intermediate"),
                     ("diabetes_control", "intermediate"), ("screening", "intermediate"),
                     ("primary_care_readiness", "system"), ("medicine_availability", "system"),
                     ("digital_followup", "system"), ("urbanization", "socioeconomic"),
                     ("insurance", "socioeconomic")]:
        n.add(Node(k, layer, "prob", b[k], lo=0, hi=1))
    n.add(Node("premature_mortality", "outcome", "prob", b["premature_mortality"], lo=0.01, hi=0.8,
               noise_sd=0.0, link="logit",
               parents=[Edge("tobacco", 0.9, 0.14, +1, b["tobacco"]),
                        Edge("alcohol", 0.5, 0.10, +1, b["alcohol"]),
                        Edge("inactivity", 0.5, 0.10, +1, b["inactivity"]),
                        Edge("salt_diet", 0.6, 0.12, +1, b["salt_diet"]),
                        Edge("obesity", 0.6, 0.12, +1, b["obesity"]),
                        Edge("urbanization", 0.3, 0.08, +1, b["urbanization"]),
                        Edge("htn_control", 0.9, 0.14, -1, b["htn_control"]),
                        Edge("diabetes_control", 0.6, 0.12, -1, b["diabetes_control"]),
                        Edge("screening", 0.5, 0.10, -1, b["screening"]),
                        Edge("primary_care_readiness", 0.6, 0.12, -1, b["primary_care_readiness"]),
                        Edge("medicine_availability", 0.5, 0.10, -1, b["medicine_availability"]),
                        Edge("insurance", 0.3, 0.08, -1, b["insurance"])]))
    return n


# ----------------------------------------------------------------- 5.10 SRHR
def build_srhr(baseline: dict | None = None) -> BayesianNetwork:
    b = {"srhr_index": 0.55, "family_planning": 0.45, "anc": 0.60, "facility_delivery": 0.65,
         "skilled_attendance": 0.70, "pmtct": 0.70, "youth_services": 0.40, "gbv_services": 0.35,
         "commodity": 0.70, "workforce": 0.55, "digital_srhr": 0.30, "education": 0.60,
         "adolescent_fertility": 0.10, "gender_inequality": 0.50}
    if baseline:
        b.update(baseline)
    n = BayesianNetwork("srhr")
    for k, layer in [("anc", "intermediate"), ("facility_delivery", "intermediate"),
                     ("skilled_attendance", "intermediate"), ("pmtct", "intermediate"),
                     ("youth_services", "system"), ("gbv_services", "system"),
                     ("workforce", "system"), ("digital_srhr", "system"),
                     ("education", "socioeconomic"), ("adolescent_fertility", "socioeconomic"),
                     ("gender_inequality", "socioeconomic"), ("commodity", "system")]:
        n.add(Node(k, layer, "prob", b[k], lo=0, hi=1))
    n.add(Node("family_planning", "intermediate", "prob", b["family_planning"], lo=0.05, hi=0.99,
               link="logit", parents=[Edge("commodity", 1.0, 0.14, +1, b["commodity"]),
                                      Edge("youth_services", 0.6, 0.10, +1, b["youth_services"])]))
    # outcome is a POSITIVE index: protective/positive drivers raise it (+1), risks lower it (-1)
    n.add(Node("srhr_index", "outcome", "prob", b["srhr_index"], lo=0.05, hi=0.99, link="logit",
               parents=[Edge("family_planning", 1.2, 0.16, +1, b["family_planning"]),
                        Edge("anc", 0.7, 0.12, +1, b["anc"]),
                        Edge("skilled_attendance", 0.7, 0.12, +1, b["skilled_attendance"]),
                        Edge("education", 0.6, 0.12, +1, b["education"]),
                        Edge("gbv_services", 0.4, 0.10, +1, b["gbv_services"]),
                        Edge("adolescent_fertility", 0.7, 0.14, -1, b["adolescent_fertility"]),
                        Edge("gender_inequality", 0.8, 0.14, -1, b["gender_inequality"])]))
    return n


# ------------------------------------------------- 5.11 Routine HIS / maturity
def _his_baseline(country: str | None) -> dict:
    b = {"his_maturity_index": 55.0, "governance": 50.0, "data_generation": 60.0,
         "data_analysis": 50.0, "communication": 52.0,
         "strategic_planning": 55.0, "policy": 45.0, "financing": 25.0, "supervision": 55.0}
    csv = Path(ROOT) / "data" / "processed" / "his" / "afro_his_maturity.csv"
    if country and csv.exists():
        import pandas as pd
        df = pd.read_csv(csv)
        row = df[df["country"].str.lower() == country.lower()]
        if not row.empty:
            r = row.iloc[0]
            b["governance"] = float(r.get("gov_score", b["governance"]))
            b["data_generation"] = float(r.get("datagen_score", b["data_generation"]))
            b["his_maturity_index"] = float(r.get("his_maturity_index", b["his_maturity_index"]))
            for k, col in [("strategic_planning", "Strategic Planning"), ("policy", "Policy Development"),
                           ("financing", "HIS Financing"), ("supervision", "Supervision National")]:
                if col in r and pd.notna(r[col]):
                    b[k] = float(r[col])
    return b


def build_rhis(country: str | None = None, baseline: dict | None = None) -> BayesianNetwork:
    b = _his_baseline(country)
    # evidence-grounded sub-domain indicators (PRISM technical/organisational/behavioural
    # determinants; WHO AFRO HIS assessment domains). Defaults where the mined table is coarse.
    for k, d in {"routine_reporting": b.get("data_generation", 55), "dhis2": 70,
                 "data_quality": b.get("data_generation", 55) * 0.9, "crvs": 35,
                 "interoperability": 40, "dashboards": b.get("communication", 50),
                 "data_use": b.get("communication", 50) * 0.95}.items():
        b.setdefault(k, d)
    if baseline:
        b.update(baseline)
    n = BayesianNetwork("rhis")
    # governance sub-domains
    for k in ("strategic_planning", "policy", "financing", "supervision"):
        n.add(Node(k, "subdomain", "continuous", b[k], lo=0, hi=100))
    # data-generation sub-domains (routine reporting, DHIS2, data quality, CRVS, interoperability)
    for k in ("routine_reporting", "dhis2", "data_quality", "crvs", "interoperability"):
        n.add(Node(k, "subdomain", "continuous", b[k], lo=0, hi=100))
    n.add(Node("data_analysis", "subdomain", "continuous", b["data_analysis"], lo=0, hi=100))
    # communication/use sub-domains
    for k in ("dashboards", "data_use"):
        n.add(Node(k, "subdomain", "continuous", b[k], lo=0, hi=100))
    # governance = weighted mean of its sub-domains
    n.add(Node("governance", "domain", "continuous", b["governance"], lo=0, hi=100,
               parents=[Edge("strategic_planning", 0.25, 0.02, +1, b["strategic_planning"], scale=1),
                        Edge("policy", 0.25, 0.02, +1, b["policy"], scale=1),
                        Edge("financing", 0.25, 0.02, +1, b["financing"], scale=1),
                        Edge("supervision", 0.25, 0.02, +1, b["supervision"], scale=1)]))
    # data generation = weighted mean of its sub-domains
    dg = b["data_generation"]
    n.add(Node("data_generation", "domain", "continuous", dg, lo=0, hi=100,
               parents=[Edge("routine_reporting", 0.24, 0.02, +1, b["routine_reporting"], scale=1),
                        Edge("dhis2", 0.22, 0.02, +1, b["dhis2"], scale=1),
                        Edge("data_quality", 0.24, 0.02, +1, b["data_quality"], scale=1),
                        Edge("crvs", 0.16, 0.02, +1, b["crvs"], scale=1),
                        Edge("interoperability", 0.14, 0.02, +1, b["interoperability"], scale=1)]))
    # communication = weighted mean of dashboards + data use
    n.add(Node("communication", "domain", "continuous", b["communication"], lo=0, hi=100,
               parents=[Edge("dashboards", 0.5, 0.02, +1, b["dashboards"], scale=1),
                        Edge("data_use", 0.5, 0.02, +1, b["data_use"], scale=1)]))
    # overall maturity index = weighted mean of the four domains
    n.add(Node("his_maturity_index", "outcome", "continuous", b["his_maturity_index"], lo=0, hi=100,
               noise_sd=0.0,
               parents=[Edge("governance", 0.25, 0.02, +1, b["governance"], scale=1),
                        Edge("data_generation", 0.25, 0.02, +1, dg, scale=1),
                        Edge("data_analysis", 0.25, 0.02, +1, b["data_analysis"], scale=1),
                        Edge("communication", 0.25, 0.02, +1, b["communication"], scale=1)]))
    return n


# ------------------------------------------------------- 5.12 SDG 3 attainment
def build_sdg3(baseline: dict | None = None) -> BayesianNetwork:
    b = {"p_sdg3": 0.35, "mmr": 350.0, "u5mr": 70.0, "hiv_incidence": 3.0, "tb": 200.0,
         "malaria": 220.0, "ncd": 0.20, "uhc": 0.50, "financial_protection": 0.55,
         "health_expenditure": 0.40, "his_maturity": 0.55, "governance": 0.50, "conflict": 0.0}
    if baseline:
        b.update(baseline)
    n = BayesianNetwork("sdg3")
    for k, layer, kind, lo, hi in [
            ("mmr", "outcome-parent", "rate", 1, 1500), ("u5mr", "outcome-parent", "rate", 1, 300),
            ("hiv_incidence", "outcome-parent", "rate", 0.01, 50), ("tb", "outcome-parent", "rate", 1, 1500),
            ("malaria", "outcome-parent", "rate", 1, 1200), ("ncd", "outcome-parent", "prob", 0.01, 0.8),
            ("uhc", "enabler", "prob", 0, 1), ("financial_protection", "enabler", "prob", 0, 1),
            ("health_expenditure", "enabler", "prob", 0, 1), ("his_maturity", "enabler", "prob", 0, 1),
            ("governance", "enabler", "prob", 0, 1), ("conflict", "shock", "continuous", 0, 1)]:
        n.add(Node(k, layer, kind, b[k], lo=lo, hi=hi))
    n.add(Node("p_sdg3", "outcome", "prob", b["p_sdg3"], lo=0.01, hi=0.99, link="logit",
               parents=[Edge("mmr", 0.8, 0.12, -1, b["mmr"], scale=b["mmr"]),
                        Edge("u5mr", 0.8, 0.12, -1, b["u5mr"], scale=b["u5mr"]),
                        Edge("hiv_incidence", 0.4, 0.08, -1, b["hiv_incidence"], scale=b["hiv_incidence"]),
                        Edge("tb", 0.3, 0.06, -1, b["tb"], scale=b["tb"]),
                        Edge("malaria", 0.3, 0.06, -1, b["malaria"], scale=b["malaria"]),
                        Edge("ncd", 0.3, 0.06, -1, b["ncd"], scale=b["ncd"]),
                        Edge("uhc", 0.8, 0.12, +1, b["uhc"], scale=0.5),
                        Edge("financial_protection", 0.4, 0.08, +1, b["financial_protection"], scale=0.5),
                        Edge("health_expenditure", 0.4, 0.08, +1, b["health_expenditure"], scale=0.4),
                        Edge("his_maturity", 0.3, 0.06, +1, b["his_maturity"], scale=0.55),
                        Edge("governance", 0.3, 0.06, +1, b["governance"], scale=0.5),
                        Edge("conflict", 0.6, 0.12, -1, 0.0, scale=1)]))
    return n



# ------------------------------------------- 5.6 Universal Health Coverage
def build_uhc(baseline: dict | None = None) -> BayesianNetwork:
    b = {"sci": 0.50, "financial_protection": 0.55,
         "gov_health_expenditure": 0.40, "prepaid_coverage": 0.30, "out_of_pocket": 0.40,
         "service_readiness": 0.55, "workforce_density": 0.45, "medicine_availability": 0.60,
         "his_maturity": 0.55, "governance": 0.50, "poverty": 0.40,
         # tracer coverage groups that compose the service coverage index (WHO & World Bank 2023)
         "rmnch_coverage": 0.55, "infectious_coverage": 0.50, "ncd_service_coverage": 0.40}
    if baseline:
        b.update(baseline)
    n = BayesianNetwork("uhc")
    for k, layer in [("gov_health_expenditure", "financing"), ("prepaid_coverage", "financing"),
                     ("out_of_pocket", "financing"), ("service_readiness", "system"),
                     ("workforce_density", "system"), ("medicine_availability", "system"),
                     ("his_maturity", "system"), ("governance", "governance"),
                     ("poverty", "socioeconomic"), ("rmnch_coverage", "intermediate"),
                     ("infectious_coverage", "intermediate"), ("ncd_service_coverage", "intermediate")]:
        n.add(Node(k, layer, "prob", b[k], lo=0, hi=1))
    # service coverage index (fraction 0-1, logit link gives diminishing returns near saturation)
    n.add(Node("sci", "outcome", "prob", b["sci"], lo=0.05, hi=0.99, link="logit",
               parents=[Edge("gov_health_expenditure", 0.9, 0.14, +1, b["gov_health_expenditure"]),
                        Edge("prepaid_coverage", 0.7, 0.12, +1, b["prepaid_coverage"]),
                        Edge("service_readiness", 1.0, 0.14, +1, b["service_readiness"]),
                        Edge("workforce_density", 0.8, 0.12, +1, b["workforce_density"]),
                        Edge("medicine_availability", 0.6, 0.10, +1, b["medicine_availability"]),
                        Edge("his_maturity", 0.5, 0.10, +1, b["his_maturity"]),
                        Edge("governance", 0.5, 0.10, +1, b["governance"]),
                        Edge("rmnch_coverage", 0.9, 0.12, +1, b["rmnch_coverage"]),   # tracer group
                        Edge("infectious_coverage", 0.8, 0.12, +1, b["infectious_coverage"]),
                        Edge("ncd_service_coverage", 0.7, 0.12, +1, b["ncd_service_coverage"]),
                        Edge("out_of_pocket", 0.5, 0.10, -1, b["out_of_pocket"]),
                        Edge("poverty", 0.4, 0.10, -1, b["poverty"])]))
    # financial protection: rises with prepayment/coverage, falls with out-of-pocket
    n.add(Node("financial_protection", "outcome", "prob", b["financial_protection"], lo=0.05, hi=0.99,
               link="logit",
               parents=[Edge("prepaid_coverage", 1.0, 0.14, +1, b["prepaid_coverage"]),
                        Edge("gov_health_expenditure", 0.6, 0.10, +1, b["gov_health_expenditure"]),
                        Edge("out_of_pocket", 1.2, 0.16, -1, b["out_of_pocket"]),
                        Edge("sci", 0.5, 0.10, +1, b["sci"])]))
    return n


BUILDERS = {"hiv": build_hiv, "uhc": build_uhc, "tb": build_tb, "malaria": build_malaria, "ncd": build_ncd,
            "srhr": build_srhr, "rhis": build_rhis, "sdg3": build_sdg3}

OUTCOME = {"hiv": "incidence", "uhc": "sci", "tb": "incidence", "malaria": "incidence", "ncd": "premature_mortality",
           "srhr": "srhr_index", "rhis": "his_maturity_index", "sdg3": "p_sdg3"}

# Domain-specific scenario libraries (do-sets across layers)
SCENARIO_LIBRARY = {
    "uhc": {"UHC investment": {"gov_health_expenditure": 0.60, "prepaid_coverage": 0.55,
                               "out_of_pocket": 0.25, "service_readiness": 0.75, "workforce_density": 0.65},
            "Financing transition": {"out_of_pocket": 0.20, "prepaid_coverage": 0.60},
            "Workforce + medicines": {"workforce_density": 0.70, "medicine_availability": 0.85}},
    "hiv": {"HIV Acceleration": {"art_coverage": 0.95, "hiv_testing": 0.95, "supply_chain": 0.90},
            "Digital Transformation": {"his_maturity": 0.90}, "Conflict shock": {"conflict": 0.8}},
    "tb": {"Find-Treat-Cure": {"genexpert": 0.90, "community_screening": 0.85, "drug_availability": 0.95,
                               "digital_adherence": 0.80, "tpt": 0.70},
           "TPT scale-up": {"tpt": 0.90},
           "HIV/TB integration": {"art_coverage": 0.95, "hiv_prevalence": 0.07}},
    "malaria": {"Vector-control scale-up": {"itn": 0.85, "irs": 0.50},
                "Chemoprevention scale-up": {"chemoprevention": 0.80, "act": 0.85},
                "Climate shock (flood)": {"floods": 0.80}},
    "ncd": {"Best buys": {"tobacco": 0.08, "salt_diet": 0.25, "htn_control": 0.55},
            "HEARTS hypertension": {"htn_control": 0.70, "medicine_availability": 0.85},
            "Urbanisation trend": {"urbanization": 0.70, "inactivity": 0.40}},
    "srhr": {"FP scale-up": {"family_planning": 0.75, "commodity": 0.90},
             "Girls' education + youth services": {"education": 0.85, "youth_services": 0.80},
             "Gender equity": {"gender_inequality": 0.20}},
    "rhis": {"Governance strengthening": {"governance": 85.0},
             "Digitalisation (data generation)": {"data_generation": 90.0},
             "Full HIS investment": {"governance": 85.0, "data_generation": 90.0,
                                     "data_analysis": 82.0, "communication": 82.0}},
    "sdg3": {"Mortality reduction": {"mmr": 200.0, "u5mr": 45.0},
             "UHC investment": {"uhc": 0.75, "health_expenditure": 0.60, "financial_protection": 0.75},
             "Integrated reform": {"mmr": 220.0, "u5mr": 48.0, "uhc": 0.72, "malaria": 140.0, "tb": 130.0}},
}


def available_networks() -> list[str]:
    return list(BUILDERS)


# ------------------------------------------------------------ UI/adapter metadata
# Outcome display: (label, unit, better_direction)   better: 'down' or 'up'
OUTCOME_META = {
    "hiv": ("HIV incidence", "per 1,000", "down"),
    "uhc": ("UHC service coverage index", "index 0–1", "up"),
    "tb": ("TB incidence", "per 100,000", "down"),
    "malaria": ("Malaria incidence", "per 1,000 at risk", "down"),
    "ncd": ("Premature NCD mortality", "probability 30–70", "down"),
    "srhr": ("SRHR coverage index", "index 0–1", "up"),
    "rhis": ("HIS maturity index", "0–100", "up"),
    "sdg3": ("SDG 3 attainment", "probability", "up"),
}

# Policy levers per domain: (node, label, kind)  kind: 'prob' (0–1 shown as %) or 'score' (0–100)
# improves: True if raising the lever improves the outcome (green dot), False if it worsens it (orange)
LEVER_SPECS = {
    "uhc": [("gov_health_expenditure", "Government health expenditure", "prob", True),
            ("prepaid_coverage", "Prepaid/pooled coverage", "prob", True),
            ("service_readiness", "Service readiness", "prob", True),
            ("workforce_density", "Health-workforce density", "prob", True),
            ("medicine_availability", "Essential-medicine availability", "prob", True),
            ("his_maturity", "HIS maturity", "prob", True),
            ("governance", "Governance", "prob", True),
            ("out_of_pocket", "Out-of-pocket share", "prob", False),
            ("poverty", "Poverty", "prob", False)],
    "tb": [("genexpert", "GeneXpert / diagnostic access", "prob", True),
           ("community_screening", "Community screening", "prob", True),
           ("drug_availability", "Drug availability", "prob", True),
           ("digital_adherence", "Digital adherence support", "prob", True),
           ("tpt", "TB preventive therapy", "prob", True),
           ("art_coverage", "ART coverage (HIV/TB)", "prob", True)],
    "malaria": [("itn", "ITN coverage / use", "prob", True),
                ("irs", "Indoor residual spraying", "prob", True),
                ("act", "ACT treatment access", "prob", True),
                ("chemoprevention", "Chemoprevention (SMC/IPTp)", "prob", True),
                ("rdt", "Rapid diagnostic tests", "prob", True),
                ("vaccine", "Malaria vaccine (RTS,S/R21)", "prob", True),
                ("larval_source_mgmt", "Larval source management", "prob", True),
                ("care_seeking", "Prompt care-seeking", "prob", True),
                ("housing", "Improved housing", "prob", True),
                ("insecticide_resistance", "Insecticide resistance", "prob", False)],
    "ncd": [("tobacco", "Tobacco use", "prob", False),
            ("alcohol", "Harmful alcohol use", "prob", False),
            ("inactivity", "Physical inactivity", "prob", False),
            ("salt_diet", "High-salt diet", "prob", False),
            ("obesity", "Obesity", "prob", False),
            ("htn_control", "Hypertension control", "prob", True),
            ("diabetes_control", "Diabetes control", "prob", True),
            ("screening", "NCD screening", "prob", True),
            ("primary_care_readiness", "Primary-care readiness", "prob", True),
            ("medicine_availability", "Essential-medicine availability", "prob", True)],
    "srhr": [("family_planning", "Modern contraception (FP)", "prob", True),
             ("anc", "Antenatal care", "prob", True),
             ("skilled_attendance", "Skilled attendance", "prob", True),
             ("education", "Girls' education", "prob", True),
             ("gbv_services", "GBV services", "prob", True),
             ("youth_services", "Youth-friendly services", "prob", True),
             ("commodity", "Commodity availability", "prob", True),
             ("gender_inequality", "Gender inequality", "prob", False),
             ("adolescent_fertility", "Adolescent fertility", "prob", False)],
    "rhis": [("strategic_planning", "Strategic planning", "score", True),
             ("policy", "Policy & governance", "score", True),
             ("financing", "HIS financing", "score", True),
             ("supervision", "Supportive supervision", "score", True),
             ("routine_reporting", "Routine reporting completeness", "score", True),
             ("dhis2", "DHIS2 use", "score", True),
             ("data_quality", "Data quality assurance", "score", True),
             ("crvs", "CRVS functionality", "score", True),
             ("interoperability", "Interoperability", "score", True),
             ("data_analysis", "Data analysis & synthesis", "score", True),
             ("dashboards", "Dashboards & visualisation", "score", True),
             ("data_use", "Data use for decisions", "score", True)],
    "sdg3": [("uhc", "UHC service coverage", "prob", True),
             ("financial_protection", "Financial protection", "prob", True),
             ("health_expenditure", "Government health expenditure", "prob", True),
             ("his_maturity", "HIS maturity", "prob", True),
             ("governance", "Governance", "prob", True)],
}

TITLES = {"uhc": "Universal Health Coverage Explorer", "tb": "Tuberculosis Explorer", "malaria": "Malaria Explorer",
          "ncd": "NCD Explorer", "srhr": "SRHR Explorer",
          "rhis": "Routine HIS / Maturity Explorer", "sdg3": "SDG 3 Attainment Explorer"}


def default_baselines(dom: str, country: str | None = None) -> dict:
    """All node baselines for a domain (introspected from the built network)."""
    net = BUILDERS[dom](country) if dom == "rhis" else BUILDERS[dom]()
    return {name: node.baseline for name, node in net.nodes.items()}
