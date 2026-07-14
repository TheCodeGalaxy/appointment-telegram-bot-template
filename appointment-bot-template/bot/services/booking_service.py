from __future__ import annotations

from datetime import date as dt_date, time
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.database.models import Appointment, AppointmentStatus, BlockedSlot, Service, User
from bot.services.schedule_service import calculate_end_time, default_schedule_config, is_working_day


class BookingError(Exception):
    """Base exception for booking-related errors."""


class SlotAlreadyBookedError(BookingError):
    """Raised when attempting to book an already occupied time slot."""


class InvalidBookingTimeError(BookingError):
    """Raised when the booking time is invalid or outside working hours."""


async def get_user_by_telegram_id(
    session: AsyncSession, telegram_id: int
) -> User | None:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalars().first()


async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    full_name: str | None = None,
    phone_number: str | None = None,
    language_code: str | None = None,
) -> User:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalars().first()

    if user is None:
        user = User(
            telegram_id=telegram_id,
            full_name=full_name,
            phone_number=phone_number,
            language_code=language_code,
        )
        session.add(user)
        await session.flush()
        await session.refresh(user)
    else:
        if full_name and user.full_name != full_name:
            user.full_name = full_name
        if phone_number and user.phone_number != phone_number:
            user.phone_number = phone_number
        if language_code and user.language_code != language_code:
            user.language_code = language_code

    return user


async def create_booking(
    session: AsyncSession,
    telegram_id: int,
    service_id: int,
    appointment_date: dt_date,
    start_time: time,
    full_name: str | None = None,
    phone_number: str | None = None,
    language_code: str | None = None,
    config=None,
    individuals_count: int = 1,
) -> Appointment:
    if config is None:
        config = default_schedule_config()

    if not is_working_day(appointment_date, config) or not (
        config.start <= start_time < config.end
    ):
        raise InvalidBookingTimeError("Booking time is invalid or outside working hours.")

    service_result = await session.execute(select(Service).where(Service.id == service_id))
    service = service_result.scalars().first()
    if service is None:
        raise BookingError("Selected service does not exist.")

    end_time = calculate_end_time(start_time, service.duration_minutes)
    if end_time > config.end:
        raise InvalidBookingTimeError(
            "Booking ends after working hours. Please choose an earlier time."
        )
    user = await get_or_create_user(
        session,
        telegram_id=telegram_id,
        full_name=full_name,
        phone_number=phone_number,
        language_code=language_code,
    )

    try:
        appointment = Appointment(
            user_id=user.id,
            service_id=service_id,
            appointment_date=appointment_date,
            start_time=start_time,
            end_time=end_time,
            status=AppointmentStatus.SCHEDULED.value,
            individuals_count=individuals_count,
        )
        session.add(appointment)
        await session.commit()
        await session.refresh(appointment, attribute_names=["user", "service"])
        return appointment

    except IntegrityError as exc:
        await session.rollback()
        raise SlotAlreadyBookedError(
            "This slot was just booked by someone else. Please choose another time."
        ) from exc
        

async def cancel_booking(session: AsyncSession, appointment_id: int) -> Appointment:
    result = await session.execute(select(Appointment).where(Appointment.id == appointment_id))
    appointment = result.scalars().first()

    if appointment is None:
        raise BookingError("Appointment not found.")

    if appointment.status == AppointmentStatus.CANCELLED.value:
        return appointment

    appointment.status = AppointmentStatus.CANCELLED.value
    await session.commit()
    return appointment


async def list_active_services(session: AsyncSession) -> Sequence[Service]:
    result = await session.execute(select(Service).where(Service.is_active == True))
    return result.scalars().all()


async def get_service(session: AsyncSession, service_id: int) -> Service | None:
    result = await session.execute(select(Service).where(Service.id == service_id))
    return result.scalars().first()


async def get_blocked_slots_for_date(session: AsyncSession, date: dt_date) -> Sequence[BlockedSlot]:
    result = await session.execute(select(BlockedSlot).where(BlockedSlot.slot_date == date))
    return result.scalars().all()


async def list_bookings(
    session: AsyncSession,
    day: dt_date | None = None,
    status: str | None = None,
) -> list[Appointment]:
    query = select(Appointment)
    if day is not None:
        query = query.where(Appointment.appointment_date == day)
    if status is not None:
        query = query.where(Appointment.status == status)
    query = query.order_by(Appointment.appointment_date, Appointment.start_time)
    result = await session.execute(query)
    return list(result.scalars().unique().all())