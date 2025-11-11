"""Safety and ethics layer (Guardrails, policy filters, etc.)."""

from importlib import import_module


def guardrails_service():
    """Return the legacy GuardrailsService for compatibility."""

    module = import_module("src.services.guardrails_service")
    return module.GuardrailsService


__all__ = ["guardrails_service"]

