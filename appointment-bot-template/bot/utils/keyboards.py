from __future__ import annotations

from datetime import date, time

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from bot.locales.messages import t
from bot.services.schedule_service import format_date_long, format_time_24h


def build_services_keyboard(services: list) -> InlineKeyboardMarkup:
    """Inline buttons for selecting a bookable service."""
    buttons = [
        [InlineKeyboardButton(service.title, callback_data=f"service:{service.id}")]
        for service in services
    ]
    return InlineKeyboardMarkup(buttons)


def build_dates_keyboard(dates: list[date], language: str | None = None) -> InlineKeyboardMarkup:
    """Inline buttons for selecting a date."""
    buttons = [
        [InlineKeyboardButton(format_date_long(d, language), callback_data=f"date:{d.isoformat()}")]
        for d in dates
    ]
    return InlineKeyboardMarkup(buttons)


def build_slots_keyboard(slots: list[time], language: str | None = None) -> InlineKeyboardMarkup:
    """Inline buttons arranged two per row for selecting a time slot."""
    row: list[InlineKeyboardButton] = []
    rows: list[list[InlineKeyboardButton]] = []
    for slot in slots:
        row.append(InlineKeyboardButton(format_time_24h(slot), callback_data=f"slot:{format_time_24h(slot)}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(rows)


def build_confirm_keyboard(language: str | None = None) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(t("confirm", language), callback_data="booking:confirm"),
                InlineKeyboardButton(t("cancel", language), callback_data="booking:cancel"),
            ]
        ]
    )


def build_admin_booking_actions(appointment_id: int, language: str | None = None) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    t("cancel_appointment", language),
                    callback_data=f"admin:cancel:{appointment_id}",
                )
            ]
        ]
    )
