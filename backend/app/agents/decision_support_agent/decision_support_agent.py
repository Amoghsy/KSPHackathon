import logging
import json
from typing import Any

logger = logging.getLogger(__name__)

class DecisionSupportAgent:
    """
    Synthesizes a structured Case Investigation Brief into a natural-language narrative summary.
    Uses LLMService to access Gemini with strict constraints to prevent hallucinations.
    """
    def __init__(self) -> None:
        try:
            from app.services.llm.llm_service import LLMService
            self._llm = LLMService()
        except Exception as exc:
            logger.warning("Could not initialize LLMService for DecisionSupportAgent: %s", exc)
            self._llm = None

    async def generate_summary(self, brief: dict[str, Any]) -> str:
        """
        Generates narrative summary from structured brief with graceful fallback.
        """
        if not self._llm:
            return "AI narrative summary temporarily unavailable."

        crime_no = brief.get("case", {}).get("crime_number", "Unknown")
        
        # Prepare structured input for the LLM (strip very large raw tables to stay concise)
        clean_brief = {
            "case": {
                "crime_number": brief.get("case", {}).get("crime_number"),
                "crime_type": brief.get("case", {}).get("crime_type"),
                "district": brief.get("case", {}).get("district"),
                "police_station": brief.get("case", {}).get("police_station"),
                "brief_facts": brief.get("case", {}).get("brief_facts")
            },
            "network_findings": {
                "repeat_offender": brief.get("network_findings", {}).get("is_repeat_offender"),
                "community_id": brief.get("network_findings", {}).get("community_id")
            },
            "risk_findings": {
                "highest_risk_score": brief.get("risk_findings", {}).get("highest_risk_score"),
                "behavioral_tags": brief.get("risk_findings", {}).get("behavioral_tags")
            },
            "similar_cases_count": len(brief.get("similar_cases", [])),
            "similar_cases_summary": [
                {
                    "crime_no": sc.get("crime_no"),
                    "district": sc.get("district"),
                    "similarity": sc.get("similarity_score"),
                    "reasons": sc.get("reasons", [])
                }
                for sc in brief.get("similar_cases", [])[:3]
            ],
            "leads": [
                {"title": l.get("title"), "priority": l.get("priority"), "source": l.get("source_modules")}
                for l in brief.get("leads", [])
            ],
            "evidence_gaps": [
                {"type": g.get("type"), "description": g.get("description"), "severity": g.get("severity")}
                for g in brief.get("evidence_gaps", [])
            ]
        }

        prompt = f"""
You are the Decision Support Agent for the Karnataka State Police.
Generate a concise, professional, government-grade intelligence narrative summary (2-4 sentences) for Case {crime_no} based on the structured findings below:

{json.dumps(clean_brief, indent=2)}

Requirements:
1. Synthesize the case relationships, similar cases, and risk alerts naturally.
2. Outline the recommended follow-ups and note any important information gaps.
3. Strict Guideline: DO NOT declare or imply the guilt of any suspect, recommend arrest, invent evidence, or construct associations not listed in the structured findings.
4. If there is a cross-district signal in the leads, mention that comparative cross-district review is recommended subject to authorization.
5. Limit the narrative to 150 words.
"""

        system_prompt = (
            "You are summarizing structured crime intelligence for authorized investigators. "
            "Use only the supplied findings. Do not infer guilt, invent evidence, or create unsupported investigative claims. "
            "Never suggest arrest or determine a suspect's criminality."
        )

        try:
            response = await self._llm.generate(prompt, system=system_prompt)
            if hasattr(response, "content") and response.content:
                return response.content.strip()
            return str(response).strip()
        except Exception as exc:
            logger.error("Failed to generate Gemini summary in DecisionSupportAgent: %s", exc)
            return "AI narrative summary temporarily unavailable."
