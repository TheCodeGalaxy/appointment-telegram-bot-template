from __future__ import annotations

from datetime import date, time
from pathlib import Path
import tempfile

import pandas as pd
import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from bot.database.models import Appointment, AppointmentStatus, Base, Service, User
from bot.services.booking_service import (
    BookingError,
    SlotAlreadyBookedError,
    create_booking,
    list_bookings,
)
from bot.services.import_service import (
    ImportError,
    import_services_from_rows,
    parse_services_spreadsheet,
)
from bot.services.schedule_service import (
    ScheduleConfig,
    calculate_end_time,
    generate_time_slots,
    is_working_day,
)


@pytest.fixture
def in_memory_engine():
    return create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)


@pytest_asyncio.fixture(scope="function")
async def db_session(in_memory_engine):
    async with in_memory_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(
        in_memory_engine, expire_on_commit=False, class_=AsyncSession
    )
    async with async_session() as session:
        yield session
        await session.rollback()


# ---------------------------------------------------------------------------
# Pure schedule logic tests
# ---------------------------------------------------------------------------

def test_calculate_end_time_adds_duration() -> None:
    assert calculate_end_time(time(9, 0), 30) == time(9, 30)
    assert calculate_end_time(time(14, 45), 60) == time(15, 45)


def test_is_working_day_respects_config() -> None:
    config = ScheduleConfig(
        start=time(9, 0),
        end=time(17, 0),
        working_days=(0, 1, 2, 3, 4),
        default_slot_duration_minutes=30,
    )
    monday = date(2026, 7, 13)
    saturday = date(2026, 7, 18)
    assert is_working_day(monday, config) is True
    assert is_working_day(saturday, config) is False


def test_generate_time_slots_excludes_appointments() -> None:
    config = ScheduleConfig(
        start=time(9, 0),
        end=time(10, 0),
        working_days=(0, 1, 2, 3, 4, 5, 6),
        default_slot_duration_minutes=30,
    )
    service = Service(id=1, title="Test", duration_minutes=30)
    existing = [
        Appointment(
            id=1,
            user_id=1,
            service_id=1,
            appointment_date=date(2026, 7, 13),
            start_time=time(9, 0),
            end_time=time(9, 30),
            status=AppointmentStatus.SCHEDULED.value,
        )
    ]
    slots = generate_time_slots(
        day=date(2026, 7, 13),
        service=service,
        existing_appointments=existing,
        config=config,
    )
    assert slots == [time(9, 30)]


def test_generate_time_slots_ignores_cancelled_appointments() -> None:
    config = ScheduleConfig(
        start=time(9, 0),
        end=time(10, 0),
        working_days=(0, 1, 2, 3, 4, 5, 6),
        default_slot_duration_minutes=30,
    )
    service = Service(id=1, title="Test", duration_minutes=30)
    existing = [
        Appointment(
            id=1,
            user_id=1,
            service_id=1,
            appointment_date=date(2026, 7, 13),
            start_time=time(9, 0),
            end_time=time(9, 30),
            status=AppointmentStatus.CANCELLED.value,
        )
    ]
    slots = generate_time_slots(
        day=date(2026, 7, 13),
        service=service,
        existing_appointments=existing,
        config=config,
    )
    assert slots == [time(9, 0), time(9, 30)]


# ---------------------------------------------------------------------------
# Async database tests
# ---------------------------------------------------------------------------

@pytest.fixture
def in_memory_engine():
    return create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)


@pytest_asyncio.fixture(scope="function")
async def db_session(in_memory_engine):
    async with in_memory_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(
        in_memory_engine, expire_on_commit=False, class_=AsyncSession
    )
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.mark.asyncio
async def test_create_booking_persists_appointment(db_session: AsyncSession) -> None:
    service = Service(title="Consultation", duration_minutes=30)
    db_session.add(service)
    await db_session.commit()

    appointment = await create_booking(
        session=db_session,
        telegram_id=1001,
        service_id=service.id,
        appointment_date=date(2026, 8, 3),
        start_time=time(10, 0),
        full_name="Test User",
        phone_number="+1234567890",
    )

    assert appointment.id is not None
    assert appointment.end_time == time(10, 30)
    assert appointment.status == AppointmentStatus.SCHEDULED.value

    bookings = await list_bookings(db_session, day=date(2026, 8, 3))
    assert len(bookings) == 1


