import os
import shutil

# === CONFIGURATION ===
SOURCE_DIR = r"C:\Users\User\Agentic-Chat-bot-"
DEST_DIR = r"C:\Users\User\HF-Active\HF-Active"

# Folders and files you DO want to copy
INCLUDE = [
    "app/",
    "anon_bot/",
    "agenticcore/",
    "backend/",
    "memory/",
    "nlu/",
    "guardrails/",
    "scripts/",
    "space_app.py",
    "README.md",
    "requirements.txt",
]

# Patterns or folder names to IGNORE entirely
EXCLUDE = [
    "__pycache__",
    ".git",
    ".github",
    "venv",
    "node_modules",
    "dist",
    "build",
    ".idea",
    ".vscode",
    ".pytest_cache",
]

# === CORE FUNCTIONALITY ===
def should_copy(path):
    """Return True if path is allowed by INCLUDE and not excluded."""
    for bad in EXCLUDE:
        if bad in path:
            return False
    for good in INCLUDE:
        if path.replace("\\", "/").startswith(os.path.join(SOURCE_DIR, good).replace("\\", "/")):
            return True
    return False

def sync_files(src, dst):
    os.makedirs(dst, exist_ok=True)
    for root, dirs, files in os.walk(src):
        rel_root = os.path.relpath(root, src)
        # Skip excluded dirs
        dirs[:] = [d for d in dirs if all(x not in d for x in EXCLUDE)]
        for file in files:
            src_file = os.path.join(root, file)
            dst_file = os.path.join(dst, rel_root, file)
            # Check include/exclude filters
            full_path = os.path.join(root, file)
            if should_copy(full_path):
                os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                shutil.copy2(src_file, dst_file)
                print(f"✅ Copied: {dst_file}")
            else:
                print(f"⏭️ Skipped: {full_path}")

if __name__ == "__main__":
    sync_files(SOURCE_DIR, DEST_DIR)
    print("\n✅ Sync complete!")
