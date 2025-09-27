#!/usr/bin/env python3
# flatten_anytree.py — Flatten a folder tree (code/config) into one text file.
# Usage:
#   python flatten_anytree.py [ROOT_DIR] [OUTPUT_FILE]
# Examples:
#   python flatten_anytree.py C:\path\to\repo FLATTENED_CODE.txt
#   python flatten_anytree.py . out.txt --include-exts .py,.ipynb --exclude-dirs .git,node_modules
#
# New in this patched version:
#   - Skips common .gitignore-style junk by default (node_modules, .venv, __pycache__, caches, etc.).
#   - Skips noisy/secret files like .env, .env.*, *.log, *.tmp, *.pyc by default.
#   - Adds CLI flags: --exclude-dirs, --exclude-files, --exclude-globs to extend ignores.
#   - Removes ".env" from default INCLUDE_EXTS for safety (you can still include via flags).
#
import json
import os
import sys
import fnmatch
from pathlib import Path
from typing import Iterable, Set, List

INCLUDE_EXTS: Set[str] = {
    ".py", ".ipynb", ".json", ".md", ".txt", ".yml", ".yaml",
    ".ini", ".cfg", ".conf", ".service", ".sh", ".bat",
    ".js", ".ts", ".tsx", ".jsx", ".css", ".html",
    ".toml", ".dockerfile"
}

EXCLUDE_DIRS: Set[str] = {
    ".git", ".hg", ".svn", "__pycache__", "node_modules",
    ".venv", "venv", "env", "dist", "build",
    "artifacts", "logs", ".idea", ".vscode", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", ".tox", ".nox", ".hypothesis",
    ".cache", ".gradle", ".parcel-cache", ".next", ".turbo",
    ".pnpm-store", ".yarn", ".yarn/cache", ".nuxt", ".svelte-kit"
}

# Filenames to always skip
EXCLUDE_FILES: Set[str] = {
    ".DS_Store", "Thumbs.db", ".coverage", ".python-version",
}

# Glob patterns to skip (gitignore-like, simple fnmatch on the basename)
EXCLUDE_GLOBS: List[str] = [
    "*.log", "*.tmp", "*.temp", "*.bak", "*.swp", "*.swo",
    "*.pyc", "*.pyo", "*.pyd", "*.class",
    "*.lock", "*.pid",
    "*.egg-info", "*.eggs",
    "*.sqlite", "*.sqlite3", "*.db", "*.pkl",
    ".env", ".env.*",
]

MAX_FILE_BYTES_DEFAULT = 2_000_000  # 2 MB safety default


def is_included_file(path: Path, include_exts: Set[str]) -> bool:
    if not path.is_file():
        return False
    # Dockerfile special-case: no suffix
    if path.name.lower() == "dockerfile":
        return True
    return path.suffix.lower() in include_exts


def read_ipynb_code_cells(nb_path: Path) -> str:
    try:
        data = json.loads(nb_path.read_text(encoding="utf-8"))
    except Exception as e:
        return f"[ERROR reading notebook JSON: {e}]"
    cells = data.get("cells", [])
    out_lines: List[str] = []
    count = 0
    for c in cells:
        if c.get("cell_type") == "code":
            count += 1
            src = c.get("source", [])
            code = "".join(src)
            out_lines.append(f"# %% [code cell {count}]")
            out_lines.append(code.rstrip() + "\\n")
    if not out_lines:
        return "[No code cells found]"
    return "\\n".join(out_lines)


def read_text_file(path: Path) -> str:
    try:
        if path.suffix.lower() == ".ipynb":
            return read_ipynb_code_cells(path)
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return f"[ERROR reading file: {e}]"


def walk_files(root: Path,
               exclude_dirs: Set[str],
               include_exts: Set[str],
               max_bytes: int,
               follow_symlinks: bool,
               exclude_files: Set[str],
               exclude_globs: List[str]) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(root, followlinks=follow_symlinks):
        # prune excluded dirs in-place
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
        for name in filenames:
            # filename-level filters
            if name in exclude_files:
                continue
            if any(fnmatch.fnmatch(name, pat) for pat in exclude_globs):
                continue

            p = Path(dirpath) / name
            if is_included_file(p, include_exts):
                try:
                    if p.stat().st_size <= max_bytes:
                        yield p
                except Exception:
                    continue


