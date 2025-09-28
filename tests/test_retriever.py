# tests/test_retriever.py
from pathlib import Path
from memory.rag.data.indexer import TfidfIndex, DocMeta
from memory.rag.data.retriever import retrieve, Filters

def _add(idx, did, text, title=None, tags=None):
    meta = DocMeta(doc_id=did, source="inline", title=title, tags=tags)
    idx.add_text(did, text, meta)

def test_retrieve_passage(tmp_path: Path, monkeypatch):
    # Build tiny in-memory index and save
    from memory.rag.data.indexer import DEFAULT_INDEX_PATH
    p = tmp_path / "idx.json"
    from memory.rag.data.indexer import TfidfIndex
    idx = TfidfIndex()
    _add(idx, "d1", "Rules for an anonymous chatbot are simple and fast.", title="Design", tags=["doc","slide"])
    _add(idx, "d2", "This document explains retrieval and index search.", title="RAG", tags=["doc"])
    idx.save(p)

    # Run retrieval against this saved index
    res = retrieve("anonymous chatbot rules", k=2, index_path=p)
    assert res and any("anonymous" in r.text.lower() for r in res)

def test_filters(tmp_path: Path):
    from memory.rag.data.indexer import TfidfIndex
    idx = TfidfIndex()
    _add(idx, "a", "hello world", title="Alpha", tags=["doc","slide"])
    _add(idx, "b", "hello world", title="Beta", tags=["doc"])
    p = tmp_path / "idx.json"
    idx.save(p)

    f = Filters(title_contains="alpha", require_tags=["doc","slide"])
    res = retrieve("hello", k=5, index_path=p, filters=f)
    assert len(res) == 1 and res[0].title == "Alpha"
