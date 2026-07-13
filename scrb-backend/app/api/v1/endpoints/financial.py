from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.graph.graph_service import GraphService

router = APIRouter()


@router.get("/")
async def get_financial_network(
    district: str | None = None,
    crime_type: str | None = None,
    police_station: str | None = None,
    time_period: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Get the directed financial transactions network graph.
    Returns nodes and links at the root for frontend compliance.
    """
    service = GraphService(db)
    data = await service.get_financial_network_data(
        district=district,
        crime_type=crime_type,
        police_station=police_station,
        time_period=time_period,
    )
    return {
        "nodes": data["graph"]["nodes"],
        "links": data["graph"]["links"],
        "patterns": data["patterns"],
        "node_count": data["node_count"],
        "edge_count": data["edge_count"],
    }
