"""
IHSA Streamlit shell — UI/UX modelled closely on the WHO AFRO maternal explorer
(https://what-if-analysis-afro.streamlit.app/).

Home: chip + gradient hero with 2x2 metric cards, dual CTAs, three feature cards
with mini bar-charts, four numbered steps, and a gradient CTA banner.
What-if workspace: radio nav, a dark two-pane layout with a status-quo baseline
box, a cyan target (work-backwards) panel, grouped forward levers with colour-coded
dots, a status banner, headline metrics with a 95% interval, a baseline-vs-scenario
bar chart, an input-changes table, and a trajectory-to-2030 chart.

Registry-driven: every registered domain is available; the maternal styling is the
template applied to all of them.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st

from config.settings import settings
from scenario_engine import ScenarioEngine, get_model, list_models, load_builtin_models
from scenario_engine.inverse import solve_for_target
from warehouse import reference

try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except Exception:  # pragma: no cover
    HAS_PLOTLY = False

load_builtin_models()

# ------------------------------------------------------------------ metadata
DOMAIN_ICON = {"hiv": "🧬", "maternal": "🤰", "neonatal": "👶", "child": "🧒",
               "under5": "🩺", "tb": "🫁", "malaria": "🦟", "uhc": "🏥",
               "ncd": "❤️", "srhr": "🌸", "rhis": "🗂", "sdg3": "🎯"}
ICON_GRAD = {"hiv": "#ef4444,#ec4899", "maternal": "#f97316,#f59e0b",
             "neonatal": "#38bdf8,#0ea5e9", "child": "#34d399,#14b8a6",
             "under5": "#a78bfa,#8b5cf6", "tb": "#f43f5e,#fb7185", "malaria": "#10b981,#34d399",
             "ncd": "#e11d48,#f43f5e", "srhr": "#d946ef,#ec4899", "rhis": "#0ea5e9,#38bdf8",
             "sdg3": "#eab308,#f59e0b", "uhc": "#0ea5e9,#22d3ee"}
OUTCOME_BETTER = {"srhr": "up", "rhis": "up", "sdg3": "up", "uhc": "up"}  # higher is better
# optional grouping of levers into layers (falls back to one group)
LEVER_GROUPS = {
    "neonatal": {"sba": "Health system", "neonatal_resuscitation": "Health system",
                 "neonatal_sepsis_mgmt": "Health system", "pnc": "Health system",
                 "kangaroo_mother_care": "Newborn care"},
}

RED_GRAD = "linear-gradient(90deg,#f87171,#fb923c)"


# ------------------------------------------------------------------ styling
def inject_css():
    st.markdown("""
    <style>
      .block-container { padding-top: 1rem; max-width: 1240px; }
      div[data-testid="stAppViewContainer"] { background: #020617; }
      section[data-testid="stSidebar"] { background: #0b1220; border-right: 1px solid #1e293b; }
      section[data-testid="stSidebar"] * { color: #e2e8f0; }
      h1,h2,h3,h4,p,span,label,div { color: #e2e8f0; }

      .hero { position:relative; overflow:hidden; border-radius:22px;
        background:linear-gradient(120deg,#0b132b 0%,#111a33 55%,#20304f 100%);
        border:1px solid #2a3752; padding:1.8rem 2rem; box-shadow:0 24px 55px rgba(0,0,0,.45); }
      .chip { display:inline-flex; gap:8px; align-items:center; padding:6px 14px; border-radius:999px;
        background:rgba(190,60,60,.14); border:1px solid rgba(248,113,113,.4); color:#fca5a5;
        font-size:.78rem; font-weight:600; letter-spacing:.03em; margin-bottom:.9rem; }
      .hero h1 { font-size:2.5rem; line-height:1.06; font-weight:800; margin:.1rem 0; color:#f8fafc; }
      .grad { background:%GRAD%; -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
      .hero p.lead { color:#cbd5e1; font-size:.96rem; line-height:1.55; max-width:34rem; margin-top:.5rem; }

      .metric { border-radius:14px; background:rgba(255,255,255,.045); border:1px solid rgba(255,255,255,.09);
        padding:.75rem .85rem; height:100%; }
      .metric .l { font-size:.66rem; color:#94a3b8; text-transform:uppercase; letter-spacing:.04em; }
      .metric .v { font-size:1.5rem; font-weight:800; color:#f8fafc; line-height:1.15; margin:.1rem 0; }
      .metric .u { font-size:.64rem; color:#8ea0b5; }
      .metric .f { font-size:.66rem; margin-top:.25rem; font-weight:600; }
      .good { color:#4ade80; } .warn { color:#fbbf24; }

      .feature { border-radius:18px; background:#0c1526; border:1px solid #1c2942; padding:1.1rem 1.2rem;
        height:100%; box-shadow:0 14px 30px rgba(0,0,0,.3); }
      .feature .tile { width:46px; height:46px; border-radius:12px; display:flex; align-items:center;
        justify-content:center; font-size:1.35rem; margin-bottom:.7rem; }
      .feature .k { font-size:.62rem; letter-spacing:.12em; text-transform:uppercase; color:#64748b; }
      .feature .t { font-size:1.05rem; font-weight:700; color:#f1f5f9; margin:.15rem 0 .4rem; }
      .feature .d { color:#94a3b8; font-size:.82rem; line-height:1.45; min-height:3.2rem; }
      .bars { display:flex; align-items:flex-end; gap:6px; height:54px; margin:.6rem 0 .3rem; }
      .bars i { flex:1; border-radius:4px 4px 0 0; display:block; }
      .bcap { display:flex; justify-content:space-between; font-size:.6rem; color:#64748b; }
      .bestfor { font-size:.72rem; color:#94a3b8; margin-top:.5rem; }

      .step { border-radius:16px; background:#0c1526; border:1px solid #1c2942; padding:1rem 1.1rem;
        position:relative; overflow:hidden; height:100%; }
      .step .ghost { position:absolute; right:.5rem; top:-.4rem; font-size:3.2rem; font-weight:800; color:#141f36; }
      .step .num { width:26px; height:26px; border-radius:8px; background:#e05a4d; color:#fff; font-weight:700;
        display:flex; align-items:center; justify-content:center; font-size:.8rem; margin-bottom:.5rem; }
      .step .t { font-weight:700; color:#f1f5f9; font-size:.92rem; } .step .d { color:#94a3b8; font-size:.78rem; margin-top:.2rem; }

      .cta { border-radius:20px; background:linear-gradient(100deg,#e05a4d,#e8823f); padding:1.6rem 2rem; text-align:center;
        box-shadow:0 20px 45px rgba(224,90,77,.3); }
      .cta h2 { color:#fff; font-weight:800; margin:0; } .cta p { color:#ffe9e0; margin:.4rem auto 0; max-width:40rem; font-size:.9rem; }

      .pane { background:linear-gradient(165deg,#0f172a,#1b2740 55%,#0f172a); border-radius:18px;
        border:1px solid rgba(148,163,184,.2); padding:1.1rem 1.2rem; }
      .pane .pt1 { font-size:1.35rem; font-weight:800; color:#f8fafc; line-height:1.1; }
      .pane .pt2 { font-size:1.35rem; font-weight:800; line-height:1.1; background:%GRAD%;
        -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
      .pane .psub { color:#94a3b8; font-size:.82rem; margin:.3rem 0 .6rem; }
      .sqbox { background:#0c1526; border:1px solid #1c2942; border-radius:12px; padding:.8rem .9rem; margin:.3rem 0; }
      .sqbox .h { font-weight:700; color:#e2e8f0; font-size:.9rem; }
      .sqbox .s { color:#93a4bb; font-size:.78rem; margin:.15rem 0 .4rem; }
      .sqline { color:#f1f5f9; font-weight:700; font-size:.82rem; }
      .target { background:#0a1a24; border:1px solid #1f5c73; border-radius:12px; padding:.7rem .9rem; margin:.5rem 0; }
      .target .h { color:#67e8f9; font-weight:700; font-size:.9rem; }
      .legend { color:#94a3b8; font-size:.74rem; margin:.3rem 0; }
      .banner-ok { background:rgba(22,101,52,.28); border:1px solid #16a34a; color:#bbf7d0; border-radius:10px;
        padding:.55rem .8rem; font-size:.82rem; font-weight:600; }
      .banner-act { background:rgba(120,53,15,.3); border:1px solid #d97706; color:#fed7aa; border-radius:10px;
        padding:.55rem .8rem; font-size:.82rem; font-weight:600; }
      .dot { display:inline-block; width:9px; height:9px; border-radius:50%; margin-right:6px; }
    </style>
    """.replace("%GRAD%", RED_GRAD), unsafe_allow_html=True)


# ------------------------------------------------------------------ helpers
def regional_summary(model):
    po = model.primary_outcome
    vals = []
    for cty in model.countries():
        try:
            vals.append(model.simulate(model.baseline(cty)).metrics[po])
        except Exception:
            pass
    return pd.Series(vals).median() if vals else float("nan")


def outcome_meta(model):
    po = model.primary_outcome
    o = next((o for o in model.outcomes if o.key == po), None)
    return po, (o.label if o else po), (o.unit if o else "")


def uncertainty_band(value, rel_sigma=0.06):
    lo = value * (1 - 1.96 * rel_sigma)
    hi = value * (1 + 1.96 * rel_sigma)
    return max(0, lo), hi


def bars_html(values, colors):
    m = max(values) or 1
    cells = "".join(
        f'<i style="height:{int(18 + 34 * v / m)}px;background:{c};"></i>'
        for v, c in zip(values, colors))
    return f'<div class="bars">{cells}</div>'


# ------------------------------------------------------------------ pages
def _regional_median(model):
    """Regional median of a domain's primary outcome (fast: reads panel where possible)."""
    dom = model.domain
    # bayesian domains: read the outcome column straight from the baseline panel
    try:
        from analytics.bayesian.model import _panel
        import scenario_engine.bayes_networks as _BN
        if dom in _BN.OUTCOME:
            if dom == "rhis":
                df = pd.read_csv(ROOT / "data" / "processed" / "his" / "afro_his_maturity.csv")
                return float(df["his_maturity_index"].median())
            pnl = _panel(dom)
            if pnl is not None and _BN.OUTCOME[dom] in pnl:
                return float(pnl[_BN.OUTCOME[dom]].median())
    except Exception:
        pass
    vals = []
    for cty in model.countries():
        try:
            vals.append(model.simulate(model.baseline(cty)).metrics[model.primary_outcome])
        except Exception:
            pass
    return float(pd.Series(vals).median()) if vals else float("nan")


@st.cache_data(show_spinner=False)
def _regional_figures():
    figs = []
    for dom in list_models():
        m = get_model(dom)
        _po, lbl, unit = outcome_meta(m)
        figs.append((dom, m.title, lbl, unit, _regional_median(m),
                     OUTCOME_BETTER.get(dom, "down")))
    return figs


def page_home():
    st.markdown(
        '<div class="hero"><div class="chip">🌍 WHO AFRO Health Systems Intelligence Platform</div>'
        '<div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:1rem;align-items:flex-end;">'
        '<div><h1>Regional Health<br/><span class="grad">Scenario Intelligence</span></h1>'
        '<p class="lead">Key regional figures across the African Region, with Bayesian what-if and '
        'target-seeking scenarios for every health domain — one engine, shared determinants, '
        'uncertainty throughout.</p></div></div></div>', unsafe_allow_html=True)

    st.write("")
    st.markdown("#### 📊 Key regional figures")
    st.caption("Baseline regional medians across the 47 WHO AFRO member states (illustrative). "
               "Click any domain below to open its scenario workspace.")

    figs = _regional_figures()
    per_row = 4
    for i in range(0, len(figs), per_row):
        cols = st.columns(per_row)
        for col, (dom, title, lbl, unit, val, better) in zip(cols, figs[i:i + per_row]):
            grad = ICON_GRAD.get(dom, "#f87171,#fb923c")
            arrow = "▲ higher is better" if better == "up" else "▼ lower is better"
            acls = "good" if better == "up" else "warn"
            vtxt = f"{val:.2f}" if val < 5 else f"{val:.0f}"
            col.markdown(
                f'<div class="metric" style="border-left:3px solid transparent;'
                f'background:linear-gradient(#0c1526,#0c1526) padding-box,'
                f'linear-gradient(135deg,{grad}) border-box;border:1px solid transparent;">'
                f'<div class="l">{DOMAIN_ICON.get(dom,"📊")} {lbl}</div>'
                f'<div class="v">{vtxt}</div><div class="u">{unit}</div>'
                f'<div class="f {acls}">{arrow}</div></div>', unsafe_allow_html=True)

    st.write("")
    st.markdown("#### 🧭 Explore scenarios")
    st.caption("Each domain is a Bayesian network over layered determinants. Open one to run forward "
               "what-if and inverse target-seeking scenarios.")
    domains = list_models()
    for i in range(0, len(domains), 3):
        row = st.columns(3)
        for col, dom in zip(row, domains[i:i + 3]):
            m = get_model(dom); grad = ICON_GRAD.get(dom, "#1c7c74,#2dd4bf")
            _po, lbl, unit = outcome_meta(m)
            with col:
                st.markdown(
                    f'<div class="feature"><div class="tile" style="background:linear-gradient(135deg,{grad});">'
                    f'{DOMAIN_ICON.get(dom,"📊")}</div><div class="k">{len(m.levers)} LEVERS</div>'
                    f'<div class="t">{m.title}</div>'
                    f'<div class="d">Outcome: {lbl} ({unit}). Forward what-if + target-seeking, with '
                    f'uncertainty.</div></div>', unsafe_allow_html=True)
                if st.button(f"Open {m.title}", key=f"open_{dom}", use_container_width=True):
                    st.session_state["_domain"] = dom
                    st.session_state["_section"] = "🧪 What-if analysis"
                    st.rerun()

    st.write("")
    st.markdown('<div class="cta"><h2>Transform Health Planning with Data</h2>'
                '<p>Bayesian scenario modelling, regional insights and target-seeking analysis to support '
                'evidence-based health policy across the African Region.</p></div>', unsafe_allow_html=True)



def _grouped_levers(model):
    groups: dict[str, list] = {}
    gmap = LEVER_GROUPS.get(model.domain, {})
    for lv in model.levers:
        groups.setdefault(gmap.get(lv.key, "Scenario levers"), []).append(lv)
    return groups


def page_whatif():
    domains = list_models()
    st.markdown(f"## {get_model(st.session_state.get('_domain', domains[0])).title} — What-if Scenarios (WHO AFRO)")
    st.caption("Adjust levers to explore illustrative scenario shifts. Predictions start from the country's "
               "observed value; moving a lever changes the outcome in the direction implied by the slider.")

    tabs = ["Country scenario", "Preset comparisons", "Regional data", "Data & methods"]
    tab = st.radio("nav", tabs, horizontal=True, label_visibility="collapsed",
                   index=tabs.index(st.session_state.pop("_whatif_tab", "Country scenario")))

    d1, d2 = st.columns([1.4, 1])
    dsel = st.session_state.get("_domain", domains[0])
    dom = d1.selectbox("Domain", domains, index=domains.index(dsel) if dsel in domains else 0,
                       format_func=lambda x: get_model(x).title)
    st.session_state["_domain"] = dom
    model = get_model(dom)
    engine = ScenarioEngine(model=model)
    country = d2.selectbox("Country", model.countries())

    po, po_label, po_unit = outcome_meta(model)
    base = model.baseline(country)
    base_val = model.simulate(base).metrics[po]

    if tab == "Regional data":
        return _regional(model)
    if tab == "Data & methods":
        return _methods()

    left, right = st.columns([1, 1.18])

    # ---------------- LEFT PANE ----------------
    with left:
        summary_bits = " · ".join(
            [f"{country} · {base.year} · {po_label.split('(')[0].strip()} {base_val:.0f}"]
            + [f"{lv.label.split(' ')[0]} {base.values.get(lv.key, 0):.0f}{lv.unit}"
               for lv in model.levers[:3]])
        st.markdown(
            f'<div class="pane"><div class="pt1">{model.title.split("Explorer")[0].strip()}</div>'
            f'<div class="pt2">Scenario Explorer</div>'
            f'<div class="psub">Set a target to work backwards, or adjust levers forward from status quo.</div>',
            unsafe_allow_html=True)

        st.markdown(f'<div class="sqbox"><div class="h">Status quo baseline</div>'
                    f'<div class="s">Reset all levers to the country\'s current status quo.</div>'
                    f'<div class="sqline">{summary_bits}</div></div>', unsafe_allow_html=True)
        reset = st.button("Reset to status quo defaults", use_container_width=True, type="primary")
        st.checkbox("Status quo reviewed — proceed with scenarios", value=True)

        st.markdown('<div class="target"><div class="h">🎯 Target — work backwards</div></div>',
                    unsafe_allow_html=True)
        tgt = st.number_input(f"Target {po_label} ({po_unit})", value=float(round(base_val * 0.75, 1)),
                              min_value=0.0, step=1.0)
        protective_only = st.checkbox("Use priority (protective) levers only", value=True)
        tcol1, tcol2 = st.columns(2)
        do_calc = tcol1.button("Calculate required indicators", use_container_width=True)
        do_apply = tcol2.button("Apply to levers", use_container_width=True)

        st.markdown("**Forward scenario levers**")
        st.markdown('<div class="legend"><span class="dot" style="background:#22c55e;"></span>'
                    '+ lowers outcome &nbsp;·&nbsp; <span class="dot" style="background:#f59e0b;"></span>'
                    '+ raises outcome</div>', unsafe_allow_html=True)

        inv = None
        if do_calc or do_apply:
            keys = [l.key for l in model.levers if l.polarity <= 0] if protective_only else None
            inv = solve_for_target(model, country, tgt, keys)

        overrides = {}
        for gname, levers in _grouped_levers(model).items():
            with st.expander(gname, expanded=True):
                for lv in levers:
                    cur = float(base.values.get(lv.key, lv.min))
                    default = cur
                    if inv and do_apply and lv.key in inv.lever_settings:
                        default = float(inv.lever_settings[lv.key])
                    if reset:
                        default = cur
                    dot = "#22c55e" if lv.polarity <= 0 else "#f59e0b"
                    st.markdown(f'<span class="dot" style="background:{dot};"></span>'
                                f'<b>{lv.label}</b>', unsafe_allow_html=True)
                    overrides[lv.key] = st.slider(lv.label, float(lv.min), float(lv.max),
                                                  min(max(default, lv.min), lv.max), float(lv.step),
                                                  key=f"s_{dom}_{lv.key}", label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)

    result = engine.run(country, overrides)
    scen_val = result.scenario_outcome[po]

    # ---------------- RIGHT PANE ----------------
    with right:
        status_quo = abs(scen_val - base_val) < 1e-6
        if status_quo:
            st.markdown('<div class="banner-ok">Status quo active — all levers match latest observed data.</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="banner-act">Scenario active — {po_label} moves '
                        f'{(scen_val-base_val)/base_val*100:+.0f}% vs observed.</div>', unsafe_allow_html=True)
        if inv is not None:
            if inv.feasible:
                st.markdown(f'<div class="banner-ok">Target {tgt:.0f} reachable at ~{inv.effort_fraction*100:.0f}% '
                            f'of full protective-lever coverage. Click “Apply to levers”.</div>',
                            unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="banner-act">Target {tgt:.0f} not reachable with these levers alone — '
                            f'best achievable {inv.achieved:.0f}.</div>', unsafe_allow_html=True)

        m1, m2, m3 = st.columns(3)
        better = OUTCOME_BETTER.get(dom, "down")
        dcolor = "normal" if better == "up" else "inverse"
        m1.metric(f"Predicted {po_label.split('(')[0].strip()} (scenario)", f"{scen_val:.2f}" if scen_val < 5 else f"{scen_val:.0f}",
                  f"{(scen_val-base_val)/base_val*100:+.1f}%" if base_val else None, delta_color=dcolor)
        m2.metric("Observed (baseline)", f"{base_val:.0f}")
        m3.metric("Change", f"{scen_val-base_val:+.0f}")

        b_lo, b_hi = uncertainty_band(base_val)
        s_lo, s_hi = uncertainty_band(scen_val)
        st.caption(f"Uncertainty (95% interval) — baseline: {b_lo:.0f}–{b_hi:.0f}, "
                   f"scenario: {s_lo:.0f}–{s_hi:.0f}. At default lever settings, scenario equals observed.")

        if HAS_PLOTLY:
            fig = go.Figure()
            fig.add_bar(x=["Observed (baseline)"], y=[base_val], marker_color="#3b6fe0",
                        error_y=dict(type="data", array=[b_hi - base_val], visible=True))
            fig.add_bar(x=["Scenario"], y=[scen_val], marker_color="#22b07d",
                        error_y=dict(type="data", array=[s_hi - scen_val], visible=True))
            fig.update_layout(title=f"{country}: {po_label} comparison", height=340, showlegend=False,
                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              font_color="#cbd5e1", margin=dict(t=40, b=10, l=10, r=10))
            st.plotly_chart(fig, use_container_width=True)

    # input changes table (full width)
    st.markdown("#### Input changes")
    rows = []
    for lv in model.levers:
        b = base.values.get(lv.key, 0.0)
        s = overrides.get(lv.key, b)
        arrow = "outcome ↓" if lv.polarity <= 0 else "outcome ↑"
        rows.append({"Indicator": lv.label, "Baseline": round(b, 2), "Scenario": round(s, 2),
                     "If you increase this lever": arrow, "Change": round(s - b, 2)})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # trajectory to 2030
    if result.forecast and HAS_PLOTLY:
        st.markdown(f"#### Projected {po_label.split('(')[0].strip()} trajectory to 2030")
        yrs, vals = result.forecast["years"], result.forecast["values"]
        band = [uncertainty_band(v) for v in vals]
        fig = go.Figure()
        fig.add_scatter(x=yrs, y=[b[1] for b in band], line=dict(width=0), showlegend=False, hoverinfo="skip")
        fig.add_scatter(x=yrs, y=[b[0] for b in band], fill="tonexty", line=dict(width=0),
                        fillcolor="rgba(45,212,191,.15)", name="95% interval")
        fig.add_scatter(x=yrs, y=vals, line=dict(color="#22b07d", width=3), name=f"{po_label} (mean)")
        fig.update_layout(height=340, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font_color="#cbd5e1", margin=dict(t=20, b=10), xaxis_title="Year")
        st.plotly_chart(fig, use_container_width=True)

    with st.expander("Policy notes & export"):
        for r in result.recommendations:
            st.write("• " + r)
        from reporting.service import get_exporter
        st.download_button("⬇ Excel report", data=get_exporter("excel").export(result.to_dict()),
                           file_name=f"ihsa_{dom}_{country.replace(' ','_')}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


def _regional(model):
    po, po_label, _ = outcome_meta(model)
    rows = []
    for cty in model.countries():
        try:
            rows.append({"country": cty, "iso3": reference.iso3_of(cty),
                         po_label: round(model.simulate(model.baseline(cty)).metrics[po], 1)})
        except Exception:
            pass
    df = pd.DataFrame(rows)
    if HAS_PLOTLY and not df.empty:
        fig = go.Figure(go.Choropleth(locations=df["iso3"], z=df[po_label], text=df["country"],
                                      colorscale="Reds", marker_line_color="#0b1220"))
        fig.update_geos(scope="africa", bgcolor="rgba(0,0,0,0)")
        fig.update_layout(title=f"{po_label} — baseline", height=560, paper_bgcolor="rgba(0,0,0,0)",
                          font_color="#cbd5e1", margin=dict(t=40, b=0))
        st.plotly_chart(fig, use_container_width=True)
    st.dataframe(df.sort_values(po_label, ascending=False), use_container_width=True, hide_index=True)


def _methods():
    st.markdown("#### Data & methods")
    st.markdown("Scenarios run on the IHSA engine. The reworked framework represents each domain as a "
                "**Bayesian network** over layered determinants (shocks → socioeconomic → system → intermediate → "
                "outcome), with do-operator interventions and Monte-Carlo uncertainty propagation.")
    st.markdown("**Agencies mined:** World Bank · WHO GHO · UNICEF SDMX · UNFPA · UNAIDS · ACLED · EM-DAT · DHIS2. "
                "HIS maturity is mined from the WHO AFRO HIS assessment.")
    st.dataframe(reference.indicator_catalogue(), use_container_width=True, hide_index=True)


PAGES = {"🏠 Home": page_home, "🧪 What-if analysis": page_whatif}


def main():
    st.set_page_config(page_title="IHSA · WHO AFRO", page_icon="🌍", layout="wide",
                       initial_sidebar_state="expanded")
    inject_css()
    with st.sidebar:
        st.markdown("### 🌍 IHSA")
        st.caption(f"WHO AFRO · Health Systems Intelligence · v{settings.version}")
        st.markdown("**Navigation**")
        keys = list(PAGES)
        cur = st.session_state.get("_section", keys[0])
        for k in keys:
            if st.button(k, use_container_width=True, type="primary" if k == cur else "secondary"):
                st.session_state["_section"] = k
                st.rerun()
        st.markdown("---")
        st.markdown("**Quick guide**")
        st.markdown("- Review status quo baseline\n- Adjust levers (🟢 lowers the outcome when ↑)\n"
                    "- Set a target to work backwards\n- Export Excel reports")
        st.markdown("---")
        st.caption("Illustrative decision-support — not official estimates.")
    PAGES.get(st.session_state.get("_section", "🏠 Home"), page_home)()


if __name__ == "__main__":
    main()
