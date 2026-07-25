from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.services.forecasting.forecasting_service import ForecastingService
from app.core.permissions import require_permission
from app.core.rbac import Permission

router = APIRouter()

@router.get("/crime")
async def get_crime_forecast(
    district: str | None = Query(None, description="Filter by district"),
    crime_type: str | None = Query(None, description="Filter by crime type (e.g., Theft, Cybercrime)"),
    periods: int = Query(3, ge=1, le=12, description="Number of future months to forecast"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get crime trend forecast filtered by district and crime type.
    """
    check_perm = require_permission(Permission.PATTERN_INTELLIGENCE)
    await check_perm(current_user)

    service = ForecastingService(db)
    return await service.get_crime_forecast(
        current_user=current_user,
        district=district,
        crime_type=crime_type,
        periods=periods
    )

@router.get("/district/{district}")
async def get_district_forecast(
    district: str,
    crime_type: str | None = Query(None, description="Filter by crime type (e.g., Theft, Cybercrime)"),
    periods: int = Query(3, ge=1, le=12, description="Number of future months to forecast"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get crime trend forecast for a specific district.
    """
    check_perm = require_permission(Permission.PATTERN_INTELLIGENCE)
    await check_perm(current_user)

    service = ForecastingService(db)
    return await service.get_crime_forecast(
        current_user=current_user,
        district=district,
        crime_type=crime_type,
        periods=periods
    )
