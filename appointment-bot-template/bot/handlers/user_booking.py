from __future__ import annotations

from datetime import date, time

from sqlalchemy import select
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from bot.database.models import Appointment
from bot.database.connection import AsyncSessionLocal as session_factory
from bot.handlers.common import cancel_conversation
from bot.config import settings
from bot.locales.messages import t
from bot.services.booking_service import (
    BookingError,
    SlotAlreadyBookedError,
    create_booking,
    get_blocked_slots_for_date,
    get_service,
    get_user_by_telegram_id,
    list_active_services,
)
from bot.services.schedule_service import (
    calculate_end_time,
    format_date_long,
    format_time_24h,
    generate_time_slots,
    generate_working_date_range,
)
from bot.utils.fsm_states import BookingState
from bot.utils.validators import ValidationError, validate_name, validate_phone


def build_services_keyboard(services: list, language: str | None) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(service.title, callback_data=f"service:{service.id}")]
        for service in services
    ]
    return InlineKeyboardMarkup(keyboard)


def build_dates_keyboard(dates: list[date], language: str | None) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(format_date_long(d, language), callback_data=f"date:{d.isoformat()}")]
        for d in dates
    ]
    return InlineKeyboardMarkup(keyboard)


def build_slots_keyboard(slots: list[str], language: str | None) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(slot, callback_data=f"slot:{slot}")]
        for slot in slots
    ]
    return InlineKeyboardMarkup(keyboard)


