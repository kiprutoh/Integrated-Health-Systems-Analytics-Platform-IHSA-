"""
Predictor screening by one-at-a-time (OAT) sensitivity analysis.

For every registered model and every predictor, we hold all other predictors at the
country baseline and swing the predictor across its full plausible range [min, max],
recording the resulting change in the primary outcome. The normalised effect

    effect(p) = | f(x with p=max) - f(x with p=min) |  /  | f(x_baseline) |

is the fraction by which the outcome moves when the predictor is driven from one end
of its range to the other. A predictor is EFFECTIVE if effect(p) exceeds a small
threshold (default 1e-3, i.e. it moves the outcome by at least 0.1%) and INERT
otherwise. Bayesian outcomes are evaluated with a fixed Monte-Carlo seed so the two
end-point evaluations share the same random draws and the delta is free of sampling
noise. Inert predictors are candidates for removal from the final variable set.

Output: docs/predictor_screening.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from scenario_engine import load_builtin_models, list_models, get_model  # noqa: E402
from scenario_engine.base import State  # noqa: E402

THRESHOLD = 1e-3          # minimum relative outcome swing to count as "has an effect"


def screen_model(m) -> list[dict]:
    country = m.countries()[0]
    base = m.baseline(country)
    po = m.primary_outcome
    o_base = m.simulate(base).metrics[po]
    rows = []
    for lev in m.levers:
        v_lo = dict(base.values); v_lo[lev.key] = lev.min
        v_hi = dict(base.values); v_hi[lev.key] = lev.max
        o_lo = m.simulate(State(country, base.year, v_lo)).metrics[po]
        o_hi = m.simulate(State(country, base.year, v_hi)).metrics[po]
        effect = abs(o_hi - o_lo) / abs(o_base) if o_base else 0.0
        rows.append({"domain": m.domain, "predictor": lev.key, "label": lev.label,
                     "outcome_at_min": round(o_lo, 5), "outcome_at_max": round(o_hi, 5),
                     "baseline": round(o_base, 5), "effect": round(effect, 6),
                     "status": "effective" if effect > THRESHOLD else "inert"})
    return rows


def main() -> None:
    load_builtin_models()
    rows = []
    for dom in list_models():
        rows.extend(screen_model(get_model(dom)))
    df = pd.DataFrame(rows).sort_values(["domain", "effect"], ascending=[True, False])
    out = ROOT / "docs" / "predictor_screening.csv"
    df.to_csv(out, index=False)

    print(f"Screened {len(df)} predictors across {df['domain'].nunique()} domains "
          f"(threshold effect > {THRESHOLD:g}).\n")
    summ = df.groupby("domain")["status"].value_counts().unstack(fill_value=0)
    summ["total"] = summ.sum(axis=1)
    for dom, r in summ.iterrows():
        inert = r.get("inert", 0)
        note = "" if inert == 0 else f"   INERT: {inert}"
        print(f"  {dom:10s} effective={r.get('effective',0):3d}  inert={inert:3d}{note}")
    print(f"\nTotal inert (no effect): {(df['status']=='inert').sum()}")
    inert = df[df.status == "inert"]
    if len(inert):
        print("\nInert predictors (to drop):")
        for _, r in inert.iterrows():
            print(f"  {r['domain']:10s} {r['predictor']:24s} effect={r['effect']:.2e}")
    print(f"\nwrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
