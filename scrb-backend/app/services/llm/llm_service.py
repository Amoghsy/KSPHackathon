"""
app/services/llm/llm_service.py — Reusable Google Gemini integration.

Provides generate(), chat(), and system_prompt() methods with robust error
handling (retry, timeout, network failures, invalid API key).

Usage:
    from app.services.llm.llm_service import LLMService

    llm = LLMService()
    result = await llm.generate("Summarise this crime report …")
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Structured response objects
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class LLMResponse:
    """Structured wrapper around a successful Gemini response."""

    content: str
    """The main text content returned by the model."""

    model: str
    """Model identifier that produced this response."""

    input_tokens: int
    """Number of tokens in the prompt."""

    output_tokens: int
    """Number of tokens in the completion."""

    stop_reason: str | None = None
    """Why the model stopped generating (e.g. 'STOP', 'MAX_TOKENS')."""

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
# Service
# ---------------------------------------------------------------------------

# Defaults — can be overridden per-call or via env vars.
_DEFAULT_MODEL = "gemini-2.5-flash"
_DEFAULT_TEMPERATURE = 0.0
_DEFAULT_MAX_TOKENS = 4096
_DEFAULT_TIMEOUT = 60.0  # seconds
_MAX_RETRIES = 3
_RETRY_BACKOFF = 1.0  # base seconds for exponential backoff


class LLMService:
    """
    Thin, reusable wrapper around the Google Gemini Python SDK.

    Configuration priority (highest → lowest):
        1. Per-call keyword arguments
        2. Constructor arguments
        3. Environment variables (GEMINI_API_KEY, LLM_MODEL, …)
        4. Hardcoded defaults
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
    ) -> None:
        resolved_key = api_key or os.getenv("GEMINI_API_KEY")
        if not resolved_key:
            raise ValueError(
                "GEMINI_API_KEY is required. "
                "Set it in .env or pass api_key= to LLMService()."
            )

        self._model = model or os.getenv("LLM_MODEL", _DEFAULT_MODEL)
        self._temperature = (
            temperature
            if temperature is not None
            else float(os.getenv("LLM_TEMPERATURE", str(_DEFAULT_TEMPERATURE)))
        )
        self._max_tokens = (
            max_tokens
            if max_tokens is not None
            else int(os.getenv("LLM_MAX_TOKENS", str(_DEFAULT_MAX_TOKENS)))
        )
        self._timeout = timeout or float(
            os.getenv("LLM_TIMEOUT", str(_DEFAULT_TIMEOUT))
        )
        self._max_retries = max_retries if max_retries is not None else _MAX_RETRIES

        # Initialise the Gemini client with the API key.
        self._client = genai.Client(api_key=resolved_key)

        logger.info(
            "LLMService initialised  model=%s  temperature=%s  max_tokens=%s  timeout=%ss",
            self._model,
            self._temperature,
            self._max_tokens,
            self._timeout,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse | LLMError:
        """
        Single-turn generation.

        Parameters
        ----------
        prompt : str
            The user message / instruction.
        system : str, optional
            System instruction to prepend.
        model, temperature, max_tokens
            Per-call overrides of the instance defaults.

        Returns
        -------
        LLMResponse on success, LLMError on failure.
        """
        contents = [prompt]
        return await self._call(
            contents,
            system=system,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        system: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse | LLMError:
        """
        Multi-turn chat completion.

        Parameters
        ----------
        messages : list[dict]
            Conversation history, each dict has 'role' and 'content'.
            Roles: 'user', 'model'.
        system : str, optional
            System instruction to prepend.
        model, temperature, max_tokens
            Per-call overrides of the instance defaults.

        Returns
        -------
        LLMResponse on success, LLMError on failure.
        """
        # Convert messages to Gemini Content format.
        contents = []
        for msg in messages:
            role = msg.get("role", "user")
            # Gemini uses "model" instead of "assistant".
            if role == "assistant":
                role = "model"
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=msg["content"])],
                )
            )

        return await self._call(
            contents,
            system=system,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def system_prompt(self, context: str) -> str:
        """
        Build a reusable system prompt string.

        This is a convenience helper — callers can compose domain-specific
        system prompts and pass them to generate() or chat() via the
        ``system`` kwarg.

        Parameters
        ----------
        context : str
            Domain-specific context to embed in the system prompt.

        Returns
        -------
        str  Formatted system prompt.
        """
        return (
            "You are an expert AI assistant for the SCRB Intelligence Platform, "
            "a crime analytics system used by Karnataka State Police.\n\n"
            f"{context}\n\n"
            "Always respond with accurate, structured information. "
            "If you are uncertain, say so rather than guessing."
        )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    async def _call(
        self,
        contents: list,
        *,
        system: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse | LLMError:
        """Execute the actual Gemini API call with error handling and retries."""
        effective_model = model or self._model
        effective_temperature = (
            temperature if temperature is not None else self._temperature
        )
        effective_max_tokens = (
            max_tokens if max_tokens is not None else self._max_tokens
        )

        # Build generation config.
        gen_config = types.GenerateContentConfig(
            temperature=effective_temperature,
            max_output_tokens=effective_max_tokens,
        )
        if system:
            gen_config.system_instruction = system

        last_error: LLMError | None = None

        for attempt in range(1, self._max_retries + 1):
            start = time.perf_counter()
            try:
                # Run the synchronous SDK call in a thread to keep async.
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        self._client.models.generate_content,
                        model=effective_model,
                        contents=contents,
                        config=gen_config,
                    ),
                    timeout=self._timeout,
                )
                elapsed_ms = (time.perf_counter() - start) * 1000

                # Extract text from response.
                content_text = ""
                if response.candidates:
                    candidate = response.candidates[0]
                    if candidate.content and candidate.content.parts:
                        for part in candidate.content.parts:
                            if part.text:
                                content_text += part.text

                # Extract token usage.
                input_tokens = 0
                output_tokens = 0
                if response.usage_metadata:
                    input_tokens = response.usage_metadata.prompt_token_count or 0
                    output_tokens = response.usage_metadata.candidates_token_count or 0

                # Extract stop reason.
                stop_reason = None
                if response.candidates:
                    finish = response.candidates[0].finish_reason
                    if finish:
                        stop_reason = str(finish)

                result = LLMResponse(
                    content=content_text,
                    model=effective_model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    stop_reason=stop_reason,
                    latency_ms=round(elapsed_ms, 2),
                    raw={
                        "model": effective_model,
                        "candidates_count": len(response.candidates) if response.candidates else 0,
                    },
                )

                logger.info(
                    "LLM OK  model=%s  in=%d  out=%d  stop=%s  %.0fms",
                    result.model,
                    result.input_tokens,
                    result.output_tokens,
                    result.stop_reason,
                    result.latency_ms,
                )
                return result

            except asyncio.TimeoutError:
                logger.warning(
                    "LLM request timed out after %.1fs (attempt %d/%d)",
                    self._timeout,
                    attempt,
                    self._max_retries,
                )
                last_error = LLMError(
                    error=f"Request timed out after {self._timeout}s.",
                    error_type="timeout",
                    retryable=True,
                )

            except Exception as exc:  # noqa: BLE001
                elapsed_ms = (time.perf_counter() - start) * 1000
                last_error = self._classify_error(exc)
                logger.warning(
                    "LLM error (attempt %d/%d, %.0fms): [%s] %s",
                    attempt,
                    self._max_retries,
                    elapsed_ms,
                    last_error.error_type,
                    last_error.error,
                )

                # Don't retry non-retryable errors.
                if not last_error.retryable:
                    return last_error

            # Exponential backoff before retry.
            if attempt < self._max_retries:
                backoff = _RETRY_BACKOFF * (2 ** (attempt - 1))
                logger.info("Retrying in %.1fs …", backoff)
                await asyncio.sleep(backoff)

        # All retries exhausted.
        return last_error or LLMError(
            error="All retry attempts exhausted.",
            error_type="exhausted",
            retryable=False,
        )

    @staticmethod
    def _classify_error(exc: Exception) -> LLMError:
        """Map an exception to a structured LLMError with retryable flag."""
        msg = str(exc).lower()

        # Authentication / API key errors.
        if "api key" in msg or "401" in msg or "permission" in msg or "forbidden" in msg:
            return LLMError(
                error="Invalid or missing GEMINI_API_KEY.",
                error_type="authentication",
                retryable=False,
            )

        # Quota / rate limit errors.
        if "429" in msg or "quota" in msg or "rate" in msg or "resource_exhausted" in msg:
            return LLMError(
                error="Gemini API rate limit or quota exceeded. Please retry later.",
                error_type="rate_limit",
                retryable=True,
            )

        # Server errors (5xx).
        if "500" in msg or "503" in msg or "502" in msg or "504" in msg or "internal" in msg:
            return LLMError(
                error=f"Gemini API server error: {exc}",
                error_type="server_error",
                retryable=True,
            )

        # Network / connection errors.
        if any(
            kw in msg
            for kw in ("connection", "network", "dns", "resolve", "refused", "reset")
        ):
            return LLMError(
                error="Network error connecting to Gemini API.",
                error_type="connection",
                retryable=True,
            )

        # Catch-all.
        logger.exception("LLM unexpected error: %s", exc)
        return LLMError(
            error=f"Unexpected error: {exc}",
            error_type="unknown",
            retryable=False,
        )
