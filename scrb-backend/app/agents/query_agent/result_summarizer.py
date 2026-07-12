"""
app/agents/query_agent/result_summarizer.py — Summarise DB results via Gemini.

Converts database rows into concise natural-language summaries.
"""

from __future__ import annotations

import logging
from typing import Any

from app.services.llm.base import LLMError
from app.services.llm.llm_factory import LLMFactory
from app.services.llm.prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)

_NO_RESULTS_MESSAGE = "No matching records were found."


class ResultSummarizer:
    """
    Converts database query results into a human-readable summary via Gemini.
    """

    def __init__(self, *, provider_name: str | None = None) -> None:
        self._provider = LLMFactory.create(provider_name)
        self._prompt_builder = PromptBuilder()

    async def summarize(
        self,
        *,
        question: str,
        sql: str,
        rows: list[dict[str, Any]],
        row_count: int,
    ) -> str:
        """
        Generate a natural-language summary of the query results.

        Returns
        -------
        str  A concise summary. Returns a canned message when no rows.
        """
        if row_count == 0 or not rows:
            return _NO_RESULTS_MESSAGE

        system_prompt, user_prompt = self._prompt_builder.build_summary_prompt(
            question=question,
            sql=sql,
            rows=rows,
            row_count=row_count,
        )

        result = await self._provider.generate(
            user_prompt,
            system=system_prompt,
            temperature=0.3,  # slightly creative for natural language
            max_tokens=1024,
        )

        if isinstance(result, LLMError):
            logger.warning("Summary LLM error: %s", result.error)
            return self._fallback_summary(row_count)

        summary = result.content.strip()
        if not summary:
            return self._fallback_summary(row_count)

        logger.info(
            "Summary generated  tokens_in=%d  tokens_out=%d  latency=%.0fms",
            result.input_tokens,
            result.output_tokens,
            result.latency_ms,
        )
        return summary

    @staticmethod
    def _fallback_summary(row_count: int) -> str:
        return f"Query returned {row_count} record(s). Unable to generate a detailed summary."
