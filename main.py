"""Main entry point for the PLOFF Cafe Telegram bot.

Run:
    python main.py
"""

from __future__ import annotations

import asyncio
import logging
from typing import Dict

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, CallbackQuery, Message

from config import ADMIN_IDS, BOT_TOKEN, CAFE_ADDRESS, KITCHEN_GROUP_ID
from utils.file_manager import append_json_record, read_json, write_json
from utils.helpers import check_working_status, get_plov_status, normalize_language
from utils.keyboards import (
    admin_menu_keyboard,
    cart_keyboard,
    category_keyboard,
    items_keyboard,
    language_keyboard,
    order_type_keyboard,
    table_keyboard,
)
from utils.models import Order, build_menu_item

MENU_PATH = "data/menu.json"
ORDERS_PATH = "data/orders.json"

router = Router()
active_orders: Dict[int, Order] = {}


TEXTS = {
    "ru": {
        "cart_empty": "🛒 Корзина пуста.",
        "your_cart": "🛒 Ваша корзина:",
        "subtotal": "Промежуточная сумма",
        "container": "Контейнер",
        "total": "ИТОГО",
        "start": (
            "🍛 Добро пожаловать в PLOFF Cafe!\n\n"
            "Выберите язык / Тілді таңдаңыз / Choose language:"
        ),
        "choose_order_type": "Выберите тип заказа:",
        "takeaway_selected": (
            "🥡 Выбран заказ навынос.\n"
            "Стоимость контейнера: +50 ₸.\n\n"
            "Выберите категорию:"
        ),
        "choose_table": "🍽 Выберите номер столика от 1 до 36:",
        "invalid_table": "❌ Введите корректный номер столика от 1 до 36.",
        "table_selected": "✅ Столик №{table} выбран.\nВыберите категорию:",
        "choose_category": "Выберите категорию:",
        "select_item": "Выберите блюдо:",
        "item_not_found": "Блюдо не найдено.",
        "added": "Добавлено",
        "cart_cleared": "🧹 Корзина очищена.",
        "cart_empty_alert": "Корзина пуста.",
        "choose_table_first": "Сначала выберите номер столика.",
        "order_confirmed": (
            "✅ Заказ подтверждён!\n\n"
            "Ваш заказ отправлен на кухню.\n\n"
            "{receipt}"
        ),
        "photo_received": (
            "📸 Изображение получено. Если это оплата или фото столика, "
            "продолжайте оформление заказа или дождитесь администратора."
        ),
        "access_denied": "⛔ Доступ запрещён.",
        "admin_panel": "⚙️ Админ-панель: управление стоп-листом.",
        "status_updated": "Статус обновлён.",
        "fallback": (
            "Я не понял сообщение.\n"
            "Используйте /start для заказа или /plov для расписания плова."
        ),
        "help": (
            "📌 Инструкция:\n"
            "/start — начать заказ\n"
            "/plov — расписание свежего плова\n"
            "/admin — админ-панель"
        ),
    },
    "kz": {
        "cart_empty": "🛒 Себет бос.",
        "your_cart": "🛒 Сіздің себетіңіз:",
        "subtotal": "Аралық сома",
        "container": "Контейнер",
        "total": "БАРЛЫҒЫ",
        "start": (
            "🍛 PLOFF Cafe ботына қош келдіңіз!\n\n"
            "Выберите язык / Тілді таңдаңыз / Choose language:"
        ),
        "choose_order_type": "Тапсырыс түрін таңдаңыз:",
        "takeaway_selected": (
            "🥡 Алып кету таңдалды.\n"
            "Контейнер құны: +50 ₸.\n\n"
            "Санатты таңдаңыз:"
        ),
        "choose_table": "🍽 1-ден 36-ға дейін үстел нөмірін таңдаңыз:",
        "invalid_table": "❌ 1-ден 36-ға дейін дұрыс үстел нөмірін енгізіңіз.",
        "table_selected": "✅ №{table} үстел таңдалды.\nСанатты таңдаңыз:",
        "choose_category": "Санатты таңдаңыз:",
        "select_item": "Тағамды таңдаңыз:",
        "item_not_found": "Тағам табылмады.",
        "added": "Қосылды",
        "cart_cleared": "🧹 Себет тазаланды.",
        "cart_empty_alert": "Себет бос.",
        "choose_table_first": "Алдымен үстел нөмірін таңдаңыз.",
        "order_confirmed": (
            "✅ Тапсырыс расталды!\n\n"
            "Тапсырысыңыз ас үйге жіберілді.\n\n"
            "{receipt}"
        ),
        "photo_received": (
            "📸 Сурет қабылданды. Егер бұл төлем немесе үстел суреті болса, "
            "тапсырысты жалғастырыңыз немесе әкімшіні күтіңіз."
        ),
        "access_denied": "⛔ Рұқсат жоқ.",
        "admin_panel": "⚙️ Админ-панель: стоп-лист басқару.",
        "status_updated": "Статус жаңартылды.",
        "fallback": (
            "Мен бұл хабарламаны түсінбедім.\n"
            "Тапсырыс үшін /start, палау кестесі үшін /plov қолданыңыз."
        ),
        "help": (
            "📌 Нұсқаулық:\n"
            "/start — тапсырысты бастау\n"
            "/plov — жаңа палау кестесі\n"
            "/admin — админ-панель"
        ),
    },
    "en": {
        "cart_empty": "🛒 Cart is empty.",
        "your_cart": "🛒 Your cart:",
        "subtotal": "Subtotal",
        "container": "Container",
        "total": "TOTAL",
        "start": (
            "🍛 Welcome to PLOFF Cafe!\n\n"
            "Выберите язык / Тілді таңдаңыз / Choose language:"
        ),
        "choose_order_type": "Choose order type:",
        "takeaway_selected": (
            "🥡 Takeaway selected.\n"
            "Container fee: +50 ₸.\n\n"
            "Choose category:"
        ),
        "choose_table": "🍽 Choose your table number from 1 to 36:",
        "invalid_table": "❌ Please enter a valid table number from 1 to 36.",
        "table_selected": "✅ Table #{table} selected.\nChoose category:",
        "choose_category": "Choose category:",
        "select_item": "Select an item:",
        "item_not_found": "Item not found.",
        "added": "Added",
        "cart_cleared": "🧹 Cart cleared.",
        "cart_empty_alert": "Cart is empty.",
        "choose_table_first": "Choose table number first.",
        "order_confirmed": (
            "✅ Order confirmed!\n\n"
            "Your order has been sent to the kitchen.\n\n"
            "{receipt}"
        ),
        "photo_received": (
            "📸 Image received. If this is a payment or table screenshot, "
            "please continue with the order flow or wait for administrator confirmation."
        ),
        "access_denied": "⛔ Access denied.",
        "admin_panel": "⚙️ Admin panel: toggle stop-list status.",
        "status_updated": "Status updated.",
        "fallback": (
            "I did not understand this message.\n"
            "Use /start to create an order or /plov to check plov schedule."
        ),
        "help": (
            "📌 Help:\n"
            "/start — start order\n"
            "/plov — fresh plov schedule\n"
            "/admin — admin panel"
        ),
    },
}


