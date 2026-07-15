"""
app/agents/orchestrator/router.py — Agent registry with pluggable routing.

Agents register themselves via `register_agent()`. The orchestrator
looks up agents by name. Future intent-classification routing can be
added without modifying existing agents.

Usage:
    from app.agents.orchestrator.router import AgentRegistry

    registry = AgentRegistry()
    registry.register("query", QueryAgent)
    agent = registry.get("query")
"""

from __future__ import annotations

import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)


class AgentRegistry:
    """
    Registry pattern for AI agents.

    Each agent is registered under a unique name. The orchestrator
    resolves agents by name. New agents plug in via `register()`
    without modifying existing code.
    """

    def __init__(self) -> None:
        self._agents: dict[str, Callable[..., Any]] = {}

    def register(self, name: str, factory: Callable[..., Any]) -> None:
        """
        Register an agent factory.

        Parameters
        ----------
        name : str
            Unique agent identifier, e.g. 'query', 'network', 'risk'.
        factory : callable
            Class or callable that returns an agent instance.
        """
        key = name.lower()
        self._agents[key] = factory
        logger.info("Agent registered: %s", key)

    def get(self, name: str, **kwargs: Any) -> Any:
        """
        Create and return an agent instance by name.

        Raises
        ------
        KeyError  If no agent is registered under the given name.
        """
        key = name.lower()
        if key not in self._agents:
            available = ", ".join(sorted(self._agents)) or "(none)"
            raise KeyError(f"Unknown agent '{key}'. Registered agents: {available}")
        return self._agents[key](**kwargs)

    def available_agents(self) -> list[str]:
        """Return names of all registered agents."""
        return sorted(self._agents)

    def has(self, name: str) -> bool:
        """Check if an agent is registered."""
        return name.lower() in self._agents
