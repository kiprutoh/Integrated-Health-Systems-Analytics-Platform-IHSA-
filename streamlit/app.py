"""
IHSA Streamlit shell (charter Sprint 5).

Pages: Home, Country Explorer, Dataset Explorer, Indicator Explorer,
Scenario Explorer, Settings.

The Scenario Explorer is generic: it reads levers/outcomes from whichever
ScenarioModel is registered for the chosen domain and calls the shared engine,
so new domains appear automatically once their analytics package registers.
"""
from __future__ import annotations

import sys
from pathlib import Path

# allow `streamlit run streamlit/app.py` from repo root
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st

from config.settings import settings
from scenario_engine import ScenarioEngine, get_model, list_models, load_builtin_models
from warehouse import reference

try:
    import plotly.express as px
    HAS_PLOTLY = True
except Exception:  # pragma: no cover
    HAS_PLOTLY = False

load_builtin_models()


def _page_home():
    st.title(f"🌍 {settings.app_name}")
    st.caption(f"Enterprise v{settings.version} · WHO AFRO · modular decision-support platform")
    c = reference.countries()
    a, b, d = st.columns(3)
    a.metric("AFRO member states", len(c))
    b.metric("Scenario domains", len(list_models()))
    d.metric("Catalogued indicators", len(reference.indicator_catalogue()))
    st.markdown(
        "This platform provides shared foundations — master data, ETL, a data "
        "warehouse, and **one scenario engine** — that every disease module plugs into. "
        "It is built to answer questions such as:"
    )
    st.markdown(
        "- What happens to **UHC** if government health expenditure rises 10%?\n"
        "- How would **HIV incidence** change if ART coverage reached 95%?\n"
        "- Which districts are likely to **miss SDG 3** targets by 2030?\n"
        "- Which investments most reduce **maternal mortality**?"
    )
    st.info("Active modules: " + ", ".join(list_models()) +
            ". More domains slot into the same engine incrementally.")


def _page_country_explorer():
    st.title("Country Explorer")
    c = reference.countries()
    country = st.selectbox("Country", c["country"].tolist())
    row = c[c["country"] == country].iloc[0]
    a, b, d = st.columns(3)
    a.metric("ISO3", row["iso3"])
    b.metric("WHO region", row["who_region"])
    d.metric("Subregion", row["subregion"])
    st.subheader("Available scenario domains for this country")
    for dom in list_models():
        m = get_model(dom)
        try:
            available = country in m.countries()
        except Exception:
            available = False
        st.write(f"{'✅' if available else '⚪'} **{m.title}** ({dom})"
                 + ("" if available else " — no data loaded for this country yet"))


def _page_dataset_explorer():
    st.title("Dataset Explorer")
    st.caption("Processed warehouse layer")
    datasets = {
        "AFRO countries (reference)": reference.countries(),
        "WHO regions (reference)": reference.who_regions(),
        "Indicator catalogue (reference)": reference.indicator_catalogue(),
    }
    for dom in list_models():
        try:
            m = get_model(dom)
            path = ROOT / "data" / "processed" / dom
            for f in path.glob("*.csv"):
                datasets[f"{dom}: {f.name}"] = pd.read_csv(f)
        except Exception:
            pass
    pick = st.selectbox("Dataset", list(datasets))
    df = datasets[pick]
    st.write(f"{len(df):,} rows × {df.shape[1]} columns")
    st.dataframe(df, use_container_width=True, height=420)
    st.download_button("⬇ CSV", df.to_csv(index=False).encode(),
                       file_name=pick.split(":")[-1].strip().replace(" ", "_") + ".csv")


def _page_indicator_explorer():
    st.title("Indicator Explorer")
    cat = reference.indicator_catalogue()
    domains = ["(all)"] + sorted(cat["domain"].unique())
    dom = st.selectbox("Domain", domains)
    view = cat if dom == "(all)" else cat[cat["domain"] == dom]
    st.dataframe(view, use_container_width=True, hide_index=True)
    st.caption("Polarity: −1 lower is better · +1 higher is better · 0 neutral")


