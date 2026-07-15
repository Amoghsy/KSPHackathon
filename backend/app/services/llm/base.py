"""
app/services/llm/base.py — Abstract base class for LLM providers.

All LLM providers (Gemini, Claude, OpenRouter, Ollama) must implement
this interface so they are interchangeable via LLMFactory.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Shared structured response objects
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class LLMResponse:
    """Structured wrapper around a successful LLM response."""

    content: str
    """The main text content returned by the model."""

    model: str
    """Model identifier that produced this response."""

    input_tokens: int = 0
    """Number of tokens in the prompt."""

    output_tokens: int = 0
    """Number of tokens in the completion."""

    stop_reason: str | None = None
    """Why the model stopped generating."""

    latency_ms: float = 0.0
    """Wall-clock time for the API call in milliseconds."""

    raw: dict[str, Any] = field(default_factory=dict)
    """Full raw API response metadata for debugging / audit."""


@dataclass(frozen=True, slots=True)
class LLMError:
    """Structured wrapper for any LLM failure."""

    error: str
    """Human-readable error description."""

    error_type: str
    """Programmatic error category (e.g. 'authentication', 'timeout')."""

    retryable: bool = False
    """Whether the caller should retry the request."""


# ---------------------------------------------------------------------------
# Abstract provider
# ---------------------------------------------------------------------------


class BaseLLMProvider(abc.ABC):
    """
    Abstract interface that every LLM provider must implement.

    Methods
    -------
    generate(prompt, *, system, model, temperature, max_tokens)
        Single-turn text generation.
    chat(messages, *, system, model, temperature, max_tokens)
        Multi-turn chat completion.
    health_check()
        Quick connectivity / API-key validation.
    """

    @abc.abstractmethod
    async def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse | LLMError:
        """Single-turn generation."""

    @abc.abstractmethod
    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        system: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse | LLMError:
        """Multi-turn chat completion."""

    @abc.abstractmethod
    async def health_check(self) -> bool:
        """Return True if the provider is reachable and the API key is valid."""
