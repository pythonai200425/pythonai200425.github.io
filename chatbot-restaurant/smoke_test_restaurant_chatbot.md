```python
"""Smoke test for the SQLite-backed restaurant chatbot."""

import os
import tempfile
import uuid

from restaurant_chatbot import RestaurantChatbot
from restaurant_db import get_menu_items, get_restaurant_details_and_hours, initialize_database


def run_smoke_test() -> None:
    # Use a unique temp-db path and keep cleanup best-effort for Windows locks.
    db_path = os.path.join(tempfile.gettempdir(), f"test_restaurant_{uuid.uuid4().hex}.sqlite")
    initialize_database(db_path)

    menu = get_menu_items(db_path)
    details, hours = get_restaurant_details_and_hours(db_path)

    assert len(menu) >= 3, "Menu should have seeded items"
    assert details.get("name"), "Restaurant details should be seeded"
    assert len(hours) == 7, "Opening hours should include all days"

    # Force local fallback path so test does not depend on network/API.
    old_key = os.environ.pop("OPENAI_API_KEY", None)
    try:
        bot = RestaurantChatbot(db_path=db_path)
        menu_reply = bot.answer("What vegetarian dishes are on the menu?")
        missing_item_reply = bot.answer("Do you have fish in the menu?")
        details_reply = bot.answer("What are your opening hours and address?")
        other_reply = bot.answer("Can you tell me a joke?")
    finally:
        if old_key is not None:
            os.environ["OPENAI_API_KEY"] = old_key

    assert "Margherita Pizza" in menu_reply or "Mushroom Risotto" in menu_reply
    assert "could not find that item" in missing_item_reply
    assert "Opening Hours" in details_reply and "Address" in details_reply
    assert "I can help with menu items" in other_reply

    try:
        os.remove(db_path)
    except OSError:
        pass


if __name__ == "__main__":
    run_smoke_test()
    print("smoke_test_restaurant_chatbot.py: PASS")

```