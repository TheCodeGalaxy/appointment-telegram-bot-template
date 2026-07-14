from __future__ import annotations

import logging
from datetime import timedelta

from sqlalchemy import delete

from bot.config import settings, today_in_tz
from bot.database.connection import AsyncSessionLocal
from bot.database.models import Appointment

logger = logging.getLogger(__name__)


async def purge_admin_archive(session) -> int:
    cutoff = today_in_tz() - timedelta(days=settings.admin_retention_days)
    result = await session.execute(
        delete(Appointment).where(Appointment.appointment_date < cutoff)
    )
    await session.commit()
    return result.rowcount or 0


async def purge_user_archive(session) -> int:
    cutoff = today_in_tz() - timedelta(days=settings.user_retention_days)
    result = await session.execute(
        delete(Appointment).where(Appointment.appointment_date < cutoff)
    )
    await session.commit()
    return result.rowcount or 0


async def run_retention_purge(session) -> tuple[int, int]:
    admin_deleted = await purge_admin_archive(session)
    user_deleted = await purge_user_archive(session)
    return admin_deleted, user_deleted


async def run_daily_retention_job(context) -> None:
    async with AsyncSessionLocal() as session:
        admin_deleted, user_deleted = await run_retention_purge(session)
    logger.info(
        "Retention purge complete: admin=%s user=%s",
        admin_deleted,
        user_deleted,
    )
