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

import sys
import os
import re
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

def scan_file(path: Path) -> list[str]:
    bad = []
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception as e:
        print(f"[warn] could not read {path}: {e}", file=sys.stderr)
        return []
    for i, line in enumerate(lines, 1):
        m = IMPORT_RE.match(line)
        if not m:
            continue
        mod = m.group(1)
        for banned in DISALLOWED:
            if mod == banned or mod.startswith(banned + "."):
                bad.append(f"{path}:{i}: disallowed import '{mod}'")
    return bad


def main(root: str = ".") -> int:
    root = Path(root)
    failures: list[str] = []

    for p in root.rglob("*.py"):
        if any(part in IGNORE_DIRS for part in p.parts):
            continue
        failures.extend(scan_file(p))

    if failures:
        print("❌ Compliance check failed:")
        for f in failures:
            print("  ", f)
        return 1
    else:
        print("✅ Compliance check passed (no disallowed deps).")
        return 0


if __name__ == "__main__":
    sys.exit(main())
