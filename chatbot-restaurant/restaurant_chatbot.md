```python
"""LangChain chatbot that routes questions to menu/details/other."""

import os
from typing import List

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from restaurant_db import get_restaurant_details_and_hours, search_menu_items


class RestaurantChatbot:
    """RAG-style restaurant assistant backed by SQLite tables."""

    def __init__(self, db_path: str, model_name: str = "gpt-4o-mini") -> None:
        self.db_path = db_path
        self.llm = None

        # If an API key exists, use OpenAI through LangChain.
        if os.getenv("OPENAI_API_KEY"):
            self.llm = ChatOpenAI(model=model_name, temperature=0)

        # Classifier prompt decides which data source we should read.
        self.classifier_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a router. Classify each question as exactly one label: "
                    "menu, details, or other. Return only the label.",
                ),
                ("human", "Question: {question}"),
            ]
        )

        # Answer prompt consumes retrieved SQL context and forms a final reply.
        self.answer_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful restaurant assistant. Use only the provided context. "
                    "If context does not contain the answer, say you are not sure and ask a clarifying question. "
                    "Never ask which restaurant the user means.",
                ),
                ("human", "Question: {question}\n\nContext:\n{context}"),
            ]
        )

    def classify_question(self, question: str) -> str:
        """Classify into menu/details/other, with a deterministic fallback path."""
        lower_q = question.lower()

        # Keyword fallback keeps the app usable even without an API key.
        if any(k in lower_q for k in ["menu", "dish", "food", "price", "vegan", "vegetarian", "spicy", "drink"]):
            return "menu"
        if any(k in lower_q for k in ["hour", "open", "close", "address", "phone", "location", "email", "website"]):
            return "details"

        if not self.llm:
            return "other"

        chain = self.classifier_prompt | self.llm | StrOutputParser()
        label = chain.invoke({"question": question}).strip().lower()
        if label in {"menu", "details", "other"}:
            return label
        return "other"

    def _build_menu_context(self, question: str) -> tuple[str, bool]:
        rows = search_menu_items(self.db_path, question)
        if not rows:
            return "No menu records matched the question.", False

        lines: List[str] = []
        for row in rows:
            veg = "vegetarian" if row["is_vegetarian"] else "non-vegetarian"
            spicy = "spicy" if row["is_spicy"] else "not spicy"
            status = "available" if row["is_available"] else "currently unavailable"
            lines.append(
                f"- {row['item_name']} ({row['category']}): {row['description']} | "
                f"${row['price']:.2f} | {veg}, {spicy}, {status}"
            )
        return "\n".join(lines), True

    def _build_details_context(self) -> str:
        details, hours = get_restaurant_details_and_hours(self.db_path)
        if not details:
            return "No restaurant details found."

        details_text = (
            f"Name: {details['name']}\n"
            f"Address: {details['address']}\n"
            f"Phone: {details['phone']}\n"
            f"Email: {details['email']}\n"
            f"Website: {details['website']}"
        )

        hours_lines = [
            f"- {h['day_of_week']}: {h['open_time']} to {h['close_time']}"
            + (f" ({h['notes']})" if h.get("notes") else "")
            for h in hours
        ]
        return details_text + "\n\nOpening Hours:\n" + "\n".join(hours_lines)

    def answer(self, question: str) -> str:
        """Route question, retrieve matching SQLite data, and generate an answer."""
        route = self.classify_question(question)

        if route == "menu":
            context, has_match = self._build_menu_context(question)
            if not has_match:
                return (
                    "I could not find that item in the current menu. "
                    "Ask me to list available mains, starters, desserts, or drinks."
                )
        elif route == "details":
            context = self._build_details_context()
        else:
            return (
                "I can help with menu items, prices, ingredients, and restaurant details "
                "like opening hours, phone, and address."
            )

        # Without OpenAI, return context directly so the app is still functional.
        if not self.llm:
            return f"(Local fallback, no OpenAI key configured)\n{context}"

        chain = self.answer_prompt | self.llm | StrOutputParser()
        return chain.invoke({"question": question, "context": context})

```