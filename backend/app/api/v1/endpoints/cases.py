from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.case import CaseService
from app.core.security import get_current_user
from app.core.permissions import require_permission, verify_district_access
from app.core.rbac import check_permission, Permission
from app.utils.masking import mask_name, mask_brief_facts

router = APIRouter()


@router.get("/")
async def get_cases(
    q: str | None = None,
    status: str | None = None,
    district: str | None = None,
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=15, ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Retrieve cases list with query, status, district filters and pagination."""
    # RBAC: Ensure user has SEARCH_CASES permission
    check_perm = require_permission(Permission.SEARCH_CASES)
    await check_perm(current_user)

    # ABAC: Enforce district access containment.
    # For unrestricted roles (SUPERVISOR, ANALYST, POLICY_MAKER) this returns "All".
    # For district-scoped roles (INVESTIGATOR, SENIOR_INVESTIGATOR) this returns their district.
    allowed_district = await verify_district_access(current_user, district, db)

    service = CaseService(db)
    result = await service.list_cases_paginated(
        q=q, status=status, district=allowed_district, page=page, page_size=pageSize
    )

    # Sensitive Data Masking: Mask brief facts if user lacks sensitive case access
    has_sensitive_access = check_permission(current_user["role"], Permission.SENSITIVE_CASE_ACCESS)
    if not has_sensitive_access:
        for item in result.get("items", []):
            if "narrative" in item:
                item["narrative"] = mask_brief_facts(item["narrative"])

    return result


@router.get("/metadata")
async def get_cases_metadata(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Retrieve metadata options for filters (districts, crime heads, statuses, gravity)."""
    service = CaseService(db)
    return await service.get_metadata()


@router.get("/{id}")
async def get_case_by_id(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Retrieve specific case parameters by ID."""
    # RBAC: Ensure user has SEARCH_CASES permission
    check_perm = require_permission(Permission.SEARCH_CASES)
    await check_perm(current_user)

    service = CaseService(db)
    case_detail = await service.get_case_detail(id)
    if not case_detail:
        raise HTTPException(status_code=404, detail=f"Case with ID {id} not found.")

    # ABAC: Enforce district access containment
    await verify_district_access(current_user, case_detail.get("district"), db)

    # Sensitive Data Masking: Mask victim names and narratives if user lacks sensitive case access
    has_sensitive_access = check_permission(current_user["role"], Permission.SENSITIVE_CASE_ACCESS)
    if not has_sensitive_access:
        if "victims" in case_detail:
            for v in case_detail["victims"]:
                v["name"] = mask_name(v["name"])
        if "narrative" in case_detail:
            case_detail["narrative"] = mask_brief_facts(case_detail["narrative"])

    return case_detail
