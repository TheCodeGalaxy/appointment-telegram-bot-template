from __future__ import annotations

import re
from datetime import date, datetime, time

from bot.config import settings


class ValidationError(ValueError):
    """Raised when user input does not match expected format or rules."""


def validate_name(text: str) -> str:
    """Return stripped name if it looks like a real name (2-100 chars, no digits)."""
    cleaned = text.strip()
    if len(cleaned) < 2 or len(cleaned) > 100:
        raise ValidationError("Name must be between 2 and 100 characters.")
    if re.search(r"\d", cleaned):
        raise ValidationError("Name should not contain numbers.")
    return cleaned


PHONE_PATTERN = re.compile(r"^(\+?[0-9\-\s()]{7,20})$")


def validate_phone(text: str) -> str:
    """Return normalized phone number if valid."""
    cleaned = text.strip()
    if not PHONE_PATTERN.match(cleaned):
        raise ValidationError("Please send a valid phone number.")
    normalized = re.sub(r"[\s()-]", "", cleaned)
    return normalized


def validate_date_text(text: str) -> date:
    """Parse YYYY-MM-DD and ensure the date is not in the past."""
    try:
        parsed = datetime.strptime(text.strip(), "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValidationError("Use the format YYYY-MM-DD, e.g. 2026-07-25.") from exc

    if parsed < date.today():
        raise ValidationError("You cannot book an appointment in the past.")
    return parsed


def validate_time_text(text: str) -> time:
    """Parse HH:MM 24-hour time."""
    try:
        return datetime.strptime(text.strip(), "%H:%M").time()
    except ValueError as exc:
        raise ValidationError("Use the format HH:MM, e.g. 14:30.") from exc


def is_admin(telegram_id: int) -> bool:
    return telegram_id in settings.admin_ids
