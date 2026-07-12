"""
app/agents/orchestrator/orchestrator.py — Central request orchestrator.

Day 2: simple pass-through router — every request goes to the Query Agent.
Day 3+: will add intent classification and multi-agent routing.

Usage:
    from app.agents.orchestrator.orchestrator import Orchestrator

    orch = Orchestrator()
    response = await orch.handle(question, db_session, request_id="abc-123")
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.orchestrator.router import AgentRegistry
from app.agents.query_agent.query_agent import QueryAgent

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Central orchestrator that receives user requests and routes them
    to the appropriate agent.

    Day 2 behaviour: all requests → Query Agent.
    Future: intent classification → multi-agent dispatch.
    """

    def __init__(self) -> None:
        self._registry = AgentRegistry()
        self._register_agents()
        logger.info(
            "Orchestrator initialised  agents=%s",
            self._registry.available_agents(),
        )

    def _register_agents(self) -> None:
        """Register all available agents."""
        self._registry.register("query", QueryAgent)
        # Future agents register here:
        # self._registry.register("network", NetworkAgent)
        # self._registry.register("pattern", PatternAgent)
        # self._registry.register("risk", RiskAgent)
        # self._registry.register("decision_support", DecisionSupportAgent)
        # self._registry.register("financial", FinancialAgent)
        # self._registry.register("audit", AuditAgent)

    async def handle(
        self,
        question: str,
        session: AsyncSession,
        *,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Process a user request end-to-end.

        Parameters
        ----------
        question : str
            The user's natural-language question.
        session : AsyncSession
            Active database session.
        request_id : str, optional
            Correlation ID for logging. Auto-generated if not provided.

        Returns
        -------
        dict  Standardised agent response with request metadata.
        """
        req_id = request_id or str(uuid.uuid4())

        logger.info(
            "Orchestrator  request_id=%s  question=%.200s",
            req_id, question,
        )

        # Day 2: route everything to Query Agent.
        agent_name = self._route(question)

        try:
            agent = self._registry.get(agent_name)
        except KeyError as exc:
            logger.error("Agent resolution failed: %s", exc)
            return {
                "status": "error",
                "request_id": req_id,
                "error": str(exc),
                "error_type": "agent_not_found",
            }

        try:
            response = await agent.run(question, session)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Agent '%s' raised an unexpected error: %s", agent_name, exc)
            return {
                "status": "error",
                "request_id": req_id,
                "error": "An internal error occurred while processing your request.",
                "error_type": "internal_error",
                "retryable": False,
            }

        # Attach orchestrator metadata.
        response["request_id"] = req_id
        response["agent"] = agent_name

        logger.info(
            "Orchestrator  request_id=%s  agent=%s  status=%s",
            req_id, agent_name, response.get("status"),
        )
        return response

    def _route(self, question: str) -> str:
        """
        Determine which agent should handle the question.

        Day 2: always returns 'query'.
        Future: intent classification via Gemini or keyword heuristics.
        """
        # TODO Day 3: implement intent classification.
        return "query"
