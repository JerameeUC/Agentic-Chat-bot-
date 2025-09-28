# /memory/rag/data/retriever.py
"""
Minimal RAG retriever that sits on top of the TF-IDF indexer.

Features
- Top-k document retrieval via indexer.search()
- Optional filters (tags, title substring)
- Passage extraction around query terms with overlap
- Lightweight proximity-based reranking of passages

No third-party dependencies; pairs with memory/rag/data/indexer.py.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple
from pathlib import Path
import math
import re

from .indexer import (
    load_index,
    search as index_search,
    DEFAULT_INDEX_PATH,
    tokenize,
    TfidfIndex,
    DocMeta,
)

# -----------------------------
# Public types
# -----------------------------

@dataclass(frozen=True)
class Passage:
    doc_id: str
    source: str
    title: Optional[str]
    tags: Optional[List[str]]
    score: float           # combined score (index score +/- rerank)
    start: int             # char start in original text
    end: int               # char end in original text
    text: str              # extracted passage
    snippet: str           # human-friendly short snippet (may equal text if short)


@dataclass(frozen=True)
class Filters:
    title_contains: Optional[str] = None        # case-insensitive containment
    require_tags: Optional[Iterable[str]] = None  # all tags must be present (AND)


# -----------------------------
# Retrieval API
# -----------------------------

def retrieve(
    query: str,
    k: int = 5,
    index_path: str | Path = DEFAULT_INDEX_PATH,
    filters: Optional[Filters] = None,
    passage_chars: int = 350,
    passage_overlap: int = 60,
    enable_rerank: bool = True,
) -> List[Passage]:
    """
    Retrieve top-k passages for a query.

    Steps:
      1. Run TF-IDF doc search
      2. Apply optional filters
      3. Extract a focused passage per doc
      4. (Optional) Rerank by term proximity within the passage
    """
    idx = load_index(index_path)
    if idx.n_docs == 0 or not query.strip():
        return []

    # initial doc hits
    hits = index_search(query, k=max(k * 3, k), path=index_path)  # overshoot; filter + rerank will trim

    # filter hits by title/tags if requested
    if filters:
        hits = _apply_filters(hits, idx, filters)

    # extract best passage per remaining doc
    q_tokens = tokenize(query)
    passages: List[Passage] = []
    for h in hits:
        doc = idx.docs.get(h.doc_id)
        if not doc:
            continue
        meta: DocMeta = doc["meta"]
        full_text: str = doc.get("text", "") or ""
        start, end, passage_text = _extract_passage(full_text, q_tokens, window=passage_chars, overlap=passage_overlap)
        snippet = passage_text if len(passage_text) <= 220 else passage_text[:220].rstrip() + "…"
        passages.append(Passage(
            doc_id=h.doc_id,
            source=meta.source,
            title=meta.title,
            tags=meta.tags,
            score=float(h.score),  # base score from index
            start=start,
            end=end,
            text=passage_text,
            snippet=snippet,
        ))

    if not passages:
        return []

    # optional rerank by proximity of query terms inside the passage
    if enable_rerank:
        passages = _rerank_by_proximity(passages, q_tokens)

    # final top-k
    passages.sort(key=lambda p: p.score, reverse=True)
    return passages[:k]


def retrieve_texts(
    query: str,
    k: int = 5,
    **kwargs,
) -> List[str]:
    """
    Convenience: return only the passage texts for a query.
    """
    return [p.text for p in retrieve(query, k=k, **kwargs)]


# -----------------------------
# Internals
# -----------------------------

def _apply_filters(hits, idx: TfidfIndex, filters: Filters):
    out = []
    want_title = (filters.title_contains or "").strip().lower() or None
    want_tags = set(t.strip().lower() for t in (filters.require_tags or []) if str(t).strip())

    for h in hits:
        d = idx.docs.get(h.doc_id)
        if not d:
            continue
        meta: DocMeta = d["meta"]

        if want_title:
            t = (meta.title or "").lower()
            if want_title not in t:
                continue

        if want_tags:
            tags = set((meta.tags or []))
            tags = set(x.lower() for x in tags)
            if not want_tags.issubset(tags):
                continue

        out.append(h)
    return out


_WORD_RE = re.compile(r"[A-Za-z0-9']+")

def _find_all(term: str, text: str) -> List[int]:
    """Return starting indices of all case-insensitive matches of term in text."""
    if not term or not text:
        return []
    term_l = term.lower()
    low = text.lower()
    out: List[int] = []
    i = low.find(term_l)
    while i >= 0:
        out.append(i)
        i = low.find(term_l, i + 1)
    return out


def _extract_passage(text: str, q_tokens: List[str], window: int = 350, overlap: int = 60) -> Tuple[int, int, str]:
    """
    Pick a passage around the earliest match of any query token.
    If no match found, return the first window.
    """
    if not text:
        return 0, 0, ""

    low = text.lower()
    # choose the earliest hit among query tokens
    hit_positions: List[int] = []
    for qt in q_tokens:
        hit_positions.extend(_find_all(qt, text))
    start: int
    end: int

    if hit_positions:
        i = max(0, min(hit_positions) - overlap)
        start = i
        end = min(len(text), start + window)
    else:
        start = 0
        end = min(len(text), window)

    return start, end, text[start:end].strip()


def _rerank_by_proximity(passages: List[Passage], q_tokens: List[str]) -> List[Passage]:
    """
    Adjust scores based on how tightly query tokens cluster inside the passage.
    Heuristic:
      - For each unique query token, find all positions in the passage (word indices).
      - Compute average pairwise distance among the closest occurrences.
      - Convert to a bonus in [0, 0.25] and add to base score.
    """
    q_unique = [t for t in dict.fromkeys(q_tokens)]  # preserve order, dedupe
    if not q_unique:
        return passages

    def word_positions(text: str, term: str) -> List[int]:
        # word-level positions for term
        positions: List[int] = []
        words = [w.group(0).lower() for w in _WORD_RE.finditer(text)]
        for i, w in enumerate(words):
            if term == w:
                positions.append(i)
        return positions

    def proximity_bonus(p: Passage) -> float:
        # collect positions per term
        pos_lists = [word_positions(p.text, t) for t in q_unique]
        if all(len(ps) == 0 for ps in pos_lists):
            return 0.0

        # flatten a representative set of positions (closest aligned indices)
        reps: List[int] = []
        for ps in pos_lists:
            reps.append(ps[0] if ps else 999999)

        # average absolute distance to the median position
        med = sorted([x for x in reps if x != 999999])
        if not med:
            return 0.0
        mid = med[len(med) // 2]
        avg_dist = sum(abs((x if x != 999999 else mid) - mid) for x in reps) / max(1, len(reps))

        # squash distance → bonus; closer = bigger bonus
        # dist 0 → 0.25 bonus; dist 10+ → ~0 bonus
        bonus = max(0.0, 0.25 * (1.0 - min(avg_dist, 10.0) / 10.0))
        return float(bonus)

    reranked: List[Passage] = []
    for p in passages:
        bonus = proximity_bonus(p)
        reranked.append(Passage(
            **{**p.__dict__, "score": p.score + bonus}
        ))
    return reranked


# -----------------------------
# CLI / quick test
# -----------------------------

if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]) or "anonymous chatbot rules"
    out = retrieve(q, k=3)
    for i, p in enumerate(out, 1):
        print(f"[{i}] {p.score:.4f}  {p.title or '(untitled)'}  —  {p.source}")
        print("    ", (p.snippet.replace("\n", " ") if p.snippet else "")[:200])
