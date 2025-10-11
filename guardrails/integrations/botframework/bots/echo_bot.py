# /integrations/botframework/bots/echo_bot.py
# from botbuilder.core import ActivityHandler, TurnContext
# from botbuilder.schema import ChannelAccount

def simple_sentiment(text: str):
    """
    Tiny, no-cost heuristic so you can demo behavior without extra services.
    You can swap this later for HF/OpenAI/Azure easily.
    """
    t = (text or "").lower()
    pos = any(w in t for w in ["love","great","good","awesome","fantastic","excellent","amazing"])
    neg = any(w in t for w in ["hate","bad","terrible","awful","worst","horrible","angry"])
    if pos and not neg:  return "positive", 0.9
    if neg and not pos:  return "negative", 0.9
    return "neutral", 0.5

CAPS = [
    "Echo what you say (baseline).",
    "Show my capabilities with 'help' or 'capabilities'.",
    "Handle malformed/empty input politely.",
    "Classify simple sentiment (positive/negative/neutral).",
]

class EchoBot(ActivityHandler):
    async def on_members_added_activity(
        self, members_added: [ChannelAccount], turn_context: TurnContext
    ):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity(
                    "Hi! I’m your sample bot.\n"
                    "- Try typing: **help**\n"
                    "- Or any sentence and I’ll echo it + sentiment."
                )

    async def on_message_activity(self, turn_context: TurnContext):
        text = (turn_context.activity.text or "").strip()

        # Handle empty/malformed
        if not text:
            await turn_context.send_activity(
                "I didn’t catch anything. Please type a message (or 'help')."
            )
            return

        # Capabilities
        if text.lower() in {"help","capabilities","what can you do"}:
            caps = "\n".join(f"• {c}" for c in CAPS)
            await turn_context.send_activity(
                "Here’s what I can do:\n" + caps
            )
            return

        # Normal message → echo + sentiment
        label, score = simple_sentiment(text)
        reply = f"You said: **{text}**\nSentiment: **{label}** (conf {score:.2f})"
        await turn_context.send_activity(reply)
