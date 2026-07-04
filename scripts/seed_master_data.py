"""
Seed the master/reference data used by every IHSA module.

Writes CSVs into data/reference/. In production these become the `reference` layer
of the warehouse and are refreshed/extended by ETL (e.g. World Bank income groups).
Run: python scripts/seed_master_data.py
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from config.settings import REFERENCE_DIR  # noqa: E402

# (country, iso3, subregion) — WHO African Region, 47 member states
AFRO = [
    ("Algeria", "DZA", "Northern Africa"),
    ("Angola", "AGO", "Central Africa"),
    ("Benin", "BEN", "Western Africa"),
    ("Botswana", "BWA", "Southern Africa"),
    ("Burkina Faso", "BFA", "Western Africa"),
    ("Burundi", "BDI", "Eastern Africa"),
    ("Cabo Verde", "CPV", "Western Africa"),
    ("Cameroon", "CMR", "Central Africa"),
    ("Central African Republic", "CAF", "Central Africa"),
    ("Chad", "TCD", "Central Africa"),
    ("Comoros", "COM", "Eastern Africa"),
    ("Congo", "COG", "Central Africa"),
    ("Cote d'Ivoire", "CIV", "Western Africa"),
    ("Democratic Republic of the Congo", "COD", "Central Africa"),
    ("Equatorial Guinea", "GNQ", "Central Africa"),
    ("Eritrea", "ERI", "Eastern Africa"),
    ("Eswatini", "SWZ", "Southern Africa"),
    ("Ethiopia", "ETH", "Eastern Africa"),
    ("Gabon", "GAB", "Central Africa"),
    ("Gambia", "GMB", "Western Africa"),
    ("Ghana", "GHA", "Western Africa"),
    ("Guinea", "GIN", "Western Africa"),
    ("Guinea-Bissau", "GNB", "Western Africa"),
    ("Kenya", "KEN", "Eastern Africa"),
    ("Lesotho", "LSO", "Southern Africa"),
    ("Liberia", "LBR", "Western Africa"),
    ("Madagascar", "MDG", "Eastern Africa"),
    ("Malawi", "MWI", "Southern Africa"),
    ("Mali", "MLI", "Western Africa"),
    ("Mauritania", "MRT", "Western Africa"),
    ("Mauritius", "MUS", "Eastern Africa"),
    ("Mozambique", "MOZ", "Southern Africa"),
    ("Namibia", "NAM", "Southern Africa"),
    ("Niger", "NER", "Western Africa"),
    ("Nigeria", "NGA", "Western Africa"),
    ("Rwanda", "RWA", "Eastern Africa"),
    ("Sao Tome and Principe", "STP", "Central Africa"),
    ("Senegal", "SEN", "Western Africa"),
    ("Seychelles", "SYC", "Eastern Africa"),
    ("Sierra Leone", "SLE", "Western Africa"),
    ("South Africa", "ZAF", "Southern Africa"),
    ("South Sudan", "SSD", "Eastern Africa"),
    ("Togo", "TGO", "Western Africa"),
    ("Uganda", "UGA", "Eastern Africa"),
    ("United Republic of Tanzania", "TZA", "Eastern Africa"),
    ("Zambia", "ZMB", "Southern Africa"),
    ("Zimbabwe", "ZWE", "Southern Africa"),
]

WHO_REGIONS = [
    ("AFRO", "African Region"),
    ("AMRO", "Region of the Americas"),
    ("SEARO", "South-East Asia Region"),
    ("EURO", "European Region"),
    ("EMRO", "Eastern Mediterranean Region"),
    ("WPRO", "Western Pacific Region"),
]

# code, name, domain, unit, source, polarity(-1 lower=better, +1 higher=better, 0 neutral)
INDICATORS = [
    # UHC
    ("UHC_SCI", "UHC service coverage index", "uhc", "index 0-100", "WHO GHO", +1),
    ("GHED_GGHE_GDP", "Government health expenditure", "uhc", "% of GDP", "WHO GHED", +1),
    ("CHE_PC", "Current health expenditure per capita", "uhc", "US$", "WHO GHED", +1),
    ("OOP_CHE", "Out-of-pocket expenditure", "uhc", "% of CHE", "WHO GHED", -1),
    # Maternal
    ("MMR", "Maternal mortality ratio", "maternal", "per 100,000 live births", "UN MMEIG", -1),
    ("SBA", "Skilled birth attendance", "maternal", "%", "DHS/UNICEF", +1),
    ("ANC4", "Antenatal care (4+ visits)", "maternal", "%", "DHS/UNICEF", +1),
    # HIV
    ("HIV_INC", "HIV incidence (15-49)", "hiv", "per 1,000 uninfected", "UNAIDS", -1),
    ("HIV_PREV", "Adult HIV prevalence", "hiv", "% (15-49)", "UNAIDS", 0),
    ("HIV_ART", "ART coverage", "hiv", "% of PLHIV", "UNAIDS", +1),
    ("HIV_VLS", "Viral load suppression", "hiv", "% of PLHIV", "UNAIDS", +1),
    # TB
    ("TB_INC", "TB incidence", "tb", "per 100,000", "WHO GTB", -1),
    ("TB_TSR", "TB treatment success rate", "tb", "%", "WHO GTB", +1),
    # Malaria
    ("MAL_INC", "Malaria incidence", "malaria", "per 1,000 at risk", "WHO GMP", -1),
    ("ITN_USE", "ITN use (children <5)", "malaria", "%", "DHS/MIS", +1),
    # NCD
    ("NCD_PMORT", "NCD premature mortality (30-70)", "ncd", "probability %", "WHO GHO", -1),
    ("HTN_CTRL", "Hypertension control", "ncd", "%", "STEPS", +1),
    # RHIS / digital
    ("RHIS_COMPLETE", "HMIS reporting completeness", "rhis", "%", "DHIS2", +1),
    ("DH_INDEX", "Digital health maturity", "digital_health", "index", "WHO/GDHI", +1),
    # SRHR / SDG3
    ("MCPR", "Modern contraceptive prevalence", "srhr", "%", "DHS/UNFPA", +1),
    ("U5MR", "Under-five mortality rate", "sdg3", "per 1,000 live births", "UN IGME", -1),
]


def _write(path: Path, header: list[str], rows: list[tuple]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"wrote {path.relative_to(ROOT)}  ({len(rows)} rows)")


def main() -> None:
    _write(REFERENCE_DIR / "who_regions.csv", ["region_code", "region_name"], WHO_REGIONS)
    _write(
        REFERENCE_DIR / "afro_countries.csv",
        ["country", "iso3", "who_region", "subregion", "wb_income_group"],
        [(c, i, "AFRO", s, "") for c, i, s in AFRO],
    )
    _write(
        REFERENCE_DIR / "indicator_catalogue.csv",
        ["indicator_code", "indicator_name", "domain", "unit", "source", "polarity"],
        INDICATORS,
    )
    print(f"AFRO member states: {len(AFRO)}")


if __name__ == "__main__":
    main()
