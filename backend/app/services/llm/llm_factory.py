"""
app/services/llm/llm_factory.py — Factory for LLM providers.

Returns the configured LLM provider. Future providers (Claude, OpenRouter,
Ollama) can be registered without modifying existing code.

Usage:
    from app.services.llm.llm_factory import LLMFactory

    provider = LLMFactory.create()          # default: Gemini
    provider = LLMFactory.create("gemini")  # explicit
"""

from __future__ import annotations

import logging
import os
from typing import Callable

from app.services.llm.base import BaseLLMProvider

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Provider registry — maps provider name → factory callable.
# ---------------------------------------------------------------------------
_REGISTRY: dict[str, Callable[..., BaseLLMProvider]] = {}

_DEFAULT_PROVIDER = "gemini"


def register_provider(
    name: str,
    factory: Callable[..., BaseLLMProvider],
) -> None:
    """
    Register an LLM provider factory.

    Parameters
    ----------
    name : str
        Short key, e.g. 'gemini', 'claude', 'ollama'.
    factory : callable
        A callable that returns a BaseLLMProvider instance.
    """
    _REGISTRY[name.lower()] = factory
    logger.debug("LLM provider registered: %s", name)


class LLMFactory:
    """
    Factory that returns the configured LLM provider.

    Resolution order:
        1. Explicit ``provider`` argument
        2. ``LLM_PROVIDER`` environment variable
        3. Default: ``gemini``
    """

    @staticmethod
    def create(provider: str | None = None, **kwargs) -> BaseLLMProvider:
        """
        Create and return an LLM provider instance.

        Parameters
        ----------
        provider : str, optional
            Provider key. Falls back to env var ``LLM_PROVIDER`` then default.
        **kwargs
            Forwarded to the provider constructor.
        """
        name = (provider or os.getenv("LLM_PROVIDER", _DEFAULT_PROVIDER)).lower()

        if name not in _REGISTRY:
            available = ", ".join(sorted(_REGISTRY)) or "(none)"
            raise ValueError(
                f"Unknown LLM provider '{name}'. " f"Registered providers: {available}"
            )

        instance = _REGISTRY[name](**kwargs)
        logger.info("LLM provider created: %s", name)
        return instance

    @staticmethod
    def available_providers() -> list[str]:
        """Return names of all registered providers."""
        return sorted(_REGISTRY)


# ---------------------------------------------------------------------------
# Auto-register built-in providers.
# ---------------------------------------------------------------------------


def _register_builtins() -> None:
    """Register the Gemini provider (always available)."""
    from app.services.llm.gemini_provider import GeminiProvider  # noqa: F811

    register_provider("gemini", GeminiProvider)


_register_builtins()
