from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.accused import AccusedMaster
from app.models.case import CaseMaster
from app.models.police_station import PoliceStation
from app.services.graph.graph_utils import normalize_name


class AccusedRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_accused(
        self, limit: int = 100, offset: int = 0
    ) -> list[AccusedMaster]:
        """Fetch accused persons from database."""
        stmt = select(AccusedMaster).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_unique_offenders(
        self, q: str | None = None, limit: int = 15, offset: int = 0
    ) -> list[AccusedMaster]:
        """Fetch distinct offender personas (grouped by person_id) matching search query."""
        # Find distinct person_id by using a subquery or group_by
        # In SQLite/PostgreSQL we can group by person_id and select the one with min accused_master_id
        subq = (
            select(
                func.min(AccusedMaster.accused_master_id).label("min_id"),
                AccusedMaster.person_id
            )
            .group_by(AccusedMaster.person_id)
        )
        if q:
            subq = subq.where(AccusedMaster.accused_name.ilike(f"%{q}%"))
            
        subq = subq.subquery()
        
        stmt = (
            select(AccusedMaster)
            .join(subq, AccusedMaster.accused_master_id == subq.c.min_id)
            .options(
                selectinload(AccusedMaster.case).selectinload(CaseMaster.police_station),
                selectinload(AccusedMaster.case).selectinload(CaseMaster.crime_type),
            )
            .limit(limit)
            .offset(offset)
            .order_by(AccusedMaster.accused_name.asc())
        )
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_unique_offenders_count(self, q: str | None = None) -> int:
        """Count unique offender personas matching search query."""
        stmt = select(func.count(func.distinct(AccusedMaster.person_id)))
        if q:
            stmt = stmt.where(AccusedMaster.accused_name.ilike(f"%{q}%"))
            
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def get_all_instances_by_person_id(self, person_id: str) -> list[AccusedMaster]:
        """Fetch all accused database records sharing the same person_id (historical offenses)."""
        stmt = (
            select(AccusedMaster)
            .where(AccusedMaster.person_id == person_id)
            .options(
                selectinload(AccusedMaster.case).selectinload(CaseMaster.police_station),
                selectinload(AccusedMaster.case).selectinload(CaseMaster.crime_type),
                selectinload(AccusedMaster.case).selectinload(CaseMaster.accused),
            )
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_master_id(self, accused_master_id: int) -> AccusedMaster | None:
        """Fetch a specific accused entry by its primary key ID."""
        stmt = select(AccusedMaster).where(AccusedMaster.accused_master_id == accused_master_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
