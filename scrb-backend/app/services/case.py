from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.case import CaseRepository


class CaseService:
    def __init__(self, db: AsyncSession):
        self.repository = CaseRepository(db)

    async def list_cases(self, limit: int = 100, offset: int = 0) -> list[dict]:
        """Get list of cases formatted for API response."""
        cases = await self.repository.get_cases(limit, offset)
        return [
            {
                "case_master_id": c.case_master_id,
                "crime_no": c.crime_no,
                "case_no": c.case_no,
                "crime_registered_date": c.crime_registered_date,
                "police_station_id": c.police_station_id,
                "incident_from_date": c.incident_from_date,
                "incident_to_date": c.incident_to_date,
                "latitude": float(c.latitude) if c.latitude is not None else None,
                "longitude": float(c.longitude) if c.longitude is not None else None,
                "brief_facts": c.brief_facts,
            }
            for c in cases
        ]
