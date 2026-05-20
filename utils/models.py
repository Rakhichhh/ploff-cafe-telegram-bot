"""Object-oriented domain models for the cafe bot.

This module demonstrates:
- classes and objects;
- inheritance: FoodItem and DrinkItem inherit from MenuItem;
- polymorphism: get_details() behaves differently in subclasses;
- encapsulation: Order hides internal calculations behind methods.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from config import MAX_TABLE_NUMBER, TAKEAWAY_CONTAINER_PRICE


@dataclass
class MenuItem:
    """Base menu item."""

    item_id: str
    name: str
    price: int
    category: str
    is_available: bool = True

    def get_details(self) -> str:
        """Return a human-readable item description."""
        status = "✅" if self.is_available else "⛔"
        return f"{status} {self.name} — {self.price} ₸"


@dataclass
class FoodItem(MenuItem):
    """Food menu item with weight and optional plov schedule logic."""

    weight_grams: int = 0
    is_plov: bool = False

    def get_details(self) -> str:
        status = "✅" if self.is_available else "⛔"
        plov_note = " | казан 12:00, 15:00, 18:00" if self.is_plov else ""
        return f"{status} 🍽 {self.name} — {self.price} ₸ | {self.weight_grams} г{plov_note}"


@dataclass
class DrinkItem(MenuItem):
    """Drink menu item with volume."""

    volume_liters: float = 0.0

    def get_details(self) -> str:
        status = "✅" if self.is_available else "⛔"
        return f"{status} 🥤 {self.name} — {self.price} ₸ | {self.volume_liters:g} л"


@dataclass
class CartLine:
    """One line inside an order cart."""

    item: MenuItem
    quantity: int = 1

    @property
    def line_total(self) -> int:
        return self.item.price * self.quantity


@dataclass
class Order:
    """Customer order with validation and receipt generation."""

    user_id: int
    username: Optional[str] = None
    order_type: str = "hall"
    table_number: Optional[int] = None
    language: str = "ru"
    items: List[CartLine] = field(default_factory=list)

    @staticmethod
    def validate_table_number(value: object) -> int:
        """Validate table number strictly in range 1..36."""
        try:
            table_number = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("Table number must be an integer.") from exc

        if not 1 <= table_number <= MAX_TABLE_NUMBER:
            raise ValueError(f"Table number must be from 1 to {MAX_TABLE_NUMBER}.")

        return table_number

    def set_table_number(self, value: object) -> None:
        self.table_number = self.validate_table_number(value)

    def set_takeaway(self) -> None:
        self.order_type = "takeaway"
        self.table_number = None

    def add_item(self, item: MenuItem, quantity: int = 1) -> None:
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")
        if not item.is_available:
            raise ValueError(f"{item.name} is currently unavailable.")

        for line in self.items:
            if line.item.item_id == item.item_id:
                line.quantity += quantity
                return

        self.items.append(CartLine(item=item, quantity=quantity))

    def remove_item(self, item_id: str) -> bool:
        before = len(self.items)
        self.items = [line for line in self.items if line.item.item_id != item_id]
        return len(self.items) != before

    def clear(self) -> None:
        self.items.clear()

    def subtotal(self) -> int:
        return sum(line.line_total for line in self.items)

    def service_fee(self) -> int:
        return TAKEAWAY_CONTAINER_PRICE if self.order_type == "takeaway" and self.items else 0

    def total(self) -> int:
        return self.subtotal() + self.service_fee()

    def is_empty(self) -> bool:
        return not self.items

    def to_dict(self) -> Dict[str, object]:
        return {
            "user_id": self.user_id,
            "username": self.username,
            "order_type": self.order_type,
            "table_number": self.table_number,
            "language": self.language,
            "items": [
                {
                    "item_id": line.item.item_id,
                    "name": line.item.name,
                    "price": line.item.price,
                    "quantity": line.quantity,
                    "line_total": line.line_total,
                }
                for line in self.items
            ],
            "subtotal": self.subtotal(),
            "service_fee": self.service_fee(),
            "total": self.total(),
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }

    def make_receipt(self) -> str:
        """Create a clear receipt for kitchen/admin group."""
        if self.is_empty():
            return "Корзина пуста."

        location = (
            f"Стол №{self.table_number}"
            if self.order_type == "hall"
            else "Навынос | Упаковать с собой"
        )
        username = f"@{self.username}" if self.username else "No username"

        lines = [
            "🧾 НОВЫЙ ЗАКАЗ | NEW ORDER",
            f"👤 User ID: {self.user_id} ({username})",
            f"📍 Location: {location}",
            "-------------------------",
        ]

        for index, line in enumerate(self.items, start=1):
            lines.append(
                f"{index}. {line.item.name} x{line.quantity} = {line.line_total} ₸"
            )

        lines.extend(
            [
                "-------------------------",
                f"Subtotal: {self.subtotal()} ₸",
                f"Container: {self.service_fee()} ₸",
                f"TOTAL: {self.total()} ₸",
            ]
        )
        return "\n".join(lines)


def build_menu_item(raw: Dict[str, object], language: str = "ru") -> MenuItem:
    """Factory that converts a JSON dictionary into a typed OOP object."""
    item_type = str(raw.get("type", "food"))
    item_id = str(raw.get("id", "unknown"))
    category = str(raw.get("category", "Other"))
    price = int(raw.get("price", 0))
    is_available = bool(raw.get("is_available", True))
    name_key = f"name_{language}"
    name = str(raw.get(name_key) or raw.get("name_ru") or raw.get("name_en") or item_id)

    if item_type == "drink":
        return DrinkItem(
            item_id=item_id,
            name=name,
            price=price,
            category=category,
            is_available=is_available,
            volume_liters=float(raw.get("volume_liters", 0.0)),
        )

    return FoodItem(
        item_id=item_id,
        name=name,
        price=price,
        category=category,
        is_available=is_available,
        weight_grams=int(raw.get("weight_grams", 0)),
        is_plov=bool(raw.get("is_plov", False)),
    )

