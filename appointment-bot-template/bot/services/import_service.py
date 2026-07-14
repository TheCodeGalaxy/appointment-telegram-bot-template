from __future__ import annotations

from pathlib import Path

import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import Service


class ImportError(ValueError):
    """Raised when a spreadsheet cannot be parsed or contains invalid data."""


REQUIRED_COLUMNS = {"title", "duration_minutes", "is_active"}


def _normalize_is_active(value) -> bool:
    """Map 1/0 or equivalent active flags to boolean."""
    if isinstance(value, bool):
        return value
    try:
        return int(value) == 1
    except (TypeError, ValueError) as exc:
        raise ImportError(f"is_active must be 0 or 1, got {value!r}") from exc


def parse_services_spreadsheet(file_path: Path) -> list[dict]:
    """Read a .xlsx or .csv file and return normalized service rows.

    The parser enforces exactly three columns: title, duration_minutes,
    is_active. Any additional columns are ignored. Malformed rows raise
    ImportError before any database write occurs.
    """
    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        df = pd.read_csv(file_path)
    elif suffix in {".xlsx", ".xls"}:
        df = pd.read_excel(file_path)
    else:
        raise ImportError(f"Unsupported file extension: {suffix!r}. Use .csv or .xlsx.")

    columns = set(df.columns)
    missing = REQUIRED_COLUMNS - columns
    if missing:
        raise ImportError(f"Missing required columns: {sorted(missing)}")

    extra = columns - REQUIRED_COLUMNS
    if extra:
        raise ImportError(
            f"Unexpected columns: {sorted(extra)}. Only title, duration_minutes, "
            "and is_active are allowed."
        )

    df = df[list(REQUIRED_COLUMNS)].copy()
    df["duration_minutes"] = pd.to_numeric(df["duration_minutes"], errors="coerce")
    df["is_active"] = pd.to_numeric(df["is_active"], errors="coerce")

    rows: list[dict] = []
    for index, row in df.iterrows():
        title = str(row["title"]).strip()
        if not title:
            raise ImportError(f"Row {index + 1}: empty title is not allowed.")
        if pd.isna(row["duration_minutes"]):
            raise ImportError(
                f"Row {index + 1}: duration_minutes must be an integer."
            )
        if pd.isna(row["is_active"]):
            raise ImportError(f"Row {index + 1}: is_active must be 0 or 1.")

        rows.append(
            {
                "title": title,
                "duration_minutes": int(row["duration_minutes"]),
                "is_active": _normalize_is_active(row["is_active"]),
            }
        )

    return rows


async def import_services_from_rows(
    session: AsyncSession,
    rows: list[dict],
) -> dict[str, int]:
    """Batch-insert or batch-update services in a single async transaction.

    Existing services are matched by title and updated in place; new titles
    are inserted. All changes are committed in one transaction to keep the
    operation atomic.
    """
    if not rows:
        return {"created": 0, "updated": 0}

    titles = [row["title"] for row in rows]
    result = await session.execute(select(Service).where(Service.title.in_(titles)))
    existing: dict[str, Service] = {service.title: service for service in result.scalars().all()}

    created = 0
    updated = 0
    for row in rows:
        title = row["title"]
        duration_minutes = row["duration_minutes"]
        is_active = row["is_active"]

        service = existing.get(title)
        if service:
            service.duration_minutes = duration_minutes
            service.is_active = is_active
            updated += 1
        else:
            session.add(
                Service(
                    title=title,
                    duration_minutes=duration_minutes,
                    is_active=is_active,
                )
            )
            created += 1

    await session.commit()
    return {"created": created, "updated": updated}
