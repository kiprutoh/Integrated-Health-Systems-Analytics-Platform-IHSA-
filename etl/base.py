"""
Reusable ETL base client (charter Sprint 3).

Provides the common features every source client shares — retries, caching,
pagination, validation and metadata versioning — so concrete clients (WHO GHO,
World Bank, UNAIDS, UNICEF, UNFPA, DHIS2) only implement source-specific URL
building and row parsing.
"""
from __future__ import annotations

import hashlib
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from config.logging_config import get_logger
from config.settings import settings

log = get_logger("etl.base")


@dataclass
class FetchResult:
    source: str
    rows: list[dict]
    fetched_at: str
    version: str
    cache_key: str


class BaseETLClient(ABC):
    """Base class for all source clients."""

    source_name: str = "base"

    def __init__(self, cache_ttl_hours: int | None = None):
        self.cache_ttl = (cache_ttl_hours if cache_ttl_hours is not None
                          else settings.cache_ttl_hours)
        self.cache_dir = Path(settings.cache_dir) / self.source_name
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    # ---- source-specific hooks (implement in subclasses) ------------------ #
    @abstractmethod
    def build_url(self, indicator: str, **params: Any) -> str:
        ...

    @abstractmethod
    def parse(self, payload: Any) -> list[dict]:
        ...

    def validate(self, rows: list[dict]) -> list[dict]:
        """Default validation: drop rows missing a value; override for stricter rules."""
        clean = [r for r in rows if r.get("value") is not None]
        dropped = len(rows) - len(clean)
        if dropped:
            log.warning("%s: dropped %d rows failing validation", self.source_name, dropped)
        return clean

    # ---- shared machinery ------------------------------------------------- #
    def _cache_key(self, url: str) -> str:
        return hashlib.sha256(url.encode()).hexdigest()[:16]

    def _cache_paths(self, key: str) -> tuple[Path, Path]:
        return self.cache_dir / f"{key}.json", self.cache_dir / f"{key}.meta.json"

    def _read_cache(self, key: str) -> list[dict] | None:
        data_p, meta_p = self._cache_paths(key)
        if not data_p.exists() or not meta_p.exists():
            return None
        meta = json.loads(meta_p.read_text())
        age_h = (time.time() - meta["epoch"]) / 3600
        if age_h > self.cache_ttl:
            log.debug("%s cache stale (%.1fh)", self.source_name, age_h)
            return None
        log.debug("%s cache hit (%s)", self.source_name, key)
        return json.loads(data_p.read_text())

    def _write_cache(self, key: str, url: str, rows: list[dict]) -> str:
        version = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        data_p, meta_p = self._cache_paths(key)
        data_p.write_text(json.dumps(rows))
        meta_p.write_text(json.dumps({
            "source": self.source_name, "url": url, "version": version,
            "epoch": time.time(), "n_rows": len(rows),
        }))
        return version

    def _http_get(self, url: str) -> Any:  # pragma: no cover - network
        """GET with exponential-backoff retries. Requires `requests`."""
        import requests
        last = None
        for attempt in range(settings.http_max_retries):
            try:
                resp = requests.get(url, timeout=settings.http_timeout)
                resp.raise_for_status()
                return resp.json()
            except Exception as exc:  # noqa: BLE001
                last = exc
                wait = 2 ** attempt
                log.warning("%s GET failed (attempt %d/%d): %s; retry in %ds",
                            self.source_name, attempt + 1, settings.http_max_retries, exc, wait)
                time.sleep(wait)
        raise RuntimeError(f"{self.source_name} GET failed after retries: {last}")

    def paginate(self, indicator: str, **params: Any) -> Iterable[Any]:  # pragma: no cover
        """Override for paginated sources. Default: single page."""
        yield self._http_get(self.build_url(indicator, **params))

    # ---- public API ------------------------------------------------------- #
    def fetch(self, indicator: str, use_cache: bool = True, **params: Any) -> FetchResult:
        url = self.build_url(indicator, **params)
        key = self._cache_key(url)
        if use_cache:
            cached = self._read_cache(key)
            if cached is not None:
                meta = json.loads(self._cache_paths(key)[1].read_text())
                return FetchResult(self.source_name, cached, meta["version"],
                                   meta["version"], key)
        rows: list[dict] = []
        for page in self.paginate(indicator, **params):  # pragma: no cover
            rows.extend(self.parse(page))
        rows = self.validate(rows)
        version = self._write_cache(key, url, rows)
        return FetchResult(self.source_name, rows,
                           datetime.now(timezone.utc).isoformat(), version, key)
