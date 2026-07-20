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
    bypass_masking: bool = Query(default=False),
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

    # Sensitive Data Masking: Mask brief facts and victimName if user lacks sensitive case access
    # Bypassed only if export permission is present and bypass_masking is requested
    has_sensitive_access = check_permission(current_user["role"], Permission.SENSITIVE_CASE_ACCESS)
    has_export_access = check_permission(current_user["role"], Permission.EXPORT_REPORTS)
    
    should_mask = not has_sensitive_access
    if bypass_masking and has_export_access:
        should_mask = False

    if should_mask:
        for item in result.get("items", []):
            if "narrative" in item:
                item["narrative"] = mask_brief_facts(item["narrative"])
            if "victimName" in item and item["victimName"]:
                item["victimName"] = mask_name(item["victimName"])

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


@router.post("/export/audit")
async def audit_export(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Log a security audit event for exporting cases.
    """
    # Check permission
    check_perm = require_permission(Permission.EXPORT_REPORTS)
    await check_perm(current_user)

    q = payload.get("q")
    status = payload.get("status")
    district = payload.get("district")
    format_type = payload.get("format", "pdf")

    # ABAC: Enforce district access containment
    allowed_district = await verify_district_access(current_user, district, db)

    import uuid
    from app.agents.audit_agent.audit_agent import AuditAgent
    
    audit = AuditAgent()
    req_id = f"export-{uuid.uuid4()}"
    await audit.log_action(
        db,
        user_id=current_user.get("id"),
        username=current_user.get("username"),
        role=current_user.get("role"),
        api=f"/api/v1/cases/export/{format_type}",
        request_id=req_id,
        action=f"EXPORT_CASES_{format_type.upper()}",
        district_id=allowed_district,
        summary=f"Exported case list as {format_type.upper()} with filters (q={q}, status={status}, district={allowed_district or 'All'})"
    )
    return {"status": "success", "requestId": req_id}

