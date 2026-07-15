"""
app/agents/query_agent/response_formatter.py — Format Query Agent responses.

Converts internal pipeline results into a standardised JSON-serialisable dict.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


import re


def extract_tables(sql: str) -> list[str]:
    """Extract table names from SQL FROM and JOIN clauses."""
    matches = re.findall(r"\b(?:from|join)\s+([a-zA-Z_0-9]+)", sql, re.IGNORECASE)
    return list(set(matches))


def format_success(
    *,
    question: str,
    generated_sql: str,
    rows: list[dict[str, Any]],
    columns: list[str],
    row_count: int,
    execution_time_ms: float,
    summary: str,
    confidence: float,
) -> dict[str, Any]:
    """
    Build the standard success response payload.
    """
    tables = extract_tables(generated_sql)
    sources = f"PostgreSQL: {', '.join(tables)}" if tables else "PostgreSQL Database"
    
    # Calculate confidence score (0-100)
    conf_pct = int(confidence * 100) if confidence <= 1.0 else int(confidence)

    explain_block = {
        "sql": generated_sql,
        "sources": sources,
        "algorithms": "NL-to-SQL Semantic Translation, Relational Database Execution",
        "confidence": conf_pct,
        "execution_time": f"{round(execution_time_ms, 2)}ms",
        "summary": summary
    }

    return {
        "status": "success",
        "question": question,
        "generated_sql": generated_sql,
        "row_count": row_count,
        "execution_time_ms": round(execution_time_ms, 2),
        "summary": summary,
        "rows": rows,
        "columns": columns,
        "confidence": confidence,
        "explain": explain_block
    }



def format_error(
    *,
    question: str,
    error: str,
    error_type: str,
    generated_sql: str | None = None,
    retryable: bool = False,
) -> dict[str, Any]:
    """
    Build the standard error response payload.

    No stack traces. Structured, user-friendly errors.
    """
    return {
        "status": "error",
        "question": question,
        "error": error,
        "error_type": error_type,
        "generated_sql": generated_sql,
        "retryable": retryable,
    }


def compute_confidence(
    *,
    sql_valid: bool,
    rows_returned: int,
    execution_ok: bool,
    summary_ok: bool,
) -> float:
    """
    Compute a heuristic confidence score (0.0 – 1.0).

    Does NOT call the LLM — purely deterministic.

    Scoring:
        +0.30  valid SQL generated
        +0.30  query executed without errors
        +0.20  rows were returned (non-empty result)
        +0.10  more than 0 but ≤ 1000 rows (reasonable result set)
        +0.10  summary generated successfully
    """
    score = 0.0

    if sql_valid:
        score += 0.30

    if execution_ok:
        score += 0.30

    if rows_returned > 0:
        score += 0.20
        if rows_returned <= 1000:
            score += 0.10

    if summary_ok:
        score += 0.10

    return min(score, 1.0)
