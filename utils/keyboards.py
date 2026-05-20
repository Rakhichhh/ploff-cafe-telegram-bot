"""Telegram keyboard builders."""

from __future__ import annotations

from typing import Iterable, List

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


BUTTONS = {
    "ru": {
        "hall": "🍽 В зале",
        "takeaway": "🥡 Навынос",
        "cart": "🛒 Корзина",
        "back": "↩️ Назад",
        "categories": "↩️ Категории",
        "menu": "↩️ Меню",
        "confirm": "✅ Подтвердить",
        "clear": "🧹 Очистить",
    },
    "kz": {
        "hall": "🍽 Залда",
        "takeaway": "🥡 Алып кету",
        "cart": "🛒 Себет",
        "back": "↩️ Артқа",
        "categories": "↩️ Санаттар",
        "menu": "↩️ Мәзір",
        "confirm": "✅ Растау",
        "clear": "🧹 Тазалау",
    },
    "en": {
        "hall": "🍽 Dine-in",
        "takeaway": "🥡 Takeaway",
        "cart": "🛒 Cart",
        "back": "↩️ Back",
        "categories": "↩️ Categories",
        "menu": "↩️ Menu",
        "confirm": "✅ Confirm",
        "clear": "🧹 Clear",
    },
}


def get_buttons(lang: str) -> dict:
    """Return button labels for selected language."""
    return BUTTONS.get(lang, BUTTONS["ru"])


def language_keyboard() -> InlineKeyboardMarkup:
    """Build language selection keyboard."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
        InlineKeyboardButton(text="🇰🇿 Қазақша", callback_data="lang:kz"),
        InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en"),
    )
    return builder.as_markup()


def order_type_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Build order type keyboard."""
    buttons = get_buttons(lang)

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=buttons["hall"],
            callback_data="order_type:hall",
        ),
        InlineKeyboardButton(
            text=buttons["takeaway"],
            callback_data="order_type:takeaway",
        ),
    )
    return builder.as_markup()


def table_keyboard() -> InlineKeyboardMarkup:
    """Build table number keyboard from 1 to 36."""
    builder = InlineKeyboardBuilder()

    for number in range(1, 37):
        builder.button(text=str(number), callback_data=f"table:{number}")

    builder.adjust(6)
    return builder.as_markup()


def category_keyboard(menu: List[dict], lang: str = "ru") -> InlineKeyboardMarkup:
    """Build menu category keyboard."""
    buttons = get_buttons(lang)
    categories = sorted({str(item["category"]) for item in menu})

    builder = InlineKeyboardBuilder()

    for category in categories:
        builder.button(text=category, callback_data=f"category:{category}")

    builder.button(text=buttons["cart"], callback_data="cart:show")
    builder.adjust(1)

    return builder.as_markup()


def items_keyboard(items: Iterable[dict], lang: str = "ru") -> InlineKeyboardMarkup:
    """Build menu item keyboard."""
    buttons = get_buttons(lang)
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

    builder.button(text=buttons["cart"], callback_data="cart:show")
    builder.button(text=buttons["categories"], callback_data="menu:categories")
    builder.adjust(1)

    return builder.as_markup()


def cart_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Build cart action keyboard."""
    buttons = get_buttons(lang)

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=buttons["confirm"],
            callback_data="cart:confirm",
        ),
        InlineKeyboardButton(
            text=buttons["clear"],
            callback_data="cart:clear",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=buttons["menu"],
            callback_data="menu:categories",
        )
    )

    return builder.as_markup()


def admin_menu_keyboard(menu: List[dict]) -> InlineKeyboardMarkup:
    """Build admin stop-list keyboard."""
    builder = InlineKeyboardBuilder()

    for item in menu:
        status = "✅" if item.get("is_available", True) else "⛔"
        name = item.get("name_ru", item.get("id"))

        builder.button(
            text=f"{status} {name}",
            callback_data=f"admin_toggle:{item['id']}",
        )

    builder.adjust(1)
    return builder.as_markup()
