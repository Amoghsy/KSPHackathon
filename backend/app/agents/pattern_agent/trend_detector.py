import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.analytics.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)


class TrendDetector:
    def __init__(self, db: AsyncSession):
        self.service = AnalyticsService(db)

    async def detect_trends(self, district: str | None = None, crime_type: str | None = None,
                            police_station: str | None = None, start_date: str | None = None,
                            end_date: str | None = None) -> dict:
        """Fetch and analyze crime trends."""
        logger.info("Detecting trends with filters: district=%s, crime_type=%s", district, crime_type)
        return await self.service.get_trends(
            district=district,
            crime_type=crime_type,
            police_station=police_station,
            start_date=start_date,
            end_date=end_date
        )
