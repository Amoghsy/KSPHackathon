from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.case import CaseService

router = APIRouter()


@router.get("/")
async def get_cases(
    limit: int = 100, offset: int = 0, db: AsyncSession = Depends(get_db)
):
    """Retrieve cases list."""
    service = CaseService(db)
    cases = await service.list_cases(limit, offset)
    return {"cases": cases, "count": len(cases)}
