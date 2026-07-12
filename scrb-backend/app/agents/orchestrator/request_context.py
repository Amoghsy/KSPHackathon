"""
app/agents/orchestrator/request_context.py — Request context container for tracking requests.
"""

from __future__ import annotations

import time
from typing import Optional

from pydantic import BaseModel, Field


class RequestContext(BaseModel):
    """
    Context model for storing per-request attributes.
    Helps carry request_id, user_id, conversation_id, and resolved question.
    """

    request_id: str = Field(..., description="Unique correlation ID for tracing.")
    conversation_id: Optional[str] = Field(
        None, description="Redis conversation session ID."
    )
    user_id: Optional[int] = Field(None, description="Authenticated user ID.")
    question: str = Field(..., description="Original user natural language question.")
    resolved_question: Optional[str] = Field(
        None, description="Context-injected resolved query."
    )
    timestamp: float = Field(
        default_factory=time.time, description="Epoch timestamp of request creation."
    )
