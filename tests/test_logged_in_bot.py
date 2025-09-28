# /test/test_logged_in_bot.py
"""
Tests for logged_in_bot.tools (no Azure required).
Run: pytest -q
"""

import os
import pytest

from logged_in_bot import tools as L


def test_help_route_and_reply():
    resp = L.handle_logged_in_turn("help", history=[], user=None)
    assert isinstance(resp, dict)
    assert "I can:" in resp["reply"]
    assert resp["meta"]["intent"] == "help"
    assert "sentiment" in resp["meta"]  # attached even in help path


def test_echo_payload():
    resp = L.handle_logged_in_turn("echo hello world", history=[], user=None)
    assert resp["reply"] == "hello world"
    assert resp["meta"]["intent"] == "echo"


def test_summarize_uses_first_sentence():
    text = "This is the first sentence. This is the second sentence."
    resp = L.handle_logged_in_turn(f"summarize {text}", history=[], user=None)
    # naive summarizer returns the first sentence (possibly truncated)
    assert "first sentence" in resp["reply"]
    assert resp["meta"]["intent"] == "summarize"
    assert "sentiment" in resp["meta"]  # sentiment computed on source text


def test_empty_input_prompts_user():
    resp = L.handle_logged_in_turn("", history=[], user=None)
    assert "Please type" in resp["reply"]
    assert resp["meta"]["intent"] == "empty"


def test_general_chat_fallback_and_sentiment():
    resp = L.handle_logged_in_turn("I love this project!", history=[], user=None)
    assert isinstance(resp["reply"], str) and len(resp["reply"]) > 0
    # sentiment present; backend may be "local" or "none" depending on env
    sent = resp["meta"].get("sentiment", {})
    assert sent.get("label") in {"positive", "neutral", "negative", None}


def test_optional_redaction_is_honored(monkeypatch):
    # Monkeypatch optional redactor to simulate PII masking
    monkeypatch.setattr(L, "pii_redact", lambda s: s.replace("555-1234", "[REDACTED]"), raising=False)
    resp = L.handle_logged_in_turn("echo call me at 555-1234", history=[], user=None)
    assert resp["meta"]["redacted"] is True
    assert resp["reply"] == "call me at [REDACTED]"


def test_input_length_cap(monkeypatch):
    # Cap input length to 10 chars; ensure ellipsis added
    monkeypatch.setenv("MAX_INPUT_CHARS", "10")
    long = "echo 1234567890ABCDEFGHIJ"
    resp = L.handle_logged_in_turn(long, history=[], user=None)
    # reply is payload of redacted/sanitized text; should end with ellipsis
    assert resp["reply"].endswith("…") or resp["reply"].endswith("...")  # handle different ellipsis if changed


def test_history_pass_through_shape():
    # History should be accepted and not crash; we don't deeply inspect here
    hist = [("user", "prev"), ("bot", "ok")]
    resp = L.handle_logged_in_turn("echo ping", history=hist, user={"id": "u1"})
    assert resp["reply"] == "ping"
    assert isinstance(resp["meta"], dict)


@pytest.mark.parametrize("msg,expected_intent", [
    ("help", "help"),
    ("echo abc", "echo"),
    ("summarize One. Two.", "summarize"),
    ("random chat", "chat"),
])
def test_intent_detection_smoke(msg, expected_intent):
    r = L.handle_logged_in_turn(msg, history=[], user=None)
    assert r["meta"]["intent"] == expected_intent

