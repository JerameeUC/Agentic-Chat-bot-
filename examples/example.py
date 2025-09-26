# /example/example.py
"""Simple CLI example that sends a message to the ChatBot and prints the JSON reply."""
import json
from agenticcore.chatbot.services import ChatBot

if __name__ == "__main__":
    bot = ChatBot()
    result = bot.reply("hello world")
    print(json.dumps(result, indent=2))
