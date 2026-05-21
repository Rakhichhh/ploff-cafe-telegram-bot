"""Telegram keyboard builders."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def language_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
        InlineKeyboardButton(text="🇰🇿 Қазақша", callback_data="lang:kz"),
        InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en"),
    )
    return builder.as_markup()


def order_type_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    texts = {
        "ru": ("🍽 В зале", "🥡 Навынос"),
        "kz": ("🍽 Залда", "🥡 Алып кету"),
        "en": ("🍽 Dine in", "🥡 Takeaway"),
    }
    hall, takeaway = texts.get(lang, texts["ru"])
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=hall, callback_data="order_type:hall"),
        InlineKeyboardButton(text=takeaway, callback_data="order_type:takeaway"),
    )
    return builder.as_markup()


def table_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for number in range(1, 37):
        builder.button(text=str(number), callback_data=f"table:{number}")
    builder.adjust(6)
    return builder.as_markup()


def category_keyboard(menu: List[dict], lang: str = "ru") -> InlineKeyboardMarkup:
    categories = sorted({str(item["category"]) for item in menu})
    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.button(text=category, callback_data=f"category:{category}")
    builder.button(text="🛒 Cart", callback_data="cart:show")
    builder.button(text="↩️ Back", callback_data="back:start")
    builder.adjust(1)
    return builder.as_markup()


def items_keyboard(items: Iterable[dict], lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    name_key = f"name_{lang}"
    for item in items:
        status = "✅" if item.get("is_available", True) else "⛔"
        name = item.get(name_key) or item.get("name_ru") or item.get("id")
        price = item.get("price")
        builder.button(
            text=f"{status} {name} — {price} ₸",
            callback_data=f"add:{item['id']}",
        )
    builder.button(text="🛒 Cart", callback_data="cart:show")
    builder.button(text="↩️ Categories", callback_data="menu:categories")
    builder.adjust(1)
    return builder.as_markup()


def cart_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Confirm", callback_data="cart:confirm"),
        InlineKeyboardButton(text="🧹 Clear", callback_data="cart:clear"),
    )
    builder.row(InlineKeyboardButton(text="↩️ Menu", callback_data="menu:categories"))
    return builder.as_markup()


def admin_menu_keyboard(menu: List[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for item in menu:
        status = "✅" if item.get("is_available", True) else "⛔"
        name = item.get("name_ru", item.get("id"))
        builder.button(text=f"{status} {name}", callback_data=f"admin_toggle:{item['id']}")
    builder.adjust(1)
    return builder.as_markup()
