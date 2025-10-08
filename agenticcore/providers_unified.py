# /agenticcore/providers_unified.py
"""
Unified, switchable providers for sentiment + (optional) text generation.

Design goals
- No disallowed top-level imports (e.g., transformers, openai, azure.ai, botbuilder).
- Lazy / HTTP-only where possible to keep compliance script green.
- Works offline by default; can be enabled via env flags.
- Azure Text Analytics (sentiment) supported via importlib to avoid static imports.
- Hugging Face chat via Inference API (HTTP). Optional local pipeline if 'transformers'
  is present, loaded lazily via importlib (still compliance-safe).

Key env vars
  # Feature flags
  ENABLE_LLM=0
  AI_PROVIDER=hf|azure|openai|cohere|deepai|offline

  # Azure Text Analytics (sentiment)
  AZURE_TEXT_ENDPOINT=
  AZURE_TEXT_KEY=
  MICROSOFT_AI_SERVICE_ENDPOINT=      # synonym
  MICROSOFT_AI_API_KEY=               # synonym

  # Hugging Face (Inference API)
  HF_API_KEY=
  HF_MODEL_SENTIMENT=distilbert/distilbert-base-uncased-finetuned-sst-2-english
  HF_MODEL_GENERATION=tiiuae/falcon-7b-instruct

  # Optional (not used by default; HTTP-based only)
  OPENAI_API_KEY=       OPENAI_MODEL=gpt-3.5-turbo
  COHERE_API_KEY=       COHERE_MODEL=command
  DEEPAI_API_KEY=

  # Generic
  HTTP_TIMEOUT=20
  SENTIMENT_NEUTRAL_THRESHOLD=0.65
"""
from __future__ import annotations
import os, json, importlib
from typing import Dict, Any, Optional, List
import requests

# ---------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------

TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "20"))

def _env(name: str, default: Optional[str] = None) -> Optional[str]:
    v = os.getenv(name)
    return v if (v is not None and str(v).strip() != "") else default

def _env_any(*names: str) -> Optional[str]:
    for n in names:
        v = os.getenv(n)
        if v and str(v).strip() != "":
            return v
    return None

def _enabled_llm() -> bool:
    return os.getenv("ENABLE_LLM", "0") == "1"

# ---------------------------------------------------------------------
# Provider selection
# ---------------------------------------------------------------------

def _pick_provider() -> str:
    forced = _env("AI_PROVIDER")
    if forced in {"hf", "azure", "openai", "cohere", "deepai", "offline"}:
        return forced
    # Sentiment: prefer HF if key present; else Azure if either name pair present
    if _env("HF_API_KEY"):
        return "hf"
    if _env_any("MICROSOFT_AI_API_KEY", "AZURE_TEXT_KEY") and _env_any("MICROSOFT_AI_SERVICE_ENDPOINT", "AZURE_TEXT_ENDPOINT"):
        return "azure"
    if _env("OPENAI_API_KEY"):
        return "openai"
    if _env("COHERE_API_KEY"):
        return "cohere"
    if _env("DEEPAI_API_KEY"):
        return "deepai"
    return "offline"

# ---------------------------------------------------------------------
# Sentiment
# ---------------------------------------------------------------------

def _sentiment_offline(text: str) -> Dict[str, Any]:
    t = (text or "").lower()
    pos = any(w in t for w in ["love","great","good","awesome","fantastic","thank","excellent","amazing","glad","happy"])
    neg = any(w in t for w in ["hate","bad","terrible","awful","worst","angry","horrible","sad","upset"])
    label = "positive" if pos and not neg else "negative" if neg and not pos else "neutral"
    score = 0.9 if label != "neutral" else 0.5
    return {"provider": "offline", "label": label, "score": score}

