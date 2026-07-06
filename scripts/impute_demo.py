"""Demonstrate the IHSA missing-data imputation framework end-to-end.

Loads (or builds) a country-year panel, reports missingness, runs multiple
imputation with auto-calibration, validates recovery on held-out cells, and shows
Rubin's-rules pooling. Run: python scripts/impute_demo.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from warehouse import imputation as imp  # noqa: E402
from warehouse import reference  # noqa: E402


def demo_panel() -> tuple[pd.DataFrame, list[str]]:
    """Illustrative correlated panel over AFRO countries with induced missingness."""
    rng = np.random.default_rng(2027)
    ref = reference.countries()[["iso3", "subregion"]].drop_duplicates().head(20)
    loads = np.array([0.9, 0.8, -0.7, 0.85, 0.6])
    offs = np.array([60, 55, 45, 50, 40])
    cols = ["sba", "anc4", "mmr_idx", "immun", "fp"]
    rows = []
    for _, r in ref.iterrows():
        dev = rng.normal(0, 10); drift = rng.normal(0.8, 0.3)
        for y in range(2015, 2024):
            f = dev + (y - 2015) * drift
            vals = offs + loads * f + rng.normal(0, 3, len(cols))
            rows.append(dict(iso3=r["iso3"], subregion=r["subregion"], year=y,
                             **{c: float(vals[k]) for k, c in enumerate(cols)}))
    df = pd.DataFrame(rows)
    df.loc[:, cols] = df[cols].mask(rng.random(df[cols].shape) < 0.28)   # 28% missing
    return df, cols


def main() -> None:
    df, cols = demo_panel()
    bounds = {c: (0, 120) for c in cols}

    print("=" * 66)
    print(imp.missingness_report(df, cols))

    print("\n--- Held-out validation across inflation factors ---")
    for infl in (1.0, "auto"):
        v = imp.holdout_validation(df, cols, frac=0.15, m=12, bounds=bounds,
                                   seed=1, noise_inflation=(1.0 if infl == 1.0 else
                                   imp.calibrate_inflation(df, cols, bounds=bounds)))
        tag = "default (1.0)" if infl == 1.0 else "auto-calibrated"
        print(f"  {tag:16s}: RMSE={v['rmse']:.2f}  bias={v['bias']:+.2f}  "
              f"95% coverage={v['coverage95']:.0%}")

    print("\n--- Multiple imputation (m=12, auto-calibrated) ---")
    res = imp.impute_panel(df, cols, m=12, bounds=bounds, noise_inflation="auto")
    print(f"  remaining missing: {int(res.data[cols].isna().sum().sum())}")
    print(f"  provenance: {res.method.stack().value_counts().to_dict()}")

    print("\n--- Rubin's-rules pooling of a downstream estimate (regional mean SBA) ---")
    est = [d.loc[d.year == 2023, "sba"].mean() for d in res.completed]
    var = [d.loc[d.year == 2023, "sba"].var() / d.loc[d.year == 2023, "sba"].count()
           for d in res.completed]
    pool = imp.rubin_pool(est, var)
    print(f"  pooled SBA 2023 = {pool['estimate']:.1f}  (95% CI "
          f"{pool['ci95'][0]:.1f}–{pool['ci95'][1]:.1f}),  "
          f"fraction of missing information = {pool['fmi']:.2f}")


if __name__ == "__main__":
    main()
