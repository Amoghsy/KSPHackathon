from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.security import get_current_user
from app.core.rbac import normalize_role
from app.db.session import get_db
from app.services.risk.risk_service import RiskService
from app.agents.risk_agent.risk_agent import RiskAgent
from app.agents.risk_agent.risk_models import OffenderRiskProfile, RiskSummaryResponse, RiskAgentResponse
from app.core.permissions import verify_district_access

router = APIRouter()

def check_investigative_access(current_user: dict):
    role = normalize_role(current_user.get("role"))
    if role in ("ADMINISTRATOR", "ANALYST", "POLICY_MAKER"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your role is not authorized to view individual offender risk profiles."
        )

async def verify_offender_district_access(accused_id: str, current_user: dict, db: AsyncSession):
    # Lookup the accused globally to check which district they belong to
    from app.models.accused import AccusedMaster
    from app.models.police_station import PoliceStation
    from app.models.case import CaseMaster
    
    if accused_id.startswith("A_"):
        name_part = accused_id[2:].replace("_", " ")
        stmt = select(PoliceStation.district).join(CaseMaster).join(AccusedMaster).where(
            func.lower(AccusedMaster.accused_name) == name_part.lower()
        )
    else:
        stmt = select(PoliceStation.district).join(CaseMaster).join(AccusedMaster).where(
            AccusedMaster.person_id == accused_id
        )
        
    res = await db.execute(stmt)
    districts = [r[0] for r in res.all() if r[0]]
    if districts:
        from app.core.permissions import get_user_authorized_districts, _ALL_DISTRICTS_SENTINEL
        authorized = await get_user_authorized_districts(current_user, db)
        if authorized == [_ALL_DISTRICTS_SENTINEL]:
            return
        # If any of the offender's districts is in the user's authorized districts, they have access
        for d in districts:
            if any(auth_d.lower() == d.lower() for auth_d in authorized):
                return
        # If none matched, trigger verify_district_access on the first one to raise the proper 403 error
        await verify_district_access(current_user, districts[0], db)

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
    allowed_district = await verify_district_access(current_user, district, db)
    
    service = RiskService(db)
    return await service.get_offenders_risk_profiles(
        current_user=current_user,
        district=allowed_district,
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
        await verify_offender_district_access(accused_id, current_user, db)
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
    
    allowed_district = await verify_district_access(current_user, district, db)
    
    service = RiskService(db)
    res = await service.get_risk_summary(current_user, allowed_district)
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
        await verify_offender_district_access(accused_id, current_user, db)
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
