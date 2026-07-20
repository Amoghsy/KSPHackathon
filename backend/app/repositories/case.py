from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.case import CaseMaster
from app.models.police_station import PoliceStation
from app.models.crime_type import CrimeType


class CaseRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_cases(self, limit: int = 100, offset: int = 0) -> list[CaseMaster]:
        """Fetch cases from database with basic pagination."""
        stmt = (
            select(CaseMaster)
            .options(
                selectinload(CaseMaster.police_station),
                selectinload(CaseMaster.crime_type),
            )
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_case_count(self) -> int:
        """Count total cases."""
        stmt = select(func.count()).select_from(CaseMaster)
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def get_filtered_cases(
        self,
        q: str | None = None,
        status_id: int | None = None,
        district: str | None = None,
        limit: int = 15,
        offset: int = 0,
    ) -> list[CaseMaster]:
        """Fetch cases matching search query, status, and district filters with pagination."""
        stmt = select(CaseMaster).outerjoin(CaseMaster.police_station).outerjoin(CaseMaster.crime_type)
        
        conditions = []
        if q:
            search_pattern = f"%{q}%"
            conditions.append(
                or_(
                    CaseMaster.crime_no.ilike(search_pattern),
                    CaseMaster.case_no.ilike(search_pattern),
                    CaseMaster.brief_facts.ilike(search_pattern),
                    PoliceStation.name.ilike(search_pattern),
                    PoliceStation.district.ilike(search_pattern),
                )
            )
        
        if status_id is not None:
            conditions.append(CaseMaster.case_status_id == status_id)
            
        if district:
            conditions.append(PoliceStation.district == district)
            
        if conditions:
            stmt = stmt.where(*conditions)
            
        stmt = (
            stmt.options(
                selectinload(CaseMaster.police_station),
                selectinload(CaseMaster.crime_type),
                selectinload(CaseMaster.victims),
            )
            .limit(limit)
            .offset(offset)
            .order_by(CaseMaster.crime_registered_date.desc())
        )
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_filtered_cases_count(
        self,
        q: str | None = None,
        status_id: int | None = None,
        district: str | None = None,
    ) -> int:
        """Get total count of cases matching the filter conditions."""
        stmt = select(func.count()).select_from(CaseMaster).outerjoin(CaseMaster.police_station)
        
        conditions = []
        if q:
            search_pattern = f"%{q}%"
            conditions.append(
                or_(
                    CaseMaster.crime_no.ilike(search_pattern),
                    CaseMaster.case_no.ilike(search_pattern),
                    CaseMaster.brief_facts.ilike(search_pattern),
                    PoliceStation.name.ilike(search_pattern),
                    PoliceStation.district.ilike(search_pattern),
                )
            )
        
        if status_id is not None:
            conditions.append(CaseMaster.case_status_id == status_id)
            
        if district:
            conditions.append(PoliceStation.district == district)
            
        if conditions:
            stmt = stmt.where(*conditions)
            
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def get_case_by_id(self, case_id: int) -> CaseMaster | None:
        """Fetch case details by ID including related associations."""
        stmt = (
            select(CaseMaster)
            .where(CaseMaster.case_master_id == case_id)
            .options(
                selectinload(CaseMaster.police_station),
                selectinload(CaseMaster.crime_type),
                selectinload(CaseMaster.accused),
                selectinload(CaseMaster.victims),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
