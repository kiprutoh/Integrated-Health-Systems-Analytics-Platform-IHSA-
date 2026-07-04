"""GIS service (charter Phase D placeholder).

Choropleth/boundary helpers will live here. v0.1.0 relies on Plotly's built-in
country geometry via ISO3 codes in the reference master data.
"""
from warehouse import reference

def afro_iso3_list() -> list[str]:
    return reference.countries()["iso3"].tolist()
