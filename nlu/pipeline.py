# /nlu/pipeline.py
"""
Lightweight rule-based NLU pipeline.

No ML dependencies — just keyword matching and simple heuristics.
Provides intent classification and placeholder entity extraction.
"""

from typing import Dict, List


# keyword → intent maps
_INTENT_KEYWORDS = {
    "greeting": {"hi", "hello", "hey", "good morning", "good evening"},
    "goodbye": {"bye", "goodbye", "see you", "farewell"},
    "help": {"help", "support", "assist", "how do i"},
    "faq": {"what is", "who is", "where is", "when is", "how to"},
    "sentiment_positive": {"great", "awesome", "fantastic", "love"},
    "sentiment_negative": {"bad", "terrible", "hate", "awful"},
}


def _match_intent(text: str) -> str:
    low = text.lower().strip()
    for intent, kws in _INTENT_KEYWORDS.items():
        for kw in kws:
            if kw in low:
                return intent
    return "general"


def _extract_entities(text: str) -> List[str]:
    """
    Placeholder entity extractor.
    For now just returns capitalized words (could be names/places).
    """
    return [w for w in text.split() if w.istitle()]


def analyze(text: str) -> Dict:
    """
    Analyze a user utterance.
    Returns:
      {
        "intent": str,
        "entities": list[str],
        "confidence": float
      }
    """
    if not text or not text.strip():
        return {"intent": "general", "entities": [], "confidence": 0.0}

    intent = _match_intent(text)
    entities = _extract_entities(text)

    # crude confidence: matched keyword = 0.9, else fallback = 0.5
    confidence = 0.9 if intent != "general" else 0.5

    return {
        "intent": intent,
        "entities": entities,
        "confidence": confidence,
    }


# quick test
if __name__ == "__main__":
    tests = [
        "Hello there",
        "Can you help me?",
        "I love this bot!",
        "Bye now",
        "Tell me what is RAG",
        "random input with no keywords",
    ]
    for t in tests:
        print(t, "->", analyze(t))
