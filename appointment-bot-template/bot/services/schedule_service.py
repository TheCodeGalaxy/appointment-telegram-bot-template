from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Sequence

from bot.config import settings, today_in_tz
from bot.database.models import Appointment, AppointmentStatus, BlockedSlot, Service
from bot.locales.messages import MONTHS_AR, WEEKDAYS_AR

class ScheduleError(Exception):
    """Raised for domain-specific scheduling failures."""

@dataclass(frozen=True)
class ScheduleConfig:
    """Configuration for working hours and slot generation."""
    start: time
    end: time
    working_days: tuple[int, ...]
    default_slot_duration_minutes: int

    def __post_init__(self):
        if self.start >= self.end:
            raise ScheduleError("Working hours start must be earlier than end.")

def default_schedule_config() -> ScheduleConfig:
    """Create a ScheduleConfig from application settings."""
    return ScheduleConfig(
        start=_parse_time(settings.working_hours_start),
        end=_parse_time(settings.working_hours_end),
        working_days=tuple(settings.working_days),
        default_slot_duration_minutes=settings.slot_duration_minutes,
    )

def _parse_time(value: str) -> time:
    """Parse a time string in HH:MM format."""
    return datetime.strptime(value, "%H:%M").time()

def _time_to_minutes(t: time) -> int:
    """Convert a time object to total minutes since midnight."""
    return t.hour * 60 + t.minute

def _minutes_to_time(minutes: int) -> time:
    """Convert minutes since midnight to a time object."""
    return time(minutes // 60, minutes % 60)

def is_working_day(day: date, config: ScheduleConfig | None = None) -> bool:
    """Check if the given date is a working day."""
    if config is None:
        config = default_schedule_config()
    return day.weekday() in config.working_days

def generate_time_slots(
    day: date,
    service: Service,
    existing_appointments: Sequence[Appointment],
    blocked_slots: Sequence[BlockedSlot] | None = None,
    config: ScheduleConfig | None = None,
) -> list[time]:
    """Generate available time slots for a given day and service."""
    if config is None:
        config = default_schedule_config()

    if not is_working_day(day, config):
        return []

    slot_duration = service.duration_minutes or config.default_slot_duration_minutes
    start_min = _time_to_minutes(config.start)
    end_min = _time_to_minutes(config.end)

    busy_ranges = []
    for appointment in existing_appointments:
        if appointment.status != AppointmentStatus.CANCELLED.value:
            busy_ranges.append(
                (
                    _time_to_minutes(appointment.start_time),
                    _time_to_minutes(appointment.end_time),
                )
            )

    if blocked_slots:
        for slot in blocked_slots:
            busy_ranges.append(
                (
                    _time_to_minutes(slot.start_time),
                    _time_to_minutes(slot.end_time),
                )
            )

    available_slots = []
    current = start_min

    while current + slot_duration <= end_min:
        slot_start = current
        slot_end = current + slot_duration
        is_available = True

        for b_start, b_end in busy_ranges:
            if max(slot_start, b_start) < min(slot_end, b_end):
                is_available = False
                break

        if is_available:
            available_slots.append(_minutes_to_time(current))

        current += config.default_slot_duration_minutes

    return available_slots

def calculate_end_time(start: time, duration_minutes: int) -> time:
    """Calculate the end time given a start time and duration in minutes."""
    start_min = _time_to_minutes(start)
    end_min = start_min + duration_minutes
    return _minutes_to_time(end_min)

def generate_date_range(days: int = 14) -> list[date]:
    """Generate a list of dates starting from today (business timezone)."""
    today = today_in_tz()
    return [today + timedelta(days=i) for i in range(days)]

def generate_working_date_range(days: int = 14, config: ScheduleConfig | None = None) -> list[date]:
    """Generate a list of working dates starting from today."""
    if config is None:
        config = default_schedule_config()

    date_range = generate_date_range(days)
    return [d for d in date_range if is_working_day(d, config)]

def format_time_24h(t: time) -> str:
    """Format a time object as a 24-hour time string (HH:MM)."""
    return t.strftime("%H:%M")

def format_date_long(d: date, language: str | None = None) -> str:
    """Format a date object as a long-form string (e.g., 'Monday, 01 January 2024')."""
    if language is None:
        language = settings.default_language

    normalized_lang = language[:2]

    for lang in (settings.default_language, normalized_lang, "en"):
        if lang == "ar":
            wd = WEEKDAYS_AR[d.weekday()]
            mo = MONTHS_AR[d.month]
            return f"{wd}، {d.day:02d} {mo} {d.year}"

    return d.strftime("%A, %d %B %Y")