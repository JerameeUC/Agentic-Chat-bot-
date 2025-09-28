# /tests/test_indexer.py
from pathlib import Path
from memory.rag.data.indexer import TfidfIndex, search, DEFAULT_INDEX_PATH

def test_add_and_search(tmp_path: Path):
    p = tmp_path / "a.md"
    p.write_text("Hello world. This is an anonymous chatbot.\nRules are simple.", encoding="utf-8")
    idx = TfidfIndex()
    idx.add_file(p)
    hits = idx.search("anonymous rules", k=5)
    assert hits and hits[0].doc_id == str(p.resolve())

def test_persist_and_load(tmp_path: Path):
    p = tmp_path / "index.json"
    idx = TfidfIndex()
    idx.add_text("id1", "cats are great, dogs are cool", meta=__meta("id1"))
    idx.save(p)
    loaded = TfidfIndex.load(p)
    hits = loaded.search("dogs", k=1)
    assert hits and hits[0].doc_id == "id1"

def __meta(i: str):
    from memory.rag.data.indexer import DocMeta
    return DocMeta(doc_id=i, source="inline", title=i)
