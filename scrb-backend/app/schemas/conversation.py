"""
app/schemas/conversation.py — Pydantic schemas for Conversation APIs.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ConversationUpdate(BaseModel):
    """Payload to update conversation session properties."""

    user_id: Optional[int] = Field(None, description="Updated user ID")
    last_question: Optional[str] = Field(None, description="Updated last question")
    resolved_entities: Optional[Dict[str, Optional[str]]] = Field(
        None, description="Updated resolved entities dict"
    )


class ConversationResponse(BaseModel):
    """Pydantic model representing a conversation session response."""

    conversation_id: str = Field(..., description="Unique conversation ID")
    user_id: Optional[int] = Field(None, description="Associated user ID")
    created_at: float = Field(
        ..., description="Epoch timestamp when conversation was created"
    )
    updated_at: float = Field(
        ..., description="Epoch timestamp when conversation was last active"
    )
    last_question: Optional[str] = Field(None, description="Last user question")
    last_generated_sql: Optional[str] = Field(
        None, description="Last generated SQL query"
    )
    resolved_entities: Dict[str, Optional[str]] = Field(
        ..., description="Currently tracked resolved entities"
    )
    conversation_history: List[Dict[str, Any]] = Field(
        ..., description="List of messages (user and assistant)"
    )

    class Config:
        from_attributes = True
