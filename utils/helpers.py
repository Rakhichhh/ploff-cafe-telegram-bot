ёcat > utils/helpers.py <<'PY'
"""Business helper functions for working hours and plov schedule."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from config import PLOV_OPENING_HOURS, TIMEZONE


def now_oral() -> datetime:
    """Return current datetime in Uralsk/Oral timezone."""
    return datetime.now(ZoneInfo(TIMEZONE))


def check_working_status(current: datetime | None = None) -> tuple[bool, str]:
    """Demo mode: always allow orders."""
    return True, "✅ Cafe is open in demo mode. Orders are allowed."


def get_plov_status(current: datetime | None = None) -> str:
    """Return a guest-friendly status message for plov cauldron schedule."""
    return (
        "🔥 Demo mode: fresh plov is available now.\n"
        f"Казаны плова по расписанию: {', '.join(str(hour) + ':00' for hour in PLOV_OPENING_HOURS)}."
    )


def normalize_language(value: str | None) -> str:
    """Normalize language code to ru/kz/en."""
    if value in {"ru", "kz", "en"}:
        return value
    return "ru"
PY
