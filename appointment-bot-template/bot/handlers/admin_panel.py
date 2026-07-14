from __future__ import annotations

from pathlib import Path
import tempfile

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from bot.config import settings, today_in_tz
from bot.database.models import Appointment, AppointmentStatus
from bot.database.connection import AsyncSessionLocal as session_factory
from bot.locales.messages import t
from bot.services.import_service import ImportError, import_services_from_rows, parse_services_spreadsheet
from bot.utils.keyboards import build_admin_booking_actions


def is_admin(user_id: int) -> bool:
    return user_id in settings.admin_ids


def build_admin_keyboard(language: str | None) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(t("admin_today", language), callback_data="admin:view_today")],
        [InlineKeyboardButton(t("admin_upcoming", language), callback_data="admin:view_upcoming")],
    ]
    return InlineKeyboardMarkup(keyboard)


async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user or not is_admin(user.id):
        await update.message.reply_text(t("not_authorized", user.language_code if user else None))
        return

    language = user.language_code if user else None
    await update.message.reply_text(
        t("admin_menu", language),
        reply_markup=build_admin_keyboard(language),
    )


async def view_bookings_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    if not user or not is_admin(user.id):
        await query.edit_message_text(t("not_authorized", user.language_code if user else None))
        return

    language = user.language_code if user else None
    selection = query.data

    async with session_factory() as session:
        stmt = (
            select(Appointment)
            .where(Appointment.status != AppointmentStatus.CANCELLED.value)
            .options(
                selectinload(Appointment.user),
                selectinload(Appointment.service),
            )
        )

        if selection == "admin:view_today":
            stmt = stmt.where(Appointment.appointment_date == today_in_tz())
        elif selection == "admin:view_upcoming":
            stmt = stmt.where(Appointment.appointment_date >= today_in_tz())
        else:
            await query.edit_message_text(t("invalid_input", language))
            return

        result = await session.execute(stmt.order_by(Appointment.appointment_date, Appointment.start_time))
        appointments = result.scalars().all()

    if not appointments:
        await query.edit_message_text(t("no_bookings", language))
        return

    await query.edit_message_text(t("admin_found_bookings", language).format(count=len(appointments)))

    for index, appointment in enumerate(appointments, start=1):
        name = appointment.user.full_name or f"User {appointment.user.telegram_id}"
        message = (
            f"{t('admin_daily_index', language).format(index=index)}\n"
            f"{t('admin_card_client', language)}: {name} ({appointment.user.phone_number or 'N/A'})\n"
            f"{t('admin_card_service', language)}: {appointment.service.title}\n"
            f"{t('admin_card_individuals', language)}: {appointment.individuals_count}\n"
            f"{t('admin_card_schedule', language)}: "
            f"{appointment.appointment_date.strftime('%Y-%m-%d')} | "
            f"{appointment.start_time.strftime('%H:%M')} - {appointment.end_time.strftime('%H:%M')}"
        )
        
        await query.message.reply_text(
            message,
            parse_mode=ParseMode.HTML,
            reply_markup=build_admin_booking_actions(appointment.id, language),
        )


async def admin_cancel_booking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    if not user or not is_admin(user.id):
        await query.edit_message_text(t("not_authorized", user.language_code if user else None))
        return

    language = user.language_code if user else None

    try:
        appointment_id = int(query.data.split(":")[2])
    except (IndexError, ValueError):
        await query.edit_message_text(t("invalid_input", language))
        return

    async with session_factory() as session:
        result = await session.execute(select(Appointment).where(Appointment.id == appointment_id))
        appointment = result.scalars().first()

        if not appointment:
            await query.edit_message_text(t("no_bookings", language))
            return

        appointment.status = AppointmentStatus.CANCELLED.value
        await session.commit()

    await query.edit_message_text(t("appointment_cancelled", language))


async def import_services_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Receive an .xlsx or .csv file from an admin and bulk-import services."""
    user = update.effective_user
    language = user.language_code if user else None
    if not user or not is_admin(user.id):
        await update.message.reply_text(t("not_authorized", language))
        return

    document = update.message.document
    file_name = (document.file_name or "").lower()
    if not file_name.endswith((".xlsx", ".xls", ".csv")):
        await update.message.reply_text(t("import_invalid_format", language))
        return

    file_obj = await context.bot.get_file(document.file_id)
    suffix = Path(file_name).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp_path = Path(tmp.name)
    await file_obj.download_to_drive(tmp_path)

    try:
        rows = parse_services_spreadsheet(tmp_path)
        async with session_factory() as session:
            stats = await import_services_from_rows(session, rows)
        await update.message.reply_text(
            t("import_success", language).format(
                created=stats["created"],
                updated=stats["updated"],
            )
        )
    except ImportError as exc:
        await update.message.reply_text(
            t("import_error", language).format(error=str(exc))
        )
    except Exception as exc:  # pragma: no cover - defensive catch for unexpected parser errors
        await update.message.reply_text(
            t("import_error", language).format(error=str(exc))
        )
    finally:
        tmp_path.unlink(missing_ok=True)


admin_menu_handler = CommandHandler("admin", admin_menu)
view_bookings_handler = CallbackQueryHandler(view_bookings_list, pattern="^admin:(view_today|view_upcoming)$")
cancel_booking_handler = CallbackQueryHandler(admin_cancel_booking, pattern="^admin:cancel:")
import_services_handler = MessageHandler(
    filters.Document.FileExtension("xlsx") | filters.Document.FileExtension("csv") | filters.Document.FileExtension("xls"),
    import_services_document,
)

__all__ = [
    "admin_menu_handler",
    "view_bookings_handler",
    "cancel_booking_handler",
    "import_services_handler",
]
