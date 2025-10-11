# /core/logging.py
from __future__ import annotations
import json
import logging
import sys
from datetime import datetime
from typing import Optional

try:
    # Optional: human-friendly console colors if installed
    import colorama  # type: ignore
    colorama.init()
    _HAS_COLOR = True
except Exception:  # pragma: no cover
    _HAS_COLOR = False

# Very small JSON formatter (avoids extra deps)
class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        payload = {
            "ts": datetime.utcfromtimestamp(record.created).isoformat(timespec="milliseconds") + "Z",
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)

class ConsoleFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        ts = datetime.utcfromtimestamp(record.created).strftime("%H:%M:%S")
        lvl = record.levelname
        name = record.name
        msg = record.getMessage()

        if _HAS_COLOR:
            COLORS = {
                "DEBUG": "\033[37m",
                "INFO": "\033[36m",
                "WARNING": "\033[33m",
                "ERROR": "\033[31m",
                "CRITICAL": "\033[41m",
            }
            RESET = "\033[0m"
            color = COLORS.get(lvl, "")
            return f"{ts} {color}{lvl:<8}{RESET} {name}: {msg}"
        return f"{ts} {lvl:<8} {name}: {msg}"


_initialized = False

def setup_logging(level: str = "INFO", json_logs: bool = False) -> None:
    """
    Initialize root logger once.
    """
    global _initialized
    if _initialized:
        return
    _initialized = True

    root = logging.getLogger()
    root.setLevel(level.upper())

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter() if json_logs else ConsoleFormatter())
    root.handlers[:] = [handler]


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger (call setup_logging() first to configure formatting).
    """
    return logging.getLogger(name or "app")
