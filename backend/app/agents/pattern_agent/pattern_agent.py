import logging
import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.analytics.analytics_service import AnalyticsService
from app.services.llm.llm_service import LLMService
from app.agents.pattern_agent.pattern_response import format_agent_success, format_agent_error

logger = logging.getLogger(__name__)


class PatternAgent:
    """
    Pattern Intelligence Agent responsible for temporal analysis, spatial hotspot detection (DBSCAN),
    anomaly detection, forecasting, and compiling professional executive summaries using Google Gemini.
    """

    def __init__(self) -> None:
        self._llm = LLMService()
        logger.info("PatternAgent initialised")

    async def analyze_patterns(
        self,
        db: AsyncSession,
        district: str | None = None,
        crime_type: str | None = None,
        police_station: str | None = None,
        start_date: datetime.date | None = None,
        end_date: datetime.date | None = None,
        authorized_districts: list[str] | None = None,
    ) -> dict:
        """
        Runs the pattern intelligence pipeline.
        Fetches all analytical metrics and prompts Gemini to write a professional summary briefing.
        """
        try:
            service = AnalyticsService(db, authorized_districts=authorized_districts)

            # Parallel fetching or sequential for simplicity
            trends = await service.get_trends(
                district=district, crime_type=crime_type, police_station=police_station,
                start_date=start_date, end_date=end_date
            )
            hotspots = await service.get_hotspots(
                district=district, crime_type=crime_type, police_station=police_station,
                start_date=start_date, end_date=end_date
            )
            anomalies = await service.get_anomalies(
                district=district, crime_type=crime_type, police_station=police_station,
                start_date=start_date, end_date=end_date
            )
            distribution = await service.get_distribution(district=district, crime_type=crime_type)
            forecast = await service.get_forecast(district=district, crime_type=crime_type)

            details = {
                "trends": trends,
                "hotspots": hotspots,
                "anomalies": anomalies,
                "distribution": distribution,
                "forecast": forecast
            }

            # Generate Gemini summary
            prompt = self._build_briefing_prompt(trends, hotspots, anomalies, forecast, district, crime_type, police_station)
            try:
                system_prompt = (
                    "You are a Senior Crime Intelligence Analyst for the Karnataka State Police. "
                    "You write concise, government-grade intelligence briefings based on calculated statistical crime data. "
                    "You never invent numbers or calculate metrics; you only summarize the provided figures."
                )
                response = await self._llm.generate(prompt, system=system_prompt)
                summary = response.content.strip()
            except Exception as exc:
                logger.warning("Failed to obtain Gemini pattern intelligence briefing: %s", exc)
                # Fallback summary
                summary = (
                    f"Statistical analysis completed. Over the selected period, {trends.get('total_cases', 0)} cases were recorded. "
                    f"Growth rate stands at {trends.get('growth_rate_percent', 0.0)}%. "
                    f"Clustering detected {len(hotspots.get('dbscan_clusters', []))} spatial hotspots. "
                    f"Forecasting models predict a volume of {forecast.get('forecast_value', 0.0)} offenses for the next month."
                )

            return format_agent_success("PatternAgent", summary, details)

        except Exception as exc:
            logger.exception("PatternAgent run failed: %s", exc)
            return format_agent_error("PatternAgent", str(exc), "agent_execution_failed")

    def _build_briefing_prompt(self, trends: dict, hotspots: dict, anomalies: list, forecast: dict,
                               district: str | None, crime_type: str | None, police_station: str | None) -> str:
        """Construct the LLM prompt with all compiled numerical results."""
        clusters_str = ""
        for i, c in enumerate(hotspots.get("dbscan_clusters", [])[:3]):
            clusters_str += f"- Cluster {i+1}: Center at ({c['center']['latitude']:.4f}, {c['center']['longitude']:.4f}) in {c['district']} district. Case count: {c['cases']}. Dominant crime: {c['dominant']}. Severity: {c['severity']}/3.\n"

        anomalies_str = ""
        for a in anomalies[:3]:
            anomalies_str += f"- {a['time_period']}: Count of {a['count']} offenses. Reason: {a['reason']}\n"

        clusters_display = clusters_str if clusters_str else "- No localized clusters identified.\n"
        anomalies_display = anomalies_str if anomalies_str else "- No significant statistical anomalies detected.\n"

        prompt = f"""
You are the Pattern Intelligence Agent for the Karnataka State Police.
Summarize the geographical, temporal, and anomaly crime patterns discovered in our analysis.

Context and Filters:
- District: {district or "All"}
- Crime Type: {crime_type or "All"}
- Police Station: {police_station or "All"}

Calculated Aggregates:
- Total Cases in selected window: {trends.get('total_cases', 0)}
- Average Monthly Crime Frequency: {trends.get('average_monthly_frequency', 0)}
- Short-term Crime Growth Rate: {trends.get('growth_rate_percent', 0.0)}%
- Top Crime Categories: {', '.join([f"{c['crime_type']} ({c['cases']} cases)" for c in trends.get('top_crimes', [])[:3]])}
- Top Active Districts: {', '.join([f"{d['district']} ({d['cases']} cases)" for d in trends.get('district_ranking', [])[:3]])}

Hotspots & Clusters:
- Number of hotspots identified: {len(hotspots.get('dbscan_clusters', []))}
{clusters_display}
Anomalies Detected:
{anomalies_display}
Forecast Projection:
- Projected offenses for next month: {forecast.get('forecast_value', 0.0)}
- Forecast Confidence: {forecast.get('confidence', 0.0) * 100:.0f}%
- Forecast Commentary: {forecast.get('commentary', '')}

Generate a concise, professional, government-grade intelligence brief (2-4 sentences) summarizing these findings for senior police officials.
Highlight key growth trends, emerging hotspots, any anomalies, and future forecasts. Do NOT mention mathematical terms like 'DBSCAN', 'Z-score', or 'linear regression'. Do not list items as bullets in the final output; format it as a cohesive paragraph.
"""
        return prompt

