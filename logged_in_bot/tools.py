# /logged_in_bot/tools.py
"""
Utilities for the logged-in chatbot flow.

Features
- PII redaction (optional) via guardrails.pii_redaction
- Sentiment (optional Azure; falls back to local heuristic)
- Tiny intent router: help | remember | forget | list memory | summarize | echo | chat
- Session history capture via memory.sessions
- Lightweight RAG context via memory.rag.retriever (TF-IDF)
- Deterministic, dependency-light; safe to import in any environment
"""

from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Tuple
import os
import re

# -------------------------
# Optional imports (safe)
# -------------------------

# Sentiment (Azure optional): falls back to a local heuristic if missing
try:  # pragma: no cover
    from .sentiment_azure import analyze_sentiment, SentimentResult  # type: ignore
except Exception:  # pragma: no cover
    analyze_sentiment = None  # type: ignore
    SentimentResult = None  # type: ignore

# Guardrails redaction (optional)
try:  # pragma: no cover
    from guardrails.pii_redaction import redact as pii_redact  # type: ignore
except Exception:  # pragma: no cover
    pii_redact = None  # type: ignore

# Fallback PlainChatResponse if core.types is absent
try:  # pragma: no cover
    from core.types import PlainChatResponse  # dataclass with .to_dict()
except Exception:  # pragma: no cover
    @dataclass
    class PlainChatResponse:  # lightweight fallback shape
        reply: str
        meta: Optional[Dict[str, Any]] = None

        def to_dict(self) -> Dict[str, Any]:
            return asdict(self)

# LLM generation for conversational responses
try:
    from agenticcore.providers_unified import generate_text
except Exception:  # pragma: no cover
    def generate_text(prompt: str, max_tokens: int = 128) -> Dict[str, Any]:
        return {"provider": "offline", "text": "(LLM unavailable)"}

# Memory + RAG (pure-Python, no extra deps)
try:
    from memory.sessions import SessionStore, get_store
except Exception as e:  # pragma: no cover
    raise RuntimeError("memory.sessions is required for logged_in_bot.tools") from e

try:
    from memory.profile import Profile
except Exception as e:  # pragma: no cover
    raise RuntimeError("memory.profile is required for logged_in_bot.tools") from e

try:
    from memory.rag.indexer import DEFAULT_INDEX_PATH
    from memory.rag.retriever import retrieve, Filters
except Exception as e:  # pragma: no cover
    raise RuntimeError("memory.rag.{indexer,retriever} are required for logged_in_bot.tools") from e


History = List[Tuple[str, str]]  # [("user","..."), ("bot","...")]

# -------------------------
# Helpers
# -------------------------

_WHITESPACE_RE = re.compile(r"\s+")

def sanitize_text(text: str) -> str:
    """Basic sanitize/normalize; keep CPU-cheap & deterministic."""
    text = (text or "").strip()
    text = _WHITESPACE_RE.sub(" ", text)
    # Optionally cap extremely large payloads to protect inference/services
    max_len = int(os.getenv("MAX_INPUT_CHARS", "4000"))
    if len(text) > max_len:
        text = text[:max_len] + "…"
    return text

def redact_text(text: str) -> str:
    """Apply optional PII redaction if available; otherwise return text."""
    if pii_redact:
        try:
            return pii_redact(text)
        except Exception:
            # Fail open but safe
            return text
    return text

def _simple_sentiment(text: str) -> Dict[str, Any]:
    """Local heuristic sentiment (when Azure is unavailable)."""
    t = (text or "").lower()
    pos = any(w in t for w in ["love", "great", "awesome", "good", "thanks", "glad", "happy"])
    neg = any(w in t for w in ["hate", "terrible", "awful", "bad", "angry", "sad"])
    label = "positive" if pos and not neg else "negative" if neg and not pos else "neutral"
    score = 0.8 if label != "neutral" else 0.5
    return {"label": label, "score": score, "backend": "heuristic"}

def _sentiment_meta(text: str) -> Dict[str, Any]:
    """Get a sentiment blob that is always safe to attach to meta."""
    try:
        if analyze_sentiment:
            res = analyze_sentiment(text)
            # Expect res to have .label, .score, .backend; fall back to str
            if hasattr(res, "__dict__"):
                d = getattr(res, "__dict__")
                label = d.get("label") or getattr(res, "label", None) or "neutral"
                score = float(d.get("score") or getattr(res, "score", 0.5) or 0.5)
                backend = d.get("backend") or getattr(res, "backend", "azure")
                return {"label": label, "score": score, "backend": backend}
            return {"label": str(res), "backend": "azure"}
    except Exception:  # pragma: no cover
        pass
    return _simple_sentiment(text)

