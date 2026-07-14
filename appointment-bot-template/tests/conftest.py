"""
Global pytest fixtures for the Appointment Booking Bot test suite.

This file defines reusable fixtures for:
- Async database sessions
- Mock Telegram bot instances
- Test configuration overrides
"""

from datetime import date, time
import tempfile
from pathlib import Path

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