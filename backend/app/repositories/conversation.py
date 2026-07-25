"""
app/repositories/conversation.py — Repository for loading, paginating, and sorting conversation sessions from Redis.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from app.services.conversation.context_store import ConversationContext
from app.services.conversation.conversation_manager import ConversationManager

logger = logging.getLogger(__name__)


class ConversationRepository:
    """
    Repository for managing conversation state stored in Redis.
    Exposes pagination and sorting to isolate Redis implementation details.
    """

    def __init__(self, manager: Optional[ConversationManager] = None) -> None:
        self.manager = manager or ConversationManager()

    async def get_all(
        self,
        limit: int = 20,
        offset: int = 0,
        sort_by: str = "updated_at",
        sort_order: str = "desc",
    ) -> List[ConversationContext]:
        """
        Scan all conversation sessions from Redis, decode them, and sort/paginate.
        """
        contexts: List[ConversationContext] = []
        try:
            client = self.manager.store.session_manager.client
            prefix = self.manager.store.session_manager.prefix

            keys = []
            cursor = 0
            while True:
                cursor, batch = await client.scan(
                    cursor=cursor, match=f"{prefix}*", count=100
                )
                keys.extend(batch)
                if cursor == 0:
                    break
        except Exception as e:
            logger.warning(
                "Redis connection error during get_all scan. Falling back to in-memory: %s",
                e,
            )
            fallback_db = self.manager.store.session_manager._fallback_db
            for session_id, data in fallback_db.items():
                try:
                    context = ConversationContext.from_dict(data)
                    if context:
                        contexts.append(context)
                except Exception as fe:
                    logger.warning("Failed to parse fallback session %s: %s", session_id, fe)
            
            # Sort
            reverse = sort_order.lower() == "desc"
            if sort_by in ["updated_at", "timestamp"]:
                contexts.sort(key=lambda c: c.updated_at, reverse=reverse)
            elif sort_by in ["created_at"]:
                contexts.sort(key=lambda c: c.created_at, reverse=reverse)
            else:
                contexts.sort(key=lambda c: c.updated_at, reverse=reverse)

            # Paginate
            return contexts[offset : offset + limit]

        for key in keys:
            session_id = key[len(prefix) :]
            try:
                context = await self.manager.get_conversation(session_id)
                if context:
                    contexts.append(context)
            except Exception as e:
                logger.warning(
                    "Error parsing conversation key %s: %s",
                    key,
                    e,
                )

        # Sort
        reverse = sort_order.lower() == "desc"
        if sort_by in ["updated_at", "timestamp"]:
            contexts.sort(key=lambda c: c.updated_at, reverse=reverse)
        elif sort_by in ["created_at"]:
            contexts.sort(key=lambda c: c.created_at, reverse=reverse)
        else:
            contexts.sort(key=lambda c: c.updated_at, reverse=reverse)

        # Paginate
        return contexts[offset : offset + limit]

    async def get_by_id(self, conversation_id: str) -> Optional[ConversationContext]:
        """Fetch a single conversation session."""
        return await self.manager.get_conversation(conversation_id)

    async def save(self, context: ConversationContext) -> None:
        """Save conversation session."""
        await self.manager.save_conversation(context)

    async def delete(self, conversation_id: str) -> bool:
        """Delete conversation session."""
        return await self.manager.delete_conversation(conversation_id)
