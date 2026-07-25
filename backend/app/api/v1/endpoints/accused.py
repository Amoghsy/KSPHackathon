from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.accused import AccusedService
from app.core.security import get_current_user
from app.core.permissions import require_permission, verify_district_access
from app.core.rbac import Permission, check_permission
from app.utils.masking import mask_name

router = APIRouter()


@router.get("/")
async def get_accused_list(
    q: str | None = None,
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=15, ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Retrieve unique repeat offender profiles list with name search and pagination."""
    # Ensure permission
    check_perm = require_permission(Permission.SEARCH_CASES)
    await check_perm(current_user)

    # Policy Makers cannot view raw accused profiles
    from app.core.rbac import normalize_role
    if normalize_role(current_user.get("role")) == "POLICY_MAKER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Policy Makers are not authorized to view raw accused profiles."
        )

    from app.core.permissions import get_user_authorized_districts, resolve_authorized_districts
    auth_districts_raw = await get_user_authorized_districts(current_user, db)
    authorized_districts = resolve_authorized_districts(auth_districts_raw)

    service = AccusedService(db)
    result = await service.list_offenders_paginated(
        q=q, page=page, page_size=pageSize, authorized_districts=authorized_districts
    )

    # Apply sensitive name masking if lacking permission and local district scope
    has_sensitive_access = check_permission(current_user["role"], Permission.SENSITIVE_CASE_ACCESS)
    from app.core.permissions import _ALL_DISTRICTS_SENTINEL
    for item in result.get("items", []):
        offender_districts = item.get("districts", [])
        is_district_authorized = False
        if auth_districts_raw == [_ALL_DISTRICTS_SENTINEL]:
            is_district_authorized = True
        elif offender_districts and auth_districts_raw:
            is_district_authorized = any(
                any(d.lower() == od.lower() for d in auth_districts_raw)
                for od in offender_districts
            )

        if not (has_sensitive_access or is_district_authorized):
            item["name"] = mask_name(item["name"])
            
    return result


@router.get("/{id}")
async def get_offender_by_id(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Retrieve detailed profile of a suspect by ID."""
    check_perm = require_permission(Permission.SEARCH_CASES)
    await check_perm(current_user)

    # Policy Makers cannot view raw accused profiles
    from app.core.rbac import normalize_role
    if normalize_role(current_user.get("role")) == "POLICY_MAKER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Policy Makers are not authorized to view raw accused profiles."
        )

    service = AccusedService(db)
    profile = await service.get_offender_detail(id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Suspect with ID {id} not found.")

    # ABAC check — allow access if the user is authorized for any district the offender has cases in
    from app.core.permissions import get_user_authorized_districts, _ALL_DISTRICTS_SENTINEL
    auth_districts_raw = await get_user_authorized_districts(current_user, db)
    offender_districts = profile.get("districts", [])

    is_district_authorized = False
    if auth_districts_raw == [_ALL_DISTRICTS_SENTINEL]:
        is_district_authorized = True
    elif offender_districts and auth_districts_raw:
        is_district_authorized = any(
            any(d.lower() == od.lower() for d in auth_districts_raw)
            for od in offender_districts
        )

    if not is_district_authorized:
        # Trigger default restriction error on lastKnown district to raise proper 403 Forbidden
        await verify_district_access(current_user, profile.get("lastKnown"), db)

    # Mask if lacking sensitive access and local district scope
    has_sensitive_access = check_permission(current_user["role"], Permission.SENSITIVE_CASE_ACCESS)
    user_has_sensitive_or_local = has_sensitive_access or is_district_authorized
    if not user_has_sensitive_or_local:
        profile["name"] = mask_name(profile["name"])
        if "associates" in profile:
            for assoc in profile["associates"]:
                assoc["name"] = mask_name(assoc["name"])

    return profile
