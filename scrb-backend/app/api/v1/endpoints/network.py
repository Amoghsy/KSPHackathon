from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.agents.network_agent.network_agent import NetworkAgent
from app.services.graph.graph_service import GraphService

router = APIRouter()


@router.get("/")
async def get_network(
    district: str | None = None,
    crime_type: str | None = None,
    police_station: str | None = None,
    time_period: str | None = None,
    focus_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Get the criminal network graph, optionally filtered and centered/focused on an entity.
    Injects nodes and links directly at top-level for frontend ForceGraph2D,
    along with summary and repeat offenders.
    """
    agent = NetworkAgent()
    data = await agent.analyze_network(
        db,
        district=district,
        crime_type=crime_type,
        police_station=police_station,
        time_period=time_period,
        focus_id=focus_id,
    )
    return {
        "nodes": data["graph"]["nodes"],
        "links": data["graph"]["links"],
        "summary": data["summary"],
        "density": data["density"],
        "node_count": data["node_count"],
        "edge_count": data["edge_count"],
        "repeat_offenders": data["repeat_offenders"],
        "communities": data["communities"],
        "focus_reason": data.get("focus_reason"),
        "center_node": data.get("center_node"),
    }



@router.get("/accused/{id}")
async def get_accused_network(id: str, db: AsyncSession = Depends(get_db)):
    """
    Get 1-degree network subgraph centered on a specific accused person.
    """
    service = GraphService(db)
    data = await service.get_criminal_network_data()

    nodes = data["graph"]["nodes"]
    links = data["graph"]["links"]

    # Find the target accused node
    accused_node = next((n for n in nodes if n["id"] == id), None)
    if not accused_node:
        accused_node = next(
            (
                n
                for n in nodes
                if n["kind"] == "accused" and n["label"].lower() == id.lower()
            ),
            None,
        )

    if not accused_node:
        raise HTTPException(status_code=404, detail=f"Accused '{id}' not found in graph.")

    target_id = accused_node["id"]
    connected_nodes = {target_id}
    connected_links = []

    for link in links:
        if link["source"] == target_id or link["target"] == target_id:
            connected_links.append(link)
            connected_nodes.add(link["source"])
            connected_nodes.add(link["target"])

    filtered_nodes = [n for n in nodes if n["id"] in connected_nodes]

    # Find repeat offender metadata if available
    offender_info = next(
        (o for o in data["repeat_offenders"] if o["id"] == target_id), None
    )

    return {
        "nodes": filtered_nodes,
        "links": connected_links,
        "accused": accused_node,
        "repeat_offender_info": offender_info,
    }


@router.get("/case/{id}")
async def get_case_network(id: str, db: AsyncSession = Depends(get_db)):
    """
    Get 1-degree network subgraph centered on a specific Case.
    """
    service = GraphService(db)
    data = await service.get_criminal_network_data()

    nodes = data["graph"]["nodes"]
    links = data["graph"]["links"]

    case_node = next(
        (
            n
            for n in nodes
            if n["id"] == id or str(n["metadata"].get("case_master_id")) == id
        ),
        None,
    )
    if not case_node:
        raise HTTPException(status_code=404, detail=f"Case '{id}' not found in graph.")

    target_id = case_node["id"]
    connected_nodes = {target_id}
    connected_links = []

    for link in links:
        if link["source"] == target_id or link["target"] == target_id:
            connected_links.append(link)
            connected_nodes.add(link["source"])
            connected_nodes.add(link["target"])

    filtered_nodes = [n for n in nodes if n["id"] in connected_nodes]

    return {
        "nodes": filtered_nodes,
        "links": connected_links,
        "case": case_node,
    }


@router.get("/community")
async def get_network_communities(db: AsyncSession = Depends(get_db)):
    """
    Get criminal gang communities detected via modularity.
    """
    service = GraphService(db)
    data = await service.get_criminal_network_data()
    return {"communities": data["communities"]}


@router.get("/repeat-offenders")
async def get_repeat_offenders(db: AsyncSession = Depends(get_db)):
    """
    Get list of repeat offenders with computed risk scores.
    """
    service = GraphService(db)
    data = await service.get_criminal_network_data()
    return {"repeat_offenders": data["repeat_offenders"]}


@router.get("/analytics")
async def get_network_analytics(db: AsyncSession = Depends(get_db)):
    """
    Get detailed graph centrality and structural density analytics.
    """
    service = GraphService(db)
    data = await service.get_criminal_network_data()
    return {
        "density": data["density"],
        "node_count": data["node_count"],
        "edge_count": data["edge_count"],
        "most_connected": data["most_connected"],
        "bridge_nodes": data["bridge_nodes"],
        "degree_centrality": data["degree_centrality"],
        "betweenness_centrality": data["betweenness_centrality"],
        "closeness_centrality": data["closeness_centrality"],
        "pagerank": data["pagerank"],
    }
