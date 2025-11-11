"""Perception layer modules for risk signal extraction."""

from importlib import import_module


def legacy_module(name: str):
    """Helper to access legacy implementations under `src` during migration."""

    return import_module(f"src.{name}")


__all__ = ["legacy_module"]