def text(lang: str, key: str) -> str:
    """Return translated text by language code."""
    return TEXTS.get(lang, TEXTS["ru"]).get(key, TEXTS["ru"][key])


class OrderFSM(StatesGroup):
    choosing_language = State()
    choosing_order_type = State()
    choosing_table = State()
    choosing_category = State()
    choosing_items = State()
    viewing_cart = State()


def load_menu() -> list[dict]:
    """Load menu from JSON."""
    data = read_json(MENU_PATH, default=[])
    return data if isinstance(data, list) else []


def find_raw_item(item_id: str) -> dict | None:
    """Find raw item dictionary in the menu JSON."""
    for item in load_menu():
        if item.get("id") == item_id:
            return item
    return None


def get_order(user_id: int, username: str | None = None, lang: str = "ru") -> Order:
    """Return an active order or create a new one."""
    if user_id not in active_orders:
        active_orders[user_id] = Order(
            user_id=user_id,
            username=username,
            language=lang,
        )
    return active_orders[user_id]


def get_lang_from_state_data(data: dict) -> str:
    """Return selected language from FSM data."""
    return normalize_language(data.get("language", "ru"))


def format_cart(order: Order, lang: str = "ru") -> str:
    """Return a readable cart summary for the guest."""
    if order.is_empty():
        return text(lang, "cart_empty")

    lines = [text(lang, "your_cart")]

    for line in order.items:
        lines.append(f"• {line.item.name} x{line.quantity} = {line.line_total} ₸")

    lines.append(f"\n{text(lang, 'subtotal')}: {order.subtotal()} ₸")

    if order.service_fee():
        lines.append(f"{text(lang, 'container')}: {order.service_fee()} ₸")

    lines.append(f"{text(lang, 'total')}: {order.total()} ₸")
    return "\n".join(lines)


@router.message(CommandStart())
async def start(message: Message, state: FSMContext) -> None:
    """Start bot and choose language."""
    await state.clear()
    await state.set_state(OrderFSM.choosing_language)
    await message.answer(
        text("ru", "start"),
        reply_markup=language_keyboard(),
    )


