"""
app/api/v1/endpoints/conversations.py — Conversation manager routes.
"""

from __future__ import annotations

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.schemas.conversation import ConversationResponse, ConversationUpdate
from app.services.conversation.conversation_service import ConversationService
from app.core.security import get_current_user
from app.core.permissions import require_permission
from app.core.rbac import Permission

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
    description="Scan Redis for all sessions, sort by updated_at or created_at, filter by user, and return paginated list.",
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
    current_user: dict = Depends(get_current_user),
):
    """Retrieve all conversations for the authenticated user with pagination and sorting."""
    # Ensure Permission
    check_perm = require_permission(Permission.CHAT_ASSISTANT)
    await check_perm(current_user)

    try:
        contexts = await service.list_conversations(
            limit=limit, offset=offset, sort_by=sort_by, sort_order=sort_order
        )
        # Filter to only return user's own conversations (standard user containment)
        filtered = [c.to_dict() for c in contexts if c.user_id == current_user["id"]]
        return filtered
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
    current_user: dict = Depends(get_current_user),
):
    """Retrieve a single conversation session by ID if owned by current user."""
    # Ensure Permission
    check_perm = require_permission(Permission.CHAT_ASSISTANT)
    await check_perm(current_user)

    context = await service.get_conversation(conversation_id)
    if not context:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation session '{conversation_id}' not found.",
        )
    if context.user_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied. You do not own this conversation.",
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
    current_user: dict = Depends(get_current_user),
):
    """Modify conversation properties by ID if owned by current user."""
    # Ensure Permission
    check_perm = require_permission(Permission.CHAT_ASSISTANT)
    await check_perm(current_user)

    context = await service.get_conversation(conversation_id)
    if not context:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation session '{conversation_id}' not found.",
        )
    if context.user_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied. You do not own this conversation.",
        )

    updates = payload.dict(exclude_none=True)
    updated_context = await service.update_conversation_metadata(conversation_id, updates)
    if not updated_context:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation session '{conversation_id}' not found.",
        )
    return updated_context.to_dict()


@router.delete(
    "/{conversation_id}",
    summary="Delete a conversation session",
    description="Permanently delete a conversation session from Redis.",
)
async def delete_conversation(
    conversation_id: str,
    service: ConversationService = Depends(get_conversation_service),
    current_user: dict = Depends(get_current_user),
):
    """Delete a conversation session by ID if owned by current user."""
    # Ensure Permission
    check_perm = require_permission(Permission.CHAT_ASSISTANT)
    await check_perm(current_user)

    context = await service.get_conversation(conversation_id)
    if not context:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation session '{conversation_id}' not found or could not be deleted.",
        )
    if context.user_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied. You do not own this conversation.",
        )

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
