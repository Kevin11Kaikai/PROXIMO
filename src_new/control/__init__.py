"""Reasoning and control layer for routing and orchestration."""

from importlib import import_module


def legacy_router():
    """Return legacy router module for compatibility."""

    return import_module("src.conversation.router")


__all__ = ["legacy_router"]

