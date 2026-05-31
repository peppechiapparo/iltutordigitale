"""Centralized configuration loaded from environment / .env."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings — loaded once at startup."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Target site
    site_url: str = "https://www.scuolakungfucipriani.it/"
    site_name: str = "Scuola Kung Fu Maestro Cipriani"
    site_instagram_handle: str = "scuolacipriani"

    # Runtime
    shan_env: Literal["development", "production"] = "production"
    shan_log_level: str = "INFO"
    shan_timezone: str = "Europe/Rome"
    shan_data_dir: Path = Path("/app/data")

    # API
    shan_api_host: str = "0.0.0.0"  # noqa: S104
    shan_api_port: int = 8765
    shan_api_token: str = ""

    # LLM
    llm_provider: Literal["anthropic", "openai", "github_models"] = "anthropic"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    # GitHub Models (github.com/marketplace/models — usa il tuo GitHub PAT)
    github_token: str = ""
    github_model: str = "gpt-4.1"

    # Telegram
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # Google Search Console
    gsc_service_account_json: Path = Path("/app/secrets/gsc-sa.json")
    gsc_site_property: str = ""

    # PageSpeed
    pagespeed_api_key: str = ""

    # Instagram
    ig_user_id: str = ""
    ig_access_token: str = ""
    ig_app_id: str = ""
    ig_app_secret: str = ""

    # IndexNow
    indexnow_key: str = ""

    # Derived
    @property
    def db_path(self) -> Path:
        return self.shan_data_dir / "shan.db"

    @property
    def reports_dir(self) -> Path:
        return self.shan_data_dir / "reports"

    def ensure_dirs(self) -> None:
        self.shan_data_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
