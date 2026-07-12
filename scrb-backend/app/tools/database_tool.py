"""
app/tools/database_tool.py — Read-only PostgreSQL interface for AI agents.

Executes validated SELECT queries and returns structured JSON results.
Rejects any write/DDL operations (INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE).

Usage:
    from app.tools.database_tool import DatabaseTool

    tool = DatabaseTool()
    result = await tool.execute("SELECT * FROM case_master LIMIT 10", db_session)
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Structured response objects
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class QueryResult:
    """Successful query execution result."""

    success: bool = True
    rows: list[dict[str, Any]] = field(default_factory=list)
    columns: list[str] = field(default_factory=list)
    row_count: int = 0
    execution_time_ms: float = 0.0


@dataclass(frozen=True, slots=True)
class QueryError:
    """Failed query execution result."""

    success: bool = False
    error: str = ""
    error_type: str = ""


# ---------------------------------------------------------------------------
# Blocked SQL patterns
# ---------------------------------------------------------------------------

_BLOCKED_KEYWORDS: set[str] = {
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "TRUNCATE",
}

# Match blocked keywords that appear as standalone SQL tokens
# (word boundary prevents false positives like column names containing these).
_BLOCKED_PATTERN = re.compile(
    r"\b(" + "|".join(_BLOCKED_KEYWORDS) + r")\b",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class DatabaseTool:
    """
    Read-only database tool for AI agents.

    - Only SELECT queries are permitted.
    - Write / DDL operations are rejected before touching the DB.
    - Results are returned as structured dataclasses, never raw exceptions.
    """

    @staticmethod
    def _strip_comments(sql: str) -> str:
        """Remove SQL comments so they cannot hide blocked keywords."""
        # Single-line comments: -- …
        sql = re.sub(r"--[^\n]*", "", sql)
        # Block comments: /* … */
        sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
        return sql

    @staticmethod
    def _validate_query(sql: str) -> str | None:
        """
        Return ``None`` if the query is safe, or an error message if not.
        """
        if not sql or not sql.strip():
            return "Empty query."

        cleaned = DatabaseTool._strip_comments(sql)

        match = _BLOCKED_PATTERN.search(cleaned)
        if match:
            keyword = match.group(1).upper()
            return f"Blocked operation: {keyword} queries are not allowed."

        # After stripping comments, first meaningful keyword must be SELECT or WITH.
        first_token = cleaned.strip().split()[0].upper()
        if first_token not in {"SELECT", "WITH"}:
            return (
                f"Only SELECT / WITH (CTE) queries are allowed. "
                f"Got leading keyword: {first_token}"
            )

        return None  # valid

    async def execute(
        self,
        sql: str,
        session: AsyncSession,
        *,
        params: dict[str, Any] | None = None,
    ) -> QueryResult | QueryError:
        """
        Execute a read-only SQL query.

        Parameters
        ----------
        sql : str
            The SQL SELECT statement.
        session : AsyncSession
            An active SQLAlchemy async session (injected via FastAPI).
        params : dict, optional
            Bind parameters for the query.

        Returns
        -------
        QueryResult on success, QueryError on failure.
        """
        # ---- Pre-flight validation ----
        validation_error = self._validate_query(sql)
        if validation_error:
            logger.warning("Query rejected: %s — SQL: %.200s", validation_error, sql)
            return QueryError(error=validation_error, error_type="validation")

        # ---- Execute ----
        start = time.perf_counter()
        try:
            result = await session.execute(text(sql), params or {})
            elapsed_ms = (time.perf_counter() - start) * 1000

            rows_raw = result.fetchall()
            columns = list(result.keys())

            rows = [dict(zip(columns, row)) for row in rows_raw]

            query_result = QueryResult(
                rows=rows,
                columns=columns,
                row_count=len(rows),
                execution_time_ms=round(elapsed_ms, 2),
            )

            logger.info(
                "Query OK  rows=%d  cols=%d  %.1fms  SQL=%.120s",
                query_result.row_count,
                len(columns),
                query_result.execution_time_ms,
                sql.strip(),
            )
            return query_result

        except Exception as exc:  # noqa: BLE001
            elapsed_ms = (time.perf_counter() - start) * 1000
            # Sanitise the exception — never expose raw DB internals.
            safe_message = self._sanitise_error(exc)
            logger.error(
                "Query FAILED after %.1fms: %s — SQL=%.200s",
                elapsed_ms, safe_message, sql,
            )
            return QueryError(error=safe_message, error_type="execution")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _sanitise_error(exc: Exception) -> str:
        """
        Return a user-safe error message without leaking credentials
        or internal stack details.
        """
        msg = str(exc)

        # Strip connection strings / passwords that might appear.
        msg = re.sub(r"(postgresql|postgres|psycopg)\S*", "[redacted]", msg, flags=re.IGNORECASE)

        # Trim to a reasonable length.
        if len(msg) > 500:
            msg = msg[:500] + "…"

        return f"Query execution error: {msg}"
