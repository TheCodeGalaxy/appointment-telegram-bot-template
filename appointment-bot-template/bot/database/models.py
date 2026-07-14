from __future__ import annotations

import enum
from datetime import date, datetime, time
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

if TYPE_CHECKING:
    pass


class Base(DeclarativeBase):
    pass


class AppointmentStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class User(Base):
    """A Telegram user who may book appointments."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    language_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    appointments: Mapped[list["Appointment"]] = relationship(
        back_populates="user", lazy="selectin"
    )


class Service(Base):
    """Bookable service or appointment category."""

    __tablename__ = "services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=30
    )
    price: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    appointments: Mapped[list["Appointment"]] = relationship(
        back_populates="service", lazy="selectin"
    )


class Appointment(Base):
    """Confirmed appointment reservation.

    The unique constraint on (appointment_date, start_time) guarantees at the
    database level that two concurrent transactions cannot book the same slot.
    """

    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"), nullable=False)
    appointment_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    individuals_count: Mapped[int] = mapped_column(
        Integer, default=1, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), default=AppointmentStatus.SCHEDULED.value, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="appointments")
    service: Mapped["Service"] = relationship(back_populates="appointments")

    __table_args__ = (
        UniqueConstraint(
            "appointment_date",
            "start_time",
            name="uq_appointment_date_start_time",
        ),
    )


class BlockedSlot(Base):
    """Time ranges manually blocked by admins (lunch, vacation, emergencies)."""

    __tablename__ = "blocked_slots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slot_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
