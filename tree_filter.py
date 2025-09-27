#!/usr/bin/env python3
r"""
Write a tree view of a folder to a file.

Usage:
  python tree.py             # current folder -> tree.txt
  python tree.py C:\proj -o proj-tree.txt
  python tree.py . --max-depth 3
"""

import os, argparse, fnmatch

EXCLUDE_DIRS = {
    ".git", ".hg", ".svn", "__pycache__", "node_modules",
    ".venv", "venv", "env", "dist", "build",
    "artifacts", "logs", ".idea", ".vscode", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", ".tox", ".nox", ".hypothesis",
    ".cache", ".gradle", ".parcel-cache", ".next", ".turbo",
    ".pnpm-store", ".yarn", ".yarn/cache", ".nuxt", ".svelte-kit",
}

EXCLUDE_FILES = {".DS_Store", "Thumbs.db", ".coverage", ".python-version"}

EXCLUDE_GLOBS = [
    "*.log", "*.tmp", "*.temp", "*.bak", "*.swp", "*.swo",
    "*.pyc", "*.pyo", "*.pyd", "*.class",
    "*.lock", "*.pid",
    "*.egg-info", "*.eggs",
    "*.sqlite", "*.sqlite3", "*.db", "*.pkl",
    ".env", ".env.*",
]


def _entries_sorted(path, exclude_dirs=None, exclude_files=None, exclude_globs=None):
    exclude_dirs = set(EXCLUDE_DIRS if exclude_dirs is None else exclude_dirs)
    exclude_files = set(EXCLUDE_FILES if exclude_files is None else exclude_files)
    exclude_globs = list(EXCLUDE_GLOBS if exclude_globs is None else exclude_globs)
    try:
        with os.scandir(path) as it:
            items = []
            for e in it:
                name = e.name
                if name in exclude_files:
                    continue
                if any(fnmatch.fnmatch(name, pat) for pat in exclude_globs):
                    continue
                if e.is_dir(follow_symlinks=False) and name in exclude_dirs:
                    continue
                items.append(e)
    except PermissionError:
        return []
    items.sort(key=lambda e: (not e.is_dir(follow_symlinks=False), e.name.lower()))
    return items


def _draw(root, out, max_depth=None, follow_symlinks=False, prefix="", exclude_dirs=None, exclude_files=None, exclude_globs=None):
    if max_depth is not None and max_depth < 0:
        return
    items = _entries_sorted(root, exclude_dirs=exclude_dirs, exclude_files=exclude_files, exclude_globs=exclude_globs)
    for i, e in enumerate(items):
        last = (i == len(items) - 1)
        connector = "└── " if last else "├── "
        line = f"{prefix}{connector}{e.name}"
        if e.is_symlink():
            try:
                line += f" -> {os.readlink(e.path)}"
            except OSError:
                pass
        print(line, file=out)
        if e.is_dir(follow_symlinks=follow_symlinks):
            new_prefix = prefix + ("    " if last else "│   ")
            next_depth = None if max_depth is None else max_depth - 1
            if next_depth is None or next_depth >= 0:
                _draw(e.path, out, next_depth, follow_symlinks, new_prefix, exclude_dirs, exclude_files, exclude_globs)


def main():
    ap = argparse.ArgumentParser(description="Print a folder tree to a file.")
    ap.add_argument("path", nargs="?", default=".", help="Root folder (default: .)")
    ap.add_argument("-o", "--out", default="tree.txt", help="Output file (default: tree.txt)")
    ap.add_argument("--max-depth", type=int, help="Limit recursion depth")
    ap.add_argument("--follow-symlinks", action="store_true", help="Recurse into symlinked dirs")
    ap.add_argument("--exclude-dirs", default="", help="Comma-separated dir names to exclude (in addition to defaults).")
    ap.add_argument("--exclude-files", default="", help="Comma-separated file names to exclude (in addition to defaults).")
    ap.add_argument("--exclude-globs", default="", help="Comma-separated glob patterns to exclude (e.g. *.log,*.tmp,.env,.env.*).")
    args = ap.parse_args()

    # Merge defaults with CLI-specified excludes
    exclude_dirs = set(EXCLUDE_DIRS)
    if args.exclude_dirs:
        exclude_dirs |= {d.strip() for d in args.exclude_dirs.split(",") if d.strip()}
    exclude_files = set(EXCLUDE_FILES)
    if args.exclude_files:
        exclude_files |= {f.strip() for f in args.exclude_files.split(",") if f.strip()}
    exclude_globs = list(EXCLUDE_GLOBS)
    if args.exclude_globs:
        exclude_globs += [g.strip() for g in args.exclude_globs.split(",") if g.strip()]

    root = os.path.abspath(args.path)
    with open(args.out, "w", encoding="utf-8") as f:
        print(root, file=f)
        _draw(root, f, args.max_depth, args.follow_symlinks, "", exclude_dirs, exclude_files, exclude_globs)

    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
