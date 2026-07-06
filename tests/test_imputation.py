"""Tests for the missing-data imputation framework."""
import numpy as np
import pandas as pd
from warehouse import imputation as imp


def _panel(missing=0.2, seed=0):
    rng = np.random.default_rng(seed)
    C = [("KEN", "Eastern Africa"), ("NGA", "Western Africa"), ("ZAF", "Southern Africa"),
         ("GHA", "Western Africa"), ("TZA", "Eastern Africa"), ("COD", "Central Africa")]
    loads = np.array([0.9, 0.8, -0.7, 0.85]); offs = np.array([55, 50, 45, 52]); rows = []
    for iso, sub in C:
        dev = rng.normal(0, 10); drift = rng.normal(0.8, 0.3)
        for y in range(2016, 2024):
            f = dev + (y - 2016) * drift
            vals = offs + loads * f + rng.normal(0, 3, 4)
            rows.append(dict(iso3=iso, subregion=sub, year=y,
                             **{f"ind{k+1}": float(vals[k]) for k in range(4)}))
    df = pd.DataFrame(rows); cols = [f"ind{k+1}" for k in range(4)]
    df.loc[:, cols] = df[cols].mask(rng.random(df[cols].shape) < missing)
    return df, cols


def test_no_missing_after_imputation():
    df, cols = _panel()
    res = imp.impute_panel(df, cols, m=3, bounds={c: (0, 120) for c in cols})
    assert int(res.data[cols].isna().sum().sum()) == 0


def test_bounds_respected():
    df, cols = _panel()
    res = imp.impute_panel(df, cols, m=3, bounds={c: (0, 100) for c in cols})
    v = res.data[cols].to_numpy()
    assert (v >= 0).all() and (v <= 100).all()


def test_temporal_interpolation_exact_linear():
    # a perfectly linear series with an interior gap is recovered exactly
    df = pd.DataFrame({"iso3": ["A"] * 5, "subregion": ["X"] * 5,
                       "year": [2019, 2020, 2021, 2022, 2023],
                       "v": [10.0, 20.0, np.nan, 40.0, 50.0]})
    out = imp.temporal_interpolate(df, ["v"])
    assert abs(float(out.sort_values("year")["v"].iloc[2]) - 30.0) < 1e-6


def test_rubin_pool_formula():
    est = [10.0, 12.0, 11.0]; var = [1.0, 1.0, 1.0]
    r = imp.rubin_pool(est, var)
    b = np.var(est, ddof=1)
    assert abs(r["between_var"] - b) < 1e-9
    assert abs(r["total_var"] - (1.0 + (1 + 1 / 3) * b)) < 1e-9
    assert 0 <= r["fmi"] <= 1


def test_provenance_flags_present():
    df, cols = _panel(missing=0.3)
    res = imp.impute_panel(df, cols, m=2)
    labels = set(res.method.stack().unique())
    assert "observed" in labels and (res.imputed_mask.values.sum() > 0)
    # every imputed cell is flagged as non-observed
    assert bool((res.method.values[res.imputed_mask.values] != "observed").all())


def test_holdout_validation_runs():
    df, cols = _panel()
    v = imp.holdout_validation(df, cols, frac=0.15, m=5, bounds={c: (0, 120) for c in cols})
    assert v["n_held_out"] > 0 and 0.0 <= v["coverage95"] <= 1.0 and v["rmse"] >= 0


def test_single_vs_multiple():
    df, cols = _panel()
    r1 = imp.impute_panel(df, cols, m=1)
    r5 = imp.impute_panel(df, cols, m=5)
    assert r1.m == 1 and r5.m == 5 and len(r5.completed) == 5
