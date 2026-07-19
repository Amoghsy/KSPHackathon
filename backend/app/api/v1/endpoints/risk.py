from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.core.rbac import normalize_role
from app.db.session import get_db
from app.services.risk.risk_service import RiskService
from app.agents.risk_agent.risk_agent import RiskAgent
from app.agents.risk_agent.risk_models import OffenderRiskProfile, RiskSummaryResponse, RiskAgentResponse

router = APIRouter()

def check_investigative_access(current_user: dict):
    role = normalize_role(current_user.get("role"))
    if role in ("ADMINISTRATOR", "ANALYST", "POLICY_MAKER"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your role is not authorized to view individual offender risk profiles."
        )

@router.get("/offenders", response_model=list[OffenderRiskProfile])
async def get_offenders(
    district: str | None = Query(None, description="Filter by district"),
    minimum_score: float | None = Query(None, description="Minimum risk score filter"),
    risk_level: str | None = Query(None, description="Filter by risk level (LOW, MEDIUM, HIGH, CRITICAL)"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    check_investigative_access(current_user)
    service = RiskService(db)
    return await service.get_offenders_risk_profiles(
        current_user=current_user,
        district=district,
        minimum_score=minimum_score,
        risk_level=risk_level,
        limit=limit,
        offset=offset
    )

@router.get("/offender/{accused_id}", response_model=OffenderRiskProfile)
async def get_offender(
    accused_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    check_investigative_access(current_user)
    service = RiskService(db)
    profile = await service.get_offender_risk_profile(current_user, accused_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Offender risk profile not found for ID: {accused_id}"
        )
    return profile

@router.get("/summary", response_model=RiskSummaryResponse)
async def get_summary(
    district: str | None = Query(None, description="Filter by district"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # All roles (including ANALYST, POLICY_MAKER) can access aggregate risk distributions.
    # But ADMINISTRATOR is blocked from viewing any investigative data.
    role = normalize_role(current_user.get("role"))
    if role == "ADMINISTRATOR":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrators do not have permission to view investigative data summaries."
        )
    
    service = RiskService(db)
    res = await service.get_risk_summary(current_user, district)
    return res

@router.get("/intelligence", response_model=RiskAgentResponse)
async def get_intelligence(
    accused_id: str = Query(..., description="ID of the offender"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    check_investigative_access(current_user)
    service = RiskService(db)
    profile = await service.get_offender_risk_profile(current_user, accused_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Offender risk profile not found for ID: {accused_id}"
        )
    
    agent = RiskAgent()
    summary = await agent.explain_risk_profile(profile)
    return {
        "agent": "RiskAgent",
        "status": "success",
        "summary": summary,
        "details": profile
    }
