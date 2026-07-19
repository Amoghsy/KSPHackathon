import datetime
from typing import Callable
from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.security import get_current_user
from app.core.rbac import check_permission, normalize_role
from app.models.district_assignment import UserDistrictAssignment
from app.models.access_request import TemporaryDistrictPermission


def require_permission(permission: str) -> Callable:
    """Dependency that requires a user to have a specific permission."""
    async def dependency(current_user: dict = Depends(get_current_user)) -> dict:
        role = current_user.get("role")
        if not check_permission(role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Role '{role}' does not have '{permission}' permission.",
            )
        return current_user
    return dependency


async def get_user_authorized_districts(user: dict, db: AsyncSession) -> list[str]:
    """
    Retrieve all authorized districts for a user dynamically from the database.
    Includes active permanent assignments and valid temporary permissions.
    """
    role = normalize_role(user.get("role"))
    # Platform administrators have no authorized districts for investigative data
    if role == "ADMINISTRATOR":
        return []

    user_id = user.get("id")
    if not user_id:
        return []

    # 1. Query active permanent assignments
    stmt1 = select(UserDistrictAssignment.district).where(
        UserDistrictAssignment.user_id == user_id,
        UserDistrictAssignment.is_active == True
    )
    res1 = await db.execute(stmt1)
    perm_districts = [r[0] for r in res1.fetchall()]

    # 2. Query valid temporary permissions (dynamic check: not revoked, not expired, currently active)
    now = datetime.datetime.utcnow()
    stmt2 = select(TemporaryDistrictPermission.district).where(
        TemporaryDistrictPermission.user_id == user_id,
        TemporaryDistrictPermission.is_revoked == False,
        TemporaryDistrictPermission.approved_at <= now,
        TemporaryDistrictPermission.expires_at > now
    )
    res2 = await db.execute(stmt2)
    temp_districts = [r[0] for r in res2.fetchall()]

    # Deduplicate districts
    all_districts = list(set(perm_districts + temp_districts))
    return all_districts


async def verify_district_access(user: dict, district: str | None, db: AsyncSession) -> str:
    """
    ABAC validator for district level data containment.
    Verifies if the user is authorized to access the requested district.
    If requested district is None/empty/all, resolves to the primary authorized district.
    
    Raises 403 Forbidden with a structured JSON detail payload if unauthorized.
    """
    role = normalize_role(user.get("role"))
    authorized = await get_user_authorized_districts(user, db)

    if not authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "DISTRICT_NOT_AUTHORIZED",
                "message": "Access Denied. User has no assigned districts.",
                "district_id": district,
                "can_request_access": False
            }
        )

    # Resolve default district if not specified or requesting all
    if not district or district.lower() == "all":
        # Return the primary (first) authorized district
        return authorized[0]

    # Check case-insensitive match
    matched = None
    for auth_d in authorized:
        if auth_d.lower() == district.lower():
            matched = auth_d
            break

    if not matched:
        # Structured error allowing the UI to present the temporary request modal
        can_request = role in ("INVESTIGATOR", "SENIOR_INVESTIGATOR")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "DISTRICT_NOT_AUTHORIZED",
                "message": f"You are not authorized to access investigations from {district}.",
                "district_id": district,
                "can_request_access": can_request
            }
        )

    return matched
