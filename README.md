# PLOFF Cafe Telegram Ordering Bot

**Final Project for Introduction to Programming 2**  
**Astana IT University — Department of Software Engineering**  
**Group:** SE-2518  
**Students:** Aibar Khairshakov and Rakhat Myrzabekov  

This project is a ready-to-run Telegram bot for automating food orders in a real cafe scenario in **Uralsk, Kazakhstan**.  
The business case is based on PLOFF-style cafe operations: dine-in orders, takeaway orders, table validation, plov cauldron schedule, kitchen notifications, and an administrator stop-list panel.

---

## 1. Project Description

The bot automates the chain:

**Guest → Telegram Menu → Cart → Order Confirmation → Kitchen Group**

The system reduces manual work for waiters and cashiers, decreases order mistakes, and allows the cafe manager to quickly update unavailable menu items through the admin panel.

---

## 2. Business Rules

### Cafe Location

**City:** Uralsk  
**Address:** Stroitel 43b

### Working Hours

The bot uses Python `datetime` and the `Asia/Oral` timezone.

| Time | Bot Behavior |
|---|---|
| 00:00–08:00 | Orders are blocked |
| 08:00–11:00 | Pre-orders are accepted |
| 11:00–00:00 | Normal orders are accepted |

### Plov Cauldron Schedule

Fresh plov cauldrons are opened at:

- 12:00
- 15:00
- 18:00

The bot can show whether fresh plov is currently available or when the next cauldron opens.

### Table Validation

For dine-in orders, the guest must choose a table number from **1 to 36**.

Invalid values such as `0`, `37`, or text are rejected with a safe validation error.

### Takeaway Logic

For takeaway orders, the system automatically adds a fixed container fee:

**+50 KZT**

### Kitchen Integration

Every confirmed order is formatted as a clear kitchen receipt and sent to a private Telegram group using:

```python
KITCHEN_GROUP_ID
```

### Admin Stop-list

Managers can use:

```text
/admin
```

Only users listed in `ADMIN_IDS` can access the admin panel. The admin can toggle menu items as available/unavailable.

---

## 3. Features

- Telegram bot built with **aiogram 3.x**
- Multilingual support:
  - Russian
  - Kazakh
  - English
- Interactive inline keyboards
- Dine-in and takeaway order flow
- Table selection from 1 to 36
- JSON-based menu database
- JSON-based order history
- Cart system
- Automatic total price calculation
- Takeaway container fee calculation
- Plov schedule helper
- Admin stop-list panel
- Photo message handling
- Safe exception handling for JSON files
- Unit tests with `unittest`
- Modular project structure
- PEP 8 friendly naming and style

---

## 4. Technologies Used

- Python 3.11+
- aiogram 3.x
- python-dotenv
- JSON
- unittest
- pathlib
- datetime
- zoneinfo

---

## 5. Object-Oriented Programming

The project uses an OOP domain model in `utils/models.py`.

### Base Class

```python
MenuItem
```

Common attributes:

- `item_id`
- `name`
- `price`
- `category`
- `is_available`

### Inheritance

```python
FoodItem(MenuItem)
DrinkItem(MenuItem)
```

`FoodItem` adds:

- `weight_grams`
- `is_plov`

`DrinkItem` adds:

- `volume_liters`

### Polymorphism

The method:

```python
get_details()
```

is implemented differently in:

- `MenuItem`
- `FoodItem`
- `DrinkItem`

This demonstrates polymorphism because the bot can call the same method but receive different item descriptions depending on the object type.

### Order Class

```python
Order
```

The `Order` class handles:

- cart storage
- table number validation
- takeaway fee calculation
- total calculation
- receipt generation
- export to dictionary for JSON persistence

---

## 6. Project Structure

```text
cafe_telegram_bot/
│
├── main.py
├── config.py
├── requirements.txt
├── README.md
├── REPORT.md
├── .env.example
├── .gitignore
│
├── data/
│   ├── menu.json
│   └── orders.json
│
├── utils/
│   ├── __init__.py
│   ├── models.py
│   ├── file_manager.py
│   ├── helpers.py
│   └── keyboards.py
│
└── tests/
    ├── __init__.py
    └── test_models.py
```

---

## 7. Installation

Clone the repository:

```bash
git clone https://github.com/your-username/cafe-telegram-bot.git
cd cafe-telegram-bot
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate it on macOS/Linux:

```bash
source venv/bin/activate
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 8. Environment Variables

Create a `.env` file from `.env.example`:

```bash
cp .env.example .env
```

Fill it with your real Telegram values:

```env
BOT_TOKEN=your_telegram_bot_token
KITCHEN_GROUP_ID=-1001234567890
ADMIN_IDS=123456789,987654321
```

Do not commit `.env` to GitHub.

---

## 9. How to Run

```bash
python main.py
```

In Telegram, open your bot and send:

```text
/start
```

Admin command:

```text
/admin
```

Plov schedule command:

```text
/plov
```

---

## 10. How to Run Tests

Run all tests:

```bash
python -m unittest discover
```

Expected result:

```text
OK
```

---

## 11. Data Persistence

The project uses JSON files as local storage.

### `data/menu.json`

Stores all menu items with:

- id
- type
- category
- multilingual names
- price
- weight or volume
- availability status

### `data/orders.json`

Stores confirmed order history.

This meets the course requirement for reading from and writing to external files.

---

## 12. Robustness and Edge Cases

The bot handles:

- missing JSON files
- broken JSON files
- invalid table numbers
- unavailable menu items
- empty cart confirmation
- blocked order time from 00:00 to 08:00
- Telegram API send errors
- invalid user input

---

## 13. Team Member Roles

### Aibar Khairshakov

Responsible for:

- OOP architecture
- `MenuItem`, `FoodItem`, `DrinkItem`, and `Order` classes
- JSON file manager
- unit tests
- table validation and price calculation logic

### Rakhat Myrzabekov

Responsible for:

- Telegram bot interface
- aiogram handlers and FSM-like order flow
- inline keyboards
- kitchen group integration
- admin stop-list panel
- multilingual user flow

---

## 14. Academic Criteria Coverage

| Requirement | Implementation |
|---|---|
| OOP | `MenuItem`, `FoodItem`, `DrinkItem`, `Order` |
| Inheritance | `FoodItem` and `DrinkItem` inherit from `MenuItem` |
| Polymorphism | `get_details()` is overridden |
| Data Persistence | `menu.json` and `orders.json` |
| Robustness | `try/except` in JSON manager and bot flow |
| Modularity | Separate `utils/`, `data/`, `tests/` |
| Testing | `tests/test_models.py` |
| Telegram Menus | Inline keyboards |
| Different message types | Text, commands, callbacks, photos |
| Admin Panel | `/admin` stop-list management |

---

## 15. Notes

Menu data was prepared from the provided cafe menu screenshot. Prices and names should be verified once more against the official cafe source before production deployment.
