# /logged_in_bot/sentiment_azure.py
"""
Optional Azure Sentiment integration with safe local fallback.

Usage:
    from logged_in_bot.sentiment_azure import analyze_sentiment, SentimentResult

    res = analyze_sentiment("I love this!")
    print(res.label, res.score, res.backend)  # e.g., "positive", 0.92, "local"

Environment (Azure path only):
    - AZURE_LANGUAGE_ENDPOINT or MICROSOFT_AI_ENDPOINT
    - AZURE_LANGUAGE_KEY or MICROSOFT_AI_KEY

If the Azure SDK or env vars are missing, we automatically fall back to a
deterministic, dependency-free heuristic that is fast and good enough for tests.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Tuple
import os
import re


# ---------------------------
# Public dataclass & API
# ---------------------------

@dataclass(frozen=True)
class SentimentResult:
    label: str           # "positive" | "neutral" | "negative"
    score: float         # 0.0 .. 1.0 (confidence-like)
    backend: str         # "azure" | "local"
    raw: Optional[dict] = None  # provider raw payload if available


def analyze_sentiment(text: str) -> SentimentResult:
    """
    Analyze sentiment using Azure if configured, otherwise use local heuristic.

    Never raises on normal use — returns a result even if Azure is misconfigured,
    satisfying 'graceful degradation' requirements.
    """
    text = (text or "").strip()
    if not text:
        return SentimentResult(label="neutral", score=0.5, backend="local", raw={"reason": "empty"})

    # Try Azure first (only if fully configured and package available)
    azure_ready, why = _is_azure_ready()
    if azure_ready:
        try:
            return _azure_sentiment(text)
        except Exception as e:
            # Degrade gracefully to local
            return _local_sentiment(text, note=f"azure_error: {e!r}")
    else:
        # Go local immediately
        return _local_sentiment(text, note=why)


# ---------------------------
# Azure path (optional)
# ---------------------------

def _is_azure_ready() -> Tuple[bool, str]:
    """
    Check env + optional SDK presence without importing heavy modules unless needed.
    """
    endpoint = os.getenv("AZURE_LANGUAGE_ENDPOINT") or os.getenv("MICROSOFT_AI_ENDPOINT")
    key = os.getenv("AZURE_LANGUAGE_KEY") or os.getenv("MICROSOFT_AI_KEY")
    if not endpoint or not key:
        return False, "missing_env"

    try:
        # Light import check
        import importlib
        client_mod = importlib.import_module("azure.ai.textanalytics")
        cred_mod = importlib.import_module("azure.core.credentials")
        # Quick sanity on expected attributes
        getattr(client_mod, "TextAnalyticsClient")
        getattr(cred_mod, "AzureKeyCredential")
    except Exception:
        return False, "sdk_not_installed"

    return True, "ok"


def _azure_sentiment(text: str) -> SentimentResult:
    """
    Call Azure Text Analytics (Sentiment). Requires:
      pip install azure-ai-textanalytics
    """
    from azure.ai.textanalytics import TextAnalyticsClient
    from azure.core.credentials import AzureKeyCredential

    endpoint = os.getenv("AZURE_LANGUAGE_ENDPOINT") or os.getenv("MICROSOFT_AI_ENDPOINT")
    key = os.getenv("AZURE_LANGUAGE_KEY") or os.getenv("MICROSOFT_AI_KEY")

    client = TextAnalyticsClient(endpoint=endpoint, credential=AzureKeyCredential(key))
    # API expects a list of documents
    resp = client.analyze_sentiment(documents=[text], show_opinion_mining=False)
    doc = resp[0]

    # Map Azure scores to our schema
    label = (doc.sentiment or "neutral").lower()
    # Choose max score among pos/neu/neg as "confidence-like"
    score_map = {
        "positive": doc.confidence_scores.positive,
        "neutral": doc.confidence_scores.neutral,
        "negative": doc.confidence_scores.negative,
    }
    score = float(score_map.get(label, max(score_map.values())))
    raw = {
        "sentiment": doc.sentiment,
        "confidence_scores": {
            "positive": doc.confidence_scores.positive,
            "neutral": doc.confidence_scores.neutral,
            "negative": doc.confidence_scores.negative,
        },
    }
    return SentimentResult(label=label, score=score, backend="azure", raw=raw)


# ---------------------------
# Local fallback (no deps)
# ---------------------------

_POSITIVE = {
    "good", "great", "love", "excellent", "amazing", "awesome", "happy",
    "wonderful", "fantastic", "like", "enjoy", "cool", "nice", "positive",
}
_NEGATIVE = {
    "bad", "terrible", "hate", "awful", "horrible", "sad", "angry",
    "worse", "worst", "broken", "bug", "issue", "problem", "negative",
}
# Simple negation tokens to flip nearby polarity
_NEGATIONS = {"not", "no", "never", "n't"}

_WORD_RE = re.compile(r"[A-Za-z']+")


def _local_sentiment(text: str, note: str | None = None) -> SentimentResult:
    """
    Tiny lexicon + negation heuristic:
      - Tokenize letters/apostrophes
      - Score +1 for positive, -1 for negative
      - If a negation appears within the previous 3 tokens, flip the sign
      - Convert final score to pseudo-confidence 0..1
    """
    tokens = [t.lower() for t in _WORD_RE.findall(text)]
    score = 0
    for i, tok in enumerate(tokens):
        window_neg = any(t in _NEGATIONS for t in tokens[max(0, i - 3):i])
        if tok in _POSITIVE:
            score += -1 if window_neg else 1
        elif tok in _NEGATIVE:
            score += 1 if window_neg else -1

    # Map integer score → label
    if score > 0:
        label = "positive"
    elif score < 0:
        label = "negative"
    else:
        label = "neutral"

    # Confidence-like mapping: squash by arctan-ish shape without math imports
    # Clamp |score| to 6 → conf in ~[0.55, 0.95]
    magnitude = min(abs(score), 6)
    conf = 0.5 + (magnitude / 6) * 0.45  # 0.5..0.95

    raw = {"engine": "heuristic", "score_raw": score, "note": note} if note else {"engine": "heuristic", "score_raw": score}
    return SentimentResult(label=label, score=round(conf, 3), backend="local", raw=raw)


# ---------------------------
# Convenience (module-level)
# ---------------------------

def sentiment_label(text: str) -> str:
    """Return only 'positive' | 'neutral' | 'negative'."""
    return analyze_sentiment(text).label


def sentiment_score(text: str) -> float:
    """Return only the 0..1 confidence-like score."""
    return analyze_sentiment(text).score
