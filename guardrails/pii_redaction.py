# /guardrails/pii_redaction.py
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Dict, List, Tuple

# ---- Types -------------------------------------------------------------------
@dataclass(frozen=True)
class PiiMatch:
    kind: str
    value: str
    span: Tuple[int, int]
    replacement: str

# ---- Patterns ----------------------------------------------------------------
# Focus on high-signal, low-false-positive patterns
_PATTERNS: Dict[str, re.Pattern] = {
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "phone": re.compile(
        r"\b(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}\b"
    ),
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "ip": re.compile(
        r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d{1,2})\.){3}(?:25[0-5]|2[0-4]\d|1?\d{1,2})\b"
    ),
    "url": re.compile(r"\bhttps?://[^\s]+"),
    # Broad CC finder; we filter with Luhn
    "cc": re.compile(r"\b(?:\d[ -]?){13,19}\b"),
}

def _only_digits(s: str) -> str:
    return "".join(ch for ch in s if ch.isdigit())

def _luhn_ok(number: str) -> bool:
    try:
        digits = [int(x) for x in number]
    except ValueError:
        return False
    parity = len(digits) % 2
    total = 0
    for i, d in enumerate(digits):
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0

# ---- Redaction core -----------------------------------------------------------
def redact_with_report(
    text: str,
    *,
    mask_map: Dict[str, str] | None = None,
    preserve_cc_last4: bool = True,
) -> tuple[str, List[PiiMatch]]:
    """
    Return (redacted_text, findings). Keeps non-overlapping highest-priority matches.
    """
    if not text:
        return text, []

    mask_map = mask_map or {
        "email": "[EMAIL]",
        "phone": "[PHONE]",
        "ssn": "[SSN]",
        "ip": "[IP]",
        "url": "[URL]",
        "cc": "[CC]",  # overridden if preserve_cc_last4
    }

    matches: List[PiiMatch] = []
    for kind, pat in _PATTERNS.items():
        for m in pat.finditer(text):
            raw = m.group(0)
            if kind == "cc":
                digits = _only_digits(raw)
                if len(digits) < 13 or len(digits) > 19 or not _luhn_ok(digits):
                    continue
                if preserve_cc_last4 and len(digits) >= 4:
                    repl = f"[CC••••{digits[-4:]}]"
                else:
                    repl = mask_map["cc"]
            else:
                repl = mask_map.get(kind, "[REDACTED]")

            matches.append(PiiMatch(kind=kind, value=raw, span=m.span(), replacement=repl))

    # Resolve overlaps by keeping earliest, then skipping overlapping tails
    matches.sort(key=lambda x: (x.span[0], -(x.span[1] - x.span[0])))
    resolved: List[PiiMatch] = []
    last_end = -1
    for m in matches:
        if m.span[0] >= last_end:
            resolved.append(m)
            last_end = m.span[1]

    # Build redacted string
    out = []
    idx = 0
    for m in resolved:
        s, e = m.span
        out.append(text[idx:s])
        out.append(m.replacement)
        idx = e
    out.append(text[idx:])
    return "".join(out), resolved

# ---- Minimal compatibility API -----------------------------------------------
def redact(t: str) -> str:
    """
    Backwards-compatible simple API: return redacted text only.
    """
    return redact_with_report(t)[0]
