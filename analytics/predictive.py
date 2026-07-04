"""
Robust statistical predictive model (generalised from the deployed maternal model).

An additive, monotone-constrained linear model on log(outcome) with risk-oriented
predictors and a bootstrap ensemble for uncertainty. Design goals:

  * every predictor enters with the evidence-implied sign (no sign flipping);
  * robust to multicollinearity among development indicators (univariate-style
    non-negative coefficients on risk-oriented, standardised features);
  * calibrated uncertainty via bootstrap resampling (prediction intervals);
  * scenario predictions anchored to the observed value through a log-gain factor.

This is the reusable engine any domain can train from its panel. It has no hard
dependency on scikit-learn (uses a closed-form non-negative least-squares-style
fit with numpy), so it runs in minimal environments.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class PredictiveModel:
    feature_cols: list[str]
    risk_sign: dict[str, float]           # +1 risk factor, -1 protective
    coef: np.ndarray = field(default=None)
    intercept: float = 0.0
    mean: np.ndarray = field(default=None)
    scale: np.ndarray = field(default=None)
    boot_coef: np.ndarray = field(default=None)
    boot_intercept: np.ndarray = field(default=None)
    log_gain: float = 1.0

    # ---- fit ----
    def _design(self, X: np.ndarray) -> np.ndarray:
        signs = np.array([self.risk_sign.get(c, 1.0) for c in self.feature_cols])
        Xr = X * signs
        return (Xr - self.mean) / self.scale

    @staticmethod
    def _nnls_ridge(Z: np.ndarray, y: np.ndarray, lam: float = 1.0,
                    iters: int = 500) -> np.ndarray:
        """Non-negative ridge via projected gradient (keeps coefficients >= 0)."""
        n, p = Z.shape
        w = np.zeros(p)
        lr = 1.0 / (np.linalg.norm(Z, 2) ** 2 + lam + 1e-9)
        for _ in range(iters):
            grad = Z.T @ (Z @ w - y) + lam * w
            w = np.maximum(0.0, w - lr * grad)
        return w

    def fit(self, X: np.ndarray, y: np.ndarray, n_boot: int = 120,
            lam: float = 1.0, seed: int = 42) -> "PredictiveModel":
        signs = np.array([self.risk_sign.get(c, 1.0) for c in self.feature_cols])
        Xr = X * signs
        self.mean = Xr.mean(axis=0)
        self.scale = Xr.std(axis=0) + 1e-9
        Z = (Xr - self.mean) / self.scale
        ylog = np.log(np.maximum(y, 1e-6))
        self.intercept = float(ylog.mean())
        self.coef = self._nnls_ridge(Z, ylog - self.intercept, lam=lam)

        rng = np.random.default_rng(seed)
        bc, bi = [], []
        n = len(y)
        for _ in range(n_boot):
            idx = rng.integers(0, n, n)
            Zi, yi = Z[idx], ylog[idx]
            inter = float(yi.mean())
            bc.append(self._nnls_ridge(Zi, yi - inter, lam=lam))
            bi.append(inter)
        self.boot_coef = np.array(bc)
        self.boot_intercept = np.array(bi)
        return self

    # ---- predict ----
    def _logmu(self, x_row: dict) -> float:
        X = np.array([[float(x_row[c]) for c in self.feature_cols]])
        Z = self._design(X)[0]
        return float(Z @ self.coef + self.intercept)

    def predict(self, x_row: dict, anchor: dict | None = None,
                anchor_value: float | None = None) -> float:
        logmu = self._logmu(x_row)
        if anchor is not None and anchor_value is not None:
            log_ref = self._logmu(anchor)
            logmu = np.log(max(anchor_value, 1e-6)) + self.log_gain * (logmu - log_ref)
        return float(np.exp(logmu))

    def predict_interval(self, x_row: dict, anchor: dict | None = None,
                         anchor_value: float | None = None,
                         q=(2.5, 97.5)) -> tuple[float, float, float]:
        X = np.array([[float(x_row[c]) for c in self.feature_cols]])
        Z = self._design(X)[0]
        samples = self.boot_coef @ Z + self.boot_intercept
        if anchor is not None and anchor_value is not None:
            Xa = np.array([[float(anchor[c]) for c in self.feature_cols]])
            Za = self._design(Xa)[0]
            ref = self.boot_coef @ Za + self.boot_intercept
            samples = np.log(max(anchor_value, 1e-6)) + self.log_gain * (samples - ref)
        vals = np.exp(samples)
        return (float(np.percentile(vals, q[0])),
                float(np.median(vals)),
                float(np.percentile(vals, q[1])))
