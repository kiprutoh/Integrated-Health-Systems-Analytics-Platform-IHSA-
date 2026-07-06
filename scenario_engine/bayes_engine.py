"""
Bayesian Health Systems Scenario Engine (reworked framework).

Each health outcome is a node in a directed acyclic graph (DAG) over layered
determinants:

    external shocks -> socioeconomic -> system -> intermediate -> outcome

The joint factorises as  P(X) = prod_j P(X_j | parents(X_j)).  Each node is a
generalised structural equation

    eta_j = beta_j0 + sum_{k in pa(j)} beta_jk * s_jk * (X_k - x_k^0)
    X_j   = link^{-1}( eta_j^0 + eta_j ) + noise

with s_jk in {-1,+1} the evidence-implied sign (from the predictor polarity),
and eta_j^0 the anchor (log/logit of the observed baseline) so that a do-nothing
scenario reproduces the observed outcome exactly.

Interventions are Pearl's do-operator: do(X_S = x_S) overrides nodes in S and the
effect propagates to descendants. Uncertainty is propagated by Monte Carlo:
coefficients are drawn from their (sign-constrained) posterior/prior each sample,
node noise is added, and the outcome's posterior predictive distribution is
summarised (mean, 95% credible interval, and P(outcome meets a target)).

Pure-numpy forward Bayesian simulation (posterior-predictive style). Full posterior
inference over coefficients uses NUTS/PyMC when country-year data are available;
this engine consumes those posteriors (or elicited priors) and does the propagation.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

LINKS = {
    "identity": (lambda x: x, lambda e: e),
    "log": (np.log, np.exp),                                  # rates: MMR, incidence
    "logit": (lambda p: np.log(p / (1 - p)),
              lambda e: 1 / (1 + np.exp(-e))),                # probabilities
}


@dataclass
class Edge:
    parent: str
    coef_mean: float          # magnitude on the linear-predictor (log/logit) scale
    coef_sd: float            # posterior/prior sd -> parameter uncertainty
    sign: float = -1.0        # -1 protective, +1 risk
    ref: float = 0.0          # parent baseline (centring)
    scale: float = 1.0        # divide (parent-ref) by this (units)


@dataclass
class Node:
    name: str
    layer: str
    kind: str                 # 'continuous' | 'rate' | 'prob'
    baseline: float
    link: str = "identity"
    noise_sd: float = 0.0
    parents: list[Edge] = field(default_factory=list)
    lo: float = -np.inf
    hi: float = np.inf


class BayesianNetwork:
    def __init__(self, name: str):
        self.name = name
        self.nodes: dict[str, Node] = {}

    def add(self, node: Node) -> "BayesianNetwork":
        self.nodes[node.name] = node
        return self

    def _order(self) -> list[str]:
        seen, order = set(), []

        def visit(n):
            if n in seen:
                return
            for e in self.nodes[n].parents:
                if e.parent in self.nodes:
                    visit(e.parent)
            seen.add(n)
            order.append(n)

        for n in self.nodes:
            visit(n)
        return order

    def sample(self, n: int = 4000, interventions: dict | None = None,
               param_uncertainty: bool = True, seed: int = 7) -> dict:
        rng = np.random.default_rng(seed)
        do = interventions or {}
        # -----------------------------------------------------------------
        # ANCESTRAL SAMPLING of the posterior predictive p(X | do(x_S), theta).
        # Because the graph is a DAG, we visit nodes in topological order so
        # every parent is already sampled before its child. For draw vector of
        # size n we build each node's LINEAR PREDICTOR eta_j and map it through
        # the inverse link g_j^{-1} (identity | exp | logistic).
        # -----------------------------------------------------------------
        vals: dict[str, np.ndarray] = {}
        for name in self._order():
            node = self.nodes[name]
            # do-intervention: fix X_j = x_j and DELETE its incoming edges
            #   p(X | do(X_S=x_S)) = prod_{j not in S} p(X_j | pa(j))     [Pearl, 2009]
            if name in do:
                vals[name] = np.full(n, float(do[name]))
                continue
            f, finv = LINKS[node.link]           # f = g_j (link), finv = g_j^{-1}
            # ANCHOR the intercept at the observed baseline on the link scale:
            #   eta_j^0 = g_j(x_j^0)   so that, with all parents at their refs,
            #   E[X_j] = g_j^{-1}(eta_j^0) = x_j^0  (do-nothing reproduces reality)
            eta = np.full(n, f(max(node.baseline, 1e-6)) if node.link != "identity" else node.baseline)
            # Add each parent's sign-constrained, centred, unit-scaled contribution:
            #   eta_j += s_jk * beta_jk * (X_k - x_k^0) / kappa_jk ,  beta_jk >= 0
            for e in node.parents:
                if e.parent not in vals:
                    continue
                coef = e.coef_mean                      # posterior/elicited mean of beta_jk
                if param_uncertainty and e.coef_sd > 0:
                    # EPISTEMIC uncertainty: draw beta_jk from its posterior; abs()
                    # enforces the Half-Normal (non-negative) magnitude, direction is s_jk
                    coef = np.abs(rng.normal(e.coef_mean, e.coef_sd, n))
                eta = eta + e.sign * coef * ((vals[e.parent] - e.ref) / e.scale)
            x = finv(eta)                                # E[X_j] = g_j^{-1}(eta_j)
            # ALEATORIC (node) noise: multiplicative log-normal for rates,
            # additive normal otherwise.  epsilon ~ N(0, sigma_j^2)
            if node.noise_sd > 0:
                x = x * np.exp(rng.normal(0, node.noise_sd, n)) if node.link == "log" \
                    else x + rng.normal(0, node.noise_sd, n)
            vals[name] = np.clip(x, node.lo, node.hi)    # respect natural support
        return vals

    def summarise(self, outcome: str, samples: dict, target: float | None = None,
                  target_dir: str = "below") -> dict:
        # Monte-Carlo estimate of the posterior predictive p(y | do(x_S), D):
        #   mean  ~ E[Y] = (1/N) sum_n y^(n)
        #   95% credible interval = (2.5th, 97.5th) sample percentiles
        #   P(target) = E[1(Y <= y*)] ~ (1/N) sum_n 1(y^(n) <= y*)
        x = samples[outcome]
        out = {"mean": float(np.mean(x)), "median": float(np.median(x)),
               "ci_low": float(np.percentile(x, 2.5)), "ci_high": float(np.percentile(x, 97.5))}
        if target is not None:
            out["p_target"] = float(np.mean(x <= target) if target_dir == "below"
                                    else np.mean(x >= target))
            out["target"] = target
        return out


def scenario_effect(net: BayesianNetwork, outcome: str, interventions: dict,
                    target: float | None = None, n: int = 4000) -> dict:
    """Baseline vs scenario posterior predictive, with intervention effect."""
    base = net.summarise(outcome, net.sample(n))
    scen = net.summarise(outcome, net.sample(n, interventions=interventions), target=target)
    scen["baseline_mean"] = base["mean"]
    scen["rel_change_pct"] = (scen["mean"] - base["mean"]) / base["mean"] * 100 if base["mean"] else 0.0
    return scen
