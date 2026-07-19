from fastapi import APIRouter, Depends, HTTPException, Query
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

    service = AccusedService(db)
    result = await service.list_offenders_paginated(q=q, page=page, page_size=pageSize)

    # ABAC: filter out offenders whose last known district the user is not allowed to see
    # And mask names if lacking sensitive access
    has_sensitive_access = check_permission(current_user["role"], Permission.SENSITIVE_CASE_ACCESS)
    
    filtered_items = []
    for item in result.get("items", []):
        try:
            # If verify_district_access raises HTTPException, it means they are not allowed to view this district
            await verify_district_access(current_user, item.get("lastKnown"), db)
            
            # Apply masking if necessary
            if not has_sensitive_access:
                item["name"] = mask_name(item["name"])
            
            filtered_items.append(item)
        except HTTPException:
            # Skip items not in authorized district
            continue
            
    result["items"] = filtered_items
    result["total"] = len(filtered_items)
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

    # ABAC check
    await verify_district_access(current_user, profile.get("lastKnown"), db)

    # Mask if lacking sensitive access
    has_sensitive_access = check_permission(current_user["role"], Permission.SENSITIVE_CASE_ACCESS)
    if not has_sensitive_access:
        profile["name"] = mask_name(profile["name"])
        if "associates" in profile:
            for assoc in profile["associates"]:
                assoc["name"] = mask_name(assoc["name"])

    return profile
