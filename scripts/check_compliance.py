# /scripts/check_compliance.py
#!/usr/bin/env python3
"""
Compliance checker for disallowed dependencies.

- Scans all .py files under project root (excluding venv/.git/etc).
- Flags imports of disallowed packages (by prefix).
- Exits nonzero if any violations are found.

Run:
    python scripts/check_compliance.py
"""
# … keep scan_file as-is …

#!/usr/bin/env python3
import sys, re
import os
from pathlib import Path

# -----------------------------
# Config
# -----------------------------

# Disallowed top-level import prefixes
DISALLOWED = {
    "torch",
    "tensorflow",
    "transformers",
    "openai",
    "azure.ai",       # heavy cloud SDK
    "azureml",
    "boto3",
    "botbuilder",     # Microsoft Bot Framework
}

IGNORE_DIRS = {".git", "__pycache__", "venv", ".venv", "env", ".env", "node_modules"}

IMPORT_RE = re.compile(r"^\s*(?:import|from)\s+([a-zA-Z0-9_.]+)")

# -----------------------------
# Scan
# -----------------------------

# top: keep existing imports/config …

def _supports_utf8() -> bool:
    enc = (sys.stdout.encoding or "").lower()
    return "utf-8" in enc

FAIL_MARK = "FAIL:" if not _supports_utf8() else "❌"
PASS_MARK = "OK:"   if not _supports_utf8() else "✅"

def scan_file(path: Path):
    fails = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return fails
    for i, line in enumerate(text.splitlines(), 1):
        m = IMPORT_RE.match(line)
        if not m:
            continue
        mod = m.group(1)
        root = mod.split(".")[0]
        if root in DISALLOWED:
            fails.append(f"{path.as_posix()}:{i}: disallowed import '{mod}'")
    return fails

def main():
    root = Path(__file__).resolve().parents[1]
    failures = []
    for p in root.rglob("*.py"):
        sp = p.as_posix()
        if any(seg in sp for seg in ("/.venv/", "/venv/", "/env/", "/__pycache__/", "/tests/")):
            continue
        failures.extend(scan_file(p))
    if failures:
        print("FAIL: Compliance check failed:")
        for msg in failures:
            print(msg)
        return 1
    print("OK: Compliance check passed (no disallowed deps).")
    return 0

if __name__ == "__main__":
    sys.exit(main())
