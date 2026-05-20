
"""Business helper functions for working hours and plov schedule."""

import os

TEST_MODE = os.getenv("TEST_MODE", "False").lower() == "true"






from __future__ import annotations

from datetime import datetime, time
from zoneinfo import ZoneInfo

from config import PLOV_OPENING_HOURS, TIMEZONE


def now_oral() -> datetime:
    """Return current datetime in Uralsk/Oral timezone."""
    return datetime.now(ZoneInfo(TIMEZONE))


def check_working_status(current: datetime | None = None) -> tuple[bool, str]:
    """Check whether orders are allowed.

    08:00-11:00: preorder is allowed.
    11:00-00:00: normal ordering is allowed.
    00:00-08:00: orders are blocked.
    """
    current = current or now_oral()
    current_time = current.time()

    if TEST_MODE:
        return True, "Cafe is open in test mode."

    if time(0, 0) <= current_time < time(8, 0):
        return (
            False,
            "Кешіріңіз, тапсырыстар 00:00-08:00 аралығында қабылданбайды.\n"
            "Извините, заказы с 00:00 до 08:00 не принимаются.\n"
            "Sorry, orders are not accepted from 00:00 to 08:00.",
        )

    if time(8, 0) <= current_time < time(11, 0):
        return (
            True,
            "✅ Предзаказ принят. Кафе открывается для гостей в 11:00.",
        )

    return True, "✅ Кафе открыто. Можно оформить заказ."


def get_plov_status(current: datetime | None = None) -> str:
    """Return a guest-friendly status message for plov cauldron schedule."""
    current = current or now_oral()
    hour = current.hour
    minute = current.minute

    for opening_hour in PLOV_OPENING_HOURS:
        if hour == opening_hour and minute <= 59:
            return f"🔥 Свежий плов доступен сейчас: казан {opening_hour}:00."

    for opening_hour in PLOV_OPENING_HOURS:
        if hour < opening_hour:
            return f"⏳ Следующий свежий казан плова откроется в {opening_hour}:00."

    return "🌙 Сегодня казаны плова уже открывались. Можно оформить предзаказ на завтра к 12:00."


def normalize_language(value: str | None) -> str:
    """Normalize language code to ru/kz/en."""
    if value in {"ru", "kz", "en"}:
        return value
    return "ru"


 
