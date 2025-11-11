"""Miscellaneous helpers for the new architecture."""

from __future__ import annotations

from typing import Any


def ensure_async(func):
    """Decorator to ensure synchronous hooks can be awaited later."""

    async def wrapper(*args: Any, **kwargs: Any):
        return func(*args, **kwargs)

    return wrapper


__all__ = ["ensure_async"]

