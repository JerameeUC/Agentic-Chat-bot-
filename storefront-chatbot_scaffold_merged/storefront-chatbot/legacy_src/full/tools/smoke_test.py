import os, json, requests
from agenticcore.chatbot.services import ChatBot

def p(title, data): print(f"\n== {title} ==\n{json.dumps(data, indent=2)}")

bot = ChatBot()
p("Lib/Direct", bot.reply("I really love this"))

url = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
r = requests.get(f"{url}/health"); p("API/Health", r.json())
r = requests.post(f"{url}/chatbot/message", json={"message":"api path test"}); p("API/Chat", r.json())
