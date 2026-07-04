"""
IHSA Streamlit shell — redesigned UI/UX (drawn from the WHO AFRO maternal explorer).

Dark hero, gradient headlines, glassmorphic cards, and a two-pane scenario
workspace supporting both forward what-if and inverse (target-seeking) analysis.
Registry-driven: every registered domain appears automatically.
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
    import plotly.express as px
    HAS_PLOTLY = True
except Exception:  # pragma: no cover
    HAS_PLOTLY = False

load_builtin_models()

DOMAIN_ICON = {"hiv": "🧬", "maternal": "🤰", "neonatal": "👶", "child": "🧒",
               "under5": "🩺", "tb": "🫁", "malaria": "🦟", "uhc": "🏥",
               "ncd": "❤️", "srhr": "🌸", "rhis": "🗂", "digital_health": "💻", "sdg3": "🎯"}
DOMAIN_GRAD = {"hiv": "#ef4444,#ec4899", "maternal": "#f97316,#f59e0b",
               "neonatal": "#38bdf8,#0ea5e9", "child": "#34d399,#14b8a6",
               "under5": "#a78bfa,#8b5cf6"}


def _css():
    st.markdown("""
    <style>
      .block-container { padding-top: 1.1rem; max-width: 1180px; }
      div[data-testid="stAppViewContainer"] { background: #020617; }
      section[data-testid="stSidebar"] { background: #0b1220; }
      .ihsa-hero { position: relative; overflow: hidden; border-radius: 24px;
        background: linear-gradient(120deg,#0b132b 0%,#1c2541 52%,#3a506b 100%);
        border: 1px solid #334155; padding: 2.3rem 2.5rem; margin-bottom: 1.6rem;
        box-shadow: 0 25px 55px rgba(0,0,0,.4); }
      .ihsa-hero-glow { position:absolute; right:-40px; top:-40px; width:45%; height:150%;
        background: radial-gradient(circle at center, rgba(28,124,116,.35), transparent 70%); }
      .ihsa-chip { display:inline-flex; align-items:center; gap:8px; padding:7px 15px;
        border-radius:999px; background:rgba(28,124,116,.18); border:1px solid rgba(45,212,191,.4);
        color:#7dd3fc; font-size:.82rem; font-weight:600; letter-spacing:.04em; margin-bottom:1rem; }
      .ihsa-h1 { font-size:2.7rem; font-weight:800; line-height:1.08; margin:0 0 .8rem 0; color:#f8fafc; letter-spacing:-.02em; }
      .ihsa-grad { background:linear-gradient(90deg,#f87171,#fb923c); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
      .ihsa-sub { color:#cbd5e1; font-size:1.02rem; line-height:1.6; max-width:44rem; }
      .ihsa-metric { border-radius:16px; background:rgba(255,255,255,.05); border:1px solid rgba(255,255,255,.1);
        padding:1rem 1.1rem; backdrop-filter:blur(8px); }
      .ihsa-metric .l { font-size:.74rem; color:#94a3b8; text-transform:uppercase; letter-spacing:.05em; }
      .ihsa-metric .v { font-size:1.9rem; font-weight:800; color:#f8fafc; margin:.15rem 0; }
      .ihsa-metric .u { font-size:.72rem; color:#94a3b8; }
      .ihsa-card { border-radius:20px; background:#0f172a; border:1px solid #1e293b; padding:1.4rem 1.5rem;
        height:100%; box-shadow:0 16px 34px rgba(0,0,0,.28); transition:transform .18s ease, border .18s ease; }
      .ihsa-card:hover { transform:translateY(-3px); border-color:#334155; }
      .ihsa-card .ic { width:54px; height:54px; border-radius:15px; display:flex; align-items:center;
        justify-content:center; font-size:1.6rem; margin-bottom:.9rem; }
      .ihsa-card .t { font-size:1.2rem; font-weight:700; color:#f1f5f9; margin:.2rem 0 .5rem 0; }
      .ihsa-card .d { color:#94a3b8; font-size:.9rem; line-height:1.5; min-height:3.4rem; }
      .ihsa-card .m { font-size:.72rem; letter-spacing:.1em; text-transform:uppercase; color:#64748b; }
      .pane-anchor { height:0; overflow:hidden; }
      div[data-testid="column"]:has(.pane-anchor) {
        background:linear-gradient(165deg,#0f172a 0%,#1e293b 48%,#0f172a 100%);
        border-radius:20px; border:1px solid rgba(148,163,184,.22); padding:.4rem 1rem 1rem 1rem;
        box-shadow:0 18px 40px rgba(2,6,23,.35); }
      div[data-testid="column"]:has(.pane-anchor) label,
      div[data-testid="column"]:has(.pane-anchor) .stMarkdown p { color:#e2e8f0 !important; }
      .pane-title { font-size:1.5rem; font-weight:800; line-height:1.12; margin:.4rem 0 .1rem 0; }
      .pane-title .l1 { color:#f8fafc; display:block; }
      .pane-title .l2 { display:block; background:linear-gradient(90deg,#f87171,#fb923c);
        -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
      .pane-sub { color:#94a3b8; font-size:.85rem; margin-bottom:.8rem; }
    </style>""", unsafe_allow_html=True)


def _nav(section):
    st.session_state["_section"] = section
    st.rerun()


def _hero_metrics():
    c = reference.countries()
    return [("Member states", f"{len(c)}", "WHO African Region"),
            ("Scenario domains", f"{len(list_models())}", "one shared engine"),
            ("Indicators", f"{len(reference.indicator_catalogue())}", "catalogued"),
            ("Data agencies", "5", "WB · WHO · UNICEF · UNFPA · UNAIDS")]


def page_home():
    st.markdown('<div class="ihsa-hero"><div class="ihsa-hero-glow"></div>'
                '<div class="ihsa-chip">🌍 WHO AFRO · Integrated Health Systems Analytics</div>'
                '<div class="ihsa-h1">Health Systems<br/><span class="ihsa-grad">Scenario Intelligence</span></div>'
                '<div class="ihsa-sub">One platform, one scenario engine, many domains — explore how '
                'health-system levers reshape mortality, disease and coverage across the African Region, '
                'with forward what-if and inverse target-seeking analysis.</div></div>',
                unsafe_allow_html=True)

    cols = st.columns(4)
    for col, (l, v, u) in zip(cols, _hero_metrics()):
        col.markdown(f'<div class="ihsa-metric"><div class="l">{l}</div>'
                     f'<div class="v">{v}</div><div class="u">{u}</div></div>', unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown("#### Explore a domain")
    domains = list_models()
    for i in range(0, len(domains), 3):
        row = st.columns(3)
        for col, dom in zip(row, domains[i:i + 3]):
            m = get_model(dom)
            g = DOMAIN_GRAD.get(dom, "#1c7c74,#2dd4bf")
            po = next((o.label for o in m.outcomes), m.primary_outcome)
            with col:
                st.markdown(
                    f'<div class="ihsa-card"><div class="ic" style="background:linear-gradient(135deg,{g});">'
                    f'{DOMAIN_ICON.get(dom,"📊")}</div><div class="t">{m.title}</div>'
                    f'<div class="d">Primary outcome: {po}. {len(m.levers)} scenario levers.</div>'
                    f'<div class="m">what-if · target-seeking</div></div>', unsafe_allow_html=True)
                if st.button(f"Open {m.title}", key=f"open_{dom}", use_container_width=True):
                    st.session_state["_domain"] = dom
                    _nav("🧪 Scenario workspace")


def page_scenario():
    st.markdown("### 🧪 Scenario workspace")
    domains = list_models()
    dcol, ccol, mcol = st.columns([1.3, 1.3, 1])
    with dcol:
        dsel = st.session_state.get("_domain", domains[0])
        dom = st.selectbox("Domain", domains, index=domains.index(dsel) if dsel in domains else 0,
                           format_func=lambda d: get_model(d).title)
    model = get_model(dom)
    engine = ScenarioEngine(model=model)
    with ccol:
        country = st.selectbox("Country", model.countries())
    with mcol:
        mode = st.radio("Mode", ["Forward", "Target-seeking"], horizontal=True)

    base = model.baseline(country)
    po = model.primary_outcome
    outcome_label = next((o.label for o in model.outcomes if o.key == po), po)
    outcome_unit = next((o.unit for o in model.outcomes if o.key == po), "")
    base_val = model.simulate(base).metrics[po]

    left, right = st.columns([1, 1.15])
    inv = None
    with left:
        st.markdown('<div class="pane-anchor"></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="pane-title"><span class="l1">{model.title}</span>'
                    f'<span class="l2">Scenario Explorer</span></div>'
                    f'<p class="pane-sub">Baseline {base.year}: {base_val:.1f} {outcome_unit}. '
                    f'{"Adjust levers forward from status quo." if mode=="Forward" else "Set a target to work backwards."}</p>',
                    unsafe_allow_html=True)

        overrides = {}
        if mode == "Forward":
            for lv in model.levers:
                cur = float(base.values.get(lv.key, lv.min))
                overrides[lv.key] = st.slider(f"{lv.label} ({lv.unit})", float(lv.min), float(lv.max),
                                              min(max(cur, lv.min), lv.max), float(lv.step), key=f"s_{dom}_{lv.key}")
            result = engine.run(country, overrides)
            scen_val = result.scenario_outcome[po]
        else:
            tgt = st.slider(f"Target {outcome_label} ({outcome_unit})",
                            float(round(base_val * 0.2, 1)), float(round(base_val, 1)),
                            float(round(base_val * 0.6, 1)))
            inv = solve_for_target(model, country, tgt)
            overrides = inv.lever_settings
            result = engine.run(country, {k: v for k, v in overrides.items() if k in base.values})
            scen_val = inv.achieved

    with right:
        delta = scen_val - base_val
        pct = delta / base_val * 100 if base_val else 0
        st.markdown(f"#### {outcome_label}")
        a, b = st.columns(2)
        a.metric("Scenario", f"{scen_val:.1f}", f"{pct:+.0f}%", delta_color="inverse")
        b.metric("Observed baseline", f"{base_val:.1f}")

        if mode == "Target-seeking" and inv is not None:
            if inv.feasible:
                st.success(f"Target reachable at ~{inv.effort_fraction*100:.0f}% of the way to full "
                           f"coverage on protective levers.")
            else:
                st.warning(f"Target not reachable with these levers alone — best achievable is "
                           f"{inv.achieved:.1f}. Consider cross-domain interventions.")
            st.caption("Required coverages:")
            req = pd.DataFrame({"Lever": [next((l.label for l in model.levers if l.key == k), k)
                                          for k in overrides], "Required %": list(overrides.values())})
            st.dataframe(req, use_container_width=True, hide_index=True, height=min(280, 60 + 35 * len(req)))

        if result.forecast and HAS_PLOTLY:
            fc = pd.DataFrame({"Year": result.forecast["years"], outcome_label: result.forecast["values"]})
            fig = px.area(fc, x="Year", y=outcome_label, title="Illustrative trajectory")
            fig.update_traces(line_color="#2dd4bf", fillcolor="rgba(45,212,191,.15)")
            fig.update_layout(height=250, margin=dict(t=36, b=8, l=8, r=8),
                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#cbd5e1")
            st.plotly_chart(fig, use_container_width=True)

    if result.sensitivity:
        st.markdown("##### Highest-leverage levers (each on its own)")
        sdf = pd.DataFrame(result.sensitivity).head(8)
        sdf["lever"] = sdf["lever"].map(lambda k: next((l.label for l in model.levers if l.key == k), k))
        if HAS_PLOTLY:
            fig = px.bar(sdf, x="solo_change_pct", y="lever", orientation="h",
                         color="solo_change_pct", color_continuous_scale="Teal_r",
                         labels={"solo_change_pct": f"% change in {outcome_label}", "lever": ""})
            fig.update_layout(height=300, margin=dict(t=10, b=10), paper_bgcolor="rgba(0,0,0,0)",
                              plot_bgcolor="rgba(0,0,0,0)", font_color="#cbd5e1", coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.dataframe(sdf, use_container_width=True, hide_index=True)

    with st.expander("Policy notes & export"):
        for r in result.recommendations:
            st.write("• " + r)
        from reporting.service import get_exporter
        st.download_button("⬇ Excel report", data=get_exporter("excel").export(result.to_dict()),
                           file_name=f"ihsa_{dom}_{country.replace(' ','_')}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


def page_regional():
    st.markdown("### 📊 Regional insights")
    dom = st.selectbox("Domain", list_models(), format_func=lambda d: get_model(d).title)
    model = get_model(dom)
    po = model.primary_outcome
    rows = []
    for cty in model.countries():
        try:
            b = model.baseline(cty)
            rows.append({"country": cty, "iso3": reference.iso3_of(cty), po: model.simulate(b).metrics[po]})
        except Exception:
            pass
    df = pd.DataFrame(rows)
    label = next((o.label for o in model.outcomes), po)
    if HAS_PLOTLY and not df.empty:
        fig = px.choropleth(df, locations="iso3", color=po, hover_name="country", scope="africa",
                            color_continuous_scale="Reds", labels={po: label}, title=f"{label} — baseline")
        fig.update_layout(height=560, paper_bgcolor="rgba(0,0,0,0)", geo_bgcolor="rgba(0,0,0,0)",
                          font_color="#cbd5e1", margin=dict(t=40, b=0))
        st.plotly_chart(fig, use_container_width=True)
    if not df.empty:
        st.dataframe(df.sort_values(po, ascending=False), use_container_width=True, hide_index=True)


def page_data():
    st.markdown("### 🗂 Data & sources")
    st.caption("Master reference data and domain panels. Production deployments refresh these by "
               "running `python scripts/mine_data.py` against the live agency APIs.")
    st.markdown("**Agencies mined:** World Bank · WHO GHO · UNICEF SDMX · UNFPA · UNAIDS")
    st.dataframe(reference.indicator_catalogue(), use_container_width=True, hide_index=True)
    st.markdown("**AFRO master country table (47 member states)**")
    st.dataframe(reference.countries(), use_container_width=True, hide_index=True, height=340)


PAGES = {"🏠 Home": page_home, "🧪 Scenario workspace": page_scenario,
         "📊 Regional insights": page_regional, "🗂 Data & sources": page_data}


def main():
    st.set_page_config(page_title="IHSA · WHO AFRO", page_icon="🌍", layout="wide",
                       initial_sidebar_state="expanded")
    _css()
    with st.sidebar:
        st.markdown("## 🌍 IHSA")
        st.caption(f"Enterprise v{settings.version}")
        keys = list(PAGES)
        default = st.session_state.get("_section", keys[0])
        choice = st.radio("Navigate", keys, index=keys.index(default) if default in keys else 0,
                          label_visibility="collapsed")
        st.session_state["_section"] = choice
        st.markdown("---")
        st.caption("Illustrative decision-support — not official estimates.")
    PAGES[choice]()


if __name__ == "__main__":
    main()