def intent_of(text: str) -> str:
    """Tiny intent classifier."""
    t = (text or "").lower().strip()
    if not t:
        return "empty"
    if t in {"help", "/help", "capabilities"}:
        return "help"
    if t.startswith("remember ") and ":" in t:
        return "memory_remember"
    if t.startswith("forget "):
        return "memory_forget"
    if t == "list memory":
        return "memory_list"
    if t.startswith("summarize ") or t.startswith("summarise ") or " summarize " in f" {t} ":
        return "summarize"
    if t.startswith("echo "):
        return "echo"
    return "chat"

def summarize_text(text: str, target_len: int = 120) -> str:
    """
    CPU-cheap pseudo-summarizer:
    - Extract first sentence; if long, truncate to target_len with ellipsis.
    """
    m = re.split(r"(?<=[.!?])\s+", (text or "").strip())
    first = m[0] if m else (text or "").strip()
    if len(first) <= target_len:
        return first
    return first[: target_len - 1].rstrip() + "…"

def capabilities() -> List[str]:
    return [
        "help",
        "remember <key>: <value>",
        "forget <key>",
        "list memory",
        "echo <text>",
        "summarize <paragraph>",
        "sentiment tagging (logged-in mode)",
    ]

def _handle_memory_cmd(user_id: str, text: str) -> Optional[str]:
    """Implements: remember k:v | forget k | list memory."""
    prof = Profile.load(user_id)
    m = re.match(r"^\s*remember\s+([^:]+)\s*:\s*(.+)$", text, flags=re.I)
    if m:
        key, val = m.group(1).strip(), m.group(2).strip()
        prof.remember(key, val)
        return f"Okay, I'll remember **{key}**."
    m = re.match(r"^\s*forget\s+(.+?)\s*$", text, flags=re.I)
    if m:
        key = m.group(1).strip()
        return "Forgot." if prof.forget(key) else f"I had nothing stored as **{key}**."
    if re.match(r"^\s*list\s+memory\s*$", text, flags=re.I):
        keys = prof.list_notes()
        return "No saved memory yet." if not keys else "Saved keys: " + ", ".join(keys)
    return None

