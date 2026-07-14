from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_int_list(value: str) -> list[int]:
    """Parse a comma-separated string of integers; empty strings become empty lists."""
    if not value or not value.strip():
        return []
    return [int(item.strip()) for item in value.split(",")]


class Settings(BaseSettings):
    """Application configuration loaded from environment variables and .env file.

    List values are read as comma-separated strings and exposed as typed lists
    through read-only properties, avoiding non-intuitive JSON parsing in .env files.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    bot_token: str
    admin_ids_str: str = Field("", alias="ADMIN_IDS")
    database_path: str = "data/appointments.db"
    slot_duration_minutes: int = 30
    timezone: str = "UTC"
    working_hours_start: str = "09:00"
    working_hours_end: str = "18:00"
    working_days_str: str = "0,1,2,3,4"
    default_language: str = "en"
    log_level: str = "INFO"
    min_booking_individuals: int = 1
    max_booking_individuals: int = 10
    admin_retention_days: int = 7
    user_retention_days: int = 14

    @property
    def admin_ids(self) -> list[int]:
        return _parse_int_list(self.admin_ids_str)

    @property
    def working_days(self) -> list[int]:
        return _parse_int_list(self.working_days_str)

    @property
    def database_url(self) -> str:
        """Return an async SQLAlchemy SQLite URL and ensure the parent directory exists."""
        path = Path(self.database_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite+aiosqlite:///{path}"


settings = Settings()


def app_timezone() -> ZoneInfo:
    """Return the configured timezone, falling back to UTC on invalid values."""
    try:
        return ZoneInfo(settings.timezone)
    except (ZoneInfoNotFoundError, ValueError, KeyError):
        return ZoneInfo("UTC")


def today_in_tz() -> date:
    """Return the current date in the configured business timezone."""
    return datetime.now(app_timezone()).date()