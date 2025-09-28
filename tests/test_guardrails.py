# /test/test_guardrails.py
"""
Guardrail tests:
- Ensure compliance checker passes (no disallowed deps imported).
- Ensure anon_bot.rules doesn't produce unsafe replies for empty / bad input.
"""

import subprocess
import sys
import pathlib

import pytest

from anon_bot import rules


def test_compliance_script_runs_clean():
    root = pathlib.Path(__file__).resolve().parent.parent
    script = root / "scripts" / "check_compliance.py"
    # Run as a subprocess so we catch real exit code
    proc = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
    # If it fails, dump output for debugging
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr, file=sys.stderr)
    assert proc.returncode == 0


@pytest.mark.parametrize("msg", ["", None, "   "])
def test_rules_empty_prompts_are_safe(msg):
    r = rules.reply_for(msg or "", [])
    # Should politely nudge the user, not crash
    assert "Please" in r.text or "help" in r.text.lower()


@pytest.mark.parametrize("msg", ["rm -rf /", "DROP TABLE users;"])
def test_rules_handles_malicious_looking_input(msg):
    r = rules.reply_for(msg, [])
    # The bot should fall back safely to generic chat response
    assert "Noted" in r.text or "help" in r.text
