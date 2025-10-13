# /logged_in_bot/__init__.py
"""
Logged-in Bot Module

This module provides comprehensive chatbot functionality for authenticated users including:
- Advanced chat handling with memory and context
- Sentiment analysis with Azure integration and local fallback
- PII redaction capabilities
- Intent detection
- RAG (Retrieval-Augmented Generation) support
- Session and profile management

Main entry points:
- handle_logged_in_turn: Process user messages with full functionality
- capabilities: Get system capabilities
- tools: Access to PII redaction, intent detection, etc.
"""

from .tools import (
    handle_logged_in_turn,
    capabilities,
    redact_text,
    intent_of
)

from .handler import handle_turn

from .sentiment_azure import (
    analyze_sentiment,
    SentimentResult,
    sentiment_label,
    sentiment_score
)

__version__ = "1.0.0"
__author__ = "Agentic Chat Bot Team"

__all__ = [
    # Main functionality
    'handle_logged_in_turn',
    'handle_turn',
    'capabilities',
    
    # Text processing tools
    'redact_text',
    'intent_of',
    
    # Sentiment analysis
    'analyze_sentiment',
    'SentimentResult',
    'sentiment_label',
    'sentiment_score'
]