from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.accused import AccusedMaster


class AccusedRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_accused(self, limit: int = 100, offset: int = 0) -> list[AccusedMaster]:
        """Fetch accused persons from database."""
        stmt = select(AccusedMaster).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
