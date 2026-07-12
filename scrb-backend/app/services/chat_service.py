"""
app/services/chat_service.py — Business logic for the chat endpoint.

Sits between the API route and the Orchestrator. All business logic
lives here — the route is just a thin HTTP adapter.
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.orchestrator.orchestrator import Orchestrator

logger = logging.getLogger(__name__)

# Module-level singleton — created on first use (lazy).
_orchestrator: Orchestrator | None = None


def _get_orchestrator() -> Orchestrator:
    """Lazily initialise the orchestrator singleton."""
    global _orchestrator  # noqa: PLW0603
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator


async def handle_chat(
    question: str,
    session: AsyncSession,
    *,
    conversation_id: str | None = None,
    request_id: str | None = None,
    user_id: int | None = None,
) -> dict[str, Any]:
    """
    Process a chat request through the orchestrator pipeline.

    Parameters
    ----------
    question : str
        User's natural-language question.
    session : AsyncSession
        Active database session.
    conversation_id : str, optional
        Unique conversation session ID.
    request_id : str, optional
        Correlation ID for tracing.
    user_id : int, optional
        Authenticated user ID.

    Returns
    -------
    dict  Standardised response from the orchestrator / agent.
    """
    orchestrator = _get_orchestrator()
    return await orchestrator.handle(
        question,
        session,
        conversation_id=conversation_id,
        request_id=request_id,
        user_id=user_id,
    )
