from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bot.config import settings
from bot.database.models import Base

logger = logging.getLogger(__name__)

engine = create_async_engine(settings.database_url, echo=settings.log_level == "DEBUG")
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def init_db() -> None:
    """Create all tables if they do not already exist and run safe migrations."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _run_migrations(conn)


async def _run_migrations(conn) -> None:
    """Apply additive schema changes without dropping existing tables.

    SQLite does not support ``ADD COLUMN IF NOT EXISTS``, so additive columns
    are created via ``create_all``. This only handles legacy renames.
    """
    migration_statements = [
        (
            "appointments_individuals_count_rename",
            "ALTER TABLE appointments RENAME COLUMN patients_count TO individuals_count",
        ),
    ]
    for name, statement in migration_statements:
        try:
            await conn.execute(text(statement))
            logger.debug("Migration applied: %s", name)
        except OperationalError as exc:
            # Column already renamed/does not exist; safe to skip.
            logger.debug("Migration %s skipped: %s", name, exc)


async def get_session() -> AsyncSession:
    """Return a new async database session.

    Callers are responsible for committing/rolling back and closing the session.
    """
    return AsyncSessionLocal()
