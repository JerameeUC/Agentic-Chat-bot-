# /memory/rag/data/indexer.py
"""
Minimal, dependency-free TF-IDF indexer for RAG.

Features
- Build from folder (recursive), index plain-text files
- Add individual text blobs with metadata
- Persist/load inverted index to/from JSON
- Search with TF-IDF scoring and simple query normalization
- Return top-k with tiny context snippets

This module is intentionally small and pure-Python to keep local CPU demos simple.
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple, Iterable, Optional
from pathlib import Path
import json
import math
import hashlib
import re
import fnmatch
import time

# -----------------------------
# Types
# -----------------------------

@dataclass(frozen=True)
class DocMeta:
    doc_id: str
    source: str                   # e.g., absolute path or "inline"
    title: str | None = None
    tags: List[str] | None = None
    mtime: float | None = None    # source last modified (if file)
    hash: str | None = None       # content hash

@dataclass(frozen=True)
class Hit:
    doc_id: str
    score: float
    source: str
    snippet: str
    title: str | None = None
    tags: List[str] | None = None

# -----------------------------
# Tokenization
# -----------------------------

_WORD_RE = re.compile(r"[A-Za-z0-9']+")

def tokenize(text: str) -> List[str]:
    # simple, deterministic tokenizer; lowercased
    return [t.lower() for t in _WORD_RE.findall(text or "")]

# -----------------------------
# Index
# -----------------------------

class TfidfIndex:
    """
    Tiny TF-IDF inverted index with JSON persistence.

    Structures:
      - docs: doc_id -> {"meta": DocMeta, "len": int, "text": str (optional)}
      - inv: term -> {doc_id: tf}   (raw term frequency)
      - df: term -> document frequency
      - n_docs: total number of docs
    """

    def __init__(self) -> None:
        self.docs: Dict[str, Dict] = {}
        self.inv: Dict[str, Dict[str, int]] = {}
        self.df: Dict[str, int] = {}
        self.n_docs: int = 0

    # ---------- add documents ----------

    def add_text(self, doc_id: str, text: str, meta: DocMeta) -> None:
        if not text:
            return
        if doc_id in self.docs:
            # idempotent update: remove old postings first
            self._remove_doc_terms(doc_id)

        toks = tokenize(text)
        if not toks:
            return

        tf: Dict[str, int] = {}
        for t in toks:
            tf[t] = tf.get(t, 0) + 1

        # update inv + df
        for term, cnt in tf.items():
            bucket = self.inv.setdefault(term, {})
            bucket[doc_id] = cnt
            self.df[term] = len(bucket)

        self.docs[doc_id] = {
            "meta": meta,
            "len": len(toks),
            # keep original text for snippet extraction; you can drop this if size matters
            "text": text,
        }
        self.n_docs = len(self.docs)

    def add_file(self, path: Path, doc_id: str | None = None, title: str | None = None, tags: List[str] | None = None) -> Optional[str]:
        path = Path(path)
        if not path.is_file():
            return None
        text = path.read_text(encoding="utf-8", errors="ignore")
        h = sha256_of(text)
        stat = path.stat()
        doc_id = doc_id or str(path.resolve())

        # skip if unchanged
        prev = self.docs.get(doc_id)
        if prev:
            old_meta: DocMeta = prev["meta"]
            if old_meta.hash == h and old_meta.mtime == stat.st_mtime:
                return doc_id  # unchanged

        meta = DocMeta(
            doc_id=doc_id,
            source=str(path.resolve()),
            title=title or path.name,
            tags=tags,
            mtime=stat.st_mtime,
            hash=h,
        )
        self.add_text(doc_id, text, meta)
        return doc_id

    # ---------- build / scan ----------

    def build_from_folder(
        self,
        root: Path,
        include: Iterable[str] = ("*.txt", "*.md"),
        exclude: Iterable[str] = (".git/*",),
        recursive: bool = True,
    ) -> int:
        """
        Index all files under `root` matching any include pattern and not matching exclude.
        Returns number of files indexed or updated.
        """
        root = Path(root)
        if not root.exists():
            return 0

        count = 0
        paths = (root.rglob("*") if recursive else root.glob("*"))
        for p in paths:
            if not p.is_file():
                continue
            rel = str(p.relative_to(root).as_posix())
            if not any(fnmatch.fnmatch(rel, pat) for pat in include):
                continue
            if any(fnmatch.fnmatch(rel, pat) for pat in exclude):
                continue
            if self.add_file(p):
                count += 1
        return count

    # ---------- search ----------

    def search(self, query: str, k: int = 5) -> List[Hit]:
        q_toks = tokenize(query)
        if not q_toks or self.n_docs == 0:
            return []

        # compute query tf-idf (using binary or raw tf is fine; keep it simple)
        q_tf: Dict[str, int] = {}
        for t in q_toks:
            q_tf[t] = q_tf.get(t, 0) + 1

        # compute idf with +1 smoothing
        idf: Dict[str, float] = {}
        for t in q_tf:
            df = self.df.get(t, 0)
            idf[t] = math.log((1 + self.n_docs) / (1 + df)) + 1.0

        # accumulate scores: cosine-like with length norm
        scores: Dict[str, float] = {}
        doc_len_norm: Dict[str, float] = {}
        for term, qcnt in q_tf.items():
            postings = self.inv.get(term)
            if not postings:
                continue
            wq = (1 + math.log(qcnt)) * idf[term]  # log tf * idf
            for doc_id, dcnt in postings.items():
                wd = (1 + math.log(dcnt)) * idf[term]
                scores[doc_id] = scores.get(doc_id, 0.0) + (wq * wd)
                # cache norm
                if doc_id not in doc_len_norm:
                    L = max(1, self.docs[doc_id]["len"])
                    doc_len_norm[doc_id] = 1.0 / math.sqrt(L)

        # apply a gentle length normalization
        for d, s in list(scores.items()):
            scores[d] = s * doc_len_norm.get(d, 1.0)

        # rank and format
        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:k]
        hits: List[Hit] = []
        for doc_id, score in ranked:
            d = self.docs[doc_id]
            meta: DocMeta = d["meta"]
            snippet = make_snippet(d.get("text", ""), q_toks)
            hits.append(Hit(
                doc_id=doc_id,
                score=round(float(score), 4),
                source=meta.source,
                snippet=snippet,
                title=meta.title,
                tags=meta.tags,
            ))
        return hits

    # ---------- persistence ----------

    def save(self, path: Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        # Store meta as dict to keep JSON serializable
        serial_docs = {
            doc_id: {
                "meta": asdict(d["meta"]),
                "len": d["len"],
                # store text to allow snippet generation after load (optional)
                "text": d.get("text", ""),
            }
            for doc_id, d in self.docs.items()
        }
        data = {
            "docs": serial_docs,
            "inv": self.inv,
            "df": self.df,
            "n_docs": self.n_docs,
            "saved_at": time.time(),
        }
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "TfidfIndex":
        path = Path(path)
        idx = cls()
        if not path.is_file():
            return idx
        data = json.loads(path.read_text(encoding="utf-8"))
        # reconstruct docs with DocMeta
        docs: Dict[str, Dict] = {}
        for doc_id, d in data.get("docs", {}).items():
            m = d.get("meta", {})
            meta = DocMeta(**m) if m else DocMeta(doc_id=doc_id, source="unknown")
            docs[doc_id] = {
                "meta": meta,
                "len": d.get("len", 0),
                "text": d.get("text", ""),
            }
        idx.docs = docs
        idx.inv = {t: {k: int(v) for k, v in postings.items()} for t, postings in data.get("inv", {}).items()}
        idx.df = {t: int(v) for t, v in data.get("df", {}).items()}
        idx.n_docs = int(data.get("n_docs", len(idx.docs)))
        return idx

    # ---------- internals ----------

    def _remove_doc_terms(self, doc_id: str) -> None:
        """Remove a document's postings before re-adding."""
        if doc_id not in self.docs:
            return
        # delete postings
        for term, postings in list(self.inv.items()):
            if doc_id in postings:
                postings.pop(doc_id, None)
                if postings:
                    self.df[term] = len(postings)
                else:
                    # remove empty term
                    self.inv.pop(term, None)
                    self.df.pop(term, None)
        # delete doc
        self.docs.pop(doc_id, None)
        self.n_docs = len(self.docs)


