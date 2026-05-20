"""Application configuration.

Secrets are loaded from .env, not hard-coded in the source code.
"""

from __future__ import annotations

import os
from typing import List

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
KITCHEN_GROUP_ID: int = int(os.getenv("KITCHEN_GROUP_ID", "0"))

ADMIN_IDS: List[int] = [
    int(admin_id.strip())
    for admin_id in os.getenv("ADMIN_IDS", "").split(",")
    if admin_id.strip().isdigit()
]

CAFE_NAME = "PLOFF Cafe"
CAFE_CITY = "Uralsk"
CAFE_ADDRESS = "Строитель, 43б, Уральск"
TIMEZONE = "Asia/Oral"

GUEST_OPEN_HOUR = 11
STAFF_START_HOUR = 8
CLOSE_HOUR = 0
MAX_TABLE_NUMBER = 36
TAKEAWAY_CONTAINER_PRICE = 50
PLOV_OPENING_HOURS = (12, 15, 18)
