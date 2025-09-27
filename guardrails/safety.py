# /guardrails/safety.py
from __future__ import annotations
import re
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Tuple

from .pii_redaction import redact_with_report, PiiMatch

# ---- Config ------------------------------------------------------------------
@dataclass(slots=True)
class SafetyConfig:
    redact_pii: bool = True
    block_on_jailbreak: bool = True
    block_on_malicious_code: bool = True
    mask_secrets: str = "[SECRET]"

# Signals kept intentionally lightweight (no extra deps)
_PROMPT_INJECTION = [
    r"\bignore (all|previous) (instructions|directions)\b",
    r"\boverride (your|all) (rules|guardrails|safety)\b",
    r"\bpretend to be (?:an|a) (?:unfiltered|unsafe) model\b",
    r"\bjailbreak\b",
    r"\bdisabl(e|ing) (safety|guardrails)\b",
]
_MALICIOUS_CODE = [
    r"\brm\s+-rf\b", r"\bdel\s+/s\b", r"\bformat\s+c:\b",
    r"\b(?:curl|wget)\s+.+\|\s*(?:bash|sh)\b",
    r"\bnc\s+-e\b", r"\bpowershell\b",
]
# Common token patterns (subset; add more as needed)
_SECRETS = [
    r"\bAKIA[0-9A-Z]{16}\b",                # AWS access key id
    r"\bgh[pousr]_[A-Za-z0-9]{36}\b",       # GitHub token
    r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b",    # Slack token
    r"\bAIza[0-9A-Za-z\-_]{35}\b",          # Google API key
    r"\bS[Kk]-[A-Za-z0-9-]{20,}\b",         # generic "sk-" style keys
]
# Keep profanity list mild to avoid overblocking
_PROFANITY = [r"\bdamn\b", r"\bhell\b"]

def _scan(patterns: List[str], text: str) -> List[Tuple[str, Tuple[int, int]]]:
    hits: List[Tuple[str, Tuple[int, int]]] = []
    for p in patterns:
        for m in re.finditer(p, text, flags=re.IGNORECASE):
            hits.append((m.group(0), m.span()))
    return hits

# ---- Report ------------------------------------------------------------------
@dataclass(slots=True)
class SafetyReport:
    original_text: str
    sanitized_text: str
    pii: List[PiiMatch] = field(default_factory=list)
    secrets: List[Tuple[str, Tuple[int, int]]] = field(default_factory=list)
    prompt_injection: List[Tuple[str, Tuple[int, int]]] = field(default_factory=list)
    malicious_code: List[Tuple[str, Tuple[int, int]]] = field(default_factory=list)
    profanity: List[Tuple[str, Tuple[int, int]]] = field(default_factory=list)
    action: str = "allow"  # "allow" | "warn" | "block"

    def to_dict(self) -> Dict[str, object]:
        d = asdict(self)
        d["pii"] = [asdict(p) for p in self.pii]
        return d

# ---- API ---------------------------------------------------------------------
def assess(text: str, cfg: SafetyConfig | None = None) -> SafetyReport:
    cfg = cfg or SafetyConfig()
    sanitized = text or ""

    # 1) PII redaction
    pii_hits: List[PiiMatch] = []
    if cfg.redact_pii:
        sanitized, pii_hits = redact_with_report(sanitized)

    # 2) Secrets detection (masked, but keep record)
    secrets = _scan(_SECRETS, sanitized)
    for val, (s, e) in secrets:
        sanitized = sanitized[:s] + cfg.mask_secrets + sanitized[e:]

    # 3) Prompt-injection & malicious code
    inj = _scan(_PROMPT_INJECTION, sanitized)
    mal = _scan(_MALICIOUS_CODE, sanitized)

    # 4) Mild profanity signal (does not block)
    prof = _scan(_PROFANITY, sanitized)

    # Decide action
    action = "allow"
    if (cfg.block_on_jailbreak and inj) or (cfg.block_on_malicious_code and mal):
        action = "block"
    elif secrets or pii_hits or prof:
        action = "warn"

    return SafetyReport(
        original_text=text or "",
        sanitized_text=sanitized,
        pii=pii_hits,
        secrets=secrets,
        prompt_injection=inj,
        malicious_code=mal,
        profanity=prof,
        action=action,
    )

def sanitize_user_input(text: str, cfg: SafetyConfig | None = None) -> tuple[str, SafetyReport]:
    """Convenience wrapper used by HTTP routes/bots."""
    rep = assess(text, cfg)
    return rep.sanitized_text, rep
