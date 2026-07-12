"""
app/services/conversation/context_store.py — Conversation context storage and model.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from app.services.conversation.entity_memory import EntityMemory
from app.services.conversation.session_manager import SessionManager


class ConversationContext:
    """
    Structured model for conversation context, containing ID, metadata,
    message history, resolved entity values, and the last generated SQL.
    """

    def __init__(
        self,
        conversation_id: str,
        user_id: Optional[int] = None,
        created_at: Optional[float] = None,
        updated_at: Optional[float] = None,
        last_question: Optional[str] = None,
        last_generated_sql: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        resolved_entities: Optional[Dict[str, Any] | EntityMemory] = None,
        messages: Optional[List[Dict[str, Any]]] = None,
        timestamp: Optional[float] = None,
    ) -> None:
        self.conversation_id = conversation_id
        self.user_id = user_id
        now = time.time()
        self.created_at = created_at or now
        self.updated_at = updated_at or timestamp or now
        self.last_question = last_question
        self.last_generated_sql = last_generated_sql
        self.conversation_history = conversation_history or messages or []

        if isinstance(resolved_entities, EntityMemory):
            self.entity_memory = resolved_entities
        elif isinstance(resolved_entities, dict):
            self.entity_memory = EntityMemory.from_dict(resolved_entities)
        else:
            self.entity_memory = EntityMemory()

    @property
    def resolved_entities(self) -> Dict[str, Optional[str]]:
        """Return the tracked entity memory as a dictionary."""
        return self.entity_memory.to_dict()

    @property
    def messages(self) -> List[Dict[str, Any]]:
        """Alias for conversation_history to support older code."""
        return self.conversation_history

    @messages.setter
    def messages(self, val: List[Dict[str, Any]]) -> None:
        self.conversation_history = val

    @property
    def timestamp(self) -> float:
        """Alias for updated_at to support older code."""
        return self.updated_at

    @timestamp.setter
    def timestamp(self, val: float) -> None:
        self.updated_at = val

    def to_dict(self) -> Dict[str, Any]:
        """Convert the conversation context into a serializable dictionary."""
        d = {
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_question": self.last_question,
            "last_generated_sql": self.last_generated_sql,
            "conversation_history": self.conversation_history,
            "messages": self.conversation_history,  # Keep for backward compatibility
            "resolved_entities": self.resolved_entities,
        }
        # Inject individual entity fields at root level for direct compatibility
        d.update(self.resolved_entities)
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ConversationContext:
        """Instantiate a ConversationContext from a dictionary."""
        history = data.get("conversation_history")
        if history is None:
            history = data.get("messages")

        resolved_entities_data = data.get("resolved_entities")
        if not isinstance(resolved_entities_data, dict):
            resolved_entities_data = {
                "last_case": data.get("last_case"),
                "last_accused": data.get("last_accused"),
                "last_victim": data.get("last_victim"),
                "last_station": data.get("last_station"),
                "last_district": data.get("last_district"),
                "last_crime_type": data.get("last_crime_type"),
                "last_date_range": data.get("last_date_range"),
            }

        return cls(
            conversation_id=data["conversation_id"],
            user_id=data.get("user_id"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            last_question=data.get("last_question"),
            last_generated_sql=data.get("last_generated_sql"),
            conversation_history=history,
            resolved_entities=resolved_entities_data,
        )


class ContextStore:
    """
    Storage layer adapter for ConversationContext using SessionManager.
    Handles serialization/deserialization details.
    """

    def __init__(self, session_manager: Optional[SessionManager] = None) -> None:
        self.session_manager = session_manager or SessionManager()

    async def save(self, context: ConversationContext, expiry: int = 86400) -> None:
        """Save a ConversationContext to the session manager."""
        await self.session_manager.update_session(
            session_id=context.conversation_id,
            data=context.to_dict(),
            expiry=expiry,
        )

    async def load(self, conversation_id: str) -> Optional[ConversationContext]:
        """Load a ConversationContext from the session manager by conversation ID."""
        data = await self.session_manager.get_session(conversation_id)
        if not data:
            return None
        return ConversationContext.from_dict(data)

    async def delete(self, conversation_id: str) -> bool:
        """Delete a ConversationContext from the session manager."""
        return await self.session_manager.delete_session(conversation_id)
