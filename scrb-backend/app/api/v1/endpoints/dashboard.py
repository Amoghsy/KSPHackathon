from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.dashboard import DashboardService

router = APIRouter()


@router.get("/")
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    """Retrieve dashboard statistics summary."""
    service = DashboardService(db)
    summary = await service.get_dashboard_summary()
    return summary
