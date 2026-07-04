"""Reference (master data) access — the `reference` layer of the warehouse.

Thin, cached loaders over the seeded CSVs. Every module reads countries and the
indicator catalogue through here rather than hard-coding lists.
"""
from __future__ import annotations

import functools

import pandas as pd

from config.settings import REFERENCE_DIR
from config.logging_config import get_logger

log = get_logger("warehouse.reference")


@functools.lru_cache(maxsize=1)
def countries() -> pd.DataFrame:
    df = pd.read_csv(REFERENCE_DIR / "afro_countries.csv")
    log.debug("loaded %d AFRO countries", len(df))
    return df


@functools.lru_cache(maxsize=1)
def who_regions() -> pd.DataFrame:
    return pd.read_csv(REFERENCE_DIR / "who_regions.csv")


@functools.lru_cache(maxsize=1)
def indicator_catalogue() -> pd.DataFrame:
    return pd.read_csv(REFERENCE_DIR / "indicator_catalogue.csv")


def country_names() -> list[str]:
    return countries()["country"].tolist()


def iso3_of(country: str) -> str | None:
    df = countries()
    hit = df.loc[df["country"] == country, "iso3"]
    return None if hit.empty else str(hit.iloc[0])


def indicators_for(domain: str) -> pd.DataFrame:
    cat = indicator_catalogue()
    return cat[cat["domain"] == domain].reset_index(drop=True)
