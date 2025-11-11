"""Adaptive layer for memory, feedback, and personalization."""

from importlib import import_module


def history_repo():
    """Return the legacy AssessmentRepo for compatibility."""

    module = import_module("src.storage.repo")
    return module.AssessmentRepo


__all__ = ["history_repo"]

