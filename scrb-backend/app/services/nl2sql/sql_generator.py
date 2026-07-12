"""
app/services/nl2sql/sql_generator.py — NL → SQL generation via Gemini.

Converts natural-language questions into PostgreSQL SQL statements using
the configured LLM provider, schema context, and few-shot examples.

Does NOT validate or execute the generated SQL — those are separate concerns.

Usage:
    from app.services.nl2sql.sql_generator import SQLGenerator

    gen = SQLGenerator()
    sql = await gen.generate("Show theft cases in Bengaluru")
"""

from __future__ import annotations

import logging
import re

from app.services.llm.base import LLMError, LLMResponse
from app.services.llm.llm_factory import LLMFactory
from app.services.llm.prompt_builder import PromptBuilder
from app.services.nl2sql.examples import format_examples_for_prompt
from app.services.nl2sql.schema_context import get_schema_context

logger = logging.getLogger(__name__)

# Sentinel returned by Gemini when it cannot produce SQL.
_CANNOT_GENERATE = "CANNOT_GENERATE_SQL"


class SQLGenerator:
    """
    Converts natural-language into PostgreSQL SQL.

    Pipeline:
        1. Build a prompt (schema + examples + question)
        2. Call LLM provider
        3. Clean the raw output (strip markdown / fences)
        4. Return plain SQL text

    Does NOT validate or execute the SQL.
    """

    def __init__(self, *, provider_name: str | None = None) -> None:
        self._provider = LLMFactory.create(provider_name)
        schema = get_schema_context()
        examples = format_examples_for_prompt()
        self._prompt_builder = PromptBuilder(
            schema_context=schema,
            examples=examples,
        )
        logger.info("SQLGenerator initialised")

    async def generate(self, question: str) -> str:
        """
        Generate a PostgreSQL SQL query from a natural-language question.

        Parameters
        ----------
        question : str
            The user's question in natural language.

        Returns
        -------
        str
            A raw SQL string (no markdown, no fences, no explanation).

        Raises
        ------
        RuntimeError
            If the LLM fails or responds with CANNOT_GENERATE_SQL.
        """
        if not question or not question.strip():
            raise ValueError("Question must not be empty.")

        system_prompt, user_prompt = self._prompt_builder.build_nl2sql_prompt(
            question.strip()
        )

        result = await self._provider.generate(
            user_prompt,
            system=system_prompt,
            temperature=0.0,  # deterministic SQL generation
        )

        if isinstance(result, LLMError):
            logger.error("SQL generation LLM error: %s", result.error)
            raise RuntimeError(f"LLM error: {result.error}")

        raw_sql = result.content.strip()

        if not raw_sql:
            raise RuntimeError("LLM returned empty response.")

        if _CANNOT_GENERATE in raw_sql:
            raise RuntimeError(
                "The AI could not generate SQL for this question. "
                "Try rephrasing or simplifying your question."
            )

        sql = self._clean_sql(raw_sql)

        if not sql:
            raise RuntimeError("LLM returned no usable SQL after cleaning.")

        logger.info(
            "SQL generated  tokens_in=%d  tokens_out=%d  latency=%.0fms",
            result.input_tokens, result.output_tokens, result.latency_ms,
        )
        logger.debug("Generated SQL: %s", sql)
        return sql

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _clean_sql(raw: str) -> str:
        """
        Strip markdown fences, backticks, comments, and leading/trailing
        whitespace that Gemini might include despite the prompt rules.
        """
        sql = raw.strip()

        # Remove ```sql ... ``` or ``` ... ``` fences.
        sql = re.sub(r"^```(?:sql)?\s*\n?", "", sql, flags=re.IGNORECASE)
        sql = re.sub(r"\n?```\s*$", "", sql)

        # Remove leading/trailing backticks.
        sql = sql.strip("`").strip()

        # Remove any trailing semicolons (the executor handles statement boundaries).
        sql = sql.rstrip(";").strip()

        return sql
