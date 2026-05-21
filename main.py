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
from aiogram.types import CallbackQuery, Message

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


def format_cart(order: Order) -> str:
    """Return a readable cart summary for the guest."""
    if order.is_empty():
        return "🛒 Корзина пуста."

    lines = ["🛒 Your cart:"]
    for line in order.items:
        lines.append(f"• {line.item.name} x{line.quantity} = {line.line_total} ₸")
    lines.append(f"\nSubtotal: {order.subtotal()} ₸")
    if order.service_fee():
        lines.append(f"Container: {order.service_fee()} ₸")
    lines.append(f"TOTAL: {order.total()} ₸")
    return "\n".join(lines)


@router.message(CommandStart())
async def start(message: Message, state: FSMContext) -> None:
    """Start bot and choose language."""
    await state.set_state(OrderFSM.choosing_language)
    await message.answer(
        "Welcome to PLOFF Cafe!\n"
        "Выберите язык / Тілді таңдаңыз / Choose language:",
        reply_markup=language_keyboard(),
    )


@router.callback_query(F.data.startswith("lang:"))
async def choose_language(callback: CallbackQuery, state: FSMContext) -> None:
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
        f"{status}\n\n📍 {CAFE_ADDRESS}\n🔥 {get_plov_status()}\n\n"
        "Choose order type:",
        reply_markup=order_type_keyboard(lang),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("order_type:"))
async def choose_order_type(callback: CallbackQuery, state: FSMContext) -> None:
    user = callback.from_user
    data = await state.get_data()
    lang = data.get("language", "ru")
    order = get_order(user.id, user.username, lang)

    order_type = callback.data.split(":")[1]
    if order_type == "takeaway":
        order.set_takeaway()
        await state.set_state(OrderFSM.choosing_category)
        await callback.message.edit_text(
            "🥡 Takeaway selected. Container fee: +50 ₸.\nChoose category:",
            reply_markup=category_keyboard(load_menu(), lang),
        )
    else:
        order.order_type = "hall"
        await state.set_state(OrderFSM.choosing_table)
        await callback.message.edit_text(
            "🍽 Choose your table number from 1 to 36:",
            reply_markup=table_keyboard(),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("table:"))
async def choose_table_button(callback: CallbackQuery, state: FSMContext) -> None:
    user = callback.from_user
    data = await state.get_data()
    lang = data.get("language", "ru")
    order = get_order(user.id, user.username, lang)

    try:
        table_number = callback.data.split(":")[1]
        order.set_table_number(table_number)
    except ValueError as error:
        await callback.answer(str(error), show_alert=True)
        return

    await state.set_state(OrderFSM.choosing_category)
    await callback.message.edit_text(
        f"✅ Table #{order.table_number} selected.\nChoose category:",
        reply_markup=category_keyboard(load_menu(), lang),
    )
    await callback.answer()