@router.callback_query(F.data.startswith("lang:"))
async def choose_language(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle language selection."""
    lang = normalize_language(callback.data.split(":")[1])
    await state.update_data(language=lang)
    await state.set_state(OrderFSM.choosing_order_type)

    user = callback.from_user
    active_orders[user.id] = Order(
        user_id=user.id,
        username=user.username,
        language=lang,
    )

    allowed, status = check_working_status()
    if not allowed:
        await callback.message.edit_text(status)
        await callback.answer()
        return

    await callback.message.edit_text(
        f"{status}\n\n"
        f"📍 {CAFE_ADDRESS}\n"
        f"🔥 {get_plov_status()}\n\n"
        f"{text(lang, 'choose_order_type')}",
        reply_markup=order_type_keyboard(lang),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("order_type:"))
async def choose_order_type(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle dine-in or takeaway selection."""
    user = callback.from_user
    data = await state.get_data()
    lang = get_lang_from_state_data(data)
    order = get_order(user.id, user.username, lang)

    order_type = callback.data.split(":")[1]

    if order_type == "takeaway":
        order.set_takeaway()
        await state.set_state(OrderFSM.choosing_category)
        await callback.message.edit_text(
            text(lang, "takeaway_selected"),
            reply_markup=category_keyboard(load_menu(), lang),
        )
    else:
        order.order_type = "hall"
        await state.set_state(OrderFSM.choosing_table)
        await callback.message.edit_text(
            text(lang, "choose_table"),
            reply_markup=table_keyboard(),
        )

    await callback.answer()


@router.callback_query(F.data.startswith("table:"))
async def choose_table_button(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle table selection by button."""
    user = callback.from_user
    data = await state.get_data()
    lang = get_lang_from_state_data(data)
    order = get_order(user.id, user.username, lang)

    try:
        table_number = callback.data.split(":")[1]
        order.set_table_number(table_number)
    except ValueError as error:
        await callback.answer(str(error), show_alert=True)
        return

    await state.set_state(OrderFSM.choosing_category)
    await callback.message.edit_text(
        text(lang, "table_selected").format(table=order.table_number),
        reply_markup=category_keyboard(load_menu(), lang),
    )
    await callback.answer()


@router.message(OrderFSM.choosing_table)
async def choose_table_text(message: Message, state: FSMContext) -> None:
    """Handle manual table number input."""
    data = await state.get_data()
    lang = get_lang_from_state_data(data)
    order = get_order(message.from_user.id, message.from_user.username, lang)

    try:
        order.set_table_number(message.text)
    except ValueError:
        await message.answer(text(lang, "invalid_table"))
        return

    await state.set_state(OrderFSM.choosing_category)
    await message.answer(
        text(lang, "table_selected").format(table=order.table_number),
        reply_markup=category_keyboard(load_menu(), lang),
    )


@router.callback_query(F.data == "menu:categories")
async def show_categories(callback: CallbackQuery, state: FSMContext) -> None:
    """Show menu categories."""
    data = await state.get_data()
    lang = get_lang_from_state_data(data)

    await state.set_state(OrderFSM.choosing_category)
    await callback.message.edit_text(
        text(lang, "choose_category"),
        reply_markup=category_keyboard(load_menu(), lang),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("category:"))
async def show_items(callback: CallbackQuery, state: FSMContext) -> None:
    """Show items inside selected category."""
    data = await state.get_data()
    lang = get_lang_from_state_data(data)
    category = callback.data.replace("category:", "", 1)
    items = [item for item in load_menu() if item.get("category") == category]

    await state.set_state(OrderFSM.choosing_items)
    await callback.message.edit_text(
        f"📋 {category}\n\n{text(lang, 'select_item')}",
        reply_markup=items_keyboard(items, lang),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("add:"))
async def add_item(callback: CallbackQuery, state: FSMContext) -> None:
    """Add selected menu item to cart."""
    data = await state.get_data()
    lang = get_lang_from_state_data(data)

    allowed, status = check_working_status()
    if not allowed:
        await callback.message.edit_text(status)
        await callback.answer()
        return

    order = get_order(callback.from_user.id, callback.from_user.username, lang)
    item_id = callback.data.split(":", 1)[1]
    raw_item = find_raw_item(item_id)

    if raw_item is None:
        await callback.answer(text(lang, "item_not_found"), show_alert=True)
        return

    try:
        item = build_menu_item(raw_item, language=lang)
        order.add_item(item)
    except ValueError as error:
        await callback.answer(str(error), show_alert=True)
        return

    await callback.answer(f"{text(lang, 'added')}: {item.name}")


@router.callback_query(F.data == "cart:show")
async def show_cart(callback: CallbackQuery, state: FSMContext) -> None:
    """Show current cart."""
    data = await state.get_data()
    lang = get_lang_from_state_data(data)
    order = get_order(callback.from_user.id, callback.from_user.username, lang)

    await state.set_state(OrderFSM.viewing_cart)
    await callback.message.edit_text(
        format_cart(order, lang),
        reply_markup=cart_keyboard(lang),
    )
    await callback.answer()


@router.callback_query(F.data == "cart:clear")
async def clear_cart(callback: CallbackQuery, state: FSMContext) -> None:
    """Clear current cart."""
    data = await state.get_data()
    lang = get_lang_from_state_data(data)
    order = get_order(callback.from_user.id, callback.from_user.username, lang)
    order.clear()

    await callback.message.edit_text(
        text(lang, "cart_cleared"),
        reply_markup=category_keyboard(load_menu(), lang),
    )
    await callback.answer()


@router.callback_query(F.data == "cart:confirm")
async def confirm_order(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    """Confirm order, save it, and send receipt to kitchen group."""
    data = await state.get_data()
    lang = get_lang_from_state_data(data)

    allowed, status = check_working_status()
    if not allowed:
        await callback.message.edit_text(status)
        await callback.answer()
        return

    order = get_order(callback.from_user.id, callback.from_user.username, lang)

    if order.is_empty():
        await callback.answer(text(lang, "cart_empty_alert"), show_alert=True)
        return

    if order.order_type == "hall" and order.table_number is None:
        await callback.answer(text(lang, "choose_table_first"), show_alert=True)
        return

    try:
    order_data = order.to_dict()
    append_json_record(ORDERS_PATH, order_data)
    logging.info("Order saved to %s: %s", ORDERS_PATH, order_data)
except Exception as error:
    logging.exception("Could not save order to orders.json: %s", error)
receipt = order.make_receipt()

    if KITCHEN_GROUP_ID != 0:
        try:
            await bot.send_message(KITCHEN_GROUP_ID, receipt)
        except Exception as error:
            logging.exception("Could not send order to kitchen group: %s", error)

    active_orders.pop(callback.from_user.id, None)
    await state.clear()

    await callback.message.edit_text(
        text(lang, "order_confirmed").format(receipt=receipt)
    )
    await callback.answer()


@router.message(F.photo)
async def handle_photo(message: Message) -> None:
    """Handle image messages, e.g., payment or table screenshots."""
    await message.answer(text("ru", "photo_received"))


@router.message(Command("plov"))
async def plov(message: Message) -> None:
    """Show plov status."""
    await message.answer(get_plov_status())


@router.message(Command("help"))
async def help_command(message: Message) -> None:
    """Show help message."""
    await message.answer(text("ru", "help"))


@router.message(Command("admin"))
async def admin(message: Message) -> None:
    """Open protected admin panel."""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer(text("ru", "access_denied"))
        return

    await message.answer(
        text("ru", "admin_panel"),
        reply_markup=admin_menu_keyboard(load_menu()),
    )


@router.callback_query(F.data.startswith("admin_toggle:"))
async def admin_toggle(callback: CallbackQuery) -> None:
    """Toggle menu item availability for admins."""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer(text("ru", "access_denied"), show_alert=True)
        return

    item_id = callback.data.split(":", 1)[1]
    menu = load_menu()
    changed = False

    for item in menu:
        if item.get("id") == item_id:
            item["is_available"] = not item.get("is_available", True)
            changed = True
            break

    if not changed:
        await callback.answer(text("ru", "item_not_found"), show_alert=True)
        return

    write_json(MENU_PATH, menu)
    await callback.message.edit_reply_markup(reply_markup=admin_menu_keyboard(menu))
    await callback.answer(text("ru", "status_updated"))


@router.message()
async def fallback(message: Message) -> None:
    """Fallback for unknown text messages."""
    await message.answer(text("ru", "fallback"))


async def main() -> None:
    """Run Telegram bot."""
    logging.basicConfig(level=logging.INFO)

    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is missing. Create .env from .env.example.")

    bot = Bot(token=BOT_TOKEN)

    await bot.set_my_commands(
        [
            BotCommand(command="start", description="🛒 Start ordering food"),
            BotCommand(command="admin", description="⚙️ Admin stop-list panel"),
            BotCommand(command="plov", description="🔥 Fresh plov schedule"),
            BotCommand(command="help", description="📌 Bot instructions"),
        ]
    )

    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
