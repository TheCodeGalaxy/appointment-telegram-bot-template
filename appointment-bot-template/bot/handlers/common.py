from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes, ConversationHandler

from bot.config import settings, today_in_tz
from bot.database.connection import AsyncSessionLocal as session_factory
from bot.database.models import Appointment, User
from bot.locales.messages import t


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    language = user.language_code if user else None

    keyboard = [
        [InlineKeyboardButton(t("book_button", language), callback_data="start_booking")],
        [InlineKeyboardButton(t("my_appointments_button", language), callback_data="view_appointments")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(t("welcome", language), reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(t("welcome", language), reply_markup=reply_markup)


async def view_appointments(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the user's upcoming appointments."""
    query = update.callback_query
    await query.answer()

    effective_user = update.effective_user
    language = effective_user.language_code if effective_user else None

    async with session_factory() as session:
        user_record = await session.execute(
            select(User).where(User.telegram_id == effective_user.id)
        )
        user_record = user_record.scalars().first()

        if not user_record:
            await query.edit_message_text(t("no_bookings", language))
            return

        retention_cutoff = today_in_tz() - timedelta(days=settings.user_retention_days)
        result = await session.execute(
            select(Appointment)
            .where(Appointment.user_id == user_record.id)
            .where(Appointment.appointment_date >= retention_cutoff)
            .options(selectinload(Appointment.service))
            .order_by(Appointment.appointment_date, Appointment.start_time)
        )
        appointments = result.scalars().all()

    if not appointments:
        await query.edit_message_text(t("no_bookings", language))
        return

    # تم استبدال النص الثابت بدالة الترجمة هنا لمنع المشكلة تماماً
    message = f"{t('my_appointments_title', language)}\n\n"
    for appointment in appointments:
        message += (
            f"🛠️ {appointment.service.title}\n"
            f"📅 {appointment.appointment_date}\n"
            f"🕒 {appointment.start_time} - {appointment.end_time}\n\n"
        )
    await query.edit_message_text(message)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    language = user.language_code if user else settings.default_language
    
    # التأكد من جلب صيغة لغة ثنائية (مثل ar أو en) لملف المساعدة
    lang_code = language[:2] if language else "en"
    help_file = f"HELP_{lang_code}.md"
    
    try:
        with open(help_file, "r", encoding="utf-8") as f:
            content = f.read()
        if len(content) > 4096:
            content = content[:4000] + "\n\n... (truncated)"
    except FileNotFoundError:
        content = f"📄 {help_file} not found. Please check the installation."

    if update.message:
        await update.message.reply_text(content)
    elif update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(content)


async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    language = user.language_code if user else None

    context.user_data.clear()
    text = t("booking_cancelled", language)

    if update.message:
        await update.message.reply_text(text)
    elif update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text)

    return ConversationHandler.END


start_handler = CommandHandler("start", start)
help_handler = CommandHandler("help", help_command)
cancel_handler = CommandHandler("cancel", cancel_conversation)
view_appointments_handler = CallbackQueryHandler(view_appointments, pattern="^view_appointments$")

__all__ = [
    "start_handler",
    "help_handler",
    "cancel_handler",
    "view_appointments_handler",
    "start",
    "help_command",
    "cancel_conversation",
    "view_appointments",
]