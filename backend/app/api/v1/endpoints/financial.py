from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.graph.graph_service import GraphService
from app.core.security import get_current_user
from app.core.permissions import require_permission, verify_district_access
from app.core.rbac import Permission, check_permission
from app.utils.masking import mask_account, mask_name

router = APIRouter()


@router.get("/")
async def get_financial_network(
    district: str | None = None,
    crime_type: str | None = None,
    police_station: str | None = None,
    time_period: str | None = None,
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
    allowed_district = verify_district_access(current_user, district)

    service = GraphService(db)
    data = await service.get_financial_network_data(
        district=allowed_district,
        crime_type=crime_type,
        police_station=police_station,
        time_period=time_period,
    )

    # Masking: Mask bank accounts if lacking sensitive access (mostly fallback)
    has_sensitive_access = check_permission(current_user["role"], Permission.SENSITIVE_CASE_ACCESS)
    nodes = data["graph"]["nodes"]
    if not has_sensitive_access:
        for node in nodes:
            if node.get("kind") == "financial":
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