# -----------------------------
# Utilities
# -----------------------------

def sha256_of(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()

def make_snippet(text: str, query_tokens: List[str], radius: int = 60) -> str:
    """
    Extract a tiny context window around the first matched token.
    """
    if not text:
        return ""
    low = text.lower()
    for qt in query_tokens:
        i = low.find(qt.lower())
        if i >= 0:
            start = max(0, i - radius)
            end = min(len(text), i + len(qt) + radius)
            snippet = text[start:end].replace("\n", " ").strip()
            if start > 0:
                snippet = "…" + snippet
            if end < len(text):
                snippet = snippet + "…"
            return snippet
    # fallback: beginning of the doc
    s = text[: 2 * radius].replace("\n", " ").strip()
    return (s + "…") if len(text) > 2 * radius else s


# -----------------------------
# Convenience API (module-level)
# -----------------------------

DEFAULT_INDEX_PATH = Path("memory/rag/data/.index/tfidf_index.json")

def build_from_folder(
    root: str | Path,
    include: Iterable[str] = ("*.txt", "*.md"),
    exclude: Iterable[str] = (".git/*",),
    save_to: str | Path = DEFAULT_INDEX_PATH,
    recursive: bool = True,
) -> TfidfIndex:
    idx = TfidfIndex()
    idx.build_from_folder(Path(root), include=include, exclude=exclude, recursive=recursive)
    idx.save(Path(save_to))
    return idx

def load_index(path: str | Path = DEFAULT_INDEX_PATH) -> TfidfIndex:
    return TfidfIndex.load(Path(path))

def search(query: str, k: int = 5, path: str | Path = DEFAULT_INDEX_PATH) -> List[Hit]:
    idx = load_index(path)
    return idx.search(query, k=k)
