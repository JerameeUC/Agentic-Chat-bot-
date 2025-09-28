# tests/test_sessions.py
from memory.sessions import SessionStore

def test_create_and_history():
    st = SessionStore(ttl_seconds=None, max_history=3)
    s = st.create(user_id="u1")
    st.append_user(s.session_id, "a")
    st.append_bot(s.session_id, "b")
    st.append_user(s.session_id, "c")
    st.append_bot(s.session_id, "d")  # caps to last 3
    h = st.get_history(s.session_id)
    assert h == [("bot","b"), ("user","c"), ("bot","d")]

def test_save_load(tmp_path):
    st = SessionStore(ttl_seconds=None)
    s = st.create()
    st.append_user(s.session_id, "hello")
    p = tmp_path / "sess.json"
    st.save(p)
    st2 = SessionStore.load(p)
    assert st2.get_history(s.session_id)[0] == ("user","hello")
