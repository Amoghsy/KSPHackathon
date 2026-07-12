"""
app/services/conversation/conversation_service.py — Service layer for Conversation API.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.repositories.conversation import ConversationRepository
from app.services.conversation.context_store import ConversationContext


class ConversationService:
    """
    Service layer providing business logic for Conversations.
    Coordinates between Controller/API and ConversationRepository.
    """

    def __init__(self, repository: Optional[ConversationRepository] = None) -> None:
        self.repository = repository or ConversationRepository()

    async def list_conversations(
        self,
        limit: int = 20,
        offset: int = 0,
        sort_by: str = "updated_at",
        sort_order: str = "desc",
    ) -> List[ConversationContext]:
        """List and paginate conversation sessions."""
        return await self.repository.get_all(
            limit=limit, offset=offset, sort_by=sort_by, sort_order=sort_order
        )

    async def get_conversation(
        self, conversation_id: str
    ) -> Optional[ConversationContext]:
        """Retrieve a specific conversation session."""
        return await self.repository.get_by_id(conversation_id)

    async def update_conversation_metadata(
        self, conversation_id: str, updates: Dict[str, Any]
    ) -> Optional[ConversationContext]:
        """Update conversation properties (like user_id, last_question, resolved_entities)."""
        context = await self.repository.get_by_id(conversation_id)
        if not context:
            return None

        # Apply updates
        if "user_id" in updates:
            context.user_id = updates["user_id"]
        if "last_question" in updates:
            context.last_question = updates["last_question"]
        if "last_generated_sql" in updates:
            context.last_generated_sql = updates["last_generated_sql"]
        if "resolved_entities" in updates:
            context.entity_memory.update(updates["resolved_entities"])

        await self.repository.save(context)
        return context

    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation session."""
        return await self.repository.delete(conversation_id)