def _page_scenario_explorer():
    st.title("Scenario Explorer")
    if not list_models():
        st.warning("No scenario domains registered.")
        return
    dom = st.selectbox("Domain", list_models(),
                       format_func=lambda d: get_model(d).title)
    model = get_model(dom)
    engine = ScenarioEngine(model=model)

    clist = model.countries()
    country = st.selectbox("Country", clist)
    base = model.baseline(country)

    st.caption(f"Baseline = latest observed values ({base.year}). Move levers to explore.")
    cols = st.columns(2)
    overrides = {}
    for i, lv in enumerate(model.levers):
        with cols[i % 2]:
            cur = float(base.values.get(lv.key, lv.min))
            overrides[lv.key] = st.slider(f"{lv.label} ({lv.unit})", float(lv.min),
                                          float(lv.max), min(max(cur, lv.min), lv.max),
                                          float(lv.step))

    result = engine.run(country, overrides)
    po = model.primary_outcome
    base_v = result.baseline_outcome[po]
    scen_v = result.scenario_outcome[po]
    chg = result.relative_change_pct[po]

    st.subheader("Projected impact")
    m1, m2 = st.columns(2)
    outcome_label = next((o.label for o in model.outcomes if o.key == po), po)
    m1.metric(outcome_label, f"{scen_v:.2f}", delta=f"{chg:+.0f}%", delta_color="inverse")
    m2.metric("Observed baseline", f"{base_v:.2f}")

    if result.forecast and HAS_PLOTLY:
        fc = pd.DataFrame({"Year": result.forecast["years"],
                           outcome_label: result.forecast["values"]})
        st.plotly_chart(px.line(fc, x="Year", y=outcome_label, markers=True,
                                title="Illustrative forecast"), use_container_width=True)

    if result.sensitivity:
        st.subheader("Sensitivity (each lever on its own)")
        sdf = pd.DataFrame(result.sensitivity)
        if HAS_PLOTLY:
            st.plotly_chart(px.bar(sdf, x="solo_change_pct", y="lever", orientation="h",
                                   labels={"solo_change_pct": "% change in " + po}),
                            use_container_width=True)
        else:
            st.dataframe(sdf, use_container_width=True, hide_index=True)

    st.subheader("Policy notes")
    for r in result.recommendations:
        st.write("• " + r)

    from reporting.service import get_exporter
    st.download_button("⬇ Excel report", data=get_exporter("excel").export(result.to_dict()),
                       file_name=f"ihsa_{dom}_{country.replace(' ', '_')}.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


def _page_settings():
    st.title("Settings")
    st.write(f"**Environment:** {settings.environment}")
    st.write(f"**Version:** {settings.version}")
    st.write(f"**Log level:** {settings.log_level}")
    st.write(f"**Registered domains:** {', '.join(list_models())}")
    st.write(f"**Plotly available:** {HAS_PLOTLY}")
    st.caption("Authentication (OAuth2/RBAC), GIS and notifications arrive in Phase D.")


PAGES = {
    "🏠 Home": _page_home,
    "🌍 Country Explorer": _page_country_explorer,
    "🗂 Dataset Explorer": _page_dataset_explorer,
    "📇 Indicator Explorer": _page_indicator_explorer,
    "🧪 Scenario Explorer": _page_scenario_explorer,
    "⚙️ Settings": _page_settings,
}


def main():
    st.set_page_config(page_title=settings.app_short if hasattr(settings, "app_short") else "IHSA",
                       page_icon="🌍", layout="wide", initial_sidebar_state="expanded")
    with st.sidebar:
        st.markdown("## IHSA")
        st.caption(f"Enterprise v{settings.version}")
        choice = st.radio("Navigate", list(PAGES), label_visibility="collapsed")
        st.markdown("---")
        st.caption("WHO AFRO · Integrated Health Systems Analytics Platform")
    PAGES[choice]()


if __name__ == "__main__":
    main()