@router.message(OrderFSM.choosing_table)
async def choose_table_text(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("language", "ru")
    order = get_order(message.from_user.id, message.from_user.username, lang)

    try:
        order.set_table_number(message.text)
    except ValueError:
        await message.answer("❌ Please enter a valid table number from 1 to 36.")
        return

    await state.set_state(OrderFSM.choosing_category)
    await message.answer(
        f"✅ Table #{order.table_number} selected.\nChoose category:",
        reply_markup=category_keyboard(load_menu(), lang),
    )


@router.callback_query(F.data == "menu:categories")
async def show_categories(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("language", "ru")
    await state.set_state(OrderFSM.choosing_category)
    await callback.message.edit_text(
        "Choose category:",
        reply_markup=category_keyboard(load_menu(), lang),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("category:"))
async def show_items(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("language", "ru")
    category = callback.data.replace("category:", "", 1)
    items = [item for item in load_menu() if item.get("category") == category]

    await state.set_state(OrderFSM.choosing_items)
    await callback.message.edit_text(
        f"📋 {category}\n\nSelect an item:",
        reply_markup=items_keyboard(items, lang),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("add:"))
async def add_item(callback: CallbackQuery, state: FSMContext) -> None:
    allowed, status = check_working_status()
    if not allowed:
        await callback.message.edit_text(status)
        await callback.answer()
        return

    data = await state.get_data()
    lang = data.get("language", "ru")
    order = get_order(callback.from_user.id, callback.from_user.username, lang)
    item_id = callback.data.split(":", 1)[1]
    raw_item = find_raw_item(item_id)

    if raw_item is None:
        await callback.answer("Item not found.", show_alert=True)
        return

    try:
        item = build_menu_item(raw_item, language=lang)
        order.add_item(item)
    except ValueError as error:
        await callback.answer(str(error), show_alert=True)
        return

    await callback.answer(f"Added: {item.name}")


@router.callback_query(F.data == "cart:show")
async def show_cart(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("language", "ru")
    order = get_order(callback.from_user.id, callback.from_user.username, lang)

    await state.set_state(OrderFSM.viewing_cart)
    await callback.message.edit_text(format_cart(order), reply_markup=cart_keyboard())
    await callback.answer()


@router.callback_query(F.data == "cart:clear")
async def clear_cart(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("language", "ru")
    order = get_order(callback.from_user.id, callback.from_user.username, lang)
    order.clear()

    await callback.message.edit_text("🧹 Cart cleared.", reply_markup=category_keyboard(load_menu(), lang))
    await callback.answer()


@router.callback_query(F.data == "cart:confirm")
async def confirm_order(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    allowed, status = check_working_status()
    if not allowed:
        await callback.message.edit_text(status)
        await callback.answer()
        return

    data = await state.get_data()
    lang = data.get("language", "ru")
    order = get_order(callback.from_user.id, callback.from_user.username, lang)

    if order.is_empty():
        await callback.answer("Cart is empty.", show_alert=True)
        return

    if order.order_type == "hall" and order.table_number is None:
        await callback.answer("Choose table number first.", show_alert=True)
        return

    append_json_record(ORDERS_PATH, order.to_dict())
    receipt = order.make_receipt()

    if KITCHEN_GROUP_ID != 0:
        try:
            await bot.send_message(KITCHEN_GROUP_ID, receipt)
        except Exception as error:  # Telegram API errors should not crash guest flow.
            logging.exception("Could not send order to kitchen group: %s", error)

    active_orders.pop(callback.from_user.id, None)
    await state.clear()
    await callback.message.edit_text(
        "✅ Order confirmed!\n\n"
        "Your order has been sent to the kitchen.\n\n"
        f"{receipt}"
    )
    await callback.answer()


@router.message(F.photo)
async def handle_photo(message: Message) -> None:
    """Handle image messages, e.g., payment or table screenshots."""
    await message.answer(
        "📸 Image received. If this is a payment or table screenshot, "
        "please continue with the order flow or wait for administrator confirmation."
    )


@router.message(Command("plov"))
async def plov(message: Message) -> None:
    await message.answer(get_plov_status())


@router.message(Command("admin"))
async def admin(message: Message) -> None:
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ Access denied.")
        return

    await message.answer(
        "Admin panel: toggle stop-list status.",
        reply_markup=admin_menu_keyboard(load_menu()),
    )


@router.callback_query(F.data.startswith("admin_toggle:"))
async def admin_toggle(callback: CallbackQuery) -> None:
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Access denied.", show_alert=True)
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
        await callback.answer("Item not found.", show_alert=True)
        return

    write_json(MENU_PATH, menu)
    await callback.message.edit_reply_markup(reply_markup=admin_menu_keyboard(menu))
    await callback.answer("Status updated.")


@router.message()
async def fallback(message: Message) -> None:
    await message.answer(
        "I did not understand this message.\n"
        "Use /start to create an order or /plov to check plov schedule."
    )


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is missing. Create .env from .env.example.")

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