def parse_str_set_arg(raw: str, default: Set[str]) -> Set[str]:
    # Parse comma-separated items into a set of strings (filenames or dirnames).
    if raw is None or not str(raw).strip():
        return set(default)
    return {s.strip() for s in raw.split(",") if s.strip()}


def parse_list_arg(raw: str, default: Set[str]) -> Set[str]:
    # Parse comma-separated items; empty -> default. Example: ".py,.ipynb,.md"
    if raw is None or not str(raw).strip():
        return set(default)
    items = [s.strip() for s in raw.split(",") if s.strip()]
    # normalize extensions to lowercase with a leading dot when applicable
    norm: Set[str] = set()
    for it in items:
        it_low = it.lower()
        if it_low == "dockerfile":
            norm.add("dockerfile")  # handled specially
        elif it_low.startswith("."):
            norm.add(it_low)
        else:
            norm.add("." + it_low)
    return norm


def main(argv: List[str]) -> int:
    import argparse

    ap = argparse.ArgumentParser(
        description="Flatten a folder tree (code/config) into one text file with file headers."
    )
    ap.add_argument("root", nargs="?", default=".", help="Root directory to scan (default: current dir)")
    ap.add_argument("out", nargs="?", default="FLATTENED_CODE.txt", help="Output text file (default: FLATTENED_CODE.txt)")
    ap.add_argument("--include-exts", dest="include_exts", default="",
                    help="Comma-separated list of extensions to include (e.g. .py,.ipynb,.md). Default uses a sane preset.")
    ap.add_argument("--exclude-dirs", dest="exclude_dirs", default="",
                    help="Comma-separated list of directory names to exclude (in addition to defaults).")
    ap.add_argument("--exclude-files", dest="exclude_files", default="",
                    help="Comma-separated list of filenames to exclude (in addition to defaults).")
    ap.add_argument("--exclude-globs", dest="exclude_globs", default="",
                    help="Comma-separated list of glob patterns to exclude (e.g. *.log,*.tmp,.env, .env.*).")
    ap.add_argument("--max-bytes", dest="max_bytes", type=int, default=MAX_FILE_BYTES_DEFAULT,
                    help=f"Skip files larger than this many bytes (default: {MAX_FILE_BYTES_DEFAULT}).")
    ap.add_argument("--follow-symlinks", action="store_true", help="Follow symlinks while walking the tree.")
    args = ap.parse_args(argv)

    root = Path(args.root).expanduser()
    out_path = Path(args.out).expanduser()

    if not root.exists():
        print(f"Root path not found: {root}", file=sys.stderr)
        return 1

    include_exts = parse_list_arg(args.include_exts, INCLUDE_EXTS)

    exclude_dirs = set(EXCLUDE_DIRS)
    if args.exclude_dirs:
        exclude_dirs |= {d.strip() for d in args.exclude_dirs.split(",") if d.strip()}

    exclude_files = set(EXCLUDE_FILES)
    if args.exclude_files:
        exclude_files |= {f.strip() for f in args.exclude_files.split(",") if f.strip()}

    exclude_globs = list(EXCLUDE_GLOBS)
    if args.exclude_globs:
        exclude_globs += [g.strip() for g in args.exclude_globs.split(",") if g.strip()]

    files = sorted(
        walk_files(root, exclude_dirs, include_exts, args.max_bytes, args.follow_symlinks, exclude_files, exclude_globs)
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as out:
        out.write(f"# Flattened code dump for: {root.resolve()}\\n")
        out.write(f"# Files included: {len(files)}\\n\\n")
        for p in files:
            try:
                rel = p.relative_to(root)
            except Exception:
                rel = p
            out.write("\\n" + "=" * 80 + "\\n")
            out.write(f"BEGIN FILE: {rel}\\n")
            out.write("=" * 80 + "\\n\\n")
            out.write(read_text_file(p))
            out.write("\\n" + "=" * 80 + "\\n")
            out.write(f"END FILE: {rel}\\n")
            out.write("=" * 80 + "\\n")

    print(f"Wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
