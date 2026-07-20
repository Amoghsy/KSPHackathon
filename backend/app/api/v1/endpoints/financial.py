from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.orm import aliased
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.graph.graph_service import GraphService
from app.core.security import get_current_user
from app.core.permissions import require_permission, verify_district_access, get_user_authorized_districts, resolve_authorized_districts
from app.core.rbac import Permission, check_permission
from app.utils.masking import mask_account, mask_name
from app.models.accused import AccusedMaster
from app.models.case import CaseMaster
from app.models.police_station import PoliceStation
from app.models.financial_transaction import FinancialTransaction

router = APIRouter()


@router.get("/")
async def get_financial_network(
    district: str | None = None,
    crime_type: str | None = None,
    police_station: str | None = None,
    time_period: str | None = None,
    focus_id: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get the directed financial transactions network graph.
    Requires FINANCIAL_CRIME permission and enforces district-level ABAC.
    """
    # Enforce permission
    check_perm = require_permission(Permission.FINANCIAL_CRIME)
    await check_perm(current_user)

    # ABAC: Enforce district access containment
    allowed_district = await verify_district_access(current_user, district, db)
    auth_districts = await get_user_authorized_districts(current_user, db)

    service = GraphService(db)
    data = await service.get_financial_network_data(
        district=allowed_district,
        crime_type=crime_type,
        police_station=police_station,
        time_period=time_period,
        focus_id=focus_id,
        authorized_districts=resolve_authorized_districts(auth_districts),
    )

    # Masking: Mask bank accounts if lacking sensitive access (mostly fallback)
    has_sensitive_access = check_permission(current_user["role"], Permission.SENSITIVE_CASE_ACCESS)
    nodes = data["graph"]["nodes"]
    if not has_sensitive_access:
        for node in nodes:
            if node.get("kind") in ("financial", "account"):
                node["label"] = mask_account(node["label"])
            elif node.get("kind") == "accused":
                node["label"] = mask_name(node["label"])

    return {
        "nodes": nodes,
        "links": data["graph"]["links"],
        "patterns": data["patterns"],
        "node_count": data["node_count"],
        "edge_count": data["edge_count"],
    }


@router.get("/top-suspects")
async def get_top_suspects(
    district: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get the top recommended profiles of financial crime accused.
    Requires FINANCIAL_CRIME permission and enforces district-level ABAC.
    """
    check_perm = require_permission(Permission.FINANCIAL_CRIME)
    await check_perm(current_user)

    allowed_district = await verify_district_access(current_user, district, db)
    auth_districts = await get_user_authorized_districts(current_user, db)
    auth_districts_resolved = resolve_authorized_districts(auth_districts)

    AllCasesAccused = aliased(AccusedMaster)

    stmt = (
        select(
            AccusedMaster.person_id,
            func.min(AccusedMaster.accused_name).label("accused_name"),
            func.count(func.distinct(AllCasesAccused.case_master_id)).label("case_count"),
            func.count(FinancialTransaction.financial_transaction_id).label("suspicious_tx_count"),
            func.sum(FinancialTransaction.amount).label("total_suspicious_amount")
        )
        .join(FinancialTransaction, AccusedMaster.accused_master_id == FinancialTransaction.accused_master_id)
        .join(AllCasesAccused, AccusedMaster.person_id == AllCasesAccused.person_id)
        .join(CaseMaster, AllCasesAccused.case_master_id == CaseMaster.case_master_id)
        .join(PoliceStation, CaseMaster.police_station_id == PoliceStation.police_station_id)
        .where(FinancialTransaction.is_suspicious == True)
        .where(AccusedMaster.person_id.isnot(None))
    )

    if auth_districts_resolved is not None:
        stmt = stmt.where(PoliceStation.district.in_(auth_districts_resolved))
    if allowed_district and allowed_district != "All":
        stmt = stmt.where(PoliceStation.district == allowed_district)

    stmt = stmt.group_by(AccusedMaster.person_id).order_by(func.sum(FinancialTransaction.amount).desc())

    result = await db.execute(stmt)
    rows = result.all()

    suspects = []
    for r in rows:
        total_amt = float(r.total_suspicious_amount or 0)
        risk_score = min(0.99, 0.4 + (total_amt / 5000000.0) * 0.5 + (r.case_count * 0.05))
        suspects.append({
            "person_id": r.person_id,
            "accused_name": r.accused_name,
            "case_count": r.case_count,
            "suspicious_tx_count": r.suspicious_tx_count,
            "total_suspicious_amount": total_amt,
            "risk_score": round(risk_score, 2),
            "district": allowed_district or "Multiple"
        })

    return suspects


@router.get("/search")
async def search_financial_network(
    q: str,
    district: str | None = None,
    crime_type: str | None = None,
    police_station: str | None = None,
    time_period: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Search by accused name or FIR/Case ID and generate directed financial transactions network graph.
    Requires FINANCIAL_CRIME permission and enforces district-level ABAC.
    """
    check_perm = require_permission(Permission.FINANCIAL_CRIME)
    await check_perm(current_user)

    allowed_district = await verify_district_access(current_user, district, db)
    auth_districts = await get_user_authorized_districts(current_user, db)

    service = GraphService(db)
    data = await service.get_financial_network_data(
        district=allowed_district,
        crime_type=crime_type,
        police_station=police_station,
        time_period=time_period,
        focus_id=q,
        authorized_districts=resolve_authorized_districts(auth_districts),
    )

    has_sensitive_access = check_permission(current_user["role"], Permission.SENSITIVE_CASE_ACCESS)
    nodes = data["graph"]["nodes"]
    if not has_sensitive_access:
        for node in nodes:
            if node.get("kind") in ("financial", "account"):
                node["label"] = mask_account(node["label"])
            elif node.get("kind") == "accused":
                node["label"] = mask_name(node["label"])

    return {
        "nodes": nodes,
        "links": data["graph"]["links"],
        "patterns": data["patterns"],
        "node_count": data["node_count"],
        "edge_count": data["edge_count"],
    }
