# /memory/profile.py
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from pathlib import Path
import json, time

PROFILE_DIR = Path("memory/.profiles")
PROFILE_DIR.mkdir(parents=True, exist_ok=True)

@dataclass
class Note:
    key: str
    value: str
    created_at: float
    updated_at: float
    tags: List[str]

@dataclass
class Profile:
    user_id: str
    display_name: Optional[str] = None
    notes: Dict[str, Note] = None

    @classmethod
    def load(cls, user_id: str) -> "Profile":
        p = PROFILE_DIR / f"{user_id}.json"
        if not p.exists():
            return Profile(user_id=user_id, notes={})
        data = json.loads(p.read_text(encoding="utf-8"))
        notes = {k: Note(**v) for k, v in data.get("notes", {}).items()}
        return Profile(user_id=data["user_id"], display_name=data.get("display_name"), notes=notes)

    def save(self) -> None:
        p = PROFILE_DIR / f"{self.user_id}.json"
        data = {
            "user_id": self.user_id,
            "display_name": self.display_name,
            "notes": {k: asdict(v) for k, v in (self.notes or {}).items()},
        }
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    # --- memory operations (explicit user consent) ---
    def remember(self, key: str, value: str, tags: Optional[List[str]] = None) -> None:
        now = time.time()
        note = self.notes.get(key)
        if note:
            note.value, note.updated_at = value, now
            if tags: note.tags = tags
        else:
            self.notes[key] = Note(key=key, value=value, tags=tags or [], created_at=now, updated_at=now)
        self.save()

    def forget(self, key: str) -> bool:
        ok = key in self.notes
        if ok:
            self.notes.pop(key)
            self.save()
        return ok

    def recall(self, key: str) -> Optional[str]:
        n = self.notes.get(key)
        return n.value if n else None

    def list_notes(self) -> List[str]:
        return sorted(self.notes.keys())
    
    def list_notes_dict(self) -> Dict[str, str]:
        return {k: v.value for k, v in (self.notes or {}).items()}
