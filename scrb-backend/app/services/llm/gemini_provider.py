"""
app/services/llm/gemini_provider.py — Google Gemini LLM provider.

Implements BaseLLMProvider using the official google-genai SDK.
Handles retry, timeout, and structured error classification.

Usage:
    from app.services.llm.gemini_provider import GeminiProvider

    provider = GeminiProvider()
    result = await provider.generate("Summarise this crime report …")
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Any

from google import genai
from google.genai import types

from app.services.llm.base import BaseLLMProvider, LLMError, LLMResponse

logger = logging.getLogger(__name__)

# Defaults — overridable per-call, per-constructor, or via env.
_DEFAULT_MODEL = "gemini-3.5-flash"
_DEFAULT_TEMPERATURE = 0.0
_DEFAULT_MAX_TOKENS = 4096
_DEFAULT_TIMEOUT = 45.0
_MAX_RETRIES = 2
_RETRY_BACKOFF = 1.0


class GeminiProvider(BaseLLMProvider):
    """
    Concrete LLM provider backed by Google Gemini.

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
                "Set it in .env or pass api_key= to GeminiProvider()."
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

        self._client = genai.Client(api_key=resolved_key)

        logger.info(
            "GeminiProvider initialised  model=%s  temp=%s  max_tokens=%s  timeout=%ss",
            self._model,
            self._temperature,
            self._max_tokens,
            self._timeout,
        )

    # ------------------------------------------------------------------
    # BaseLLMProvider interface
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
        """Single-turn generation."""
        return await self._call(
            contents=[prompt],
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
        """Multi-turn chat completion."""
        contents = []
        for msg in messages:
            role = msg.get("role", "user")
            if role == "assistant":
                role = "model"
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=msg["content"])],
                )
            )
        return await self._call(
            contents=contents,
            system=system,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    async def health_check(self) -> bool:
        """Quick connectivity test — generate a trivial prompt."""
        try:
            result = await self.generate("Reply with OK.", max_tokens=8)
            return isinstance(result, LLMResponse)
        except Exception:  # noqa: BLE001
            return False

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
        effective_model = model or self._model
        effective_temp = temperature if temperature is not None else self._temperature
        effective_max = max_tokens if max_tokens is not None else self._max_tokens

        gen_config = types.GenerateContentConfig(
            temperature=effective_temp,
            max_output_tokens=effective_max,
        )
        if system:
            gen_config.system_instruction = system

        last_error: LLMError | None = None

        for attempt in range(1, self._max_retries + 1):
            start = time.perf_counter()
            try:
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
                return self._parse_response(response, effective_model, elapsed_ms)

            except asyncio.TimeoutError:
                logger.warning(
                    "Gemini timeout after %.1fs (attempt %d/%d)",
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
                last_error = self._classify_error(exc)
                logger.warning(
                    "Gemini error (attempt %d/%d): [%s] %s",
                    attempt,
                    self._max_retries,
                    last_error.error_type,
                    last_error.error,
                )
                if not last_error.retryable:
                    return last_error

            if attempt < self._max_retries:
                backoff = _RETRY_BACKOFF * (2 ** (attempt - 1))
                await asyncio.sleep(backoff)

        return last_error or LLMError(
            error="All retry attempts exhausted.",
            error_type="exhausted",
            retryable=False,
        )

    @staticmethod
    def _parse_response(
        response: Any,
        model: str,
        elapsed_ms: float,
    ) -> LLMResponse:
        content_text = ""
        if response.candidates:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                for part in candidate.content.parts:
                    if part.text:
                        content_text += part.text

        input_tokens = 0
        output_tokens = 0
        if response.usage_metadata:
            input_tokens = response.usage_metadata.prompt_token_count or 0
            output_tokens = response.usage_metadata.candidates_token_count or 0

        stop_reason = None
        if response.candidates:
            finish = response.candidates[0].finish_reason
            if finish:
                stop_reason = str(finish)

        result = LLMResponse(
            content=content_text,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            stop_reason=stop_reason,
            latency_ms=round(elapsed_ms, 2),
            raw={
                "model": model,
                "candidates_count": (
                    len(response.candidates) if response.candidates else 0
                ),
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

    @staticmethod
    def _classify_error(exc: Exception) -> LLMError:
        msg = str(exc).lower()

        if (
            "api key" in msg
            or "401" in msg
            or "permission" in msg
            or "forbidden" in msg
        ):
            return LLMError(
                error="Invalid or missing GEMINI_API_KEY.",
                error_type="authentication",
                retryable=False,
            )
        if (
            "429" in msg
            or "quota" in msg
            or "rate" in msg
            or "resource_exhausted" in msg
        ):
            return LLMError(
                error="Gemini API rate limit or quota exceeded.",
                error_type="rate_limit",
                retryable=True,
            )
        if any(c in msg for c in ("500", "503", "502", "504", "internal")):
            return LLMError(
                error=f"Gemini API server error: {exc}",
                error_type="server_error",
                retryable=True,
            )
        if any(
            kw in msg for kw in ("connection", "network", "dns", "refused", "reset")
        ):
            return LLMError(
                error="Network error connecting to Gemini API.",
                error_type="connection",
                retryable=True,
            )
        logger.exception("Gemini unexpected error: %s", exc)
        return LLMError(
            error=f"Unexpected error: {exc}",
            error_type="unknown",
            retryable=False,
        )
