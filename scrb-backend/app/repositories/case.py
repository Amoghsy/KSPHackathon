from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case import CaseMaster


class CaseRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_cases(self, limit: int = 100, offset: int = 0) -> list[CaseMaster]:
        """Fetch cases from database."""
        stmt = select(CaseMaster).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_case_count(self) -> int:
        """Count total cases."""
        # Simple count for health/dashboard check
        from sqlalchemy import func
        stmt = select(func.count()).select_from(CaseMaster)
        result = await self.db.execute(stmt)
        return result.scalar() or 0
