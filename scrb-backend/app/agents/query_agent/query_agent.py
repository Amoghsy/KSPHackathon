"""
app/agents/query_agent/query_agent.py — The reference Query Agent.

Pipeline:
    User Question → SQL Generator → SQL Validator → Database Tool → Summarizer

The agent NEVER directly accesses SQLAlchemy or PostgreSQL — everything
flows through the composable service layers.

Usage:
    from app.agents.query_agent.query_agent import QueryAgent

    agent = QueryAgent()
    response = await agent.run("Show theft cases in Bengaluru", db_session)
"""

from __future__ import annotations

import logging
import time
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.query_agent.response_formatter import (
    compute_confidence,
    format_error,
    format_success,
)
from app.agents.query_agent.result_summarizer import ResultSummarizer
from app.services.nl2sql.sql_generator import SQLGenerator
from app.services.nl2sql.sql_validator import SQLValidator
from app.tools.database_tool import DatabaseTool, QueryError

logger = logging.getLogger(__name__)


class QueryAgent:
    """
    End-to-end query agent: NL → SQL → Validate → Execute → Summarise.

    This is the reference implementation for all future agents.
    """

    def __init__(self, *, provider_name: str | None = None) -> None:
        self._sql_generator = SQLGenerator(provider_name=provider_name)
        self._sql_validator = SQLValidator(strict_columns=False)
        self._db_tool = DatabaseTool()
        self._summarizer = ResultSummarizer(provider_name=provider_name)
        logger.info("QueryAgent initialised")

    async def run(
        self,
        question: str,
        session: AsyncSession,
    ) -> dict[str, Any]:
        """
        Execute the full query pipeline.

        Parameters
        ----------
        question : str
            Natural-language question from the user.
        session : AsyncSession
            Active database session (injected by the caller).

        Returns
        -------
        dict  Standardised response (see response_formatter).
        """
        start = time.perf_counter()

        # ---- Step 1: Generate SQL ----
        try:
            generated_sql = await self._sql_generator.generate(question)
        except (RuntimeError, ValueError) as exc:
            logger.warning("SQL generation failed: %s", exc)
            return format_error(
                question=question,
                error=str(exc),
                error_type="sql_generation_failed",
                retryable=True,
            )

        # ---- Step 2: Validate SQL ----
        validation = self._sql_validator.validate(generated_sql)
        if not validation.valid:
            logger.warning("SQL validation failed: %s", validation.errors)
            return format_error(
                question=question,
                error=f"Generated SQL failed validation: {'; '.join(validation.errors)}",
                error_type="sql_validation_failed",
                generated_sql=generated_sql,
                retryable=True,
            )

        # ---- Step 3: Execute SQL ----
        try:
            result = await self._db_tool.execute(generated_sql, session)
        except Exception as exc:  # noqa: BLE001
            logger.error("Database execution error: %s", exc)
            return format_error(
                question=question,
                error="Database query execution failed.",
                error_type="sql_execution_failed",
                generated_sql=generated_sql,
                retryable=True,
            )

        if isinstance(result, QueryError):
            logger.warning("Query execution error: %s", result.error)
            return format_error(
                question=question,
                error=result.error,
                error_type="sql_execution_failed",
                generated_sql=generated_sql,
                retryable=True,
            )

        # ---- Step 4: Summarise ----
        summary_ok = True
        try:
            summary = await self._summarizer.summarize(
                question=question,
                sql=generated_sql,
                rows=result.rows,
                row_count=result.row_count,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Summary generation failed: %s", exc)
            summary = f"Query returned {result.row_count} record(s)."
            summary_ok = False

        # ---- Step 5: Compute confidence ----
        confidence = compute_confidence(
            sql_valid=True,
            rows_returned=result.row_count,
            execution_ok=True,
            summary_ok=summary_ok,
        )

        total_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "QueryAgent OK  rows=%d  confidence=%.2f  total=%.0fms",
            result.row_count,
            confidence,
            total_ms,
        )

        return format_success(
            question=question,
            generated_sql=generated_sql,
            rows=result.rows,
            columns=result.columns,
            row_count=result.row_count,
            execution_time_ms=result.execution_time_ms,
            summary=summary,
            confidence=confidence,
        )
