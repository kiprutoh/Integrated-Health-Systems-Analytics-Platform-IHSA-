"""Illustrative child-survival panel for AFRO countries (offline demo data).

Columns: neonatal mortality rate (NMR), under-five mortality rate (U5MR) and the
intervention coverages used by the cause-deletion (LiST-style) child-survival
models. Replace with UN IGME / UNICEF SDMX / World Bank via the mining pipeline.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from warehouse import reference  # noqa: E402

RNG = np.random.default_rng(2027)
OUT = ROOT / "data" / "processed" / "child_survival"

# burden seed by subregion (illustrative U5MR/NMR anchors, 2023-ish)
TIER = {
    "Western Africa": (95, 32), "Central Africa": (90, 30),
    "Eastern Africa": (55, 24), "Southern Africa": (48, 20),
    "Northern Africa": (22, 14),
}


def _clip(x, lo, hi):
    return float(np.clip(x, lo, hi))


def build() -> pd.DataFrame:
    df = reference.countries()
    rows = []
    for _, r in df.iterrows():
        u5_anchor, nmr_anchor = TIER.get(r["subregion"], (70, 26))
        u5 = _clip(u5_anchor * RNG.normal(1, 0.18), 12, 150)
        nmr = _clip(min(nmr_anchor * RNG.normal(1, 0.15), u5 * 0.7), 6, 60)
        # coverages (%) — better where mortality is lower
        scale = np.interp(u5, [12, 150], [1.0, 0.0])
        def cov(base):
            return _clip(base * (0.55 + 0.45 * scale) * RNG.normal(1, 0.06), 5, 98)
        rows.append(dict(
            country=r["country"], iso3=r["iso3"], year=2023,
            nmr=round(nmr, 1), u5mr=round(u5, 1),
            sba=round(cov(90), 1), pnc=round(cov(75), 1),
            dtp3=round(cov(88), 1), measles=round(cov(85), 1),
            pcv=round(cov(80), 1), rota=round(cov(75), 1),
            itn_use=round(cov(65), 1), ors_zinc=round(cov(55), 1),
            careseeking_pneumonia=round(cov(60), 1),
            exclusive_bf=round(cov(50), 1), vitamin_a=round(cov(70), 1),
            neonatal_resuscitation=round(cov(55), 1),
            kangaroo_mother_care=round(cov(35), 1),
            neonatal_sepsis_mgmt=round(cov(45), 1),
        ))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    out = build()
    out.to_csv(OUT / "afro_child_survival_panel.csv", index=False)
    print(f"wrote {len(out)} rows -> {OUT/'afro_child_survival_panel.csv'}")
    print(out[["country", "nmr", "u5mr", "dtp3", "itn_use"]].head(6).to_string(index=False))