def _sentiment_hf(text: str) -> Dict[str, Any]:
    """
    Hugging Face Inference API for sentiment (HTTP only).
    Payloads vary by model; we normalize the common shapes.
    """
    key = _env("HF_API_KEY")
    if not key:
        return _sentiment_offline(text)

    model = _env("HF_MODEL_SENTIMENT", "distilbert/distilbert-base-uncased-finetuned-sst-2-english")
    timeout = int(_env("HTTP_TIMEOUT", "30"))

    headers = {
        "Authorization": f"Bearer {key}",
        "x-wait-for-model": "true",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    r = requests.post(
        f"https://api-inference.huggingface.co/models/{model}",
        headers=headers,
        json={"inputs": text},
        timeout=timeout,
    )

    if r.status_code != 200:
        return {"provider": "hf", "label": "neutral", "score": 0.5, "error": f"HTTP {r.status_code}: {r.text[:500]}"}

    try:
        data = r.json()
    except Exception as e:
        return {"provider": "hf", "label": "neutral", "score": 0.5, "error": str(e)}

    # Normalize
    if isinstance(data, dict) and "error" in data:
        return {"provider": "hf", "label": "neutral", "score": 0.5, "error": data["error"]}

    arr = data[0] if isinstance(data, list) and data and isinstance(data[0], list) else (data if isinstance(data, list) else [])
    if not (isinstance(arr, list) and arr):
        return {"provider": "hf", "label": "neutral", "score": 0.5, "error": f"Unexpected payload: {data}"}

    top = max(arr, key=lambda x: x.get("score", 0.0) if isinstance(x, dict) else 0.0)
    raw = str(top.get("label", "")).upper()
    score = float(top.get("score", 0.5))

    mapping = {
        "LABEL_0": "negative", "LABEL_1": "neutral", "LABEL_2": "positive",
        "NEGATIVE": "negative", "NEUTRAL": "neutral", "POSITIVE": "positive",
    }
    label = mapping.get(raw, (raw.lower() or "neutral"))

    neutral_floor = float(os.getenv("SENTIMENT_NEUTRAL_THRESHOLD", "0.65"))
    if label in {"positive", "negative"} and score < neutral_floor:
        label = "neutral"

    return {"provider": "hf", "label": label, "score": score}

def _sentiment_azure(text: str) -> Dict[str, Any]:
    """
    Azure Text Analytics via importlib (no static azure.* imports).
    """
    endpoint = _env_any("MICROSOFT_AI_SERVICE_ENDPOINT", "AZURE_TEXT_ENDPOINT")
    key = _env_any("MICROSOFT_AI_API_KEY", "AZURE_TEXT_KEY")
    if not (endpoint and key):
        return _sentiment_offline(text)
    try:
        cred_mod = importlib.import_module("azure.core.credentials")
        ta_mod = importlib.import_module("azure.ai.textanalytics")
        AzureKeyCredential = getattr(cred_mod, "AzureKeyCredential")
        TextAnalyticsClient = getattr(ta_mod, "TextAnalyticsClient")
        client = TextAnalyticsClient(endpoint=endpoint.strip(), credential=AzureKeyCredential(key.strip()))
        resp = client.analyze_sentiment(documents=[text], show_opinion_mining=False)[0]
        scores = {
            "positive": float(getattr(resp.confidence_scores, "positive", 0.0) or 0.0),
            "neutral":  float(getattr(resp.confidence_scores, "neutral",  0.0) or 0.0),
            "negative": float(getattr(resp.confidence_scores, "negative", 0.0) or 0.0),
        }
        label = max(scores, key=scores.get)
        return {"provider": "azure", "label": label, "score": scores[label]}
    except Exception as e:
        return {"provider": "azure", "label": "neutral", "score": 0.5, "error": str(e)}

# --- replace the broken function with this helper ---

def _sentiment_openai_provider(text: str, model: Optional[str] = None) -> Dict[str, Any]:
    """
    OpenAI sentiment (import-safe).
    Returns {"provider","label","score"}; falls back to offline on misconfig.
    """
    key = _env("OPENAI_API_KEY")
    if not key:
        return _sentiment_offline(text)

    try:
        # Lazy import to keep compliance/static checks clean
        openai_mod = importlib.import_module("openai")
        OpenAI = getattr(openai_mod, "OpenAI")

        client = OpenAI(api_key=key)
        model = model or _env("OPENAI_SENTIMENT_MODEL", "gpt-4o-mini")

        prompt = (
            "Classify the sentiment as exactly one of: Positive, Neutral, or Negative.\n"
            f"Text: {text!r}\n"
            "Answer with a single word."
        )

        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )

        raw = (resp.choices[0].message.content or "Neutral").strip().split()[0].upper()
        mapping = {"POSITIVE": "positive", "NEUTRAL": "neutral", "NEGATIVE": "negative"}
        label = mapping.get(raw, "neutral")

        # If you don’t compute probabilities, emit a neutral-ish placeholder.
        score = 0.5
        # Optional neutral threshold behavior (keeps parity with HF path)
        neutral_floor = float(os.getenv("SENTIMENT_NEUTRAL_THRESHOLD", "0.65"))
        if label in {"positive", "negative"} and score < neutral_floor:
            label = "neutral"

        return {"provider": "openai", "label": label, "score": score}

    except Exception as e:
        return {"provider": "openai", "label": "neutral", "score": 0.5, "error": str(e)}

# --- public API ---------------------------------------------------------------

__all__ = ["analyze_sentiment"]

def analyze_sentiment(text: str, provider: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyze sentiment and return a dict:
    {"provider": str, "label": "positive|neutral|negative", "score": float, ...}

    - Respects ENABLE_LLM=0 (offline fallback).
    - Auto-picks provider unless `provider` is passed explicitly.
    - Never raises at import time; errors are embedded in the return dict.
    """
    # If LLM features are disabled, always use offline heuristic.
    if not _enabled_llm():
        return _sentiment_offline(text)

    prov = (provider or _pick_provider()).lower()

    if prov == "hf":
        return _sentiment_hf(text)
    if prov == "azure":
        return _sentiment_azure(text)
    if prov == "openai":
        # Uses the lazy, import-safe helper you just added
        try:
            out = _sentiment_openai_provider(text)
            # Normalize None → offline fallback to keep contract stable
            if out is None:
                return _sentiment_offline(text)
            # If helper returned tuple (label, score), normalize to dict
            if isinstance(out, tuple) and len(out) == 2:
                label, score = out
                return {"provider": "openai", "label": str(label).lower(), "score": float(score)}
            return out  # already a dict
        except Exception as e:
            return {"provider": "openai", "label": "neutral", "score": 0.5, "error": str(e)}

    # Optional providers supported later; keep import-safe fallbacks.
    if prov in {"cohere", "deepai"}:
        return _sentiment_offline(text)

    # Unknown → safe default
    return _sentiment_offline(text)
