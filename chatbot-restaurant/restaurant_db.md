```python
"""SQLite setup and query helpers for the restaurant chatbot."""

import sqlite3
from typing import Any, Dict, List, Tuple, cast


def initialize_database(db_path: str = "restaurant.sqlite") -> None:
    """Create tables and seed starter data if this is a new database."""
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS menu_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                price REAL NOT NULL,
                is_vegetarian INTEGER NOT NULL DEFAULT 0,
                is_spicy INTEGER NOT NULL DEFAULT 0,
                is_available INTEGER NOT NULL DEFAULT 1
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS restaurant_details (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                name TEXT NOT NULL,
                address TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT NOT NULL,
                website TEXT NOT NULL
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS opening_hours (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                day_of_week TEXT NOT NULL UNIQUE,
                open_time TEXT NOT NULL,
                close_time TEXT NOT NULL,
                notes TEXT
            )
            """
        )

        _seed_if_empty(conn)


def _seed_if_empty(conn: sqlite3.Connection) -> None:
    """Insert a small demo dataset once, keeping reruns idempotent."""
    has_menu = conn.execute("SELECT COUNT(*) FROM menu_items").fetchone()[0] > 0
    has_details = conn.execute("SELECT COUNT(*) FROM restaurant_details").fetchone()[0] > 0
    has_hours = conn.execute("SELECT COUNT(*) FROM opening_hours").fetchone()[0] > 0

    if not has_menu:
        menu_rows = [
            ("Margherita Pizza", "Main", "Tomato, mozzarella, basil", 10.50, 1, 0, 1),
            ("Spicy Chicken Burger", "Main", "Grilled chicken, jalapeno mayo", 11.90, 0, 1, 1),
            ("Caesar Salad", "Starter", "Romaine, parmesan, croutons", 7.25, 0, 0, 1),
            ("Mushroom Risotto", "Main", "Creamy arborio rice with mushrooms", 12.75, 1, 0, 1),
            ("Lemon Tart", "Dessert", "House-made tart with lemon curd", 5.20, 1, 0, 1),
            ("Iced Latte", "Drinks", "Espresso with cold milk and ice", 4.60, 1, 0, 1),
        ]
        conn.executemany(
            """
            INSERT INTO menu_items
            (item_name, category, description, price, is_vegetarian, is_spicy, is_available)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            menu_rows,
        )

    if not has_details:
        conn.execute(
            """
            INSERT INTO restaurant_details (id, name, address, phone, email, website)
            VALUES (1, ?, ?, ?, ?, ?)
            """,
            (
                "Sunset Bistro",
                "123 Market Street, Springfield",
                "+1-555-0142",
                "hello@sunsetbistro.example",
                "www.sunsetbistro.example",
            ),
        )

    if not has_hours:
        hours_rows = [
            ("Monday", "09:00", "21:00", ""),
            ("Tuesday", "09:00", "21:00", ""),
            ("Wednesday", "09:00", "21:00", ""),
            ("Thursday", "09:00", "22:00", ""),
            ("Friday", "09:00", "23:00", ""),
            ("Saturday", "10:00", "23:00", "Brunch menu until 14:00"),
            ("Sunday", "10:00", "20:00", "Family set menu available"),
        ]
        conn.executemany(
            """
            INSERT INTO opening_hours (day_of_week, open_time, close_time, notes)
            VALUES (?, ?, ?, ?)
            """,
            hours_rows,
        )


def get_menu_items(db_path: str) -> List[Dict[str, Any]]:
    """Return all menu rows as dictionaries."""
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT item_name, category, description, price, is_vegetarian, is_spicy, is_available
            FROM menu_items
            ORDER BY category, item_name
            """
        ).fetchall()
    return [cast(Dict[str, Any], dict(row)) for row in rows]


def search_menu_items(db_path: str, query: str) -> List[Dict[str, Any]]:
    """Simple LIKE-based search used to fetch only relevant menu rows."""
    tokens = [t.strip().lower() for t in query.split() if len(t.strip()) >= 3]
    if not tokens:
        return get_menu_items(db_path)

    where_clauses = []
    params: List[str] = []
    for token in tokens[:6]:
        where_clauses.append("(LOWER(item_name) LIKE ? OR LOWER(description) LIKE ? OR LOWER(category) LIKE ?)")
        wildcard = f"%{token}%"
        params.extend([wildcard, wildcard, wildcard])

    sql = (
        "SELECT item_name, category, description, price, is_vegetarian, is_spicy, is_available "
        "FROM menu_items WHERE " + " OR ".join(where_clauses) + " ORDER BY category, item_name"
    )

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(sql, params).fetchall()

    return [cast(Dict[str, Any], dict(row)) for row in rows]


def get_restaurant_details_and_hours(db_path: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Return one restaurant details row and all opening-hours rows."""
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        details_row = conn.execute(
            "SELECT name, address, phone, email, website FROM restaurant_details WHERE id = 1"
        ).fetchone()
        hours_rows = conn.execute(
            "SELECT day_of_week, open_time, close_time, notes FROM opening_hours ORDER BY id"
        ).fetchall()

    details = cast(Dict[str, Any], dict(details_row)) if details_row else {}
    hours = [cast(Dict[str, Any], dict(row)) for row in hours_rows]
    return details, hours


```