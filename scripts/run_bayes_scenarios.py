"""Run the full Bayesian scenario library across all domain networks.

Prints each domain's baseline posterior-predictive outcome (with 95% credible
interval) and the effect of every scenario package. Demonstrates the reworked
framework end-to-end. Usage: python scripts/run_bayes_scenarios.py [--country X]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scenario_engine.bayes_engine import scenario_effect  # noqa: E402
from scenario_engine import bayes_networks as BN  # noqa: E402

# labels and direction come straight from the network metadata (stays in sync)
LABEL = {d: f"{lbl} ({unit})" for d, (lbl, unit, _b) in BN.OUTCOME_META.items()}
BETTER_UP = {d for d, (_l, _u, b) in BN.OUTCOME_META.items() if b == "up"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="Kenya")
    ap.add_argument("--n", type=int, default=6000)
    args = ap.parse_args()

    for dom, build in BN.BUILDERS.items():
        net = build(args.country) if dom == "rhis" else build()
        oc = BN.OUTCOME[dom]
        base = net.summarise(oc, net.sample(args.n))
        arrow = "higher = better" if dom in BETTER_UP else "lower = better"
        print(f"\n=== {dom.upper()} — {LABEL[dom]}  ({arrow}) ===")
        print(f"  baseline: {base['mean']:.2f}  [95% CrI {base['ci_low']:.2f}–{base['ci_high']:.2f}]")
        for name, pkg in BN.SCENARIO_LIBRARY[dom].items():
            r = scenario_effect(net, oc, pkg, n=args.n)
            print(f"    · {name:32s} {r['baseline_mean']:.2f} -> {r['mean']:.2f}  "
                  f"({r['rel_change_pct']:+.0f}%)  CrI[{r['ci_low']:.2f}–{r['ci_high']:.2f}]")


if __name__ == "__main__":
    main()
