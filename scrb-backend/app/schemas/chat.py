"""
app/schemas/chat.py — Request / response models for the chat endpoint.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Request
# ---------------------------------------------------------------------------


class ChatRequest(BaseModel):
    """POST /api/v1/chat request body."""

    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Natural-language question to ask the AI.",
        examples=["Show theft cases in Bengaluru during 2025"],
    )
    conversation_id: Optional[str] = Field(
        default=None,
        description="Optional conversation ID to maintain session context.",
    )


# ---------------------------------------------------------------------------
# Response — success
# ---------------------------------------------------------------------------


class ChatResponse(BaseModel):
    """Successful chat response payload."""

    status: str = Field(default="success", description="Response status.")
    request_id: str = Field(..., description="Unique correlation ID.")
    agent: str = Field(default="query", description="Agent that handled the request.")
    question: str = Field(..., description="Original user question.")
    generated_sql: str = Field(..., description="AI-generated SQL query.")
    row_count: int = Field(..., ge=0, description="Number of result rows.")
    execution_time_ms: float = Field(
        ..., ge=0, description="Query execution time (ms)."
    )
    summary: str = Field(..., description="Natural-language summary of results.")
    rows: list[dict[str, Any]] = Field(default_factory=list, description="Result rows.")
    columns: list[str] = Field(default_factory=list, description="Column names.")
    confidence: float = Field(
        ..., ge=0, le=1, description="Heuristic confidence score."
    )


# ---------------------------------------------------------------------------
# Response — error
# ---------------------------------------------------------------------------


class ChatErrorResponse(BaseModel):
    """Error chat response payload."""

    status: str = Field(default="error", description="Response status.")
    request_id: str = Field(..., description="Unique correlation ID.")
    error: str = Field(..., description="Human-readable error message.")
    error_type: str = Field(..., description="Machine-readable error category.")
    generated_sql: str | None = Field(
        default=None, description="SQL if generated before failure."
    )
    retryable: bool = Field(
        default=False, description="Whether the request can be retried."
    )
