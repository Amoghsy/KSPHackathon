"""
app/api/v1/endpoints/conversations.py — Conversation manager routes.
"""

from __future__ import annotations

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.schemas.conversation import ConversationResponse, ConversationUpdate
from app.services.conversation.conversation_service import ConversationService

logger = logging.getLogger(__name__)

router = APIRouter()


# Service dependency
def get_conversation_service() -> ConversationService:
    """Dependency provider for ConversationService."""
    return ConversationService()


@router.get(
    "/",
    response_model=List[ConversationResponse],
    summary="List all conversation sessions",
    description="Scan Redis for all sessions, sort by updated_at or created_at, and return paginated list.",
)
async def list_conversations(
    limit: int = Query(
        20, ge=1, le=100, description="Max number of conversations to return"
    ),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    sort_by: str = Query(
        "updated_at", description="Field to sort by (updated_at, created_at)"
    ),
    sort_order: str = Query("desc", description="Sort order (asc, desc)"),
    service: ConversationService = Depends(get_conversation_service),
):
    """Retrieve all conversations with pagination and sorting."""
    try:
        contexts = await service.list_conversations(
            limit=limit, offset=offset, sort_by=sort_by, sort_order=sort_order
        )
        return [c.to_dict() for c in contexts]
    except Exception as e:
        logger.exception("Error listing conversations: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load conversations: {str(e)}",
        )


@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
    summary="Retrieve a specific conversation session",
    description="Fetch a conversation session from Redis by ID.",
)
async def get_conversation(
    conversation_id: str,
    service: ConversationService = Depends(get_conversation_service),
):
    """Retrieve a single conversation session by ID."""
    context = await service.get_conversation(conversation_id)
    if not context:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation session '{conversation_id}' not found.",
        )
    return context.to_dict()


@router.patch(
    "/{conversation_id}",
    response_model=ConversationResponse,
    summary="Update conversation metadata",
    description="Modify conversation metadata (e.g. user_id or resolved entities) manually.",
)
async def update_conversation(
    conversation_id: str,
    payload: ConversationUpdate,
    service: ConversationService = Depends(get_conversation_service),
):
    """Modify conversation properties by ID."""
    updates = payload.dict(exclude_none=True)
    context = await service.update_conversation_metadata(conversation_id, updates)
    if not context:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation session '{conversation_id}' not found.",
        )
    return context.to_dict()


@router.delete(
    "/{conversation_id}",
    summary="Delete a conversation session",
    description="Permanently delete a conversation session from Redis.",
)
async def delete_conversation(
    conversation_id: str,
    service: ConversationService = Depends(get_conversation_service),
):
    """Delete a conversation session by ID."""
    deleted = await service.delete_conversation(conversation_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation session '{conversation_id}' not found or could not be deleted.",
        )
    return {
        "status": "success",
        "message": f"Conversation '{conversation_id}' deleted.",
    }
