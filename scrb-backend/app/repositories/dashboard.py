from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.accused import AccusedMaster
from app.models.case import CaseMaster
from app.models.victim import VictimMaster


class DashboardRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_stats(self) -> dict[str, int]:
        """Query basic aggregate stats for the dashboard."""
        cases_stmt = select(func.count()).select_from(CaseMaster)
        accused_stmt = select(func.count()).select_from(AccusedMaster)
        victims_stmt = select(func.count()).select_from(VictimMaster)

        cases_res = await self.db.execute(cases_stmt)
        accused_res = await self.db.execute(accused_stmt)
        victims_res = await self.db.execute(victims_stmt)

        return {
            "total_cases": cases_res.scalar() or 0,
            "total_accused": accused_res.scalar() or 0,
            "total_victims": victims_res.scalar() or 0,
        }
