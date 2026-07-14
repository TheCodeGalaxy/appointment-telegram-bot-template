from __future__ import annotations

import enum


class BookingState(enum.IntEnum):
    """Finite states for the appointment booking conversation."""

    SELECT_SERVICE = 0
    SELECT_PATIENTS = 1
    SELECT_DATE = 2
    SELECT_TIME = 3
    COLLECT_NAME = 4
    COLLECT_PHONE = 5
    CONFIRM = 6
