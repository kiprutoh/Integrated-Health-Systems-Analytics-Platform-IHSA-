"""
IHSA missing-data imputation framework.
=======================================

Country-year health panels are pervasively incomplete. This module provides one
principled, reusable imputation pipeline for every IHSA module, replacing ad-hoc
fills. It is numpy/pandas-only (no scikit-learn) so it runs in minimal
environments, and it flags the provenance of every imputed cell.

Missingness mechanisms (Rubin, 1976; Little & Rubin, 2019)
----------------------------------------------------------
Let R be the missingness indicator (1 = observed). Writing the data as
(X_obs, X_mis):
    MCAR :  P(R | X_obs, X_mis) = P(R)                 (missing completely at random)
    MAR  :  P(R | X_obs, X_mis) = P(R | X_obs)         (missing at random)
    MNAR :  depends on X_mis itself                    (not at random)
Multiple imputation is valid under MAR, which is the working assumption here:
missingness in one indicator is explained by the other observed indicators, by
the country's own time trend, and by its subregion.

The method hierarchy (applied in order by `impute_panel`)
--------------------------------------------------------
1. TEMPORAL interpolation within each country. Health indicators are smooth in
   time, so interior gaps are linearly interpolated and edges carried
   forward/backward (LOCF/NOCB). For observed years t0 < t < t1:
       x_t = x_{t0} + (x_{t1} - x_{t0}) * (t - t0)/(t1 - t0)

2. MULTIVARIATE imputation by chained equations (MICE; van Buuren &
   Groothuis-Oudshoorn, 2011). Each still-missing indicator X_j is imputed from a
   regression on the other indicators X_{-j}, cycling until stable. Each draw is a
   PROPER imputation: prediction plus a residual draw, so between-imputation
   spread reflects real uncertainty:
       X_j^{mis} <- x_hat_j + e,   e ~ N(0, sigma_j^2)

3. HIERARCHICAL shrinkage fallback for cells MICE cannot reach (e.g. an indicator
   a country never reports). Under a normal hierarchical model
   x_c ~ N(mu_sub, tau^2), x_obs ~ N(x_c, s^2), the posterior mean shrinks the
   country toward its subregion mean mu_sub (empirical-Bayes / James-Stein):
       x_hat_c = mu_sub + (1 - B)(x_bar_c - mu_sub),  B = s^2/(s^2 + tau^2)
   With no country observation the estimate is simply mu_sub.

Multiple imputation & pooling (Rubin, 1987)
-------------------------------------------
Running the pipeline m times yields m completed datasets. A downstream estimate Q
with within-imputation variances U_l is pooled by Rubin's rules:
       Qbar = (1/m) sum_l Q_l
       Ubar = (1/m) sum_l U_l                          (within-imputation)
       B    = (1/(m-1)) sum_l (Q_l - Qbar)^2           (between-imputation)
       T    = Ubar + (1 + 1/m) B                       (total variance)
       lambda = (1 + 1/m) B / T                        (fraction of missing info)
This propagates imputation uncertainty into the scenario engine's intervals.

All imputed values are truncated to plausibility bounds (e.g. coverage in [0,100],
rates >= 0) and flagged with the method used, honouring the platform rule that no
imputed figure is mistaken for an observation.

References
----------
Little, R.J.A. & Rubin, D.B. (2019) Statistical Analysis with Missing Data. 3rd edn.
Rubin, D.B. (1976) 'Inference and missing data', Biometrika, 63(3), pp. 581-592.
Rubin, D.B. (1987) Multiple Imputation for Nonresponse in Surveys.
van Buuren, S. & Groothuis-Oudshoorn, K. (2011) 'mice: multivariate imputation by
    chained equations in R', Journal of Statistical Software, 45(3), pp. 1-67.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


# ----------------------------------------------------------------- diagnostics
@dataclass
class MissingnessReport:
    n_rows: int
    per_column: dict            # col -> fraction missing
    overall: float
    monotone: bool

    def __str__(self) -> str:
        lines = [f"Missingness: {self.overall:.1%} overall across {self.n_rows} rows"]
        for c, f in sorted(self.per_column.items(), key=lambda kv: -kv[1]):
            if f > 0:
                lines.append(f"  {c:32s} {f:6.1%}")
        return "\n".join(lines)


def missingness_report(df: pd.DataFrame, value_cols: list[str]) -> MissingnessReport:
    m = df[value_cols].isna()
    per = {c: float(m[c].mean()) for c in value_cols}
    # monotone pattern = columns can be ordered so that missingness is nested
    order = sorted(value_cols, key=lambda c: per[c])
    mono = True
    for i in range(len(order) - 1):
        a, b = m[order[i]], m[order[i + 1]]
        if not bool((~a | b).all()):   # a missing implies b missing?
            mono = False
            break
    return MissingnessReport(len(df), per, float(m.values.mean()), mono)


# --------------------------------------------------------------- bounds
def _bounds(value_cols, bounds):
    b = {c: (0.0, np.inf) for c in value_cols}          # default: non-negative
    if bounds:
        b.update(bounds)
    return b


def _column_noise(df: pd.DataFrame, value_cols: list[str], group: str, time: str) -> dict:
    """Honest per-column imputation noise, estimated as the leave-one-out (LOO)
    temporal-interpolation residual SD: for each observed point, interpolate it
    from the country's remaining points and record the error. This measures the
    actual predictive uncertainty of the temporal stage (including gaps and edge
    extrapolation) and calibrates the multiple-imputation spread. Falls back to a
    fraction of the column SD where a series is too short."""
    sigma = {}
    for c in value_cols:
        errs = []
        if group in df.columns and time in df.columns:
            for _, g in df[[group, time, c]].dropna().groupby(group):
                g = g.sort_values(time)
                t = g[time].to_numpy(float); y = g[c].to_numpy(float)
                if len(t) < 3:
                    continue
                for i in range(len(t)):
                    tt = np.delete(t, i); yy = np.delete(y, i)
                    if tt.min() <= t[i] <= tt.max():          # interior -> interpolate
                        yi = float(np.interp(t[i], tt, yy))
                    else:                                     # edge -> nearest (LOCF/NOCB)
                        yi = yy[0] if t[i] < tt.min() else yy[-1]
                    errs.append(y[i] - yi)
        s = float(np.std(errs)) if len(errs) >= 3 else np.nan
        if not np.isfinite(s) or s == 0:
            gs = float(np.nanstd(df[c])) if np.isfinite(np.nanstd(df[c])) else 1.0
            s = 0.5 * gs
        sigma[c] = max(s, 1e-6)
    return sigma


def _apply_bounds(series: pd.Series, lohi) -> pd.Series:
    lo, hi = lohi
    return series.clip(lower=lo, upper=hi)


# --------------------------------------------------------------- 1. temporal
def temporal_interpolate(df: pd.DataFrame, value_cols: list[str],
                         group: str = "iso3", time: str = "year") -> pd.DataFrame:
    """Linear interpolation of interior gaps within each country, LOCF/NOCB at edges."""
    out = df.sort_values([group, time]).copy()

    def _fill(g):
        g = g.sort_values(time)
        for c in value_cols:
            s = g[c]
            if s.notna().sum() >= 2:
                s = s.interpolate(method="linear", limit_direction="both")
            elif s.notna().sum() == 1:
                s = s.ffill().bfill()
            g[c] = s
        return g

    return out.groupby(group, group_keys=False).apply(_fill)


# --------------------------------------------------------------- 3. hierarchical
def hierarchical_fill(df: pd.DataFrame, value_cols: list[str],
                      group: str = "subregion") -> pd.DataFrame:
    """Fill remaining gaps with the subregional mean, then the global mean."""
    out = df.copy()
    for c in value_cols:
        if group in out.columns:
            out[c] = out[c].fillna(out.groupby(group)[c].transform("mean"))
        out[c] = out[c].fillna(out[c].mean())
    return out


def shrinkage_estimate(country_vals: np.ndarray, sub_mean: float,
                       sub_var: float, obs_var: float) -> float:
    """Empirical-Bayes posterior mean: shrink country mean toward subregion mean.

    x_hat = mu_sub + (1 - B)(x_bar - mu_sub),  B = obs_var / (obs_var + sub_var)
    """
    vals = country_vals[~np.isnan(country_vals)]
    if vals.size == 0:
        return sub_mean
    x_bar = float(vals.mean())
    B = obs_var / (obs_var + sub_var) if (obs_var + sub_var) > 0 else 0.0
    return sub_mean + (1 - B) * (x_bar - sub_mean)


# --------------------------------------------------------------- 2. MICE core
def _ridge(X: np.ndarray, y: np.ndarray, lam: float = 1.0):
    """Ridge regression with intercept: beta = (X'X + lam I)^-1 X'y. Returns
    (intercept, coef, residual_sd). Retained for point-estimate use."""
    Xc = np.column_stack([np.ones(len(X)), X])
    p = Xc.shape[1]
    A = Xc.T @ Xc + lam * np.eye(p)
    A[0, 0] -= lam                                   # do not penalise the intercept
    beta = np.linalg.solve(A, Xc.T @ y)
    resid = y - Xc @ beta
    sd = float(np.sqrt(max(np.var(resid), 1e-9)))
    return beta[0], beta[1:], sd


def _bayes_linear_impute(Xtr: np.ndarray, ytr: np.ndarray, Xmis: np.ndarray,
                         lam: float, rng, inflate: float = 1.0) -> np.ndarray:
    """Proper Bayesian linear imputation (van Buuren, 2011, the 'norm' method).

    Draws the residual variance and the coefficients from their posteriors before
    predicting, so imputations carry BOTH parameter and residual uncertainty — the
    ingredient a point-estimate regression omits:
        beta_hat = (X'X + lam I)^-1 X'y ;  Ainv = (X'X + lam I)^-1
        sigma^2* = RSS / chi^2_{df}                     (posterior of variance)
        beta*    = beta_hat + chol(sigma^2* · Ainv) · z ,  z ~ N(0, I)
        y_mis    = X_mis · beta* + N(0, sigma^2*)
    """
    Xc = np.column_stack([np.ones(len(Xtr)), Xtr])
    p = Xc.shape[1]
    A = Xc.T @ Xc + lam * np.eye(p)
    A[0, 0] -= lam
    Ainv = np.linalg.inv(A)
    beta_hat = Ainv @ Xc.T @ ytr
    resid = ytr - Xc @ beta_hat
    dfree = max(len(ytr) - p, 1)
    rss = float(resid @ resid)
    sigma2 = rss / rng.chisquare(dfree) if dfree > 0 and rss > 0 else max(np.var(resid), 1e-6)
    sigma2 *= inflate ** 2
    cov = sigma2 * Ainv
    cov = (cov + cov.T) / 2 + 1e-9 * np.eye(p)       # symmetrise + jitter for stability
    try:
        L = np.linalg.cholesky(cov)
    except np.linalg.LinAlgError:
        L = np.diag(np.sqrt(np.clip(np.diag(cov), 0, None)))
    beta_star = beta_hat + L @ rng.standard_normal(p)
    Xm = np.column_stack([np.ones(len(Xmis)), Xmis])
    return Xm @ beta_star + rng.normal(0, np.sqrt(sigma2), len(Xmis))


def chained_equations(df: pd.DataFrame, value_cols: list[str], *, m: int = 5,
                      n_iter: int = 10, bounds: dict | None = None,
                      seed: int = 0, inflate: float = 1.0) -> list[pd.DataFrame]:
    """Multivariate Imputation by Chained Equations (van Buuren, 2011).

    Returns m completed copies of df. Standardises predictors, imputes each
    incomplete column from a Bayesian linear regression on the others (carrying
    parameter + residual uncertainty), cycling n_iter times per imputation.
    """
    bnd = _bounds(value_cols, bounds)
    X = df[value_cols].to_numpy(float)
    na = np.isnan(X)
    col_mean = np.nanmean(X, axis=0)
    col_mean = np.where(np.isnan(col_mean), 0.0, col_mean)
    col_sd = np.nanstd(X, axis=0)
    col_sd = np.where((col_sd == 0) | np.isnan(col_sd), 1.0, col_sd)

    completed = []
    for imp in range(m):
        rng = np.random.default_rng(seed + imp)
        Z = X.copy()
        for j in range(Z.shape[1]):          # mean-init missing cells
            Z[na[:, j], j] = col_mean[j]
        for _ in range(n_iter):
            for j in range(Z.shape[1]):
                miss = na[:, j]
                if not miss.any() or miss.all():
                    continue
                pred_cols = [k for k in range(Z.shape[1]) if k != j]
                Zs = (Z - col_mean) / col_sd            # standardise predictors
                draw = _bayes_linear_impute(Zs[~miss][:, pred_cols], Z[~miss, j],
                                            Zs[miss][:, pred_cols], lam=1.0,
                                            rng=rng, inflate=inflate)
                lo, hi = bnd[value_cols[j]]
                Z[miss, j] = np.clip(draw, lo, hi)
        out = df.copy()
        out[value_cols] = Z
        completed.append(out)
    return completed


# --------------------------------------------------------------- Rubin's rules
def rubin_pool(estimates: list[float], variances: list[float]) -> dict:
    """Pool m estimates and their within-imputation variances (Rubin, 1987)."""
    m = len(estimates)
    q = np.asarray(estimates, float)
    u = np.asarray(variances, float)
    qbar = float(q.mean())
    ubar = float(u.mean())
    b = float(q.var(ddof=1)) if m > 1 else 0.0
    t = ubar + (1 + 1 / m) * b
    lam = ((1 + 1 / m) * b / t) if t > 0 else 0.0       # fraction of missing information
    se = float(np.sqrt(t))
    return {"estimate": qbar, "within_var": ubar, "between_var": b,
            "total_var": t, "se": se, "fmi": lam,
            "ci95": (qbar - 1.96 * se, qbar + 1.96 * se)}


# --------------------------------------------------------------- orchestrator
@dataclass
class ImputationResult:
    completed: list[pd.DataFrame]           # m completed datasets (m>=1)
    imputed_mask: pd.DataFrame              # True where a value was imputed
    method: pd.DataFrame                    # per-cell method label
    report: MissingnessReport
    m: int = 1

    @property
    def data(self) -> pd.DataFrame:
        """Point-estimate completed dataset (mean across imputations)."""
        if self.m == 1:
            return self.completed[0]
        base = self.completed[0].copy()
        num = [c for c in base.columns if pd.api.types.is_numeric_dtype(base[c])]
        stack = np.stack([d[num].to_numpy(float) for d in self.completed])
        base[num] = stack.mean(axis=0)
        return base


def calibrate_inflation(df: pd.DataFrame, value_cols: list[str], *, target: float = 0.95,
                        grid=(1.0, 1.4, 1.8, 2.2, 2.6, 3.0), m: int = 10,
                        frac: float = 0.15, seed: int = 0, **kwargs) -> float:
    """Self-calibration: choose the smallest noise-inflation factor whose held-out
    95% interval coverage reaches `target`. Averages over a few hold-out replicates
    for stability. Returns the chosen factor (the largest grid value if none reach
    target)."""
    best, best_cov = grid[-1], -1.0
    for infl in grid:
        covs = [holdout_validation(df, value_cols, frac=frac, m=m, seed=seed + r,
                                   noise_inflation=infl, **kwargs)["coverage95"]
                for r in range(3)]
        cov = float(np.mean(covs))
        if cov >= target:
            return infl
        if cov > best_cov:
            best, best_cov = infl, cov
    return best


def impute_panel(df: pd.DataFrame, value_cols: list[str], *, m: int = 5,
                 group: str = "iso3", time: str = "year", subgroup: str = "subregion",
                 bounds: dict | None = None, n_iter: int = 10, seed: int = 0,
                 use_temporal: bool = True, noise_inflation=1.0) -> ImputationResult:
    """End-to-end imputation: temporal -> MICE -> hierarchical, flagged & bounded.

    Parameters
    ----------
    m : number of multiple imputations (m=1 -> single imputation).
    bounds : {col: (lo, hi)} plausibility limits; defaults to non-negative.
    noise_inflation : multiplier on all multiple-imputation noise, or the string
        "auto" to self-calibrate to ~95% held-out coverage on this dataset.
    """
    if noise_inflation == "auto":
        noise_inflation = calibrate_inflation(df, value_cols, m=m, bounds=bounds,
                                              group=group, time=time, subgroup=subgroup,
                                              n_iter=n_iter, seed=seed)
    bnd = _bounds(value_cols, bounds)
    report = missingness_report(df, value_cols)
    original_na = df[value_cols].isna()
    sigma = _column_noise(df, value_cols, group, time) if m > 1 else {c: 0.0 for c in value_cols}
    sigma = {c: s * noise_inflation for c, s in sigma.items()}

    completed, stage_na = [], None
    for l in range(max(1, m)):
        rng = np.random.default_rng(seed + l)
        w = temporal_interpolate(df, value_cols, group=group, time=time) if (
            use_temporal and time in df.columns and group in df.columns) else df.copy()
        na_after_temporal = w[value_cols].isna()
        temporal_cells = original_na.values & ~na_after_temporal.values
        if m > 1:
            for j, cc in enumerate(value_cols):
                idx = np.where(temporal_cells[:, j])[0]
                if idx.size:
                    w.iloc[idx, w.columns.get_loc(cc)] += rng.normal(0, sigma[cc], idx.size)
        comp = chained_equations(w, value_cols, m=1, n_iter=n_iter, bounds=bnd,
                                 seed=seed + l, inflate=noise_inflation)[0]
        na_after_mice = comp[value_cols].isna()
        comp = hierarchical_fill(comp, value_cols, group=subgroup)
        if m > 1:
            hier_cells = na_after_mice.values
            for j, cc in enumerate(value_cols):
                idx = np.where(hier_cells[:, j])[0]
                if idx.size:
                    comp.iloc[idx, comp.columns.get_loc(cc)] += rng.normal(0, sigma[cc], idx.size)
        for cc in value_cols:
            comp[cc] = _apply_bounds(comp[cc], bnd[cc])
        completed.append(comp)
        if stage_na is None:
            stage_na = (na_after_temporal, na_after_mice)

    na_after_temporal, na_after_mice = stage_na
    method = pd.DataFrame("observed", index=df.index, columns=value_cols)
    method = method.mask(original_na.values & ~na_after_temporal.values, "temporal")
    method = method.mask(na_after_temporal.values & ~na_after_mice.values, "mice")
    method = method.mask(na_after_mice.values, "hierarchical")

    return ImputationResult(completed=completed, imputed_mask=original_na,
                            method=method, report=report, m=max(1, m))


# --------------------------------------------------------------- validation
def holdout_validation(df: pd.DataFrame, value_cols: list[str], *, frac: float = 0.1,
                       seed: int = 0, **kwargs) -> dict:
    """Mask a fraction of OBSERVED cells, impute, and score recovery (RMSE, MAE,
    bias, 95% interval coverage under multiple imputation)."""
    rng = np.random.default_rng(seed)
    truth = df[value_cols].to_numpy(float)
    observed = ~np.isnan(truth)
    idx = np.argwhere(observed)
    take = rng.choice(len(idx), size=max(1, int(frac * len(idx))), replace=False)
    holes = idx[take]

    masked = df.copy()
    arr = masked[value_cols].to_numpy(float).copy()
    for r, cc in holes:
        arr[r, cc] = np.nan
    masked[value_cols] = arr

    res = impute_panel(masked, value_cols, **kwargs)
    stack = np.stack([d[value_cols].to_numpy(float) for d in res.completed])
    pred_mean = stack.mean(axis=0)
    pred_lo = np.percentile(stack, 2.5, axis=0)
    pred_hi = np.percentile(stack, 97.5, axis=0)

    t = np.array([truth[r, cc] for r, cc in holes])
    p = np.array([pred_mean[r, cc] for r, cc in holes])
    lo = np.array([pred_lo[r, cc] for r, cc in holes])
    hi = np.array([pred_hi[r, cc] for r, cc in holes])
    err = p - t
    return {"n_held_out": len(holes), "rmse": float(np.sqrt(np.mean(err ** 2))),
            "mae": float(np.mean(np.abs(err))), "bias": float(np.mean(err)),
            "coverage95": float(np.mean((t >= lo) & (t <= hi)))}
