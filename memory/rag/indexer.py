# /memory/rag/indexer.py
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Iterable
from pathlib import Path
import json
import math
import re

DEFAULT_INDEX_PATH = Path(__file__).with_suffix(".json")

_WORD_RE = re.compile(r"[A-Za-z0-9']+")

def tokenize(text: str) -> List[str]:
    return [m.group(0).lower() for m in _WORD_RE.finditer(text or "")]

@dataclass(frozen=True)
class DocMeta:
    doc_id: str
    source: str
    title: Optional[str] = None
    tags: Optional[List[str]] = None

    def to_dict(self) -> Dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: Dict) -> "DocMeta":
        return DocMeta(
            doc_id=str(d["doc_id"]),
            source=str(d.get("source", "")),
            title=d.get("title"),
            tags=list(d.get("tags") or []) or None,
        )

@dataclass(frozen=True)
class DocHit:
    doc_id: str
    score: float

class TfidfIndex:
    """
    Minimal TF-IDF index used by tests:
      - add_text / add_file
      - save / load
      - search(query, k)
    """
    def __init__(self) -> None:
        self.docs: Dict[str, Dict] = {}          # doc_id -> {"text": str, "meta": DocMeta}
        self.df: Dict[str, int] = {}             # term -> document frequency
        self.n_docs: int = 0

    # ---- building ----
    def add_text(self, doc_id: str, text: str, meta: DocMeta) -> None:
        text = text or ""
        self.docs[doc_id] = {"text": text, "meta": meta}
        self.n_docs = len(self.docs)
        seen = set()
        for t in set(tokenize(text)):
            if t not in seen:
                self.df[t] = self.df.get(t, 0) + 1
                seen.add(t)

    def add_file(self, path: str | Path) -> None:
        p = Path(path)
        text = p.read_text(encoding="utf-8", errors="ignore")
        did = str(p.resolve())
        meta = DocMeta(doc_id=did, source=did, title=p.name, tags=None)
        self.add_text(did, text, meta)

    # ---- persistence ----
    def save(self, path: str | Path) -> None:
        p = Path(path)
        payload = {
            "n_docs": self.n_docs,
            "docs": {
                did: {"text": d["text"], "meta": d["meta"].to_dict()}
                for did, d in self.docs.items()
            }
        }
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "TfidfIndex":
        p = Path(path)
        idx = cls()
        if not p.exists():
            return idx
        raw = json.loads(p.read_text(encoding="utf-8"))
        docs = raw.get("docs", {})
        for did, d in docs.items():
            meta = DocMeta.from_dict(d["meta"])
            idx.add_text(did, d.get("text", ""), meta)
        return idx

    # ---- search ----
    def _idf(self, term: str) -> float:
        df = self.df.get(term, 0)
        # smooth to avoid div-by-zero; +1 in both numerator/denominator
        return math.log((self.n_docs + 1) / (df + 1)) + 1.0

    def search(self, query: str, k: int = 5) -> List[DocHit]:
        q_terms = tokenize(query)
        if not q_terms or self.n_docs == 0:
            return []
        # doc scores via simple tf-idf (sum over terms)
        scores: Dict[str, float] = {}
        for did, d in self.docs.items():
            text_terms = tokenize(d["text"])
            if not text_terms:
                continue
            tf: Dict[str, int] = {}
            for t in text_terms:
                tf[t] = tf.get(t, 0) + 1
            s = 0.0
            for qt in set(q_terms):
                s += (tf.get(qt, 0) * self._idf(qt))
            if s > 0.0:
                scores[did] = s
        hits = [DocHit(doc_id=did, score=sc) for did, sc in scores.items()]
        hits.sort(key=lambda h: h.score, reverse=True)
        return hits[:k]

# -------- convenience used by retriever/tests --------
_index_cache = {}
_index_mtime = {}

def load_index(path: str | Path = DEFAULT_INDEX_PATH) -> TfidfIndex:
    """Load index with simple file-based caching."""
    path = Path(path)
    path_str = str(path)
    
    # Check if file exists and get modification time
    if path.exists():
        current_mtime = path.stat().st_mtime
        
        # Return cached version if file hasn't changed
        if (path_str in _index_cache and 
            path_str in _index_mtime and 
            _index_mtime[path_str] == current_mtime):
            return _index_cache[path_str]
        
        # Load fresh index and cache it
        idx = TfidfIndex.load(path)
        _index_cache[path_str] = idx
        _index_mtime[path_str] = current_mtime
        return idx
    else:
        # No file exists, return empty index
        return TfidfIndex()

def search(query: str, k: int = 5, path: str | Path = DEFAULT_INDEX_PATH) -> List[DocHit]:
    idx = load_index(path)
    return idx.search(query, k=k)

def clear_index_cache(path: str | Path = DEFAULT_INDEX_PATH) -> None:
    """Clear the index cache for a specific path."""
    path_str = str(Path(path))
    _index_cache.pop(path_str, None)
    _index_mtime.pop(path_str, None)
