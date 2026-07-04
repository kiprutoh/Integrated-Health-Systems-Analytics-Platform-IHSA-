"""
Concrete source clients.

World Bank is fully wired (real API, paginated). The others declare their
source-specific endpoints and are ready to complete — they inherit all shared
machinery (retries, cache, validation, metadata) from BaseETLClient.
"""
from __future__ import annotations

from typing import Any

from config.logging_config import get_logger
from etl.base import BaseETLClient

log = get_logger("etl.clients")


class WorldBankClient(BaseETLClient):
    source_name = "worldbank"
    BASE = "https://api.worldbank.org/v2"

    def build_url(self, indicator: str, iso3: str = "all", start: int = 2000,
                  end: int = 2023, page: int = 1) -> str:
        return (f"{self.BASE}/country/{iso3}/indicator/{indicator}"
                f"?format=json&per_page=1000&date={start}:{end}&page={page}")

    def parse(self, payload: Any) -> list[dict]:
        if not isinstance(payload, list) or len(payload) < 2 or payload[1] is None:
            return []
        return [
            {"iso3": r["countryiso3code"], "year": int(r["date"]),
             "value": r["value"], "indicator": r["indicator"]["id"]}
            for r in payload[1]
        ]

    def paginate(self, indicator: str, **params: Any):  # pragma: no cover - network
        page = 1
        while True:
            payload = self._http_get(self.build_url(indicator, page=page, **params))
            if not isinstance(payload, list) or len(payload) < 2 or payload[1] is None:
                break
            yield payload
            total_pages = payload[0].get("pages", 1)
            if page >= total_pages:
                break
            page += 1


class WHOGhoClient(BaseETLClient):
    source_name = "who_gho"
    BASE = "https://ghoapi.azureedge.net/api"

    def build_url(self, indicator: str, **params: Any) -> str:
        return f"{self.BASE}/{indicator}"

    def parse(self, payload: Any) -> list[dict]:
        rows = payload.get("value", []) if isinstance(payload, dict) else []
        return [{"iso3": r.get("SpatialDim"), "year": r.get("TimeDim"),
                 "value": r.get("NumericValue"), "indicator": r.get("IndicatorCode")}
                for r in rows]


class UNAIDSClient(BaseETLClient):
    source_name = "unaids"

    def build_url(self, indicator: str, **params: Any) -> str:
        raise NotImplementedError("Wire the UNAIDS AIDSinfo bulk export/endpoint here.")

    def parse(self, payload: Any) -> list[dict]:
        raise NotImplementedError


class UNICEFClient(BaseETLClient):
    source_name = "unicef"
    BASE = "https://sdmx.data.unicef.org/ws/public/sdmxapi/rest/data"

    def build_url(self, indicator: str, **params: Any) -> str:
        raise NotImplementedError("Wire the UNICEF SDMX dataflow query here.")

    def parse(self, payload: Any) -> list[dict]:
        raise NotImplementedError


class UNFPAClient(BaseETLClient):
    source_name = "unfpa"

    def build_url(self, indicator: str, **params: Any) -> str:
        raise NotImplementedError("Wire the UNFPA data portal endpoint here.")

    def parse(self, payload: Any) -> list[dict]:
        raise NotImplementedError


class DHIS2Client(BaseETLClient):
    source_name = "dhis2"

    def __init__(self, base_url: str = "", **kw):
        super().__init__(**kw)
        self.base_url = base_url  # instance-specific DHIS2 server

    def build_url(self, indicator: str, **params: Any) -> str:
        if not self.base_url:
            raise NotImplementedError("Set the DHIS2 server base_url and analytics query.")
        return f"{self.base_url}/api/analytics.json?dimension=dx:{indicator}"

    def parse(self, payload: Any) -> list[dict]:
        raise NotImplementedError


CLIENTS = {
    "worldbank": WorldBankClient,
    "who_gho": WHOGhoClient,
    "unaids": UNAIDSClient,
    "unicef": UNICEFClient,
    "unfpa": UNFPAClient,
    "dhis2": DHIS2Client,
}


def get_client(source: str, **kw) -> BaseETLClient:
    if source not in CLIENTS:
        raise KeyError(f"Unknown source '{source}'. Available: {sorted(CLIENTS)}")
    return CLIENTS[source](**kw)
