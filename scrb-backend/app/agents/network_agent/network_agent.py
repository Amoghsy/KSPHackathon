import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.graph.graph_service import GraphService
from app.services.llm.llm_service import LLMService

logger = logging.getLogger(__name__)


class NetworkAgent:
    """
    Network Intelligence Agent responsible for analyzing criminal relationships,
    co-offending groups, repeat offender risk, and summarizing network structures.
    Uses GraphService for NetworkX calculations and Gemini for summaries.
    """

    def __init__(self) -> None:
        self._llm = LLMService()
        logger.info("NetworkAgent initialised")

    async def analyze_network(
        self,
        session: AsyncSession,
        district: str | None = None,
        crime_type: str | None = None,
        police_station: str | None = None,
        time_period: str | None = None,
        focus_id: str | None = None,
    ) -> dict:
        """
        Runs network intelligence pipeline.
        Calls GraphService to fetch/analyze graph, then triggers Gemini for commentary.
        """
        service = GraphService(session)
        data = await service.get_criminal_network_data(
            district=district,
            crime_type=crime_type,
            police_station=police_station,
            time_period=time_period,
            focus_id=focus_id,
        )

        if data["node_count"] == 0:
            data["summary"] = "No criminal network data found matching the selected filters."
            return data

        # Ask Gemini to generate explanation summary
        prompt = self._build_explain_prompt(data)
        try:
            system_prompt = (
                "You are an expert criminal intelligence analyst for the Karnataka State Police. "
                "You explain mathematical graph analytics in high-quality professional briefings."
            )
            response = await self._llm.generate(prompt, system=system_prompt)
            data["summary"] = response.content.strip()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to get Gemini network summary: %s", exc)
            data["summary"] = (
                f"Graph analytics completed. The network consists of {data['node_count']} nodes "
                f"and {data['edge_count']} links with a density of {data['density']}. "
                f"Top repeat offenders include {', '.join(o['name'] for o in data['repeat_offenders'][:3])}."
            )

        return data

    def _build_explain_prompt(self, stats: dict) -> str:
        """Constructs the prompt for Gemini intelligence briefing."""
        focus_info = stats.get("focus_reason", "")
        prompt = f"""
You are the Network Intelligence Agent for the Karnataka State Police.
Explain the structural patterns discovered in the criminal network graph based on the following mathematical analysis:

{f"Investigation Focus: {focus_info}" if focus_info else ""}

- Nodes count: {stats['node_count']}
- Edges count: {stats['edge_count']}
- Graph Density: {stats['density']}
- Most Connected Criminals: {', '.join(stats['most_connected'][:5])}
- Bridge/Broker Suspects: {stats['bridge_nodes'][:5]}
- Detected Crime Gangs/Clusters: {len(stats['crime_clusters'])} distinct groups

Top Repeat Offenders:
"""
        for o in stats["repeat_offenders"][:5]:
            prompt += (
                f"- {o['name']} (Risk Score: {o['risk_score']}, cases: {', '.join(o['cases'][:3])}, "
                f"Associates: {', '.join(o['known_associates'][:3])})\n"
            )

        prompt += """
Generate a concise, professional, government-grade intelligence brief (2-4 sentences) summarizing these findings.
Do NOT list numbers in bullet points; format it as a cohesive report. Highlight key suspects who act as bridges or leaders and explain the coordination risk. Do not mention mathematical formulas.
"""
        return prompt
