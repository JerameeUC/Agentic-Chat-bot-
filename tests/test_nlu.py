# /test/test_nlu.py
"""
Basic tests for the NLU pipeline and router.
Run with:  pytest -q
"""

import pytest

from nlu import pipeline, router


def test_pipeline_greeting():
    out = pipeline.analyze("Hello there")
    assert out["intent"] == "greeting"
    assert out["confidence"] > 0.5


def test_pipeline_general():
    out = pipeline.analyze("completely random utterance")
    assert out["intent"] == "general"
    assert "entities" in out


def test_router_route_and_respond():
    # Route a help query
    r = router.route("Can you help me?")
    assert r["intent"] == "help"
    assert r["action"] == "HELP"

    reply = router.respond("Can you help me?")
    assert isinstance(reply, str)
    assert "help" in reply.lower()


def test_router_sentiment_positive():
    r = router.route("I love this bot!")
    assert r["intent"] == "sentiment_positive"
    reply = router.respond("I love this bot!")
    assert "glad" in reply.lower() or "hear" in reply.lower()


def test_router_goodbye():
    r = router.route("bye")
    assert r["action"] == "GOODBYE"
    reply = router.respond("bye")
    assert "goodbye" in reply.lower()
