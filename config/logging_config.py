"""Shared logging configuration for the whole platform.

Call `configure_logging()` once at process start (Streamlit app, API, ETL jobs).
Use `get_logger(__name__)` everywhere else. Supports plain or JSON output.
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone

from config.settings import settings

_CONFIGURED = False


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def configure_logging(level: str | None = None) -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    handler = logging.StreamHandler(sys.stdout)
    if settings.log_json:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"))
    root = logging.getLogger("ihsa")
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level or settings.log_level)
    root.propagate = False
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(f"ihsa.{name}")
