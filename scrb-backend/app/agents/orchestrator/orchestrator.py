"""
app/agents/orchestrator/orchestrator.py — Upgraded request orchestrator.
"""

from __future__ import annotations

import datetime
import logging
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.orchestrator.router import AgentRegistry
from app.models.audit_log import AuditLog
from app.services.conversation.context_injector import ContextInjector
from app.services.conversation.conversation_manager import ConversationManager
from app.services.conversation.entity_resolver import EntityResolver

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Central orchestrator that receives user requests, manages conversation sessions,
    resolves follow-ups, dispatches to agents, extracts entities, and updates session state.
    """

    def __init__(self) -> None:
        self._registry = AgentRegistry()
        self._register_agents()
        self.conversation_manager = ConversationManager()
        self.entity_resolver = EntityResolver()
        self.context_injector = ContextInjector()
        logger.info(
            "Orchestrator initialised  agents=%s",
            self._registry.available_agents(),
        )

    def _register_agents(self) -> None:
        """Register all available agents."""
        from app.agents.query_agent.query_agent import QueryAgent

        self._registry.register("query", QueryAgent)

    async def handle(
        self,
        question: str,
        session: AsyncSession,
        *,
        conversation_id: str | None = None,
        request_id: str | None = None,
        user_id: int | None = None,
    ) -> dict[str, Any]:
        """
        Process a user request end-to-end.
        """
        req_id = request_id or str(uuid.uuid4())
        conv_id = conversation_id or str(uuid.uuid4())

        logger.info(
            "Orchestrator request_id=%s conversation_id=%s question=%.200s",
            req_id,
            conv_id,
            question,
        )

        # 1. Load or Create Redis session
        conv_context = await self.conversation_manager.get_conversation(conv_id)
        if not conv_context:
            logger.info(
                "No session found. Creating new session for conversation_id=%s", conv_id
            )
            conv_context = await self.conversation_manager.create_conversation(
                conv_id, user_id=user_id
            )

        # 2. Inject Context to resolve follow-up questions
        resolved_question = self.context_injector.inject(
            question, conv_context.entity_memory, conv_context.last_question
        )
        logger.info("Resolved Question: %s", resolved_question)

        # 3. Call Query Agent with resolved question
        agent_name = "query"
        try:
            agent = self._registry.get(agent_name)
        except KeyError as exc:
            logger.error("Agent resolution failed: %s", exc)
            response = {
                "status": "error",
                "request_id": req_id,
                "error": str(exc),
                "error_type": "agent_not_found",
            }
            await self._log_conversation(
                session, question, resolved_question, response, req_id, conv_id, user_id
            )
            return response

        try:
            response = await agent.run(resolved_question, session)
        except Exception as exc:
            logger.exception(
                "Agent '%s' raised an unexpected error: %s", agent_name, exc
            )
            response = {
                "status": "error",
                "request_id": req_id,
                "error": "An internal error occurred while processing your request.",
                "error_type": "internal_error",
                "retryable": False,
            }
            await self._log_conversation(
                session, question, resolved_question, response, req_id, conv_id, user_id
            )
            return response

        # Attach orchestrator metadata
        response["request_id"] = req_id
        response["agent"] = agent_name
        response["conversation_id"] = conv_id
        response["resolved_question"] = resolved_question

        # 4. Extract entities from the completed response and update session state
        try:
            resolved_entities = self.entity_resolver.resolve(
                resolved_question, response
            )
            entities_dict = resolved_entities.dict(exclude_none=True)

            # Build user/assistant message pair
            user_msg = {
                "role": "user",
                "content": question,
                "timestamp": datetime.datetime.utcnow().timestamp(),
            }
            assistant_content = response.get("summary") or response.get("error") or ""
            assistant_msg = {
                "role": "assistant",
                "content": assistant_content,
                "timestamp": datetime.datetime.utcnow().timestamp(),
                "generated_sql": response.get("generated_sql"),
                "resolved_entities": entities_dict,
            }

            # Update Redis session
            await self.conversation_manager.update_conversation(
                conv_id,
                messages=conv_context.conversation_history + [user_msg, assistant_msg],
                resolved_entities=entities_dict,
                last_generated_sql=response.get("generated_sql"),
                last_question=question,
            )
        except Exception as exc:
            logger.error("Failed to update Redis conversation session: %s", exc)

        # 5. Log conversation safely
        await self._log_conversation(
            session, question, resolved_question, response, req_id, conv_id, user_id
        )

        return response

    async def _log_conversation(
        self,
        session: AsyncSession,
        question: str,
        resolved_question: str,
        response: dict[str, Any],
        req_id: str,
        conv_id: str,
        user_id: int | None,
    ) -> None:
        """Helper to write conversation details to AuditLog. Safe from failures."""
        try:
            summary_content = response.get("summary") or response.get("error") or ""

            logger.info(
                "Audit Log Request: conversation_id=%s, request_id=%s, question=%s, resolved_question=%s, generated_sql=%s, summary=%s, execution_time=%s, user_id=%s",
                conv_id,
                req_id,
                question,
                resolved_question,
                response.get("generated_sql"),
                summary_content,
                response.get("execution_time_ms"),
                user_id,
            )

            # Rollback if transaction failed to clear errors before writing audit log
            if session.in_transaction():
                await session.rollback()

            async with session.begin():
                audit = AuditLog(
                    question=question,
                    generated_sql=response.get("generated_sql"),
                    execution_time_ms=response.get("execution_time_ms"),
                    summary=summary_content,
                    user_id=user_id,
                    request_id=req_id,
                    timestamp=datetime.datetime.utcnow(),
                )
                session.add(audit)
        except Exception as exc:
            logger.warning("Failed to write audit log to database: %s", exc)
            try:
                await session.rollback()
            except Exception:
                pass
