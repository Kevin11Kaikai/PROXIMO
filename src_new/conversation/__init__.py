"""Conversation execution layer for risk-aware agents."""

from importlib import import_module


def legacy_engine():
    """Return the legacy ConversationEngine class for migration support."""

    module = import_module("src.conversation.engine")
    return module.ConversationEngine


__all__ = ["legacy_engine"]

