"""
Mine indicator data from open agency APIs into the medallion warehouse.

Sources: World Bank, WHO GHO, UNICEF SDMX, UNAIDS, UNFPA. Runs the shared ETL
clients (retries, caching, pagination, validation, metadata versioning), lands raw
pulls in warehouse/raw/ and a merged country-year panel in warehouse/processed/.

Network is required. With no network (or a failing source) the orchestrator logs
the failure and leaves the committed illustrative panels in place, so the platform
keeps running. Run: python scripts/mine_data.py [--sources worldbank who_gho ...]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from config.logging_config import get_logger  # noqa: E402
from etl import get_client  # noqa: E402
from warehouse import reference  # noqa: E402

log = get_logger("scripts.mine_data")
RAW = ROOT / "warehouse" / "raw"
PROCESSED = ROOT / "warehouse" / "processed"

# World Bank indicator bundle (extend freely)
WORLD_BANK = {
    "SH.STA.MMRT": "maternal_mortality_ratio",
    "SH.DYN.MORT": "under5_mortality",
    "SH.DYN.NMRT": "neonatal_mortality",
    "SP.DYN.IMRT.IN": "infant_mortality",
    "SH.STA.BRTC.ZS": "skilled_birth_attendance",
    "SH.IMM.IDPT": "dtp3_immunisation",
    "SH.IMM.MEAS": "measles_immunisation",
    "SP.DYN.TFRT.IN": "fertility_rate",
    "SP.DYN.CONM.ZS": "contraception_modern",
    "SH.DYN.AIDS.ZS": "hiv_prevalence",
    "SH.MLR.INCD.P3": "malaria_incidence",
    "SH.TBS.INCD": "tb_incidence",
    "SH.XPD.GHED.GD.ZS": "gov_health_expenditure",
    "SH.XPD.OOPC.CH.ZS": "oop_expenditure",
    "SE.ADT.LITR.FE.ZS": "female_literacy",
}

# WHO GHO OData indicator codes (representative)
WHO_GHO = {
    "UHC_INDEX_REPORTED": "uhc_service_coverage_index",
    "NCDMORT3070": "ncd_premature_mortality",
}


def mine_world_bank(iso3: list[str]) -> pd.DataFrame:
    client = get_client("worldbank")
    frames = []
    for code, name in WORLD_BANK.items():
        try:
            res = client.fetch(code, iso3="all")
            df = pd.DataFrame(res.rows)
            if df.empty:
                continue
            df = df[df["iso3"].isin(iso3)][["iso3", "year", "value"]].rename(columns={"value": name})
            frames.append(df)
            log.info("World Bank %s: %d rows (v%s)", name, len(df), res.version)
        except Exception as exc:  # noqa: BLE001
            log.warning("World Bank %s failed: %s", code, exc)
    if not frames:
        return pd.DataFrame()
    out = frames[0]
    for f in frames[1:]:
        out = out.merge(f, on=["iso3", "year"], how="outer")
    return out


def mine_who_gho(iso3: list[str]) -> pd.DataFrame:
    client = get_client("who_gho")
    frames = []
    for code, name in WHO_GHO.items():
        try:
            res = client.fetch(code)
            df = pd.DataFrame(res.rows)
            if df.empty:
                continue
            df = df[df["iso3"].isin(iso3)][["iso3", "year", "value"]].rename(columns={"value": name})
            frames.append(df)
            log.info("WHO GHO %s: %d rows", name, len(df))
        except Exception as exc:  # noqa: BLE001
            log.warning("WHO GHO %s failed: %s", code, exc)
    if not frames:
        return pd.DataFrame()
    out = frames[0]
    for f in frames[1:]:
        out = out.merge(f, on=["iso3", "year"], how="outer")
    return out


SOURCE_FN = {"worldbank": mine_world_bank, "who_gho": mine_who_gho}


def impute(panel: pd.DataFrame) -> pd.DataFrame:
    """Impute the merged indicator panel with the IHSA imputation framework
    (temporal -> MICE -> hierarchical); see warehouse/imputation.py."""
    from warehouse.imputation import impute_panel

    df = panel.copy()
    if "subregion" not in df.columns:
        ref = reference.countries()[["iso3", "subregion"]]
        df = df.merge(ref, on="iso3", how="left")
    value_cols = [c for c in df.columns if c not in ("iso3", "year", "country", "subregion")]
    if not value_cols:
        return panel
    res = impute_panel(df, value_cols, m=1)          # single completed panel for the warehouse
    out = res.data
    log.info("imputation: %s", str(res.report).splitlines()[0])
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", nargs="*", default=["worldbank", "who_gho"])
    args = ap.parse_args()

    iso3 = reference.countries()["iso3"].tolist()
    RAW.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)

    merged = None
    for src in args.sources:
        fn = SOURCE_FN.get(src)
        if fn is None:
            log.warning("no orchestrator wired for source '%s' (client exists; extend here)", src)
            continue
        df = fn(iso3)
        if df.empty:
            log.warning("%s returned no data (offline?). Keeping illustrative panels.", src)
            continue
        df.to_csv(RAW / f"{src}_raw.csv", index=False)
        merged = df if merged is None else merged.merge(df, on=["iso3", "year"], how="outer")

    if merged is None:
        log.warning("No live data mined. Illustrative panels remain authoritative.")
        return
    merged = impute(merged)
    merged = merged.merge(reference.countries()[["iso3", "country"]], on="iso3", how="left")
    out = PROCESSED / "afro_indicator_panel.csv"
    merged.to_csv(out, index=False)
    log.info("wrote merged panel: %d rows, %d indicators -> %s",
             len(merged), merged.shape[1], out)


if __name__ == "__main__":
    main()
