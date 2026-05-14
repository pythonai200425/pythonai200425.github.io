import argparse
import json
import sys
import threading
import time
from typing import List, Dict

import requests

DEFAULT_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "llama3.1:8b"
DEFAULT_MAX_TOKENS = 120
DEFAULT_CONTEXT = 1024


def wait_for_ollama(base_url: str, timeout_seconds: int = 120) -> bool:
    """Wait until the Ollama API is reachable."""
    # Poll the tags endpoint once per second until the server responds.
    for _ in range(timeout_seconds):
        try:
            r = requests.get(f"{base_url}/api/tags", timeout=2)
            if r.status_code == 200:
                return True
        except requests.RequestException:
            pass
    return False


def chat_once(
    base_url: str,
    model: str,
    messages: List[Dict[str, str]],
    max_tokens: int,
    context_size: int,
) -> str:
    # Use non-stream mode for simpler, robust parsing on slower machines.
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            # Keep responses short and context small for faster CPU inference.
            "num_predict": max_tokens,
            "num_ctx": context_size,
        },
    }

    r = requests.post(
        f"{base_url}/api/chat",
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload),
        timeout=600,
    )

    if r.status_code != 200:
        raise RuntimeError(f"Ollama error {r.status_code}: {r.text}")

    data = r.json()
    return data["message"]["content"]


def show_wait_spinner(stop_event: threading.Event) -> None:
    frames = ["|", "/", "-", "\\"]
    i = 0
    while not stop_event.is_set():
        print(f"\rAssistant is thinking {frames[i % len(frames)]}", end="", flush=True)
        i += 1
        time.sleep(0.2)
    # Clear the spinner line before printing the model response.
    print("\r" + " " * 40 + "\r", end="", flush=True)


def interactive_chat(base_url: str, model: str, max_tokens: int, context_size: int) -> None:
    print(f"Connected to {base_url}")
    print(f"Using model: {model}")
    print("Type 'exit' to quit.\n")

    messages: List[Dict[str, str]] = [
        # Keep one system instruction at the start of the conversation.
        {
            "role": "system",
            "content": "You are a helpful assistant.",
        }
    ]

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            print("Goodbye.")
            return
        if not user_input:
            continue

        messages.append({"role": "user", "content": user_input})

        try:
            # First response can take time on CPU, so show visible progress.
            stop_event = threading.Event()
            spinner_thread = threading.Thread(
                target=show_wait_spinner, args=(stop_event,), daemon=True
            )
            spinner_thread.start()
            reply = chat_once(base_url, model, messages, max_tokens, context_size)
            stop_event.set()
            spinner_thread.join(timeout=1)
        except Exception as exc:  # noqa: BLE001
            # Always stop spinner on failures to avoid a stuck terminal line.
            stop_event.set()
            spinner_thread.join(timeout=1)
            print(f"Error: {exc}", file=sys.stderr)
            continue

        print(f"Assistant: {reply}\n")
        messages.append({"role": "assistant", "content": reply})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Chat with a local Ollama model")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Ollama API URL")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Model name in Ollama")
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=DEFAULT_MAX_TOKENS,
        help="Maximum tokens per assistant reply (smaller is faster)",
    )
    parser.add_argument(
        "--context-size",
        type=int,
        default=DEFAULT_CONTEXT,
        help="Context window size to use for generation (smaller is faster)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not wait_for_ollama(args.base_url):
        raise SystemExit(
            "Ollama is not reachable. Start docker compose first and wait for model download."
        )

    interactive_chat(args.base_url, args.model, args.max_tokens, args.context_size)


if __name__ == "__main__":
    main()
