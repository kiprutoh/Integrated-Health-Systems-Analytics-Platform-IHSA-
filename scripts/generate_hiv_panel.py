"""
Generate an ILLUSTRATIVE AFRO HIV country-year panel.

This script fabricates a synthetic-but-plausible panel so that the app and model
run offline. In production, `build_dataset.py` replaces this file by pulling real
indicators from UNAIDS AIDSinfo, WHO GHO, DHS/PHIA and the World Bank API.

The synthetic data-generating process encodes the *direction* of well-established
HIV epidemiological relationships (treatment-as-prevention, VMMC, condoms, PrEP,
structural drivers) so the fitted statistical model behaves sensibly. Absolute
values are illustrative and MUST NOT be cited as estimates.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

RNG = np.random.default_rng(20240607)

# (country, iso3, burden tier, baseline 2010 adult prevalence %, baseline incidence /1000)
COUNTRIES = [
    ("Eswatini", "SWZ", "very_high", 26.0, 22.0),
    ("Lesotho", "LSO", "very_high", 23.0, 20.0),
    ("Botswana", "BWA", "very_high", 21.0, 14.0),
    ("South Africa", "ZAF", "very_high", 17.0, 12.0),
    ("Zimbabwe", "ZWE", "high", 15.0, 9.0),
    ("Namibia", "NAM", "high", 13.0, 8.0),
    ("Zambia", "ZMB", "high", 12.5, 8.5),
    ("Mozambique", "MOZ", "high", 12.0, 10.0),
    ("Malawi", "MWI", "high", 11.0, 7.0),
    ("Uganda", "UGA", "high", 7.2, 5.5),
    ("Kenya", "KEN", "high", 6.0, 4.5),
    ("Tanzania", "TZA", "high", 5.5, 3.8),
    ("Cameroon", "CMR", "moderate", 4.5, 2.8),
    ("Gabon", "GAB", "moderate", 4.2, 2.5),
    ("Rwanda", "RWA", "moderate", 3.2, 1.6),
    ("Cote d'Ivoire", "CIV", "moderate", 3.5, 2.0),
    ("Nigeria", "NGA", "moderate", 1.6, 1.2),
    ("Ghana", "GHA", "moderate", 1.8, 1.1),
    ("Angola", "AGO", "moderate", 2.0, 1.8),
    ("DR Congo", "COD", "low", 1.2, 0.8),
    ("Ethiopia", "ETH", "low", 1.1, 0.6),
    ("Burkina Faso", "BFA", "low", 0.9, 0.5),
    ("Senegal", "SEN", "low", 0.5, 0.3),
    ("Niger", "NER", "low", 0.4, 0.25),
    ("Madagascar", "MDG", "low", 0.4, 0.35),
]

YEARS = list(range(2010, 2024))

# UNAIDS/WHO structural priors by burden tier (2010 starting points, %).
TIER = {
    "very_high": dict(art0=25, know0=45, vls0=20, condom0=55, vmmc0=15, prep0=0,
                      lit0=80, gii0=0.55, gdp0=6000, sti0=9, urban0=40, know_comp0=45),
    "high":      dict(art0=22, know0=42, vls0=18, condom0=45, vmmc0=25, prep0=0,
                      lit0=70, gii0=0.58, gdp0=1600, sti0=8, urban0=35, know_comp0=40),
    "moderate":  dict(art0=20, know0=38, vls0=16, condom0=40, vmmc0=45, prep0=0,
                      lit0=60, gii0=0.62, gdp0=2200, sti0=6, urban0=45, know_comp0=35),
    "low":       dict(art0=18, know0=35, vls0=15, condom0=35, vmmc0=60, prep0=0,
                      lit0=45, gii0=0.66, gdp0=900, sti0=5, urban0=30, know_comp0=30),
}

# Response elasticities used to build the synthetic incidence surface.
# These mirror the mechanistic model in src/cascade_model.py.
E_VLS = 0.85      # viral load suppression -> infectious pool reduction
E_CONDOM = 0.72   # population condom effectiveness
E_VMMC = 0.60     # VMMC reduction in female->male transmission
E_PREP = 0.55     # PrEP population effectiveness
STI_MULT = 0.06   # per-point STI prevalence cofactor multiplier


def _clip(x, lo, hi):
    return float(np.clip(x, lo, hi))


def build() -> pd.DataFrame:
    rows = []
    for name, iso3, tier, prev0, inc0 in COUNTRIES:
        p = TIER[tier]
        prev = prev0
        # scale-up speeds differ by tier (very_high countries ran the fastest ART scale-up)
        art_speed = {"very_high": 5.2, "high": 4.6, "moderate": 3.8, "low": 3.0}[tier]
        for i, year in enumerate(YEARS):
            t = year - 2010
            # --- programmatic scale-up trajectories (logistic-ish, with noise) ---
            art = _clip(p["art0"] + art_speed * t + RNG.normal(0, 2), 5, 98)
            know = _clip(p["know0"] + 3.6 * t + RNG.normal(0, 2), 20, 97)
            # viral suppression tracks ART but lags
            vls = _clip(p["vls0"] + 4.6 * t + RNG.normal(0, 2), 8, 95)
            condom = _clip(p["condom0"] + 0.9 * t + RNG.normal(0, 2), 20, 85)
            vmmc = _clip(p["vmmc0"] + (2.6 if tier in ("very_high", "high") else 0.4) * t
                         + RNG.normal(0, 2), 5, 90)
            prep = _clip((0 if t < 6 else 0.8 * (t - 5)) + RNG.normal(0, 0.4), 0, 12)
            lit = _clip(p["lit0"] + 0.8 * t + RNG.normal(0, 1.5), 20, 99)
            gii = _clip(p["gii0"] - 0.006 * t + RNG.normal(0, 0.01), 0.30, 0.75)
            gdp = _clip(p["gdp0"] * (1.03 ** t) * RNG.normal(1, 0.05), 300, 20000)
            he = _clip(4.5 + 0.06 * t + RNG.normal(0, 0.6), 2, 9)
            sti = _clip(p["sti0"] - 0.10 * t + RNG.normal(0, 0.6), 2, 14)
            urban = _clip(p["urban0"] + 0.6 * t + RNG.normal(0, 1), 15, 80)
            know_comp = _clip(p["know_comp0"] + 1.6 * t + RNG.normal(0, 2), 15, 80)

            # --- mechanistic incidence surface (relative to baseline drivers) ---
            infectious_pool = max(0.02, 1 - E_VLS * vls / 100)
            m_condom = 1 - E_CONDOM * (condom - p["condom0"]) / 100
            m_vmmc = 1 - E_VMMC * 0.5 * (vmmc - p["vmmc0"]) / 100  # applies to ~half (male) share
            m_prep = 1 - E_PREP * prep / 100
            m_sti = 1 + STI_MULT * (sti - p["sti0"])
            m_struct = (1 - 0.15 * (lit - p["lit0"]) / 100) * (1 + 0.4 * (gii - p["gii0"]))

            rel = (infectious_pool / max(0.02, 1 - E_VLS * p["vls0"] / 100))
            incidence = inc0 * rel * m_condom * m_vmmc * m_prep * m_sti * m_struct
            incidence = _clip(incidence * RNG.normal(1, 0.06), 0.02, 30)

            # prevalence evolves: + new infections (approx), - AIDS/background mortality,
            # strongly damped once ART scale-up suppresses mortality.
            aids_mort = _clip((prev * (1 - vls / 130)) * 6 * RNG.normal(1, 0.08), 1, 400)
            prev = _clip(prev + 0.08 * incidence - 0.015 * prev * (1 + vls / 200)
                         + RNG.normal(0, 0.15), 0.1, 30)

            rows.append(dict(
                country=name, iso3=iso3, year=year, burden_tier=tier,
                hiv_prevalence=round(prev, 2),
                hiv_incidence=round(incidence, 3),
                aids_mortality=round(aids_mort, 1),
                art_coverage=round(art, 1),
                pct_know_status=round(know, 1),
                viral_suppression=round(vls, 1),
                condom_use=round(condom, 1),
                vmmc_coverage=round(vmmc, 1),
                prep_coverage=round(prep, 2),
                comprehensive_knowledge=round(know_comp, 1),
                sti_prevalence=round(sti, 1),
                female_literacy=round(lit, 1),
                gender_inequality=round(gii, 3),
                gdp_per_capita=round(gdp, 0),
                health_expenditure_pct=round(he, 2),
                urban_pct=round(urban, 1),
            ))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = build()
    out = "data/processed/hiv/afro_hiv_panel.csv"
    df.to_csv(out, index=False)
    print(f"Wrote {out}: {len(df)} rows, {df['country'].nunique()} countries, "
          f"{df['year'].min()}-{df['year'].max()}")
    print(df.groupby('burden_tier')[['hiv_incidence', 'hiv_prevalence', 'viral_suppression']]
          .mean().round(2))
