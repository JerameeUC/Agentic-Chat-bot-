"""
providers_unified.py
Unified, switchable providers for sentiment + (optional) text generation.
Selection order unless AI_PROVIDER is set:
  HF -> AZURE -> OPENAI -> COHERE -> DEEPAI -> OFFLINE
Env vars:
  HF_API_KEY
  MICROSOFT_AI_SERVICE_ENDPOINT, MICROSOFT_AI_API_KEY
  OPENAI_API_KEY,  OPENAI_MODEL=gpt-3.5-turbo
  COHERE_API_KEY,  COHERE_MODEL=command
  DEEPAI_API_KEY
  AI_PROVIDER = hf|azure|openai|cohere|deepai|offline
  HTTP_TIMEOUT = 20
"""
from __future__ import annotations
import os, json
from typing import Dict, Any, Optional
import requests

TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "20"))

def _env(name: str, default: Optional[str] = None) -> Optional[str]:
    v = os.getenv(name)
    return v if (v is not None and str(v).strip() != "") else default

def _pick_provider() -> str:
    forced = _env("AI_PROVIDER")
    if forced in {"hf", "azure", "openai", "cohere", "deepai", "offline"}:
        return forced
    if _env("HF_API_KEY"): return "hf"
    if _env("MICROSOFT_AI_API_KEY") and _env("MICROSOFT_AI_SERVICE_ENDPOINT"): return "azure"
    if _env("OPENAI_API_KEY"): return "openai"
    if _env("COHERE_API_KEY"): return "cohere"
    if _env("DEEPAI_API_KEY"): return "deepai"
    return "offline"

# ---------------------------
# Sentiment
# ---------------------------

def analyze_sentiment(text: str) -> Dict[str, Any]:
    provider = _pick_provider()
    try:
        if provider == "hf":     return _sentiment_hf(text)
        if provider == "azure":  return _sentiment_azure(text)
        if provider == "openai": return _sentiment_openai_prompt(text)
        if provider == "cohere": return _sentiment_cohere_prompt(text)
        if provider == "deepai": return _sentiment_deepai(text)
        return _sentiment_offline(text)
    except Exception as e:
        return {"provider": provider, "label": "neutral", "score": 0.5, "error": str(e)}

def _sentiment_offline(text: str) -> Dict[str, Any]:
    t = (text or "").lower()
    pos = any(w in t for w in ["love","great","good","awesome","fantastic","thank","excellent","amazing"])
    neg = any(w in t for w in ["hate","bad","terrible","awful","worst","angry","horrible"])
    label = "positive" if pos and not neg else "negative" if neg and not pos else "neutral"
    score = 0.9 if label != "neutral" else 0.5
    return {"provider": "offline", "label": label, "score": score}

def _sentiment_hf(text: str) -> Dict[str, Any]:
    """
    Hugging Face Inference API for sentiment.
    Uses canonical repo id and handles 404/401 and various payload shapes.
    """
    key = _env("HF_API_KEY")
    if not key:
        return _sentiment_offline(text)

    # canonical repo id to avoid 404
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

    if isinstance(data, dict) and "error" in data:
        return {"provider": "hf", "label": "neutral", "score": 0.5, "error": data["error"]}

    # normalize list shape
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
    try:
        from azure.core.credentials import AzureKeyCredential  # type: ignore
        from azure.ai.textanalytics import TextAnalyticsClient  # type: ignore
    except Exception:
        return _sentiment_offline(text)
    endpoint = _env("MICROSOFT_AI_SERVICE_ENDPOINT")
    key = _env("MICROSOFT_AI_API_KEY")
    if not (endpoint and key): return _sentiment_offline(text)
    client = TextAnalyticsClient(endpoint=endpoint.strip(), credential=AzureKeyCredential(key.strip()))
    resp = client.analyze_sentiment(documents=[text], show_opinion_mining=False)[0]
    scores = {
        "positive": float(getattr(resp.confidence_scores, "positive", 0.0) or 0.0),
        "neutral":  float(getattr(resp.confidence_scores, "neutral",  0.0) or 0.0),
        "negative": float(getattr(resp.confidence_scores, "negative", 0.0) or 0.0),
    }
    label = max(scores, key=scores.get)
    return {"provider": "azure", "label": label, "score": scores[label]}

def _sentiment_openai_prompt(text: str) -> Dict[str, Any]:
    key = _env("OPENAI_API_KEY")
    model = _env("OPENAI_MODEL", "gpt-3.5-turbo")
    if not key: return _sentiment_offline(text)
    url = "https://api.openai.com/v1/chat/completions"
    prompt = f"Classify the sentiment of this text as positive, negative, or neutral. Reply JSON with keys label and score (0..1). Text: {text!r}"
    r = requests.post(
        url,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0},
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    content = r.json()["choices"][0]["message"]["content"]
    try:
        obj = json.loads(content)
        label = str(obj.get("label", "neutral")).lower()
        score = float(obj.get("score", 0.5))
        return {"provider": "openai", "label": label, "score": score}
    except Exception:
        l = "positive" if "positive" in content.lower() else "negative" if "negative" in content.lower() else "neutral"
        return {"provider": "openai", "label": l, "score": 0.5}

