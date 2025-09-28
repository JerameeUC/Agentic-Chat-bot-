# /example/example.py
"""
Simple CLI/REPL example for the ChatBot.

Usage:
    python example/example.py "hello world"
    python example/example.py        # enters interactive mode
"""

import argparse
import json
import sys

try:
    from agenticcore.chatbot.services import ChatBot
except ImportError as e:
    print("❌ Could not import ChatBot. Did you set PYTHONPATH or install agenticcore?")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="ChatBot CLI/REPL example")
    parser.add_argument(
        "message",
        nargs="*",
        help="Message to send. Leave empty to start interactive mode.",
    )
    args = parser.parse_args()

    try:
        bot = ChatBot()
    except Exception as e:
        print(f"❌ Failed to initialize ChatBot: {e}")
        sys.exit(1)

    if args.message:
        # One-shot mode
        msg = " ".join(args.message)
        result = bot.reply(msg)
        print(json.dumps(result, indent=2))
    else:
        # Interactive REPL
        print("💬 Interactive mode. Type 'quit' or 'exit' to stop.")
        while True:
            try:
                msg = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n👋 Exiting.")
                break

            if msg.lower() in {"quit", "exit"}:
                print("👋 Goodbye.")
                break

            if not msg:
                continue

            result = bot.reply(msg)
            print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
