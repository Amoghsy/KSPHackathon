from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.accused import AccusedService

router = APIRouter()


@router.get("/")
async def get_accused(
    limit: int = 100, offset: int = 0, db: AsyncSession = Depends(get_db)
):
    """Retrieve accused persons list."""
    service = AccusedService(db)
    accused = await service.list_accused(limit, offset)
    return {"accused": accused, "count": len(accused)}
