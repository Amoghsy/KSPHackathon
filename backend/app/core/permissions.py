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

# Roles that are NOT district-scoped — they see all districts without assignment.
# RBAC controls which features they can access; ABAC does NOT restrict their data by district.
_UNRESTRICTED_ROLES = {"ANALYST", "POLICY_MAKER"}

# Sentinel value returned for unrestricted roles so callers know not to filter by district.
_ALL_DISTRICTS_SENTINEL = "__ALL__"


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


async def get_user_authorized_districts(user: dict | None, db: AsyncSession) -> list[str]:
    """
    Retrieve all authorized districts for a user dynamically from the database.
    Includes active permanent assignments and valid temporary permissions.

    Returns:
      - [] for ADMINISTRATOR (no investigative data access)
      - [\"__ALL__\"] for ANALYST, POLICY_MAKER (unrestricted state-wide view)
      - list of assigned district names for INVESTIGATOR, SENIOR_INVESTIGATOR, and SUPERVISOR

    Use resolve_authorized_districts() when passing to service/repository queries.
    """
    if not user:
        return [_ALL_DISTRICTS_SENTINEL]
    role = normalize_role(user.get("role"))

    # Platform administrators have no investigative district access
    if role == "ADMINISTRATOR":
        return []

    # Analysts and policy makers are not district-scoped.
    # They see all data across the state without requiring explicit assignments.
    if role in _UNRESTRICTED_ROLES:
        return [_ALL_DISTRICTS_SENTINEL]

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


def resolve_authorized_districts(districts: list[str]) -> list[str] | None:
    """
    Convert the result of get_user_authorized_districts() into a form suitable for
    service/repository queries.

    - ["__ALL__"] (unrestricted roles) → None  (no district filter in SQL)
    - []          (admin / unassigned)  → []   (empty list = no data shown)
    - [d1, d2]    (assigned)            → [d1, d2]  (filter to those districts)
    """
    if districts == [_ALL_DISTRICTS_SENTINEL]:
        return None  # No district filter — all data visible
    return districts


async def verify_district_access(user: dict | None, district: str | None, db: AsyncSession) -> str:
    """
    ABAC validator for district level data containment.
    Verifies if the user is authorized to access the requested district.
    If requested district is None/empty/all, resolves to the primary authorized district.

    Raises 403 Forbidden with a structured JSON detail payload if unauthorized.

    For unrestricted roles (ANALYST, POLICY_MAKER), any district is allowed.
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User authentication context is missing.",
        )
    role = normalize_role(user.get("role"))
    authorized = await get_user_authorized_districts(user, db)

    # Unrestricted roles pass through without district containment
    if authorized == [_ALL_DISTRICTS_SENTINEL]:
        # Return the requested district as-is, or "All" if none specified
        return district if district else "All"

    if not authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "DISTRICT_NOT_AUTHORIZED",
                "message": "Access Denied. User has no assigned districts.",
                "district_id": district,
                # Only INVESTIGATOR and SENIOR_INVESTIGATOR can request temporary access
                "can_request_access": role in ("INVESTIGATOR", "SENIOR_INVESTIGATOR"),
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
                "can_request_access": can_request,
            }
        )

    return matched
