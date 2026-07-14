from __future__ import annotations

from datetime import date, timedelta, time

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import Appointment, AppointmentStatus, Service, User
from bot.services.retention_service import (
    purge_admin_archive,
    purge_user_archive,
    run_retention_purge,
)


def _make_appointment(user_id: int, service_id: int, offset_days: int) -> Appointment:
    day = date.today() - timedelta(days=offset_days)
    return Appointment(
        user_id=user_id,
        service_id=service_id,
        appointment_date=day,
        start_time=time(9, 0),
        end_time=time(9, 30),
        status=AppointmentStatus.COMPLETED.value,
    )


@pytest.mark.asyncio
async def test_purge_admin_archive_deletes_older_than_7_days(db_session: AsyncSession) -> None:
    user = User(telegram_id=9001)
    service = Service(title="X", duration_minutes=30)
    db_session.add_all([user, service])
    await db_session.commit()

    recent = _make_appointment(user.id, service.id, 3)
    old = _make_appointment(user.id, service.id, 10)
    very_old = _make_appointment(user.id, service.id, 20)
    db_session.add_all([recent, old, very_old])
    await db_session.commit()

    deleted = await purge_admin_archive(db_session)

    remaining = (await db_session.execute(select(Appointment))).scalars().all()
    assert deleted == 2
    assert {a.id for a in remaining} == {recent.id}
    assert all((date.today() - a.appointment_date).days < 7 for a in remaining)


@pytest.mark.asyncio
async def test_purge_user_archive_deletes_older_than_14_days(db_session: AsyncSession) -> None:
    user = User(telegram_id=9002)
    service = Service(title="Y", duration_minutes=30)
    db_session.add_all([user, service])
    await db_session.commit()

    within = _make_appointment(user.id, service.id, 10)
    expired = _make_appointment(user.id, service.id, 15)
    db_session.add_all([within, expired])
    await db_session.commit()

    deleted = await purge_user_archive(db_session)

    remaining = (await db_session.execute(select(Appointment))).scalars().all()
    assert deleted == 1
    assert {a.id for a in remaining} == {within.id}


@pytest.mark.asyncio
async def test_run_retention_purge_keeps_recent_and_future(db_session: AsyncSession) -> None:
    user = User(telegram_id=9003)
    service = Service(title="Z", duration_minutes=30)
    db_session.add_all([user, service])
    await db_session.commit()

    future = Appointment(
        user_id=user.id,
        service_id=service.id,
        appointment_date=date.today() + timedelta(days=5),
        start_time=time(9, 0),
        end_time=time(9, 30),
        status=AppointmentStatus.SCHEDULED.value,
    )
    recent = _make_appointment(user.id, service.id, 1)
    db_session.add_all([future, recent])
    await db_session.commit()

    admin_deleted, user_deleted = await run_retention_purge(db_session)

    assert admin_deleted == 0
    assert user_deleted == 0
    remaining = (await db_session.execute(select(Appointment))).scalars().all()
    assert {a.id for a in remaining} == {future.id, recent.id}
