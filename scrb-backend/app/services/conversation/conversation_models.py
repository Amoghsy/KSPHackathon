"""
app/services/conversation/conversation_models.py — Pydantic models for Conversation State.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ConversationMessage(BaseModel):
    """Represents a single message in the conversation history."""

    role: str = Field(
        ..., description="Role of the message sender, e.g., 'user', 'assistant'"
    )
    content: str = Field(..., description="Text content of the message")
    timestamp: float = Field(
        default_factory=time.time, description="Epoch timestamp of the message"
    )


class ConversationSessionModel(BaseModel):
    """Pydantic model representing the full state of a conversation stored in Redis."""

    conversation_id: str = Field(
        ..., description="Unique identifier of the conversation"
    )
    user_id: Optional[int] = Field(None, description="Optional ID of the user")
    created_at: float = Field(
        default_factory=time.time, description="Epoch timestamp of creation"
    )
    updated_at: float = Field(
        default_factory=time.time, description="Epoch timestamp of last update"
    )
    last_question: Optional[str] = Field(None, description="Last user question")
    last_generated_sql: Optional[str] = Field(
        None, description="Last generated SQL query"
    )
    conversation_history: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="History of all messages in the conversation (role, content, timestamp)",
    )
    resolved_entities: Dict[str, Optional[str]] = Field(
        default_factory=lambda: {
            "last_case": None,
            "last_accused": None,
            "last_victim": None,
            "last_station": None,
            "last_district": None,
            "last_crime_type": None,
            "last_date_range": None,
        },
        description="Tracked entity parameters in the conversation context",
    )
