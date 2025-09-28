# /test/test_memory.py
"""
Tests for memory.sessions
Run: pytest -q
"""

import time
from pathlib import Path

from memory import sessions as S


def test_create_and_append_history():
    store = S.SessionStore(ttl_seconds=None, max_history=10)
    sess = store.create(user_id="u1")
    assert sess.session_id
    sid = sess.session_id

    store.append_user(sid, "hello")
    store.append_bot(sid, "hi there")
    hist = store.get_history(sid)
    assert hist == [("user", "hello"), ("bot", "hi there")]

    # ensure timestamps update
    before = sess.updated_at
    store.append_user(sid, "next")
    assert store.get(sid).updated_at >= before


def test_max_history_cap():
    store = S.SessionStore(ttl_seconds=None, max_history=3)
    s = store.create()
    sid = s.session_id

    # 4 appends → only last 3 kept
    store.append_user(sid, "a")
    store.append_bot(sid, "b")
    store.append_user(sid, "c")
    store.append_bot(sid, "d")
    hist = store.get_history(sid)
    assert hist == [("bot", "b"), ("user", "c"), ("bot", "d")]


def test_ttl_sweep_expires_old_sessions():
    store = S.SessionStore(ttl_seconds=0)  # expire immediately
    s1 = store.create()
    s2 = store.create()
    # Nudge updated_at into the past
    store._sessions[s1.session_id].updated_at -= 10
    store._sessions[s2.session_id].updated_at -= 10

    removed = store.sweep()
    assert removed >= 1
    # After sweep, remaining sessions (if any) must be fresh
    for sid in store.all_ids():
        assert not store._expired(store.get(sid))


def test_key_value_store_helpers():
    store = S.SessionStore(ttl_seconds=None)
    s = store.create()
    sid = s.session_id

    store.set(sid, "mode", "anonymous")
    store.set(sid, "counter", 1)
    assert store.get_value(sid, "mode") == "anonymous"
    assert store.data_dict(sid)["counter"] == 1

    # get_value default
    assert store.get_value(sid, "missing", default="x") == "x"


def test_persistence_save_and_load(tmp_path: Path):
    p = tmp_path / "sess.json"

    st1 = S.SessionStore(ttl_seconds=None)
    s = st1.create(user_id="uX")
    st1.append_user(s.session_id, "hello")
    st1.append_bot(s.session_id, "hi")
    st1.save(p)

    st2 = S.SessionStore.load(p)
    hist2 = st2.get_history(s.session_id)
    assert hist2 == [("user", "hello"), ("bot", "hi")]
    assert st2.get(s.session_id).user_id == "uX"


def test_module_level_singleton_and_helpers():
    s = S.new_session(user_id="alice")
    sid = s.session_id
    S.append_user(sid, "hey")
    S.append_bot(sid, "hello!")
    assert S.history(sid)[-2:] == [("user", "hey"), ("bot", "hello!")]
    S.set_value(sid, "flag", True)
    assert S.get_value(sid, "flag") is True
