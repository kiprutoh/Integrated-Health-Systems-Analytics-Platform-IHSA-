"""
Domain Bayesian networks and the multi-domain scenario library.

Sign convention (structural): sign = +1 means increasing the parent increases
this node (on its link scale); sign = -1 means it decreases it. Coefficients are
non-negative magnitudes; direction is carried entirely by `sign`. A protective
driver of an adverse outcome (viral suppression -> HIV incidence) carries -1;
a positive driver of a positive node (ART coverage -> viral suppression) carries +1.
Coefficients are illustrative/elicited and replaced by fitted posteriors on mining.
"""
from __future__ import annotations

from scenario_engine.bayes_engine import BayesianNetwork, Edge, Node


def build_hiv(baseline: dict | None = None) -> BayesianNetwork:
    b = {"incidence": 4.0, "viral_suppression": 0.75, "art_coverage": 0.78,
         "hiv_testing": 0.80, "supply_chain": 0.75, "his_maturity": 0.55,
         "condom_use": 0.45, "sti_prevalence": 0.10, "female_literacy": 0.65, "conflict": 0.0}
    if baseline:
        b.update(baseline)
    net = BayesianNetwork("hiv")
    net.add(Node("female_literacy", "socioeconomic", "prob", b["female_literacy"], lo=0, hi=1))
    net.add(Node("conflict", "shock", "continuous", b["conflict"], lo=0, hi=1))
    net.add(Node("his_maturity", "system", "continuous", b["his_maturity"], lo=0, hi=1))
    net.add(Node("condom_use", "intermediate", "prob", b["condom_use"], lo=0, hi=1))
    net.add(Node("sti_prevalence", "disease", "prob", b["sti_prevalence"], lo=0, hi=1))
    net.add(Node("supply_chain", "system", "prob", b["supply_chain"], lo=0.05, hi=1, link="logit",
                 parents=[Edge("his_maturity", 0.9, 0.12, sign=+1, ref=b["his_maturity"]),
                          Edge("conflict", 1.2, 0.20, sign=-1, ref=0.0)]))
    net.add(Node("hiv_testing", "system", "prob", b["hiv_testing"], lo=0.05, hi=1, link="logit",
                 parents=[Edge("his_maturity", 0.8, 0.12, sign=+1, ref=b["his_maturity"])]))
    net.add(Node("art_coverage", "intermediate", "prob", b["art_coverage"], lo=0.05, hi=0.99, link="logit",
                 parents=[Edge("hiv_testing", 1.4, 0.18, sign=+1, ref=b["hiv_testing"]),
                          Edge("supply_chain", 0.9, 0.14, sign=+1, ref=b["supply_chain"])]))
    net.add(Node("viral_suppression", "intermediate", "prob", b["viral_suppression"], lo=0.05, hi=0.99,
                 link="logit",
                 parents=[Edge("art_coverage", 2.2, 0.25, sign=+1, ref=b["art_coverage"]),
                          Edge("supply_chain", 0.6, 0.12, sign=+1, ref=b["supply_chain"])]))
    net.add(Node("incidence", "outcome", "rate", b["incidence"], lo=0.01, hi=50, noise_sd=0.05, link="log",
                 parents=[Edge("viral_suppression", 2.4, 0.28, sign=-1, ref=b["viral_suppression"]),
                          Edge("condom_use", 0.6, 0.12, sign=-1, ref=b["condom_use"]),
                          Edge("sti_prevalence", 0.9, 0.16, sign=+1, ref=b["sti_prevalence"]),
                          Edge("female_literacy", 0.4, 0.10, sign=-1, ref=b["female_literacy"])]))
    return net


SCENARIO_PACKAGES = {
    "Baseline": {},
    "HIV Acceleration": {"art_coverage": 0.95, "hiv_testing": 0.95, "supply_chain": 0.90},
    "Digital Transformation": {"his_maturity": 0.90},
    "Conflict shock": {"conflict": 0.8},
}

BUILDERS = {"hiv": build_hiv}
