# /core/config.py
from __future__ import annotations
import os
from dataclasses import dataclass, field
from typing import List, Optional


def _as_bool(v: Optional[str], default: bool = False) -> bool:
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "y", "on"}

def _as_int(v: Optional[str], default: int) -> int:
    try:
        return int(v) if v is not None else default
    except ValueError:
        return default

def _as_list(v: Optional[str], default: List[str] | None = None) -> List[str]:
    if not v:
        return list(default or [])
    return [item.strip() for item in v.split(",") if item.strip()]


@dataclass(slots=True)
class Settings:
    # Runtime / environment
    env: str = field(default_factory=lambda: os.getenv("ENV", "dev"))
    debug: bool = field(default_factory=lambda: _as_bool(os.getenv("DEBUG"), False))

    # Host/port
    host: str = field(default_factory=lambda: os.getenv("HOST", "127.0.0.1"))
    port: int = field(default_factory=lambda: _as_int(os.getenv("PORT"), 3978))

    # Logging
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    json_logs: bool = field(default_factory=lambda: _as_bool(os.getenv("JSON_LOGS"), False))

    # CORS
    cors_allow_origins: List[str] = field(
        default_factory=lambda: _as_list(os.getenv("CORS_ALLOW_ORIGINS"), ["*"])
    )
    cors_allow_methods: List[str] = field(
        default_factory=lambda: _as_list(os.getenv("CORS_ALLOW_METHODS"), ["GET", "POST", "OPTIONS"])
    )
    cors_allow_headers: List[str] = field(
        default_factory=lambda: _as_list(os.getenv("CORS_ALLOW_HEADERS"), ["*"])
    )

    # Bot Framework credentials
    microsoft_app_id: Optional[str] = field(default_factory=lambda: os.getenv("MicrosoftAppId"))
    microsoft_app_password: Optional[str] = field(default_factory=lambda: os.getenv("MicrosoftAppPassword"))

    def to_dict(self) -> dict:
        return {
            "env": self.env,
            "debug": self.debug,
            "host": self.host,
            "port": self.port,
            "log_level": self.log_level,
            "json_logs": self.json_logs,
            "cors_allow_origins": self.cors_allow_origins,
            "cors_allow_methods": self.cors_allow_methods,
            "cors_allow_headers": self.cors_allow_headers,
            "microsoft_app_id": bool(self.microsoft_app_id),
            "microsoft_app_password": bool(self.microsoft_app_password),
        }


# singleton-style settings object
settings = Settings()
