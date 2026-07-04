"""Simulated per-country baselines for the Bayesian domain networks (offline demo).

For domains without a mined panel (TB, malaria, NCD, SRHR, SDG 3), generate a
plausible country baseline for each AFRO member state by perturbing the network's
default node baselines around a subregional burden tier. Clearly illustrative;
replaced by mined data on deployment. RHIS uses the mined HIS maturity panel and
is not simulated here.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from scenario_engine import bayes_networks as BN  # noqa: E402
from warehouse import reference  # noqa: E402

RNG = np.random.default_rng(4242)
OUT = ROOT / "data" / "processed" / "bayes"

# outcome burden multiplier by subregion (higher = worse for 'down' outcomes)
BURDEN = {"Western Africa": 1.25, "Central Africa": 1.2, "Eastern Africa": 0.95,
          "Southern Africa": 0.85, "Northern Africa": 0.6}
SIM_DOMAINS = ["tb", "malaria", "ncd", "srhr", "sdg3"]


def _clip01(x):
    return float(np.clip(x, 0.03, 0.98))


def build_domain(dom: str) -> pd.DataFrame:
    base = BN.default_baselines(dom)
    outcome = BN.OUTCOME[dom]
    _, _, better = BN.OUTCOME_META[dom]
    lever_keys = [k for (k, *_ ) in BN.LEVER_SPECS[dom]]
    countries = reference.countries()
    rows = []
    for _, r in countries.iterrows():
        b = BURDEN.get(r["subregion"], 1.0)
        dev = np.interp(b, [0.6, 1.25], [1.0, 0.0])  # development proxy (higher where burden lower)
        row = {"country": r["country"], "iso3": r["iso3"], "subregion": r["subregion"]}
        # outcome
        o = base[outcome]
        if better == "down":
            row[outcome] = round(max(o * b * RNG.normal(1, 0.12), 0.02), 3)
        else:  # positive index: better where development higher
            row[outcome] = _clip01(o * (0.7 + 0.5 * dev) * RNG.normal(1, 0.06))
        # levers
        for k, _lbl, kind, improves in BN.LEVER_SPECS[dom]:
            v = base.get(k, 0.5)
            if kind == "prob":
                # protective coverages higher where development higher; risk factors higher where lower
                factor = (0.55 + 0.5 * dev) if improves else (1.4 - 0.5 * dev)
                row[k] = _clip01(v * factor * RNG.normal(1, 0.08))
            else:  # score 0-100
                row[k] = round(float(np.clip(v * (0.7 + 0.5 * dev) * RNG.normal(1, 0.08), 3, 98)), 1)
        rows.append(row)
    return pd.DataFrame(rows)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for dom in SIM_DOMAINS:
        df = build_domain(dom)
        df.to_csv(OUT / f"{dom}_baselines.csv", index=False)
        oc = BN.OUTCOME[dom]
        print(f"{dom:8s} -> {len(df)} countries | {oc} range "
              f"{df[oc].min():.2f}–{df[oc].max():.2f}")
