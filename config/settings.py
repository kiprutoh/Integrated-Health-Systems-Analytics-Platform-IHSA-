"""
IHSA central configuration.

Uses pydantic-settings when available (12-factor, env-driven). Falls back to a
lightweight dataclass reading os.environ so the platform still imports in minimal
environments. All paths are resolved relative to the repository root, so code
works regardless of the current working directory.
"""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
REFERENCE_DIR = DATA_DIR / "reference"
CACHE_DIR = DATA_DIR / "cache"
WAREHOUSE_DIR = ROOT / "warehouse"

APP_NAME = "Integrated Health Systems Analytics Platform"
APP_SHORT = "IHSA"
VERSION = "0.1.0"

try:  # preferred: pydantic-settings
    from pydantic_settings import BaseSettings, SettingsConfigDict

    class Settings(BaseSettings):
        model_config = SettingsConfigDict(env_prefix="IHSA_", env_file=".env", extra="ignore")

        app_name: str = APP_NAME
        version: str = VERSION
        environment: str = "development"
        log_level: str = "INFO"
        log_json: bool = False

        # data / cache
        data_dir: Path = DATA_DIR
        reference_dir: Path = REFERENCE_DIR
        cache_dir: Path = CACHE_DIR
        cache_ttl_hours: int = 24

        # ETL
        http_timeout: int = 30
        http_max_retries: int = 4

        # api / auth (Phase D placeholders)
        api_host: str = "0.0.0.0"
        api_port: int = 8000
        auth_enabled: bool = False

    settings = Settings()

except Exception:  # pragma: no cover - fallback path
    from dataclasses import dataclass

    def _b(name: str, default: bool) -> bool:
        return os.getenv(name, str(default)).lower() in {"1", "true", "yes", "on"}

    @dataclass
    class Settings:  # type: ignore[no-redef]
        app_name: str = os.getenv("IHSA_APP_NAME", APP_NAME)
        version: str = VERSION
        environment: str = os.getenv("IHSA_ENVIRONMENT", "development")
        log_level: str = os.getenv("IHSA_LOG_LEVEL", "INFO")
        log_json: bool = _b("IHSA_LOG_JSON", False)
        data_dir: Path = DATA_DIR
        reference_dir: Path = REFERENCE_DIR
        cache_dir: Path = CACHE_DIR
        cache_ttl_hours: int = int(os.getenv("IHSA_CACHE_TTL_HOURS", "24"))
        http_timeout: int = int(os.getenv("IHSA_HTTP_TIMEOUT", "30"))
        http_max_retries: int = int(os.getenv("IHSA_HTTP_MAX_RETRIES", "4"))
        api_host: str = os.getenv("IHSA_API_HOST", "0.0.0.0")
        api_port: int = int(os.getenv("IHSA_API_PORT", "8000"))
        auth_enabled: bool = _b("IHSA_AUTH_ENABLED", False)

    settings = Settings()


def ensure_dirs() -> None:
    for d in (settings.data_dir, settings.reference_dir, settings.cache_dir):
        Path(d).mkdir(parents=True, exist_ok=True)
