# /example/example-dev.py
"""
Dev environment sanity example.

- Imports ChatBot
- Sends a test message
- Prints the JSON reply
- Confirms basic dependencies work

Usage:
    python example/example-dev.py
"""

import json
import sys

try:
    from agenticcore.chatbot.services import ChatBot
except ImportError as e:
    print("❌ Could not import ChatBot. Did you set PYTHONPATH or install dependencies?")
    sys.exit(1)


def main():
    bot = ChatBot()
    msg = "Hello from example-dev!"
    result = bot.reply(msg)

    print("✅ Dev environment is working")
    print("Input:", msg)
    print("Reply JSON:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
