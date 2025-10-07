# guardrails/__init__.py
from typing import Optional, List

# Try to re-export the real implementation if it exists.
try:
    # adjust to where the real function lives if different:
    from .core import enforce_guardrails as _enforce_guardrails  # e.g., .core/.enforce/.rules
    enforce_guardrails = _enforce_guardrails
except Exception:
    # Doc-safe fallback: no-op so pdoc (and imports) never crash.
    def enforce_guardrails(message: str, *, rules: Optional[List[str]] = None) -> str:
        """
        No-op guardrails shim used when the real implementation is unavailable
        (e.g., during documentation builds or minimal environments).
        """
        return message

__all__ = ["enforce_guardrails"]
