# /core/types.py
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Literal, Optional, Tuple, TypedDict

Role = Literal["system", "user", "assistant"]

# Basic chat message
@dataclass(slots=True)
class ChatMessage:
    role: Role
    content: str

# Pair-based history (simple UI / anon_bot style)
ChatTurn = List[str]                # [user, bot]
ChatHistory = List[ChatTurn]        # [[u,b], [u,b], ...]

# Plain chat API payloads (/plain-chat)
@dataclass(slots=True)
class PlainChatRequest:
    text: str

@dataclass(slots=True)
class PlainChatResponse:
    reply: str
    meta: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

# Optional error shape for consistent JSON error responses
class ErrorPayload(TypedDict, total=False):
    error: str
    detail: str
