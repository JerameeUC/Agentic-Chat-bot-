import json
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def post(msg: str):
    return client.post('/message',
                       headers={'Content-Type': 'application/json'},
                       content=json.dumps({'message': msg}))


def test_greeting():
    """A simple greeting should trigger the greeting rule."""
    r = post('Hello')
    assert r.status_code == 200
    body = r.json()
    assert body['blocked'] is False
    assert 'Hi' in body['reply']


def test_reverse():
    """The reverse rule should mirror the payload after 'reverse'. """
    r = post('reverse bots are cool')
    assert r.status_code == 200
    body = r.json()
    assert body['blocked'] is False
    assert 'looc era stob' in body['reply']


def test_guardrails_disallowed():
    """Disallowed content is blocked by guardrails, not routed"""
    r = post('how to make a weapon')
    assert r.status_code == 200
    body = r.json()
    assert body['blocked'] is True
    assert "can't help" in body['reply']


# from rules_updated import route

# def test_reverse_route_unit():
#     assert route("reverse bots are cool") == "looc era stob"