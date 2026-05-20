"""Unit tests for the domain models."""

import unittest

from utils.models import DrinkItem, FoodItem, Order


class TestOrderModel(unittest.TestCase):
    def setUp(self):
        self.plov = FoodItem(
            item_id="chaihana_plov",
            name="Chaykhana plov",
            price=1990,
            category="Main dishes",
            weight_grams=350,
            is_plov=True,
        )
        self.cola = DrinkItem(
            item_id="cola_05",
            name="Cola 0.5 L",
            price=990,
            category="Cold drinks",
            volume_liters=0.5,
        )

    def test_hall_order_total_without_container_fee(self):
        order = Order(user_id=1, order_type="hall", table_number=10)
        order.add_item(self.plov, quantity=2)
        order.add_item(self.cola, quantity=1)

        self.assertEqual(order.subtotal(), 4970)
        self.assertEqual(order.service_fee(), 0)
        self.assertEqual(order.total(), 4970)

    def test_takeaway_order_total_with_container_fee(self):
        order = Order(user_id=1, order_type="takeaway")
        order.add_item(self.plov, quantity=1)

        self.assertEqual(order.subtotal(), 1990)
        self.assertEqual(order.service_fee(), 50)
        self.assertEqual(order.total(), 2040)

    def test_valid_table_number(self):
        self.assertEqual(Order.validate_table_number("36"), 36)
        self.assertEqual(Order.validate_table_number(1), 1)

    def test_invalid_table_number_zero(self):
        with self.assertRaises(ValueError):
            Order.validate_table_number(0)

    def test_invalid_table_number_above_range(self):
        with self.assertRaises(ValueError):
            Order.validate_table_number(37)

    def test_invalid_table_number_text(self):
        with self.assertRaises(ValueError):
            Order.validate_table_number("abc")

    def test_unavailable_item_cannot_be_added(self):
        self.plov.is_available = False
        order = Order(user_id=1)
        with self.assertRaises(ValueError):
            order.add_item(self.plov)


if __name__ == "__main__":
    unittest.main()
