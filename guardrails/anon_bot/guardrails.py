import re

MAX_INPUT_LEN = 500  # cap to keep things safe and fast

# Verifying lightweight 'block' patterns:
DISALLOWED = [r"(?:kill|suicide|bomb|explosive|make\s+a\s+weapon)",  # harmful instructions
              r"(?:credit\s*card\s*number|ssn|social\s*security)"  # sensitive info requests
              ]

# Verifying lightweight profanity redaction:
PROFANITY = [r"\b(?:damn|hell|shit|fuck)\b"]

PII_PATTERNS = {
    "email": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    "phone": re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}"),
}


def too_long(text: str) -> bool:
    return len(text) > MAX_INPUT_LEN


def matches_any(text: str, patterns) -> bool:
    return any(re.search(p, text, flags=re.IGNORECASE) for p in patterns)


def redact_pii(text: str) -> str:
    redacted = PII_PATTERNS['email'].sub('[EMAIL_REDACTED]', text)
    redacted = PII_PATTERNS['phone'].sub('[PHONE_REDACTED]', redacted)
    return redacted


def redact_profanity(text: str) -> str:
    out = text
    for p in PROFANITY:
        out = re.sub(p, '[REDACTED]', out, flags=re.IGNORECASE)
        return out


def enforce_guardrails(user_text: str):
    """
    Returns: (ok: bool, cleaned_or_reason: str)
    - ok=True: proceed with cleaned text
    - ok=False: return refusal reason in cleaned_or_reason
    """
    if too_long(user_text):
        return False, 'Sorry, that message is too long. Please shorten it.'

    if matches_any(user_text, DISALLOWED):
        return False, "I can't help with that topic. Please ask something safe and appropriate"

    cleaned = redact_pii(user_text)
    cleaned = redact_profanity(cleaned)

    return True, cleaned