def _sentiment_cohere_prompt(text: str) -> Dict[str, Any]:
    key = _env("COHERE_API_KEY")
    model = _env("COHERE_MODEL", "command")
    if not key: return _sentiment_offline(text)
    url = "https://api.cohere.ai/v1/generate"
    prompt = f"Classify the sentiment (positive, negative, neutral) and return JSON with keys label and score (0..1). Text: {text!r}"
    r = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Cohere-Version": "2022-12-06",
        },
        json={"model": model, "prompt": prompt, "max_tokens": 30, "temperature": 0},
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    gen = (r.json().get("generations") or [{}])[0].get("text", "")
    try:
        obj = json.loads(gen)
        label = str(obj.get("label", "neutral")).lower()
        score = float(obj.get("score", 0.5))
        return {"provider": "cohere", "label": label, "score": score}
    except Exception:
        l = "positive" if "positive" in gen.lower() else "negative" if "negative" in gen.lower() else "neutral"
        return {"provider": "cohere", "label": l, "score": 0.5}

def _sentiment_deepai(text: str) -> Dict[str, Any]:
    key = _env("DEEPAI_API_KEY")
    if not key: return _sentiment_offline(text)
    url = "https://api.deepai.org/api/sentiment-analysis"
    r = requests.post(url, headers={"api-key": key}, data={"text": text}, timeout=TIMEOUT)
    r.raise_for_status()
    data = r.json()
    label = (data.get("output") or ["neutral"])[0].lower()
    return {"provider": "deepai", "label": label, "score": 0.5 if label == "neutral" else 0.9}

# ---------------------------
# Text generation (optional)
# ---------------------------

def generate_text(prompt: str, max_tokens: int = 128) -> Dict[str, Any]:
    provider = _pick_provider()
    try:
        if provider == "hf":     return _gen_hf(prompt, max_tokens)
        if provider == "openai": return _gen_openai(prompt, max_tokens)
        if provider == "cohere": return _gen_cohere(prompt, max_tokens)
        if provider == "deepai": return _gen_deepai(prompt, max_tokens)
        return {"provider": "offline", "text": f"(offline) {prompt[:160]}"}
    except Exception as e:
        return {"provider": provider, "text": f"(error) {str(e)}"}

def _gen_hf(prompt: str, max_tokens: int) -> Dict[str, Any]:
    key = _env("HF_API_KEY")
    if not key: return {"provider": "offline", "text": f"(offline) {prompt[:160]}"}
    model = _env("HF_MODEL_GENERATION", "tiiuae/falcon-7b-instruct")
    r = requests.post(
        f"https://api-inference.huggingface.co/models/{model}",
        headers={"Authorization": f"Bearer {key}"},
        json={"inputs": prompt, "parameters": {"max_new_tokens": max_tokens}},
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    data = r.json()
    if isinstance(data, list) and data and "generated_text" in data[0]:
        return {"provider": "hf", "text": data[0]["generated_text"]}
    return {"provider": "hf", "text": str(data)}

def _gen_openai(prompt: str, max_tokens: int) -> Dict[str, Any]:
    key = _env("OPENAI_API_KEY")
    model = _env("OPENAI_MODEL", "gpt-3.5-turbo")
    if not key: return {"provider": "offline", "text": f"(offline) {prompt[:160]}"}
    url = "https://api.openai.com/v1/chat/completions"
    r = requests.post(
        url,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens},
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    data = r.json()
    text = data["choices"][0]["message"]["content"]
    return {"provider": "openai", "text": text}

def _gen_cohere(prompt: str, max_tokens: int) -> Dict[str, Any]:
    key = _env("COHERE_API_KEY")
    model = _env("COHERE_MODEL", "command")
    if not key: return {"provider": "offline", "text": f"(offline) {prompt[:160]}"}
    url = "https://api.cohere.ai/v1/generate"
    r = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Cohere-Version": "2022-12-06",
        },
        json={"model": model, "prompt": prompt, "max_tokens": max_tokens},
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    data = r.json()
    text = data.get("generations", [{}])[0].get("text", "")
    return {"provider": "cohere", "text": text}

def _gen_deepai(prompt: str, max_tokens: int) -> Dict[str, Any]:
    key = _env("DEEPAI_API_KEY")
    if not key: return {"provider": "offline", "text": f"(offline) {prompt[:160]}"}
    url = "https://api.deepai.org/api/text-generator"
    r = requests.post(url, headers={"api-key": key}, data={"text": prompt}, timeout=TIMEOUT)
    r.raise_for_status()
    data = r.json()
    return {"provider": "deepai", "text": data.get("output", "")}
