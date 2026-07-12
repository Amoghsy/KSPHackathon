"""
app/api/v1/endpoints/chat.py — POST /api/v1/chat endpoint.

Thin HTTP adapter — all business logic lives in chat_service.

Architecture:
    FastAPI Route → Chat Service → Orchestrator → Query Agent → Response
"""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user, oauth2_scheme
from app.db.session import get_db
from app.schemas.chat import ChatErrorResponse, ChatRequest, ChatResponse
from app.services.chat_service import handle_chat

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/",
    response_model=ChatResponse | ChatErrorResponse,
    summary="Ask a natural-language question",
    description=(
        "Converts a natural-language question into SQL, executes it against "
        "the SCRB database, and returns a structured response with a "
        "natural-language summary."
    ),
    responses={
        200: {
            "description": "Successful query — may also contain structured errors in the body.",
            "model": ChatResponse,
        },
        422: {"description": "Validation error — invalid request body."},
        500: {"description": "Internal server error."},
    },
)
async def chat_endpoint(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    token: str | None = Depends(oauth2_scheme),
) -> dict:
    """
    Accept a natural-language question and return AI-powered analytics.

    The pipeline:
    1. Generate SQL from the question (Gemini)
    2. Validate the SQL (safety + schema)
    3. Execute against PostgreSQL
    4. Summarise results (Gemini)
    5. Return structured response with confidence score
    """
    request_id = str(uuid.uuid4())

    logger.info(
        "Chat request  request_id=%s  question=%.200s",
        request_id,
        request.question,
    )

    # Extract user ID if authenticated
    user_id = None
    if token:
        try:
            current_user = await get_current_user(token)
            user_id = current_user.get("id")
        except HTTPException:
            # If token is invalid, we do not interrupt the request
            # since authentication is optional for now / log failures shouldn't block
            pass

    # Rate limiting hook (stub — implement with Redis in Day 3+).
    # await _check_rate_limit(request_id)

    try:
        response = await handle_chat(
            question=request.question,
            session=db,
            conversation_id=request.conversation_id,
            request_id=request_id,
            user_id=user_id,
            response_language=request.response_language,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Chat endpoint unhandled error: %s", exc)
        return {
            "status": "error",
            "request_id": request_id,
            "error": "An unexpected error occurred. Please try again.",
            "error_type": "internal_error",
            "retryable": True,
        }

    return response
