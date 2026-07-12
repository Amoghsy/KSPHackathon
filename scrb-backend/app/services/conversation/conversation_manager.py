"""
app/services/conversation/conversation_manager.py — High-level Conversation Manager.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from app.services.conversation.context_store import ContextStore, ConversationContext


class ConversationManager:
    """
    High-level manager for coordinating conversation lifecycle and context.
    Provides simple interface for creation, loading, updating, saving and deleting sessions.
    """

    def __init__(self, store: Optional[ContextStore] = None) -> None:
        self.store = store or ContextStore()
        self.default_expiry = 86400  # 24 hours

    async def create_conversation(
        self,
        conversation_id: str,
        user_id: Optional[int] = None,
        expiry: int = 86400,
    ) -> ConversationContext:
        """
        Create a new conversation session, saving it to storage with the default TTL.
        """
        context = ConversationContext(
            conversation_id=conversation_id,
            user_id=user_id,
            created_at=time.time(),
            updated_at=time.time(),
        )
        await self.store.save(context, expiry=expiry)
        return context

    async def get_conversation(
        self, conversation_id: str
    ) -> Optional[ConversationContext]:
        """
        Retrieve an existing conversation context by ID.
        """
        return await self.store.load(conversation_id)

    async def update_conversation(
        self,
        conversation_id: str,
        *,
        messages: Optional[List[Dict[str, Any]]] = None,
        new_message: Optional[Dict[str, Any]] = None,
        resolved_entities: Optional[Dict[str, Any]] = None,
        last_generated_sql: Optional[str] = None,
        last_question: Optional[str] = None,
        expiry: int = 86400,
    ) -> Optional[ConversationContext]:
        """
        Update the attributes of an existing conversation context and save the updates.

        - If messages is provided, it replaces the message history.
        - If new_message is provided, it appends to the message history.
        - If resolved_entities is provided, it merges them into current entity memory.
        - If last_generated_sql is provided, it updates the SQL query history.
        - If last_question is provided, it updates the last user question.
        """
        context = await self.store.load(conversation_id)
        if not context:
            return None

        if messages is not None:
            context.conversation_history = messages
        if new_message is not None:
            context.conversation_history.append(new_message)
        if resolved_entities is not None:
            context.entity_memory.update(resolved_entities)
        if last_generated_sql is not None:
            context.last_generated_sql = last_generated_sql
        if last_question is not None:
            context.last_question = last_question

        context.updated_at = time.time()
        await self.store.save(context, expiry=expiry)
        return context

    async def save_conversation(
        self, context: ConversationContext, expiry: int = 86400
    ) -> None:
        """
        Directly persist an entire ConversationContext object.
        """
        context.updated_at = time.time()
        await self.store.save(context, expiry=expiry)

    async def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation session by ID.
        """
        return await self.store.delete(conversation_id)

    # Session interface aliases requested in Part 3
    async def create_session(
        self, conversation_id: str, user_id: Optional[int] = None, expiry: int = 86400
    ) -> ConversationContext:
        """Alias for create_conversation."""
        return await self.create_conversation(
            conversation_id, user_id=user_id, expiry=expiry
        )

    async def get_session(self, conversation_id: str) -> Optional[ConversationContext]:
        """Alias for get_conversation."""
        return await self.get_conversation(conversation_id)

    async def update_session(
        self, conversation_id: str, context: ConversationContext, expiry: int = 86400
    ) -> None:
        """Alias for save_conversation."""
        await self.save_conversation(context, expiry=expiry)

    async def append_message(
        self, conversation_id: str, message: Dict[str, Any], expiry: int = 86400
    ) -> Optional[ConversationContext]:
        """Append a message to the conversation context."""
        data = await self.store.session_manager.append_message(
            conversation_id, message, expiry=expiry
        )
        if not data:
            return None
        return ConversationContext.from_dict(data)

    async def delete_session(self, conversation_id: str) -> bool:
        """Alias for delete_conversation."""
        return await self.delete_conversation(conversation_id)

    async def expire_session(self, conversation_id: str, seconds: int) -> bool:
        """Set key expiration in seconds."""
        return await self.store.session_manager.expire_session(conversation_id, seconds)
