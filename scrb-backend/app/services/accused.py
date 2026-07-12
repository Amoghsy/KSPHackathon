from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.accused import AccusedRepository


class AccusedService:
    def __init__(self, db: AsyncSession):
        self.repository = AccusedRepository(db)

    async def list_accused(self, limit: int = 100, offset: int = 0) -> list[dict]:
        """Get list of accused persons formatted for API response."""
        accused_list = await self.repository.get_accused(limit, offset)
        return [
            {
                "accused_master_id": a.accused_master_id,
                "case_master_id": a.case_master_id,
                "accused_name": a.accused_name,
                "age_year": a.age_year,
                "gender_id": a.gender_id,
                "person_id": a.person_id,
            }
            for a in accused_list
        ]
