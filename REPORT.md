# Project Report: PLOFF Cafe Telegram Ordering Bot

**Course:** Introduction to Programming 2  
**University:** Astana IT University  
**Department:** Software Engineering  
**Group:** SE-2518  
**Team Members:** Aibar Khairshakov, Rakhat Myrzabekov  

---

## 1. Problem Statement

Traditional cafe service often creates operational delays during peak hours. Waiters and cashiers spend time accepting orders manually, writing them down, calculating totals, and transferring information to the kitchen. This process increases the risk of human mistakes, such as incorrect order details, missed items, or wrong table numbers.

Another problem is menu availability. Some dishes, such as plov from a cauldron, depend on a strict preparation schedule. Paper menus cannot quickly reflect unavailable items, and guests may order dishes that are temporarily out of stock.

The project solves these problems by creating a Telegram-based self-service ordering system for a cafe in Uralsk.

---

## 2. Solution Overview

The solution is a Python Telegram bot built with aiogram 3.x. The bot allows guests to choose a language, select dine-in or takeaway, choose a table number if needed, browse the menu, add items to the cart, and confirm the order.

After confirmation, the order is saved in a JSON file and sent to a private kitchen/admin Telegram group as a formatted receipt.

The bot also includes an admin panel where authorized managers can turn menu items on or off. This implements a stop-list system for unavailable dishes.

---

## 3. System Design

The project follows a modular architecture.

```text
User
  ↓
Telegram Bot Interface
  ↓
Order Flow and Validation
  ↓
OOP Domain Models
  ↓
JSON Storage
  ↓
Kitchen/Admin Telegram Group
```

Main modules:

- `main.py` — Telegram bot entry point and handlers
- `utils/models.py` — OOP models for menu items and orders
- `utils/file_manager.py` — safe JSON read/write operations
- `utils/helpers.py` — business logic for working hours and plov schedule
- `utils/keyboards.py` — Telegram inline keyboard builders
- `data/menu.json` — menu database
- `data/orders.json` — saved order history
- `tests/test_models.py` — unit tests

---

## 4. OOP Implementation

The system uses a base class `MenuItem` and two inherited classes: `FoodItem` and `DrinkItem`.

`FoodItem` adds food-specific attributes such as weight and plov logic. `DrinkItem` adds drink-specific volume information.

Polymorphism is implemented through the `get_details()` method. The same method name is used in all three classes, but the output changes depending on the object type.

The `Order` class aggregates selected `MenuItem` objects and handles business rules such as table validation, takeaway fee calculation, and receipt generation.

---

## 5. Data Persistence

The project uses JSON files to store persistent data.

`menu.json` stores menu items, prices, categories, language names, and availability statuses. Admin changes are written back to this file.

`orders.json` stores all confirmed orders, including user ID, order type, table number, items, subtotal, service fee, total price, and timestamp.

This allows data to remain available after the program is restarted.

---

## 6. Robustness and Edge Cases

The bot handles several important edge cases:

- invalid table numbers
- empty carts
- unavailable menu items
- broken or missing JSON files
- order attempts between 00:00 and 08:00
- Telegram kitchen group sending errors
- non-text image messages

The file manager uses `try/except` blocks to avoid crashes when a file is missing or corrupted.

---

## 7. Testing

The project includes unit tests with Python `unittest`.

The tests verify:

- correct total for dine-in orders
- correct total for takeaway orders with the 50 KZT container fee
- valid table number handling
- invalid table number handling
- unavailable item validation

Tests can be run with:

```bash
python -m unittest discover
```

---

## 8. Challenges Faced

The main challenge was converting real cafe rules into clean software logic. For example, the bot had to combine table validation, takeaway pricing, menu availability, working hours, and plov schedule logic in one consistent user flow.

Another challenge was keeping the project modular. Instead of placing all logic in one file, the system was separated into models, helpers, keyboard builders, and file storage modules.

---

## 9. Team Contributions

### Aibar Khairshakov

Aibar worked on the OOP architecture, domain classes, JSON file management, table validation, order calculation, and unit tests.

### Rakhat Myrzabekov

Rakhat worked on the Telegram bot interface, aiogram handlers, multilingual interaction flow, kitchen group integration, and admin stop-list functionality.

---

## 10. Conclusion

The project demonstrates practical Python skills applied to a real-world cafe automation scenario. It satisfies the course requirements for OOP, data persistence, robustness, modularity, testing, and project documentation.
