```python
"""CLI entrypoint for the LangChain + SQLite restaurant chatbot."""

from dotenv import load_dotenv

from restaurant_chatbot import RestaurantChatbot
from restaurant_db import initialize_database


def main() -> None:
    # Load OPENAI_API_KEY from the project's .env file.
    load_dotenv()

    db_path = "restaurant.sqlite"

    # Ensure tables exist and starter rows are present before chatting.
    initialize_database(db_path)

    bot = RestaurantChatbot(db_path=db_path)

    print("Restaurant chatbot is ready. Type 'exit' to quit.")
    print("Try: 'What vegetarian dishes do you have?' or 'What are your opening hours?'\n")

    while True:
        user_input = input("You: ").strip()
        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit"}:
            print("Bot: Goodbye!")
            break

        reply = bot.answer(user_input)
        print(f"Bot: {reply}\n")


if __name__ == "__main__":
    main()

```