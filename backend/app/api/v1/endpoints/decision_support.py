import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.security import get_current_user
from app.core.rbac import normalize_role
from app.services.decision_support.decision_service import DecisionSupportService
from app.agents.audit_agent.audit_agent import AuditAgent

router = APIRouter()
audit = AuditAgent()

async def check_investigative_role(current_user: dict, request: Request, case_id: int | None, db: AsyncSession):
    """
    Guards decision support endpoints against non-investigative roles
    (ADMINISTRATOR and POLICY_MAKER).
    """
    role = normalize_role(current_user.get("role"))
    if role in ("ADMINISTRATOR", "POLICY_MAKER"):
        # Log unauthorized attempt synchronously
        req_id = f"ds-unauth-{uuid.uuid4()}"
        await audit.log_action(
            db,
            user_id=current_user.get("id"),
            username=current_user.get("username"),
            role=current_user.get("role"),
            api=request.url.path,
            request_id=req_id,
            action="UNAUTHORIZED_DECISION_SUPPORT_ATTEMPT",
            case_id=case_id,
            summary=f"Role '{role}' attempted to access investigative decision support for case ID {case_id}."
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission Denied. Role '{role}' is not authorized to access Decision Support."
        )

@router.get("/case/{case_id}")
async def get_case_intelligence(
    case_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get complete decision-support intelligence overview for a single case.
    """
    await check_investigative_role(current_user, request, case_id, db)
    service = DecisionSupportService(db)
    
    # Retrieves case & checks district ABAC
    case = await service.get_authorized_case(case_id, current_user)
    
    # Audit log
    await audit.log_action(
        db,
        user_id=current_user.get("id"),
        username=current_user.get("username"),
        role=current_user.get("role"),
        api=request.url.path,
        request_id=f"ds-view-{uuid.uuid4()}",
        action="CASE_INTELLIGENCE_VIEWED",
        case_id=case_id,
        district_id=case.police_station.district if case.police_station else "Unknown",
        summary=f"Investigator viewed decision support intelligence for case {case.crime_no}."
    )
    
    # Re-use brief logic to pack summary, network, patterns, etc.
    brief = await service.get_investigation_brief(case_id, current_user, generate_ai_summary=False)
    return brief

@router.get("/case/{case_id}/similar")
async def get_similar_cases(
    case_id: int,
    request: Request,
    limit: int = Query(default=5, ge=1, le=20),
    min_score: float = Query(default=0.0, ge=0.0, le=100.0),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Retrieve similar cases with scores and explanations. Enforces district ABAC masking.
    """
    await check_investigative_role(current_user, request, case_id, db)
    service = DecisionSupportService(db)
    
    case = await service.get_authorized_case(case_id, current_user)
    similar = await service.get_similar_cases(case_id, current_user, limit=limit, min_score=min_score)
    
    # Audit log
    await audit.log_action(
        db,
        user_id=current_user.get("id"),
        username=current_user.get("username"),
        role=current_user.get("role"),
        api=request.url.path,
        request_id=f"ds-sim-{uuid.uuid4()}",
        action="SIMILAR_CASE_SEARCHED",
        case_id=case_id,
        district_id=case.police_station.district if case.police_station else "Unknown",
        summary=f"Investigator ran case similarity search for case {case.crime_no}."
    )
    return similar

@router.get("/case/{case_id}/leads")
async def get_investigation_leads(
    case_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get evidence-backed follow-up investigative leads for the case.
    """
    await check_investigative_role(current_user, request, case_id, db)
    service = DecisionSupportService(db)
    
    leads = await service.get_leads(case_id, current_user)
    return leads

@router.get("/case/{case_id}/gaps")
async def get_evidence_gaps(
    case_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Retrieve identified evidence and metadata gaps for the case.
    """
    await check_investigative_role(current_user, request, case_id, db)
    service = DecisionSupportService(db)
    
    gaps = await service.get_evidence_gaps(case_id, current_user)
    return gaps

@router.get("/case/{case_id}/timeline")
async def get_case_timeline(
    case_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Retrieve chronological timeline of actual events in the case.
    """
    await check_investigative_role(current_user, request, case_id, db)
    service = DecisionSupportService(db)
    
    timeline = await service.get_timeline(case_id, current_user)
    return timeline

@router.get("/case/{case_id}/brief")
async def get_investigation_brief(
    case_id: int,
    request: Request,
    generate_ai: bool = Query(default=True),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Retrieve comprehensive Investigation Brief and natural-language AI summary.
    """
    await check_investigative_role(current_user, request, case_id, db)
    service = DecisionSupportService(db)
    
    brief = await service.get_investigation_brief(case_id, current_user, generate_ai_summary=generate_ai)
    return brief
