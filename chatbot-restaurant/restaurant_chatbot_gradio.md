```python
"""Gradio web UI for the SQLite + LangChain restaurant chatbot."""

from dotenv import load_dotenv
import gradio as gr

from restaurant_chatbot import RestaurantChatbot
from restaurant_db import initialize_database


def create_bot(db_path: str = "restaurant.sqlite") -> RestaurantChatbot:
    """Load environment variables, ensure DB exists, then build chatbot."""
    # Reads OPENAI_API_KEY from .env if present.
    load_dotenv()

    # Creates tables and seed rows before the first user question.
    initialize_database(db_path)
    return RestaurantChatbot(db_path=db_path)


def build_demo(bot: RestaurantChatbot) -> gr.Blocks:
    """Construct the Gradio chat interface around the chatbot backend."""

    def chat_handler(message: str, history: list[dict]) -> tuple[list[dict], str]:
        """Append the user question and bot answer in Gradio messages format."""
        history = history or []
        user_text = (message or "").strip()
        if not user_text:
            return history, ""

        answer = bot.answer(user_text)
        updated_history = history + [
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": answer},
        ]
        return updated_history, ""

    with gr.Blocks(title="Restaurant Chatbot") as demo:
        gr.Markdown("## Restaurant Chatbot\nAsk about menu items, prices, or opening hours.")

        chatbot = gr.Chatbot(label="Conversation", height=450)
        message_box = gr.Textbox(label="Your question", placeholder="e.g., What vegetarian dishes do you have?")

        with gr.Row():
            send_btn = gr.Button("Send", variant="primary")
            clear_btn = gr.Button("Clear")

        send_btn.click(chat_handler, inputs=[message_box, chatbot], outputs=[chatbot, message_box])
        message_box.submit(chat_handler, inputs=[message_box, chatbot], outputs=[chatbot, message_box])
        clear_btn.click(lambda: [], outputs=chatbot, queue=False)

        gr.Examples(
            examples=[
                "What are your opening hours?",
                "What spicy dishes are available?",
                "What is your phone number and address?",
            ],
            inputs=message_box,
        )

    return demo


def main() -> None:
    """Run the web app."""
    bot = create_bot()
    demo = build_demo(bot)
    # Use port 7861 to avoid conflict with rag_pdf.py which runs on 7860.
    demo.launch(server_port=7861)


if __name__ == "__main__":
    main()

```