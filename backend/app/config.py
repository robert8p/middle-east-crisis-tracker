from __future__ import annotations

from functools import lru_cache
from typing import Dict

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_base_url: str = "http://127.0.0.1:8000"
    app_admin_token: str = "change-me"
    app_database_url: str = "sqlite:///./mect.db"
    app_refresh_interval_minutes: int = 15
    app_source_timeout_seconds: int = 12
    app_fetch_user_agent: str = "MiddleEastCrisisTracker/1.0 (+https://example.com)"
    app_enable_background_refresh: bool = True
    app_max_items_per_source: int = 25
    app_event_lookback_hours: int = 48
    app_source_enabled_overrides: str = ""
    app_export_default_format: str = "json"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("app_export_default_format")
    @classmethod
    def validate_export_format(cls, value: str) -> str:
        if value not in {"json", "csv"}:
            raise ValueError("APP_EXPORT_DEFAULT_FORMAT must be json or csv")
        return value

    def enabled_overrides(self) -> Dict[str, bool]:
        overrides: Dict[str, bool] = {}
        raw = (self.app_source_enabled_overrides or "").strip()
        if not raw:
            return overrides
        for pair in raw.split(","):
            if "=" not in pair:
                continue
            key, value = pair.split("=", 1)
            overrides[key.strip()] = value.strip() in {"1", "true", "yes", "on"}
        return overrides


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()