"""
app/services/conversation package.
"""

from __future__ import annotations

from app.repositories.conversation import ConversationRepository
from app.services.conversation.context_injector import ContextInjector
from app.services.conversation.context_store import ContextStore, ConversationContext
from app.services.conversation.conversation_manager import ConversationManager
from app.services.conversation.conversation_models import (
    ConversationMessage,
    ConversationSessionModel,
)
from app.services.conversation.conversation_service import ConversationService
from app.services.conversation.entity_memory import EntityMemory
from app.services.conversation.entity_resolver import EntityResolver, ResolvedEntity
from app.services.conversation.session_manager import SessionManager

__all__ = [
    "ConversationManager",
    "ContextStore",
    "ConversationContext",
    "EntityMemory",
    "SessionManager",
    "ConversationSessionModel",
    "ConversationMessage",
    "EntityResolver",
    "ResolvedEntity",
    "ContextInjector",
    "ConversationService",
    "ConversationRepository",
]