@pytest.mark.asyncio
async def test_double_booking_same_slot_raises(db_session: AsyncSession) -> None:
    service = Service(title="Consultation", duration_minutes=30)
    db_session.add(service)
    await db_session.commit()

    await create_booking(
        session=db_session,
        telegram_id=1002,
        service_id=service.id,
        appointment_date=date(2026, 8, 4),
        start_time=time(11, 0),
        full_name="First User",
        phone_number="+1111111111",
    )

    with pytest.raises(SlotAlreadyBookedError):
        await create_booking(
            session=db_session,
            telegram_id=1003,
            service_id=service.id,
            appointment_date=date(2026, 8, 4),
            start_time=time(11, 0),
            full_name="Second User",
            phone_number="+2222222222",
        )


@pytest.mark.asyncio
async def test_create_booking_fails_for_missing_service(db_session: AsyncSession) -> None:
    with pytest.raises(BookingError):
        await create_booking(
            session=db_session,
            telegram_id=1004,
            service_id=9999,
            appointment_date=date(2026, 8, 3),
            start_time=time(12, 0),
            full_name="User",
            phone_number="+3333333333",
        )


@pytest.mark.asyncio
async def test_create_booking_stores_individuals_count(db_session: AsyncSession) -> None:
    service = Service(title="Consultation", duration_minutes=30)
    db_session.add(service)
    await db_session.commit()

    appointment = await create_booking(
        session=db_session,
        telegram_id=1005,
        service_id=service.id,
        appointment_date=date(2026, 8, 5),
        start_time=time(10, 0),
        full_name="Family",
        phone_number="+5555555555",
        individuals_count=4,
    )

    assert appointment.individuals_count == 4
    result = await db_session.execute(
        select(Appointment.individuals_count).where(Appointment.id == appointment.id)
    )
    assert result.scalar_one() == 4


@pytest.mark.asyncio
async def test_import_services_from_rows_creates_and_updates(
    db_session: AsyncSession,
) -> None:
    existing = Service(title="Existing", duration_minutes=30, is_active=True)
    db_session.add(existing)
    await db_session.commit()

    rows = [
        {"title": "Existing", "duration_minutes": 45, "is_active": False},
        {"title": "New", "duration_minutes": 60, "is_active": True},
    ]
    stats = await import_services_from_rows(db_session, rows)

    assert stats == {"created": 1, "updated": 1}

    result = await db_session.execute(select(Service).order_by(Service.title))
    services = result.scalars().all()
    assert len(services) == 2

    by_title = {s.title: s for s in services}
    assert by_title["Existing"].duration_minutes == 45
    assert by_title["Existing"].is_active is False
    assert by_title["New"].duration_minutes == 60
    assert by_title["New"].is_active is True


def test_parse_services_spreadsheet_csv() -> None:
    df = pd.DataFrame(
        {
            "title": ["Consultation", "Follow-up"],
            "duration_minutes": [30, 15],
            "is_active": [1, 0],
        }
    )
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
        df.to_csv(f.name, index=False)
        path = Path(f.name)

    try:
        rows = parse_services_spreadsheet(path)
        assert rows == [
            {"title": "Consultation", "duration_minutes": 30, "is_active": True},
            {"title": "Follow-up", "duration_minutes": 15, "is_active": False},
        ]
    finally:
        path.unlink(missing_ok=True)


def test_parse_services_spreadsheet_xlsx() -> None:
    df = pd.DataFrame(
        {
            "title": ["X-Ray", "MRI"],
            "duration_minutes": [20, 90],
            "is_active": [0, 1],
        }
    )
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
        df.to_excel(f.name, index=False)
        path = Path(f.name)

    try:
        rows = parse_services_spreadsheet(path)
        assert rows == [
            {"title": "X-Ray", "duration_minutes": 20, "is_active": False},
            {"title": "MRI", "duration_minutes": 90, "is_active": True},
        ]
    finally:
        path.unlink(missing_ok=True)


def test_parse_services_spreadsheet_rejects_extra_columns() -> None:
    df = pd.DataFrame(
        {
            "title": ["Checkup"],
            "duration_minutes": [30],
            "is_active": [1],
            "price": [100],
        }
    )
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
        df.to_csv(f.name, index=False)
        path = Path(f.name)

    try:
        with pytest.raises(ImportError, match="Unexpected columns"):
            parse_services_spreadsheet(path)
    finally:
        path.unlink(missing_ok=True)
