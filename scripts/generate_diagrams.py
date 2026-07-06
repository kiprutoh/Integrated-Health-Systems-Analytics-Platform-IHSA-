"""Generate diagrammatic illustrations of the IHSA modelling framework.

Outputs PNGs to docs/figures/ for embedding in the methodology document:
  fig_hierarchy.png       — the five-layer determinant DAG (general template)
  fig_hiv_dag.png         — the HIV domain Bayesian network (worked example)
  fig_method_selection.png— method chosen per domain (Bayesian vs alternatives)
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = Path(__file__).resolve().parent.parent / "docs" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

NAVY = "#0B132B"; TEAL = "#1C7C74"; RED = "#C0392B"; SLATE = "#334155"
AMBER = "#B7791F"; PURP = "#5B3A86"; LIGHT = "#EEF2F6"; INK = "#1A1A1A"


def _box(ax, x, y, w, h, text, fc, tc="white", fs=9, bold=True):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.06",
                                linewidth=1.1, edgecolor="white", facecolor=fc, zorder=2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", color=tc,
            fontsize=fs, fontweight="bold" if bold else "normal", zorder=3, wrap=True)


def _arrow(ax, p1, p2, color=SLATE, lw=1.3, style="-|>"):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle=style, mutation_scale=12,
                                 color=color, lw=lw, zorder=1,
                                 connectionstyle="arc3,rad=0.0"))


# ---------------------------------------------------------------- Fig 1: hierarchy
def fig_hierarchy():
    fig, ax = plt.subplots(figsize=(11, 5.2))
    ax.set_xlim(0, 11); ax.set_ylim(0, 5.4); ax.axis("off")
    layers = [("EXTERNAL\nSHOCKS", RED, ["Conflict", "Epidemic", "Floods / drought", "Displacement"]),
              ("SOCIO-\nECONOMIC", AMBER, ["Education", "Poverty", "Gender inequality", "Urbanisation"]),
              ("SYSTEM", PURP, ["Workforce", "Financing", "Supply chain", "HIS maturity"]),
              ("INTERMEDIATE", TEAL, ["Effective coverage of", "the interventions that", "act on the outcome"]),
              ("OUTCOME", NAVY, ["Incidence / mortality", "coverage index /", "P(SDG 3)"])]
    xw = 2.02; gap = 0.16; x = 0.15
    centers = []
    for title, color, members in layers:
        _box(ax, x, 3.9, xw, 0.9, title, color, fs=11)
        ax.add_patch(FancyBboxPatch((x, 0.5), xw, 3.1, boxstyle="round,pad=0.02,rounding_size=0.05",
                                    linewidth=1.0, edgecolor=color, facecolor=LIGHT, zorder=1))
        for i, m in enumerate(members):
            ax.text(x + xw / 2, 3.25 - i * 0.55, m, ha="center", va="center",
                    color=INK, fontsize=8.2, zorder=2)
        centers.append(x + xw)
        x += xw + gap
    for i in range(len(layers) - 1):
        _arrow(ax, (centers[i], 4.35), (centers[i] + gap, 4.35), color=SLATE, lw=1.6)
    ax.text(5.6, 0.12, "Information flows upward: each layer is a parent of the next; "
            "the joint factorises as  P(X) = \u220F\u2c7c p(X\u2c7c | parents(X\u2c7c))",
            ha="center", va="center", fontsize=8.6, style="italic", color=SLATE)
    ax.set_title("Figure 1.  The five-layer determinant hierarchy (general DAG template)",
                 fontsize=12, fontweight="bold", color=NAVY, loc="left")
    fig.tight_layout(); fig.savefig(OUT / "fig_hierarchy.png", dpi=170, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------- Fig 2: HIV DAG
def fig_hiv_dag():
    fig, ax = plt.subplots(figsize=(11, 5.6))
    ax.set_xlim(0, 11); ax.set_ylim(0, 5.8); ax.axis("off")
    nodes = {
        "conflict": (0.5, 4.7, "Conflict", RED), "his": (0.5, 3.1, "HIS\nmaturity", PURP),
        "literacy": (0.5, 1.4, "Female\nliteracy", AMBER),
        "supply": (3.0, 4.2, "Supply\nchain", PURP), "testing": (3.0, 2.4, "HIV\ntesting", PURP),
        "art": (5.5, 3.9, "ART\ncoverage", TEAL), "condom": (5.5, 1.2, "Condom\nuse", TEAL),
        "vls": (7.9, 3.0, "Viral\nsuppression", TEAL), "sti": (7.9, 1.2, "STI\nprevalence", AMBER),
        "inc": (9.9, 3.0, "HIV\nINCIDENCE", NAVY),
    }
    w, h = 1.15, 0.72
    for k, (x, y, t, c) in nodes.items():
        _box(ax, x, y, w, h, t, c, fs=8.4)
    def cen(k, side="r"):
        x, y, *_ = nodes[k]
        return (x + (w if side == "r" else 0 if side == "l" else w / 2),
                y + h / 2 if side in ("r", "l") else (y + h if side == "t" else y))
    edges = [("his", "supply"), ("his", "testing"), ("conflict", "supply"),
             ("testing", "art"), ("supply", "art"), ("art", "vls"), ("supply", "vls"),
             ("vls", "inc"), ("condom", "inc"), ("sti", "inc"), ("literacy", "inc")]
    for a, b in edges:
        _arrow(ax, cen(a, "r"), cen(b, "l"), color=SLATE, lw=1.2)
    ax.text(5.5, 0.2, "log E[incidence] = log(inc\u2070) \u2212 \u03b2\u2081(VLS\u2212VLS\u2070) \u2212 \u03b2\u2082(condom\u2212condom\u2070) "
            "+ \u03b2\u2083(STI\u2212STI\u2070) \u2212 \u03b2\u2084(literacy\u2212literacy\u2070)",
            ha="center", fontsize=8.2, style="italic", color=ACCENT if (ACCENT:="#1C2541") else NAVY)
    ax.set_title("Figure 2.  HIV domain network — the treatment cascade drives incidence",
                 fontsize=12, fontweight="bold", color=NAVY, loc="left")
    fig.tight_layout(); fig.savefig(OUT / "fig_hiv_dag.png", dpi=170, bbox_inches="tight")
    plt.close(fig)


# ------------------------------------------------------- Fig 3: method selection
def fig_method_selection():
    rows = [
        ("HIV, TB, malaria", "Bayesian network with cascade / force-of-infection structure",
         "Transmission via an infectious-pool proxy; cascade nodes; shocks", TEAL),
        ("Maternal mortality", "Additive monotonic (log-linear) model embedded as a network node",
         "Rare rate; risk-oriented predictors; three-delays", NAVY),
        ("Neonatal, child, under-5", "Cause-deletion (Lives Saved Tool) + survival decomposition",
         "Deaths averted by cause \u00d7 efficacy \u00d7 \u0394coverage; U5MR = NMR + PNMR", PURP),
        ("NCD (premature mortality)", "Comparative risk assessment (population attributable fraction)",
         "PAF from risk-factor prevalence and relative risks", AMBER),
        ("UHC", "Financing production function (concave) + financial-protection model",
         "Diminishing returns; coverage vs catastrophic expenditure", TEAL),
        ("SRHR", "Bayesian network + demand-satisfied impact chain",
         "Positive index; contraception \u2192 pregnancies/deaths averted", PURP),
        ("Routine HIS / maturity", "Composite maturity index (PRISM-aligned)",
         "Weighted mean of assessed domain scores; mined baselines", NAVY),
        ("SDG 3 attainment", "Target-gap trajectory + integrating logistic node",
         "Required vs achieved AARR; aggregates other outcomes", RED),
    ]
    fig, ax = plt.subplots(figsize=(11, 5.6))
    ax.set_xlim(0, 11); ax.set_ylim(0, len(rows) + 1.2); ax.axis("off")
    ax.text(0.1, len(rows) + 0.5, "Domain", fontsize=9.5, fontweight="bold", color="white")
    ax.text(2.5, len(rows) + 0.5, "Method selected", fontsize=9.5, fontweight="bold", color="white")
    ax.text(6.8, len(rows) + 0.5, "Why this method", fontsize=9.5, fontweight="bold", color="white")
    ax.add_patch(FancyBboxPatch((0, len(rows) + 0.25), 11, 0.55, boxstyle="square,pad=0",
                                facecolor=NAVY, edgecolor="none", zorder=1))
    for i, (dom, method, why, c) in enumerate(rows):
        y = len(rows) - 1 - i + 0.2
        ax.add_patch(FancyBboxPatch((0, y), 0.12, 0.8, boxstyle="square,pad=0", facecolor=c,
                                    edgecolor="none", zorder=2))
        ax.text(0.25, y + 0.4, dom, fontsize=8.3, va="center", color=INK, fontweight="bold")
        ax.text(2.5, y + 0.4, method, fontsize=8.0, va="center", color=INK)
        ax.text(6.8, y + 0.4, why, fontsize=7.6, va="center", color=SLATE)
        ax.axhline(y - 0.02, color="#E2E8F0", lw=0.6)
    ax.set_title("Figure 3.  Method selected by domain — Bayesian networks where appropriate, "
                 "purpose-built methods otherwise", fontsize=11.5, fontweight="bold", color=NAVY, loc="left")
    fig.tight_layout(); fig.savefig(OUT / "fig_method_selection.png", dpi=170, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    fig_hierarchy(); fig_hiv_dag(); fig_method_selection()
    for f in sorted(OUT.glob("*.png")):
        print("wrote", f.relative_to(OUT.parent.parent), f.stat().st_size, "bytes")


# ------------------------------------------------------- Fig 4: imputation flow
def fig_imputation():
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
    fig, ax = plt.subplots(figsize=(11, 6.0))
    ax.set_xlim(0, 11); ax.set_ylim(0, 6.2); ax.axis("off")

    def box(x, y, w, h, t, fc, fs=8.6, tc="white"):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.06",
                                    linewidth=1.1, edgecolor="white", facecolor=fc, zorder=2))
        ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", color=tc, fontsize=fs,
                fontweight="bold", zorder=3)

    def arr(p1, p2, color=SLATE, lw=1.4):
        ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=13, color=color, lw=lw, zorder=1))

    box(0.3, 4.9, 2.1, 0.9, "Incomplete\npanel D", NAVY)
    box(0.3, 3.2, 2.1, 0.9, "Missingness\ndiagnosis\n(MCAR/MAR/MNAR)", SLATE, fs=7.8)
    arr((1.35, 4.9), (1.35, 4.1))

    box(3.1, 4.9, 2.3, 0.9, "1  Temporal\ninterpolation\n(within country)", TEAL, fs=7.9)
    box(3.1, 3.4, 2.3, 0.9, "2  MICE\n(Bayesian, across\nindicators)", "#5B3A86", fs=7.9)
    box(3.1, 1.9, 2.3, 0.9, "3  Hierarchical\nshrinkage\n(subregion)", AMBER, fs=7.9)
    arr((2.4, 5.35), (3.1, 5.35)); arr((4.25, 4.9), (4.25, 4.3)); arr((4.25, 3.4), (4.25, 2.8))

    box(6.1, 3.4, 2.3, 2.4, "Constrain to\nbounds  +\nflag provenance\n\n(repeat m times\nwith independent\nnoise)", RED, fs=8.0)
    arr((5.4, 5.35), (6.1, 4.7)); arr((5.4, 3.85), (6.1, 4.3)); arr((5.4, 2.35), (6.1, 3.9))

    box(9.0, 4.4, 1.8, 1.4, "m completed\ndatasets", NAVY, fs=8.2)
    box(9.0, 2.5, 1.8, 1.4, "Rubin's rules\npooling\nT = Ū + (1+1/m)B", TEAL, fs=7.6)
    arr((8.4, 4.9), (9.0, 5.1)); arr((9.9, 4.4), (9.9, 3.9))

    box(6.1, 0.5, 4.7, 1.0, "Held-out validation → auto-calibrate interval width to nominal coverage",
        "#334155", fs=8.2)
    arr((9.9, 2.5), (8.45, 1.5), color=AMBER); arr((6.1, 1.0), (4.25, 1.9), color=AMBER, lw=1.1)

    ax.set_title("Figure 4.  The IHSA missing-data imputation framework",
                 fontsize=12.5, fontweight="bold", color=NAVY, loc="left")
    fig.tight_layout(); fig.savefig(OUT / "fig_imputation.png", dpi=170, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    fig_imputation()
