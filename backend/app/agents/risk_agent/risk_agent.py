import logging
from app.agents.risk_agent.risk_models import OffenderRiskProfile

logger = logging.getLogger(__name__)

def get_deterministic_briefing_summary(profile: OffenderRiskProfile) -> str:
    """
    Generate an explainable briefing summary using deterministic rules.
    Used as a fallback when the LLM service is offline or fails.
    """
    factors_summary = "\n".join(
        f"- {f.label}: {f.reason} (Score contribution: {f.score}/{f.max_score})" 
        for f in profile.risk_factors if f.score > 0
    )
    tags_summary = ", ".join(t.label for t in profile.behavioral_tags) if profile.behavioral_tags else "None"
    return (
        f"Offender Security Briefing Summary for {profile.name}:\n"
        f"Assigned Risk Level: {profile.risk_level} (Prioritization Score: {profile.risk_score}/100)\n"
        f"Primary District: {profile.district}\n"
        f"Total Linked Cases: {profile.case_count}\n"
        f"Behavioral Tags: {tags_summary}\n\n"
        f"Risk Factors Analysis:\n{factors_summary}\n\n"
        f"Note: This score and classification represent decision support indicators based on historical case patterns "
        f"and are not predictive of future personal behavior."
    )

class RiskAgent:
    """
    AI Security Briefing Agent that utilizes Gemini to synthesize risk assessments
    into structured, natural-language briefing text.
    """

    def __init__(self) -> None:
        try:
            from app.services.llm.llm_service import LLMService
            self.llm = LLMService()
        except Exception as exc:
            logger.warning("Could not initialize LLMService for RiskAgent: %s", exc)
            self.llm = None

    async def explain_risk_profile(self, profile: OffenderRiskProfile) -> str:
        """
        Generate a natural-language description explaining the prioritization score and tags.
        """
        if not self.llm:
            return get_deterministic_briefing_summary(profile)

        # Build prompt
        prompt = (
            f"Please generate a professional, concise intelligence briefing summary for the suspect {profile.name}.\n"
            f"Role Context: You are a risk evaluation agent providing support for law enforcement supervisors. Your summary should explain "
            f"the risk classification and the exact contribution of each factor in a professional tone.\n\n"
            f"Suspect Info:\n"
            f"- Name: {profile.name}\n"
            f"- Risk Level: {profile.risk_level} (Score: {profile.risk_score}/100)\n"
            f"- District: {profile.district}\n"
            f"- Cases: {profile.case_count}\n"
            f"- Behavioral Tags: {', '.join(t.label for t in profile.behavioral_tags) if profile.behavioral_tags else 'None'}\n\n"
            f"Risk Factors Detail:\n"
        )
        for f in profile.risk_factors:
            if f.score > 0:
                prompt += f"- {f.label}: {f.reason} (Score: {f.score}/{f.max_score})\n"
        
        prompt += (
            "\nRequirements:\n"
            "1. State the overall risk level and prioritize the most significant risk factors.\n"
            "2. Explain how the behavioral tags correlate with their offending history.\n"
            "3. Conclude with a standard warning: 'This briefing represents decision support indicators based on historical patterns "
            "and is not predictive of future personal behavior.'\n"
            "4. Keep the summary under 150 words."
        )

        system_prompt = (
            "You are an AI Security Briefing Agent for the Karnataka State Police. "
            "You write highly structured, concise, and professional intelligence summaries."
        )

        try:
            response = await self.llm.generate(prompt, system=system_prompt)
            # Extract content from LLMResponse object if applicable
            if hasattr(response, "content"):
                return response.content
            return str(response)
        except Exception as exc:
            logger.error(
                "LLM generation failed in RiskAgent: %s. Falling back to deterministic summary.", 
                exc
            )
            return get_deterministic_briefing_summary(profile)
