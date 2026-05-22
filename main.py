"""Main entry point for the PLOFF Cafe Telegram bot.

Run:
    python main.py
"""

from __future__ import annotations

import asyncio
import logging
from functools import wraps
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


def admin_required(handler):
    """Custom decorator that allows only admins to use protected handlers."""

    @wraps(handler)
    async def wrapper(event, *args, **kwargs):
        if event.from_user.id not in ADMIN_IDS:
            if isinstance(event, CallbackQuery):
                await event.answer("⛔ Access denied.", show_alert=True)
            else:
                await event.answer("⛔ Access denied.")
            return

        return await handler(event, *args, **kwargs)

    return wrapper


def generate_cart_lines(order: Order):
    """Generator that creates cart text line by line."""
    if order.is_empty():
        yield "🛒 Корзина пуста."
        return

    yield "🛒 Your cart:"

    for line in order.items:
        yield f"• {line.item.name} x{line.quantity} = {line.line_total} ₸"

    yield f"\nSubtotal: {order.subtotal()} ₸"

    if order.service_fee():
        yield f"Container: {order.service_fee()} ₸"

    yield f"TOTAL: {order.total()} ₸"


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
    return "\n".join(generate_cart_lines(order))


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
        f"{status}\n\n📍 {CAFE_ADDRESS}\n🔥 {get_plov_status()}\n\n"
        "Choose order type:",
        reply_markup=order_type_keyboard(lang),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("order_type:"))
async def choose_order_type(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle dine-in or takeaway selection."""
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
    """Handle table number selected by button."""
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
    """Handle manually typed table number."""
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
    """Show menu categories."""
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
    """Show items from selected category."""
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
    """Add selected item to cart."""
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
    """Show cart."""
    data = await state.get_data()
    lang = data.get("language", "ru")
    order = get_order(callback.from_user.id, callback.from_user.username, lang)

    await state.set_state(OrderFSM.viewing_cart)
    await callback.message.edit_text(format_cart(order), reply_markup=cart_keyboard())
    await callback.answer()


@router.callback_query(F.data == "cart:clear")
async def clear_cart(callback: CallbackQuery, state: FSMContext) -> None:
    """Clear cart."""
    data = await state.get_data()
    lang = data.get("language", "ru")
    order = get_order(callback.from_user.id, callback.from_user.username, lang)
    order.clear()

    await callback.message.edit_text(
        "🧹 Cart cleared.",
        reply_markup=category_keyboard(load_menu(), lang),
    )
    await callback.answer()


@router.callback_query(F.data == "cart:confirm")
async def confirm_order(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    """Confirm order, save it to JSON, and send receipt to kitchen group."""
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
    """Show plov schedule."""
    await message.answer(get_plov_status())


@router.message(Command("help"))
async def help_command(message: Message) -> None:
    """Show help command."""
    await message.answer(
        "📌 Commands:\n"
        "/start — start order\n"
        "/plov — check fresh plov schedule\n"
        "/admin — open admin panel"
    )


@router.message(Command("admin"))
@admin_required
async def admin(message: Message) -> None:
    """Open protected admin panel."""
    await message.answer(
        "Admin panel: toggle stop-list status.",
        reply_markup=admin_menu_keyboard(load_menu()),
    )


@router.callback_query(F.data.startswith("admin_toggle:"))
@admin_required
async def admin_toggle(callback: CallbackQuery) -> None:
    """Toggle menu item availability."""
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
    """Fallback for unknown messages."""
    await message.answer(
        "I did not understand this message.\n"
        "Use /start to create an order or /plov to check plov schedule."
    )


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
