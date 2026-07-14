from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.dashboard import DashboardRepository


class DashboardService:
    def __init__(self, db: AsyncSession):
        self.repository = DashboardRepository(db)

    async def get_dashboard_summary(self) -> dict:
        """Fetch summary of key metrics for the dashboard."""
        kpis = await self.repository.get_stats_kpis()
        monthly_trend = await self.repository.get_monthly_trends()
        district_counts = await self.repository.get_district_counts()
        status_breakdown = await self.repository.get_status_breakdown()
        
        return {
            "kpis": kpis,
            "monthlyTrend": monthly_trend,
            "districtCounts": district_counts,
            "statusBreakdown": status_breakdown
        }
