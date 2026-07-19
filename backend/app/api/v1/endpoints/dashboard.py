from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.dashboard import DashboardService
from app.core.security import get_current_user
from app.core.permissions import require_permission, get_user_authorized_districts
from app.core.rbac import Permission

router = APIRouter()


@router.get("/")
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Retrieve dashboard statistics summary scoped to user's authorized districts."""
    # Ensure permission
    check_perm = require_permission(Permission.DASHBOARD)
    await check_perm(current_user)

    # ABAC: fetch authorized districts
    auth_districts = await get_user_authorized_districts(current_user, db)

    service = DashboardService(db)
    summary = await service.get_dashboard_summary(authorized_districts=auth_districts)
    return summary
