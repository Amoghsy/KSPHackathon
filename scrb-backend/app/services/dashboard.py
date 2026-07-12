from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.dashboard import DashboardRepository


class DashboardService:
    def __init__(self, db: AsyncSession):
        self.repository = DashboardRepository(db)

    async def get_dashboard_summary(self) -> dict:
        """Fetch summary of key metrics for the dashboard."""
        stats = await self.repository.get_stats()
        # Add placeholder charts/trends logic if needed, or keep it minimal
        return {
            "stats": stats,
            "crime_trends": [
                {"month": "Jan", "count": 45},
                {"month": "Feb", "count": 52},
                {"month": "Mar", "count": 48},
            ],  # Placeholder trend data
            "status": "success",
        }
