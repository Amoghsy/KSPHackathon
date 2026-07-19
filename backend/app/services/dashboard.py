from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.dashboard import DashboardRepository


class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_dashboard_summary(self, authorized_districts: list[str] | None = None) -> dict:
        """Fetch summary of key metrics for the dashboard."""
        repository = DashboardRepository(self.db, authorized_districts=authorized_districts)
        kpis = await repository.get_stats_kpis()
        monthly_trend = await repository.get_monthly_trends()
        district_counts = await repository.get_district_counts()
        status_breakdown = await repository.get_status_breakdown()
        
        return {
            "kpis": kpis,
            "monthlyTrend": monthly_trend,
            "districtCounts": district_counts,
            "statusBreakdown": status_breakdown
        }
