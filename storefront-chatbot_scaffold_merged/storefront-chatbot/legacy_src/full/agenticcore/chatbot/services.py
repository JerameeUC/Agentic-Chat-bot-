from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Dict

# Delegate sentiment to the unified provider layer
# If you put providers_unified.py under agenticcore/chatbot/, change the import to:
#   from agenticcore.chatbot.providers_unified import analyze_sentiment
from agenticcore.providers_unified import analyze_sentiment
from ..providers_unified import analyze_sentiment


def _trim(s: str, max_len: int = 2000) -> str:
    s = (s or "").strip()
    return s if len(s) <= max_len else s[: max_len - 1] + "…"


@dataclass(frozen=True)
class SentimentResult:
    label: str          # "positive" | "neutral" | "negative" | "mixed" | "unknown"
    confidence: float   # 0.0 .. 1.0


class ChatBot:
    """
    Minimal chatbot that uses provider-agnostic sentiment via providers_unified.
    Public API:
      - reply(text: str) -> Dict[str, object]
      - capabilities() -> Dict[str, object]
    """

    def __init__(self, system_prompt: str = "You are a concise helper.") -> None:
        self._system_prompt = _trim(system_prompt, 800)
        # Expose which provider is intended/active (for diagnostics)
        self._mode = os.getenv("AI_PROVIDER") or "auto"

    def capabilities(self) -> Dict[str, object]:
        """List what this bot can do."""
        return {
            "system": "chatbot",
            "mode": self._mode,  # "auto" or a pinned provider (hf/azure/openai/cohere/deepai/offline)
            "features": ["text-input", "sentiment-analysis", "help"],
            "commands": {"help": "Describe capabilities and usage."},
        }

    def reply(self, text: str) -> Dict[str, object]:
        """Produce a reply and sentiment for one user message."""
        user = _trim(text)
        if not user:
            return self._make_response(
                "I didn't catch that. Please provide some text.",
                SentimentResult("unknown", 0.0),
            )

        if user.lower() in {"help", "/help"}:
            return {"reply": self._format_help(), "capabilities": self.capabilities()}

        s = analyze_sentiment(user)  # -> {"provider", "label", "score", ...}
        sr = SentimentResult(label=str(s.get("label", "neutral")), confidence=float(s.get("score", 0.5)))
        return self._make_response(self._compose(sr), sr)

    # ---- internals ----

    def _format_help(self) -> str:
        caps = self.capabilities()
        feats = ", ".join(caps["features"])
        return f"I can analyze sentiment and respond concisely. Features: {feats}. Send any text or type 'help'."

    @staticmethod
    def _make_response(reply: str, s: SentimentResult) -> Dict[str, object]:
        return {"reply": reply, "sentiment": s.label, "confidence": round(float(s.confidence), 2)}

    @staticmethod
    def _compose(s: SentimentResult) -> str:
        if s.label == "positive":
            return "Thanks for sharing. I detected a positive sentiment."
        if s.label == "negative":
            return "I hear your concern. I detected a negative sentiment."
        if s.label == "neutral":
            return "Noted. The sentiment appears neutral."
        if s.label == "mixed":
            return "Your message has mixed signals. Can you clarify?"
        return "I could not determine the sentiment. Please rephrase."


# Optional: local REPL for quick manual testing
def _interactive_loop() -> None:
    bot = ChatBot()
    try:
        while True:
            msg = input("> ").strip()
            if msg.lower() in {"exit", "quit"}:
                break
            print(json.dumps(bot.reply(msg), ensure_ascii=False))
    except (EOFError, KeyboardInterrupt):
        pass


if __name__ == "__main__":
    _interactive_loop()
