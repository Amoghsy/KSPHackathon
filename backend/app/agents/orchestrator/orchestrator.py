"""
app/agents/orchestrator/orchestrator.py — Upgraded request orchestrator.
"""

from __future__ import annotations

import asyncio
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
        current_user: dict | None = None,
        response_language: str = "auto",
    ) -> dict[str, Any]:
        """
        Process a user request end-to-end.
        """
        req_id = request_id or str(uuid.uuid4())
        conv_id = conversation_id or str(uuid.uuid4())
        u_id = user_id or (current_user.get("id") if current_user else None)

        logger.info(
            "Orchestrator request_id=%s conversation_id=%s question=%.200s",
            req_id,
            conv_id,
            question,
        )

        # 1. Load Redis session (async — does not block anything else yet)
        conv_context = await self.conversation_manager.get_conversation(conv_id)
        if not conv_context:
            logger.info(
                "No session found. Creating new session for conversation_id=%s", conv_id
            )
            conv_context = await self.conversation_manager.create_conversation(
                conv_id, user_id=u_id
            )

        
        # Update preference in context
        conv_context.preferred_language = response_language

        # 2. Inject context to resolve follow-up questions
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
            # Fire-and-forget audit log — don't block the error response
            asyncio.create_task(
                self._log_conversation(
                    None, question, resolved_question, response, req_id, conv_id, current_user, user_id=user_id
                )
            )
            return response

        try:
            response = await agent.run(
                resolved_question,
                session,
                response_language=response_language,
                current_user=current_user,
            )
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
            asyncio.create_task(
                self._log_conversation(
                    None, question, resolved_question, response, req_id, conv_id, current_user, user_id=user_id
                )
            )
            return response

        # Attach orchestrator metadata
        response["request_id"] = req_id
        response["agent"] = agent_name
        response["conversation_id"] = conv_id
        response["resolved_question"] = resolved_question

        # 4. Extract entities and build message objects (sync — cheap)
        try:
            resolved_entities = self.entity_resolver.resolve(
                resolved_question, response
            )
            entities_dict = resolved_entities.dict(exclude_none=True)

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
                "rows": response.get("rows"),
                "columns": response.get("columns"),
                "explain": response.get("explain"),
                "statistics": response.get("statistics"),
            }

            # 5. Fire-and-forget: Redis session update + audit log — user gets response NOW.
            async def _persist() -> None:
                """Background task: update session and write audit log concurrently."""
                try:
                    await asyncio.gather(
                        self.conversation_manager.update_conversation(
                            conv_id,
                            messages=conv_context.conversation_history + [user_msg, assistant_msg],
                            resolved_entities=entities_dict,
                            last_generated_sql=response.get("generated_sql"),
                            last_question=question,
                            preferred_language=response_language,
                        ),
                        self._log_conversation(
                            None, question, resolved_question, response,
                            req_id, conv_id, current_user, user_id=user_id,
                        ),
                    )
                except Exception as bg_exc:
                    logger.error("Background persist task failed: %s", bg_exc)

            asyncio.create_task(_persist())

        except Exception as exc:
            logger.error("Failed to build persist task: %s", exc)
            # Still log the conversation even if entity resolution failed
            asyncio.create_task(
                self._log_conversation(
                    None, question, resolved_question, response, req_id, conv_id, current_user, user_id=user_id
                )
            )

        return response


    async def _log_conversation(
        self,
        session: AsyncSession | None,
        question: str,
        resolved_question: str,
        response: dict[str, Any],
        req_id: str,
        conv_id: str,
        current_user: dict | None,
        user_id: int | None = None,
    ) -> None:
        """Helper to write conversation details to AuditLog. Safe from failures."""
        try:
            summary_content = response.get("summary") or response.get("error") or ""
            final_user_id = current_user.get("id") if current_user else user_id
            username = current_user.get("username") if current_user else None
            role = current_user.get("role") if current_user else None

            logger.info(
                "Audit Log Request: conversation_id=%s, request_id=%s, question=%s, resolved_question=%s, generated_sql=%s, summary=%s, execution_time=%s, user_id=%s",
                conv_id,
                req_id,
                question,
                resolved_question,
                response.get("generated_sql"),
                summary_content,
                response.get("execution_time_ms"),
                final_user_id,
            )

            from app.db.session import SessionLocal
            from app.agents.audit_agent.audit_agent import AuditAgent

            async with SessionLocal() as db_session:
                audit_agent = AuditAgent()
                await audit_agent.log_action(
                    db_session,
                    user_id=final_user_id,
                    username=username,
                    role=role,
                    api="chat",
                    question=question,
                    generated_sql=response.get("generated_sql"),
                    execution_time_ms=response.get("execution_time_ms"),
                    response_size=response.get("row_count") or len(response.get("rows", [])),
                    ip_address="127.0.0.1",
                    request_id=req_id,
                    status=response.get("status", "success"),
                    summary=summary_content,
                )
        except Exception as exc:
            logger.warning("Failed to write audit log to database: %s", exc)