def build_confirm_keyboard(language: str | None) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(t("confirm", language), callback_data="booking:confirm"),
            InlineKeyboardButton(t("cancel", language), callback_data="booking:cancel"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def _has_complete_profile(user) -> bool:
    """Return True when the stored user has a non-empty full name and phone number."""
    return bool(user and user.full_name and user.phone_number)


def _format_confirmation_summary(
    service,
    selected_date: date,
    start_time: time,
    language: str | None,
    individuals_count: int = 1,
) -> str:
    end_time = calculate_end_time(start_time, service.duration_minutes)
    return t("booking_summary", language).format(
        service=service.title,
        date=format_date_long(selected_date, language),
        time=format_time_24h(start_time),
        end_time=format_time_24h(end_time),
        duration=service.duration_minutes,
        individuals_count=individuals_count,
    )


async def start_booking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the booking flow by listing available services."""
    user = update.effective_user
    language = user.language_code if user else None

    # Handle callback_query or message
    if update.callback_query:
        await update.callback_query.answer()
        reply = update.callback_query.edit_message_text
    elif update.message:
        reply = update.message.reply_text
    else:
        return ConversationHandler.END

    async with session_factory() as session:
        services = await list_active_services(session)

    if not services:
        await reply(
            t("no_services", language),
            reply_markup=None
        )
        return ConversationHandler.END

    await reply(
        t("select_service", language),
        reply_markup=build_services_keyboard(services, language)
    )
    return BookingState.SELECT_SERVICE


async def handle_service_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    language = update.effective_user.language_code if update.effective_user else None

    service_id = int(query.data.split(":")[1])
    context.user_data["service_id"] = service_id

    await query.edit_message_text(t("select_individuals", language))
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=t("enter_individuals", language).format(
            min=settings.min_booking_individuals,
            max=settings.max_booking_individuals,
        ),
        reply_markup=ReplyKeyboardRemove(),
    )
    return BookingState.SELECT_PATIENTS


async def handle_individuals_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    language = update.effective_user.language_code if update.effective_user else None
    min_count = settings.min_booking_individuals
    max_count = settings.max_booking_individuals

    try:
        count = int(text)
    except ValueError:
        await update.message.reply_text(
            t("invalid_individuals", language).format(min=min_count, max=max_count)
        )
        return BookingState.SELECT_PATIENTS

    if count < min_count or count > max_count:
        await update.message.reply_text(
            t("invalid_individuals", language).format(min=min_count, max=max_count)
        )
        return BookingState.SELECT_PATIENTS

    context.user_data["individuals_count"] = count

    working_dates = generate_working_date_range(days=14)
    await update.message.reply_text(
        t("select_date", language),
        reply_markup=build_dates_keyboard(working_dates, language),
    )
    return BookingState.SELECT_DATE


async def handle_date_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    language = update.effective_user.language_code if update.effective_user else None

    selected_date = date.fromisoformat(query.data.split(":")[1])
    service_id = context.user_data["service_id"]

    async with session_factory() as session:
        service = await get_service(session, service_id)
        if not service:
            await query.edit_message_text(t("service_unavailable", language))
            return ConversationHandler.END

        result = await session.execute(
            select(Appointment).where(
                Appointment.appointment_date == selected_date,
                Appointment.service_id == service_id,
            )
        )
        existing_appointments = result.scalars().all()
        blocked_slots = await get_blocked_slots_for_date(session, selected_date)

    available_slots = generate_time_slots(
        day=selected_date,
        service=service,
        existing_appointments=existing_appointments,
        blocked_slots=blocked_slots,
    )

    if not available_slots:
        await query.edit_message_text(t("no_slots", language))
        return ConversationHandler.END

    formatted_slots = [format_time_24h(t) for t in available_slots]
    context.user_data["slots"] = formatted_slots
    context.user_data["date"] = selected_date

    await query.edit_message_text(
        t("select_time", language).format(slot=""),
        reply_markup=build_slots_keyboard(formatted_slots, language),
    )
    return BookingState.SELECT_TIME


async def _show_confirmation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    language: str | None,
) -> int:
    """Render the confirmation summary and transition to CONFIRM state."""
    service_id = context.user_data["service_id"]
    selected_date = context.user_data["date"]
    start_time = context.user_data["start_time"]
    individuals_count = context.user_data.get("individuals_count", 1)

    async with session_factory() as session:
        service = await get_service(session, service_id)
    if not service:
        if update.message:
            await update.message.reply_text(t("service_unavailable", language))
        elif update.callback_query:
            await update.callback_query.edit_message_text(t("service_unavailable", language))
        return ConversationHandler.END

    summary = _format_confirmation_summary(
        service,
        selected_date,
        start_time,
        language,
        individuals_count,
    )

    if update.message:
        await update.message.reply_text(
            summary,
            reply_markup=build_confirm_keyboard(language),
        )
    elif update.callback_query:
        await update.callback_query.edit_message_text(
            summary,
            reply_markup=build_confirm_keyboard(language),
        )

    return BookingState.CONFIRM


async def handle_time_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    language = update.effective_user.language_code if update.effective_user else None

    selected_slot = query.data.split(":", 1)[1]
    if selected_slot not in context.user_data.get("slots", []):
        await query.edit_message_text(t("invalid_input", language))
        return BookingState.SELECT_TIME

    selected_time = time.fromisoformat(selected_slot)
    context.user_data["start_time"] = selected_time

    user_id = update.effective_user.id if update.effective_user else None
    fast_track_user = None
    if user_id is not None:
        async with session_factory() as session:
            fast_track_user = await get_user_by_telegram_id(session, user_id)

    if _has_complete_profile(fast_track_user):
        context.user_data["name"] = fast_track_user.full_name
        context.user_data["phone"] = fast_track_user.phone_number
        return await _show_confirmation(update, context, language)

    await query.edit_message_text(
        t("select_time", language).format(slot=f"({selected_slot})"),
        reply_markup=None
    )

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=t("enter_name", language),
        reply_markup=ReplyKeyboardRemove(),
    )

    return BookingState.COLLECT_NAME


async def handle_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    language = update.effective_user.language_code if update.effective_user else None

    try:
        name = validate_name(text)
        context.user_data["name"] = name
        await update.message.reply_text(t("enter_phone", language))
        return BookingState.COLLECT_PHONE
    except ValidationError as e:
        await update.message.reply_text(str(e))
        return BookingState.COLLECT_NAME


async def handle_phone_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    language = update.effective_user.language_code if update.effective_user else None

    try:
        phone = validate_phone(text)
        context.user_data["phone"] = phone
        return await _show_confirmation(update, context, language)
    except ValidationError as e:
        await update.message.reply_text(str(e))
        return BookingState.COLLECT_PHONE


async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    language = update.effective_user.language_code if update.effective_user else None

    if query.data == "booking:cancel":
        await query.edit_message_text(t("booking_cancelled", language))
        context.user_data.clear()
        return ConversationHandler.END

    if update.effective_user is None:
        await query.edit_message_text(t("invalid_input", language))
        return ConversationHandler.END

    user_id = update.effective_user.id
    service_id = context.user_data["service_id"]
    selected_date = context.user_data["date"]
    start_time = context.user_data["start_time"]
    full_name = context.user_data.get("name")
    phone_number = context.user_data.get("phone")
    individuals_count = context.user_data.get("individuals_count", 1)

    try:
        async with session_factory() as session:
            appointment = await create_booking(
                session=session,
                telegram_id=user_id,
                service_id=service_id,
                appointment_date=selected_date,
                start_time=start_time,
                full_name=full_name,
                phone_number=phone_number,
                language_code=language,
                individuals_count=individuals_count,
            )

        summary = t("booking_confirmed", language).format(
            service=appointment.service.title,
            date=format_date_long(appointment.appointment_date, language),
            time=format_time_24h(appointment.start_time),
            end_time=format_time_24h(appointment.end_time),
            duration=appointment.service.duration_minutes,
            individuals_count=appointment.individuals_count,
        )
        await query.edit_message_text(summary)

    except SlotAlreadyBookedError:
        await query.edit_message_text(t("slot_taken", language))
    except BookingError as e:
        await query.edit_message_text(str(e))
    finally:
        context.user_data.clear()

    return ConversationHandler.END


async def booking_fallback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    language = update.effective_user.language_code if update.effective_user else None
    if update.message:
        await update.message.reply_text(t("invalid_input", language))
    elif update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(t("invalid_input", language))
    return ConversationHandler.END


conversation_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_booking, pattern="^start_booking$")],
    states={
        BookingState.SELECT_SERVICE: [
            CallbackQueryHandler(handle_service_selection, pattern="^service:"),
        ],
        BookingState.SELECT_PATIENTS: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_individuals_input),
        ],
        BookingState.SELECT_DATE: [
            CallbackQueryHandler(handle_date_selection, pattern="^date:"),
        ],
        BookingState.SELECT_TIME: [
            CallbackQueryHandler(handle_time_selection, pattern="^slot:"),
        ],
        BookingState.COLLECT_NAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name_input),
        ],
        BookingState.COLLECT_PHONE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone_input),
        ],
        BookingState.CONFIRM: [
            CallbackQueryHandler(handle_confirmation, pattern="^booking:"),
        ],
    },
    fallbacks=[
        CommandHandler("cancel", cancel_conversation),
        MessageHandler(filters.TEXT & ~filters.COMMAND, booking_fallback),
    ],
    allow_reentry=True,
)
__all__ = [
    "conversation_handler",
]