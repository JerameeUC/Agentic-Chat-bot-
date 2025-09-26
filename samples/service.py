# /samples/services.py
import os
from typing import Dict, Any

# Use the unified provider layer (HF, Azure, OpenAI, Cohere, DeepAI, or offline)
from packages.agenticcore.agenticcore.providers_unified import analyze_sentiment, generate_text


class ChatBot:
    """
    Thin façade over provider-agnostic functions.
    - Provider selection is automatic unless AI_PROVIDER is set (hf|azure|openai|cohere|deepai|offline).
    - Reply shape: {"reply": str, "sentiment": str, "confidence": float}
    """

    def __init__(self) -> None:
        # Optional: pin a provider via env; otherwise providers_unified auto-detects.
        self.provider = os.getenv("AI_PROVIDER") or "auto"

    def reply(self, message: str) -> Dict[str, Any]:
        msg = (message or "").strip()
        if not msg:
            return {"reply": "Please enter some text.", "sentiment": "unknown", "confidence": 0.0}

        if msg.lower() in {"help", "/help"}:
            return {
                "reply": self._help_text(),
                "capabilities": {
                    "system": "chatbot",
                    "mode": self.provider,
                    "features": ["text-input", "sentiment-analysis", "help"],
                    "commands": {"help": "Describe capabilities and usage."},
                },
            }

        s = analyze_sentiment(msg)  # -> {"provider","label","score",...}
        label = str(s.get("label", "neutral"))
        score = float(s.get("score", 0.5))

        # Keep the same phrasing used elsewhere so surfaces are consistent.
        reply = self._compose(label)
        return {"reply": reply, "sentiment": label, "confidence": round(score, 2)}

    @staticmethod
    def _compose(label: str) -> str:
        if label == "positive":
            return "Thanks for sharing. I detected a positive sentiment."
        if label == "negative":
            return "I hear your concern. I detected a negative sentiment."
        if label == "neutral":
            return "Noted. The sentiment appears neutral."
        if label == "mixed":
            return "Your message has mixed signals. Can you clarify?"
        return "I could not determine the sentiment. Please rephrase."

    @staticmethod
    def _help_text() -> str:
        return "I analyze sentiment and respond concisely. Send any text or type 'help'."
