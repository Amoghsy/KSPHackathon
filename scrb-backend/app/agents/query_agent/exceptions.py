"""
app/agents/query_agent/exceptions.py — Structured exceptions for the Query Agent.

Every failure mode returns a machine-readable error instead of a stack trace.
"""

from __future__ import annotations


class QueryAgentError(Exception):
    """Base exception for all Query Agent failures."""

    def __init__(self, message: str, error_type: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.error_type = error_type
        self.retryable = retryable


class SQLGenerationError(QueryAgentError):
    """Gemini failed to produce valid SQL."""

    def __init__(self, message: str = "Failed to generate SQL from the question.") -> None:
        super().__init__(message, error_type="sql_generation_failed", retryable=True)


class SQLValidationError(QueryAgentError):
    """Generated SQL failed safety / schema validation."""

    def __init__(self, message: str, errors: list[str] | None = None) -> None:
        super().__init__(message, error_type="sql_validation_failed", retryable=False)
        self.validation_errors = errors or []


class SQLExecutionError(QueryAgentError):
    """SQL execution against the database failed."""

    def __init__(self, message: str = "Query execution failed.") -> None:
        super().__init__(message, error_type="sql_execution_failed", retryable=True)


class SummaryError(QueryAgentError):
    """Gemini failed to summarise query results."""

    def __init__(self, message: str = "Failed to summarise results.") -> None:
        super().__init__(message, error_type="summary_failed", retryable=True)


class DatabaseUnavailableError(QueryAgentError):
    """Database is unreachable."""

    def __init__(self, message: str = "Database is currently unavailable.") -> None:
        super().__init__(message, error_type="database_unavailable", retryable=True)


class LLMUnavailableError(QueryAgentError):
    """Gemini API is unreachable."""

    def __init__(self, message: str = "Gemini API is currently unavailable.") -> None:
        super().__init__(message, error_type="llm_unavailable", retryable=True)
