# /logged_in_bot/handler.py

from agenticcore.chatbot.services import ChatBot

_bot = ChatBot()

def handle_turn(message, history, user):
    history = history or []
    try:
        res = _bot.reply(message)
        reply = res.get("reply") or "Noted."
        label = res.get("sentiment")
        conf = res.get("confidence")
        if label is not None and conf is not None:
            reply = f"{reply} (sentiment: {label}, confidence: {float(conf):.2f})"
    except Exception as e:
        reply = f"Sorry—error in ChatBot: {type(e).__name__}. Using fallback."
    history = history + [[message, reply]]
    return history

