# /test/test_anon_bot.py
"""
Comprehensive smoke tests for anon_bot.
Run with:  pytest -q
"""

import pytest
from anon_bot import handler, rules


# ---------- rules: intents & handlers ----------

@pytest.mark.parametrize(
    "msg,expected",
    [
        ("", "empty"),
        ("help", "help"),
        ("/help", "help"),
        ("capabilities", "help"),
        ("reverse abc", "reverse"),
        ("echo hello world", "echo"),
        ("hi", "greet"),
        ("hello", "greet"),
        ("hey", "greet"),
        ("who are you", "chat"),
    ],
)
def test_rules_intent_of(msg, expected):
    assert rules.intent_of(msg) == expected


def test_rules_capabilities_contains_expected_items():
    caps = rules.capabilities()
    assert "help" in caps
    assert any(c.startswith("reverse") for c in caps)
    assert any(c.startswith("echo") for c in caps)


def test_rules_handlers_basic():
    assert "I can:" in rules.handle_help().text
    assert rules.handle_reverse("reverse hello").text == "olleh"
    assert rules.handle_reverse("reverse").text == "(nothing to reverse)"
    assert rules.handle_echo("echo one two").text == "one two"
    assert rules.handle_echo("echo").text == "(nothing to echo)"
    assert "Type 'help'" in rules.handle_greet().text


def test_rules_reply_for_empty_and_chat_paths():
    r = rules.reply_for("", [])
    assert "Please type something" in r.text

    r2 = rules.reply_for("who are you", [])
    assert "tiny anonymous chatbot" in r2.text

    r3 = rules.reply_for("can you help me", [])
    assert "I can:" in r3.text  # chat fallback detects 'help' and returns help


# ---------- handler: history & turn processing ----------

def test_handle_turn_appends_user_and_bot():
    hist = []
    out = handler.handle_turn("hello", hist, user=None)
    # last two entries should be ("user", ...), ("bot", ...)
    assert out[-2][0] == "user" and out[-2][1] == "hello"
    assert out[-1][0] == "bot" and "Type 'help'" in out[-1][1]


def test_handle_turn_with_existing_history_preserves_items():
    h2 = [("user", "prev"), ("bot", "ok")]
    out2 = handler.handle_turn("echo ping", h2, user=None)
    assert out2[:2] == h2  # preserved
    assert out2[-1][0] == "bot"
    assert out2[-1][1] == "ping"  # echo payload


def test_handle_text_convenience():
    reply = handler.handle_text("reverse abc")
    assert reply == "cba"


def test_handle_turn_empty_message_produces_prompt():
    out = handler.handle_turn("", [], user=None)
    assert out[-1][0] == "bot"
    assert "Please type" in out[-1][1]


def test_handler_coerces_weird_history_without_crashing():
    # Mix of tuples, lists, malformed entries, and non-iterables
    weird = [
        ("user", "ok"),
        ["bot", "fine"],
        "garbage",
        ("only_one_element",),
        ("user", 123),
        42,
        None,
    ]
    out = handler.handle_turn("hi", weird, user=None)
    # Should include a normalized user entry and a bot reply at the end
    assert out[-2] == ("user", "hi")
    assert out[-1][0] == "bot"


# ---------- end-to-end mini scriptable checks ----------

def test_greet_help_echo_reverse_flow():
    h = []
    h = handler.handle_turn("hi", h, None)
    assert "help" in h[-1][1].lower()

    h = handler.handle_turn("help", h, None)
    assert "I can:" in h[-1][1]

    h = handler.handle_turn("echo alpha beta", h, None)
    assert h[-1][1] == "alpha beta"

    h = handler.handle_turn("reverse zed", h, None)
    assert h[-1][1] == "dez"


