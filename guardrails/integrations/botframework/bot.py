# /intergrations/botframework/bot.py
"""
Simple MBF bot:
- 'help' / 'capabilities' shows features
- 'reverse <text>' returns reversed text
- otherwise delegates to AgenticCore ChatBot (sentiment) if available
"""

from typing import List, Optional, Dict, Any
# from botbuilder.core import ActivityHandler, TurnContext
# from botbuilder.schema import ChannelAccount, ActivityTypes

from skills import normalize, reverse_text, capabilities, is_empty

# Try to import AgenticCore; if unavailable, provide a tiny fallback.
try:
    from agenticcore.chatbot.services import ChatBot  # real provider-backed bot
except Exception:
    class ChatBot:  # fallback shim for offline/dev
        def reply(self, message: str) -> Dict[str, Any]:
            return {
                "reply": "Noted. (local fallback reply)",
                "sentiment": "neutral",
                "confidence": 0.5,
            }

def _format_sentiment(res: Dict[str, Any]) -> str:
    """Compose a user-facing string from ChatBot reply payload."""
    reply = (res.get("reply") or "").strip()
    label: Optional[str] = res.get("sentiment")
    conf = res.get("confidence")
    if label is not None and conf is not None:
        return f"{reply} (sentiment: {label}, confidence: {float(conf):.2f})"
    return reply or "I'm not sure what to say."

def _help_text() -> str:
    """Single source of truth for the help/capability text."""
    feats = "\n".join(f"- {c}" for c in capabilities())
    return (
        "I can reverse text and provide concise replies with sentiment.\n"
        "Commands:\n"
        "- help | capabilities\n"
        "- reverse <text>\n"
        "General text will be handled by the ChatBot service.\n\n"
        f"My capabilities:\n{feats}"
    )

class SimpleBot(ActivityHandler):
    """Minimal ActivityHandler with local commands + ChatBot fallback."""

    def __init__(self, chatbot: Optional[ChatBot] = None):
        self._chatbot = chatbot or ChatBot()

    async def on_members_added_activity(
        self, members_added: List[ChannelAccount], turn_context: TurnContext
    ):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity("Hello! Type 'help' to see what I can do.")

    async def on_message_activity(self, turn_context: TurnContext):
        if turn_context.activity.type != ActivityTypes.message:
            return

        text = (turn_context.activity.text or "").strip()
        if is_empty(text):
            await turn_context.send_activity("Please enter a message (try 'help').")
            return

        cmd = normalize(text)

        if cmd in {"help", "capabilities"}:
            await turn_context.send_activity(_help_text())
            return

        if cmd.startswith("reverse "):
            original = text.split(" ", 1)[1] if " " in text else ""
            await turn_context.send_activity(reverse_text(original))
            return

        # ChatBot fallback (provider-agnostic sentiment/reply)
        try:
            result = self._chatbot.reply(text)
            await turn_context.send_activity(_format_sentiment(result))
        except Exception:
            await turn_context.send_activity(f"You said: {text}")
