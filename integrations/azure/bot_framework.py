# integrations/azure/bot_framework.py
"""
Azure Bot Framework integration (stub).

This module is a placeholder for connecting the chatbot
to Microsoft Azure Bot Framework. It is optional —
the anonymous bot does not depend on this code.

If you want to enable Azure:
    1. Install `botbuilder` SDK (pip install botbuilder-core aiohttp).
    2. Fill in the adapter setup and message handling below.
"""

from typing import Any, Dict


class AzureBotFrameworkNotConfigured(Exception):
    """Raised when Azure Bot Framework is called but not set up."""


def init_adapter(config: Dict[str, Any] | None = None):
    """
    Placeholder for BotFrameworkAdapter initialization.
    Returns a dummy object unless replaced with actual Azure code.
    """
    raise AzureBotFrameworkNotConfigured(
        "Azure Bot Framework integration is not configured. "
        "Use anon_bot for local testing."
    )


def handle_activity(activity: Dict[str, Any]) -> Dict[str, Any]:
    """
    Placeholder for handling an incoming Bot Framework activity.
    Echoes back a dummy response if called directly.
    """
    if not activity:
        return {"type": "message", "text": "(no activity received)"}
    return {"type": "message", "text": f"Echo: {activity.get('text', '')}"}