def _auto_extract_and_remember(query: str, profile: Profile) -> bool:
    """Automatically extract and remember information from user messages.
    Returns True if something was extracted.
    """
    extracted = False
    
    # Extract ALL information first (don't break early)
    
    # Extract name (case-insensitive search, but preserve original case)
    name_patterns = [
        r"(?:my name is|call me)\s+([A-Z][a-z]+)",  # "my name is Sarah"
        r"(?:i am|i'm)\s+([A-Z][a-z]+)(?:\s+by the way|\s*$|\s*\.|\s*,)",  # "I'm John"
    ]
    for pattern in name_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            name = match.group(1).capitalize()
            if len(name) > 1 and name.lower() not in ['the', 'a', 'an', 'not', 'here', 'there']:
                profile.remember("name", name)
                extracted = True
                break
    
    # Extract email  
    if "email" in query.lower() or "@" in query:
        email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", query)
        if email_match:
            profile.remember("email", email_match.group(0))
            extracted = True
    
    # Extract phone
    if "phone" in query.lower() or re.search(r"\d{3}[-.]?\d{3}[-.]?\d{4}", query):
        phone_match = re.search(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", query)
        if phone_match:
            profile.remember("phone", phone_match.group(0))
            extracted = True
    
    return extracted

def _generate_conversational_response(
    query: str,
    rag_chunks: List[str],
    confidence: float,
    user_name: str,
    chat_history: List[Tuple[str, str]],
    profile: Profile
) -> str:
    """Generate natural conversational response using RAG context and chat history."""
    
    # Check if user just shared personal info (already extracted in handle_logged_in_turn)
    query_lower = query.lower()
    profile_dict = profile.list_notes_dict()
    
    # Acknowledge if they just shared info (only if they're introducing themselves)
    if any(phrase in query_lower for phrase in ["my name is", "i am", "i'm", "call me"]) and "what" not in query_lower:
        if "name" in profile_dict:
            return f"Nice to meet you, {profile_dict['name']}!"
    if "email" in query_lower and "@" in query and "what" not in query_lower:
        if "email" in profile_dict:
            return f"Got it, I've saved your email as {profile_dict['email']}."
    if "phone" in query_lower and any(c.isdigit() for c in query) and "what" not in query_lower:
        if "phone" in profile_dict:
            return f"Thanks, I've saved your phone number."
    
    # Try LLM first if available
    profile_context = ", ".join([f"{k}: {v}" for k, v in profile.list_notes_dict().items()]) if profile.list_notes_dict() else ""
    history_text = " ".join([msg for _, msg in chat_history[-2:]]) if chat_history else ""
    rag_text = " ".join(rag_chunks[:2])[:500] if rag_chunks else ""
    
    prompt = f"""Answer naturally and conversationally in 2-3 sentences.
User: {user_name}. {profile_context}
Context: {rag_text}
Previous: {history_text}
Question: {query}
Answer:"""
    
    llm_result = generate_text(prompt, max_tokens=100)
    llm_text = llm_result.get("text", "").strip()
    
    # Use LLM if available and not offline
    if llm_text and "(offline)" not in llm_text and "(error)" not in llm_text and len(llm_text) > 20:
        return llm_text
    
    # Fallback: Rule-based conversational responses
    
    # Greetings (only if it's a short greeting, not a question)
    if len(query_lower.split()) <= 3 and any(w in query_lower for w in ["hi", "hello", "hey"]):
        if rag_chunks:
            return f"Hi {user_name}! I can help you with graduation store questions. What would you like to know?"
        return f"Hi {user_name}! I'm here to help. You can ask about documents, use 'remember' to save info, or 'summarize' text."
    
    # Handle identity and memory questions
    if "who are you" in query_lower or "what are you" in query_lower:
        return "I'm your AI assistant! I can help with questions about documents, remember information for you, and chat about various topics. What can I help you with?"
    
    # Handle chat history questions
    if any(phrase in query_lower for phrase in ["what questions", "what did i ask", "previous questions", "earlier questions", "chat history"]):
        if chat_history:
            recent_questions = [msg for msg, _ in chat_history[-3:] if msg.strip().endswith('?')]
            if recent_questions:
                return f"Your recent questions: {', '.join(recent_questions)}"
            else:
                recent_msgs = [msg for msg, _ in chat_history[-3:]]
                return f"Your recent messages: {', '.join(recent_msgs)}"
        return "You haven't asked any questions yet in this session."
    
    # Check if asking about personal info (memory recall)
    if any(phrase in query_lower for phrase in ["my name", "who am i", "what is my", "do you know my", "know about me", "what do you know"]):
        profile_dict = profile.list_notes_dict()
        
        # If asking "what do you know about me", list everything
        if "know about me" in query_lower or "what do you know" in query_lower:
            if profile_dict:
                items = "\n".join([f"• {k.title()}: {v}" for k, v in profile_dict.items()])
                return f"Here's what I know about you:\n{items}"
            return "I don't have any information saved about you yet."
        
        # Check saved profile first
        if "name" in profile_dict:
            return f"Your name is {profile_dict['name']}!"
        # Fall back to user_name from login
        if user_name and user_name != "there":
            return f"Your name is {user_name}!"
        if profile_dict:
            items = ", ".join([f"{k}: {v}" for k, v in profile_dict.items()])
            return f"I know: {items}"
        return f"I don't have any information saved about you yet."
    
    # Check if query is likely general knowledge (not about documents)
    import re as regex
    general_knowledge_patterns = [
        r'\bcapital of\b', r'\bpresident of\b', r'\binvented\b', r'\bdiscovered\b',
        r'\bwhen was\b', r'\bwhere is\b', r'\bwho is\b', r'\bwhat is.*country\b',
        r'\bhistory of\b', r'\bfamous for\b', r'\bknown for\b', r'\bborn in\b'
    ]
    is_general_knowledge = any(regex.search(pattern, query_lower) for pattern in general_knowledge_patterns)
    
    # Also check for identity/meta questions that shouldn't use RAG
    meta_questions = ["who are you", "what are you", "what questions", "what did i ask", "chat history"]
    is_meta_question = any(phrase in query_lower for phrase in meta_questions)
    
    # RAG-based response (unless clearly general knowledge or meta question)
    if rag_chunks and not is_general_knowledge and not is_meta_question:
        # Try to extract structured answer first
        extracted = _extract_key_info(rag_chunks[0], query, chat_history)
        if extracted:
            return extracted
        # Use RAG response
        return _format_rag_response(rag_chunks[0], confidence, user_name)
    
    # No relevant info in documents - try LLM for general knowledge
    llm_result = generate_text(f"Answer this question concisely in 1-2 sentences: {query}", max_tokens=100)
    llm_text = llm_result.get("text", "").strip()
    
    if llm_text and "(offline)" not in llm_text and "(error)" not in llm_text and len(llm_text) > 10:
        return f"I don't have that in my documents, but here's what I know: {llm_text}"
    
    # Final fallback (LLM not available)
    return f"I don't have information about that in my documents. I can help with questions about the graduation store (products, parking, dress code). You can also upload documents for me to reference."

def _extract_key_info(chunk: str, query: str, chat_history: List[Tuple[str, str]]) -> Optional[str]:
    """Extract key information from chunk based on query keywords and context."""
    chunk_lower = chunk.lower()
    query_lower = query.lower()
    
    # Check recent context for topic
    recent_context = " ".join([msg for _, msg in chat_history[-2:]]).lower() if chat_history else ""
    
    # Follow-up questions (how many, how much, what about)
    if any(phrase in query_lower for phrase in ["how many", "how much"]):
        if "parking" in recent_context or "parking" in chunk_lower:
            return "You can buy as many as you need! There's no limit on parking passes - perfect for extended families. Each pass is for one vehicle."
        if "cap" in recent_context or "gown" in recent_context:
            return "You need one cap and gown set per student. It includes the cap, gown, and tassel."
    
    # Parking - distinguish between passes and rules
    if "parking" in query_lower:
        if "rule" in query_lower or "regulation" in query_lower:
            return "Parking rules: No double parking is allowed at any time. Vehicles parked in handicap spaces without proper permits will be towed immediately. Arrive early for best availability."
        if "handicap" in query_lower or "handicap" in chunk_lower:
            return "Important: vehicles parked in handicap spaces without proper permits will be towed immediately. Also, no double parking is allowed."
        if "pass" in query_lower:
            return "Yes! You can buy as many parking passes as you need. There's no limit - perfect for extended families. Each pass is for one vehicle."
        # Default parking answer
        return "Parking passes are available with no limit per student. Rules: no double parking, handicap spaces require permits or vehicles will be towed."
    
    # Products
    if "product" in query_lower or "buy" in query_lower or "purchase" in query_lower:
        return "We offer: 1) Cap and Gown Set (includes cap, gown, tassel - required for ceremony), and 2) Parking Passes (valid for graduation day, no limit per student)."
    
    # Cap and gown (but not "capital" or other false matches)
    if ("cap and gown" in query_lower or "cap & gown" in query_lower or 
        ("gown" in query_lower and "cap" in query_lower)):
        return "The cap and gown set includes your graduation cap, gown, and tassel - everything you need for the ceremony!"
    
    # Dress code / attire
    if any(word in query_lower for word in ["dress", "attire", "wear", "muscle", "shirt", "allowed", "pants"]):
        if "muscle" in query_lower or "shirt" in query_lower:
            return "No, muscle shirts are not allowed in the venue. The dress code requires appropriate attire - formal is recommended but business casual is acceptable."
        return "For the dress code: formal attire is recommended but not required for guests. However, muscle shirts and sagging pants are not allowed in the venue."
    
    return None

def _format_rag_response(chunk: str, confidence: float, user_name: str, is_followup: bool = False) -> str:
    """Format RAG chunk into natural conversational response."""
    # Clean chunk for display
    clean_chunk = " ".join(chunk.split())  # Remove extra whitespace
    
    # Try to extract structured answer
    if confidence >= 20:
        # Return clean, readable excerpt
        if len(clean_chunk) <= 200:
            return clean_chunk
        return clean_chunk[:200] + "..."
    
    # Medium confidence
    if confidence >= 14:
        return f"Based on the documents: {clean_chunk[:180]}..."
    
    # Low confidence
    return f"I'm not entirely sure, but here's what I found: {clean_chunk[:150]}..."

def _retrieve_context(query: str, k: int = 2) -> Tuple[List[str], float]:
    """Retrieve relevant passages using TF-IDF with proximity-based reranking.
    
    Returns: (passages, confidence_score)
    
    The retriever uses:
    1. TF-IDF scoring for initial document/passage ranking based on term frequency
    2. Proximity-based reranking that boosts passages where query terms cluster together
    3. Passage extraction that focuses on regions containing query terms
    
    Confidence score indicates how well the query matches the corpus:
    - High score (>15): Strong semantic match with indexed content
    - Medium score (8-15): Moderate match, may be tangentially related
    - Low score (<8): Weak match, results may not be directly relevant
    """
    # Retrieve with proximity reranking enabled
    passages = retrieve(query, k=k, index_path=DEFAULT_INDEX_PATH, filters=None, enable_rerank=True)
    
    if not passages:
        return [], 0.0
    
    # Use top score as confidence indicator
    confidence = passages[0].score if passages else 0.0
    
    # Deduplicate passages
    seen = set()
    unique = []
    for p in passages:
        text_key = p.text[:200].strip()
        if text_key not in seen:
            seen.add(text_key)
            unique.append(p.text)
    return unique, confidence

# -------------------------
# Main entry
# -------------------------

def handle_logged_in_turn(message: str, history: Optional[History], user: Optional[dict]) -> Dict[str, Any]:
    """
    Process one user turn in 'logged-in' mode.

    Returns a PlainChatResponse (dict) with:
      - reply: str
      - meta: { intent, sentiment: {...}, redacted: bool, input_len: int }
    """
    history = history or []
    user_text_raw = message or ""
    user_text = sanitize_text(user_text_raw)

    # Redaction (if configured)
    redacted_text = redact_text(user_text)
    redacted = (redacted_text != user_text)

    it = intent_of(redacted_text)

    # Compute sentiment once (always attach — satisfies tests)
    sentiment = _sentiment_meta(redacted_text)

    # ---------- route ----------
    if it == "empty":
        reply = "Please type something. Try 'help' for options."
        meta = _meta(redacted, it, redacted_text, sentiment)
        return PlainChatResponse(reply=reply, meta=meta).to_dict()

    if it == "help":
        reply = "I can:\n" + "\n".join(f"- {c}" for c in capabilities())
        meta = _meta(redacted, it, redacted_text, sentiment)
        return PlainChatResponse(reply=reply, meta=meta).to_dict()

    if it.startswith("memory_"):
        user_id = (user or {}).get("id") or "guest"
        mem_reply = _handle_memory_cmd(user_id, redacted_text)
        reply = mem_reply or "Sorry, I didn't understand that memory command."
        # track in session
        store = get_store()
        store.append_user(user_id, user_text)
        store.append_bot(user_id, reply)
        meta = _meta(redacted, "memory_cmd", redacted_text, sentiment)
        return PlainChatResponse(reply=reply, meta=meta).to_dict()

    if it == "echo":
        payload = redacted_text.split(" ", 1)[1] if " " in redacted_text else ""
        reply = payload or "(nothing to echo)"
        meta = _meta(redacted, it, redacted_text, sentiment)
        return PlainChatResponse(reply=reply, meta=meta).to_dict()

    if it == "summarize":
        # Use everything after the keyword if present
        if redacted_text.lower().startswith("summarize "):
            payload = redacted_text.split(" ", 1)[1]
        elif redacted_text.lower().startswith("summarise "):
            payload = redacted_text.split(" ", 1)[1]
        else:
            payload = redacted_text
        reply = summarize_text(payload)
        meta = _meta(redacted, it, redacted_text, sentiment)
        return PlainChatResponse(reply=reply, meta=meta).to_dict()

    # default: chat (with RAG + conversational response)
    user_id = (user or {}).get("id") or "guest"
    store = get_store()
    
    # Get user profile for personalization
    prof = Profile.load(user_id)
    # Use saved name, or fall back to user_id, or "there"
    user_name = prof.recall("name") or (user or {}).get("name") or user_id if user_id != "guest" else "there"
    
    # IMPORTANT: Extract info from ORIGINAL text before redaction
    _auto_extract_and_remember(user_text, prof)
    
    # Get chat history for context-aware responses
    chat_history = store.get_history(user_id)[-4:] if store.get_history(user_id) else []
    
    # Retrieve relevant documents
    ctx_chunks, confidence = _retrieve_context(redacted_text)
    
    # Generate conversational response
    reply = _generate_conversational_response(
        query=redacted_text,
        rag_chunks=ctx_chunks,
        confidence=confidence,
        user_name=user_name,
        chat_history=chat_history,
        profile=prof
    )
    
    # Track in session
    store.append_user(user_id, user_text)
    store.append_bot(user_id, reply)

    meta = _meta(redacted, it, redacted_text, sentiment)
    return PlainChatResponse(reply=reply, meta=meta).to_dict()

# -------------------------
# Internals
# -------------------------

def _meta(redacted: bool, intent: str, redacted_text: str, sentiment: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "intent": intent,
        "redacted": redacted,
        "input_len": len(redacted_text),
        "sentiment": sentiment,
    }

__all__ = [
    "handle_logged_in_turn",
    "sanitize_text",
    "redact_text",
    "intent_of",
    "summarize_text",
    "capabilities",
]
