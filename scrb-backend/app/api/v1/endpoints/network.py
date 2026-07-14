from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.agents.network_agent.network_agent import NetworkAgent
from app.services.graph.graph_service import GraphService
from app.core.security import get_current_user
from app.core.permissions import require_permission, verify_district_access
from app.core.rbac import Permission, check_permission
from app.utils.masking import mask_name

router = APIRouter()


@router.get("/")
async def get_network(
    district: str | None = None,
    crime_type: str | None = None,
    police_station: str | None = None,
    time_period: str | None = None,
    focus_id: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get the criminal network graph, optionally filtered and centered/focused on an entity.
    Injects nodes and links directly at top-level for frontend ForceGraph2D.
    """
    # Enforce permission
    check_perm = require_permission(Permission.CRIMINAL_NETWORK)
    await check_perm(current_user)

    # ABAC: Enforce district access containment
    allowed_district = verify_district_access(current_user, district)

    agent = NetworkAgent()
    data = await agent.analyze_network(
        db,
        district=allowed_district,
        crime_type=crime_type,
        police_station=police_station,
        time_period=time_period,
        focus_id=focus_id,
    )

    # Sensitive data masking: mask victim names and accused names if no sensitive access
    has_sensitive_access = check_permission(current_user["role"], Permission.SENSITIVE_CASE_ACCESS)
    if not has_sensitive_access:
        for node in data.get("graph", {}).get("nodes", []):
            if node.get("kind") in ("accused", "victim"):
                node["label"] = mask_name(node["label"])
        for offender in data.get("repeat_offenders", []):
            offender["name"] = mask_name(offender["name"])

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


@router.get("/expand")
async def expand_node(
    node_id: str,
    kind: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get 1-degree neighbors of a node for lazy-loading.
    """
    check_perm = require_permission(Permission.CRIMINAL_NETWORK)
    await check_perm(current_user)

    service = GraphService(db)
    data = await service.get_node_expansion_data(node_id, kind)

    # Mask if necessary
    has_sensitive_access = check_permission(current_user["role"], Permission.SENSITIVE_CASE_ACCESS)
    if not has_sensitive_access:
        for node in data.get("nodes", []):
            if node.get("kind") in ("accused", "victim"):
                node["label"] = mask_name(node["label"])

    return data


@router.get("/accused/{id}")
async def get_accused_network(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get 1-degree network subgraph centered on a specific accused person.
    """
    check_perm = require_permission(Permission.CRIMINAL_NETWORK)
    await check_perm(current_user)

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

    # ABAC: check district access if the node has one in metadata
    district = accused_node.get("metadata", {}).get("district")
    if district:
        verify_district_access(current_user, district)

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

    # Mask if necessary
    has_sensitive_access = check_permission(current_user["role"], Permission.SENSITIVE_CASE_ACCESS)
    if not has_sensitive_access:
        for node in filtered_nodes:
            if node.get("kind") in ("accused", "victim"):
                node["label"] = mask_name(node["label"])
        if accused_node:
            accused_node["label"] = mask_name(accused_node["label"])
        if offender_info:
            offender_info["name"] = mask_name(offender_info["name"])

    return {
        "nodes": filtered_nodes,
        "links": connected_links,
        "accused": accused_node,
        "repeat_offender_info": offender_info,
    }


@router.get("/case/{id}")
async def get_case_network(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get 1-degree network subgraph centered on a specific Case.
    """
    check_perm = require_permission(Permission.CRIMINAL_NETWORK)
    await check_perm(current_user)

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

    # ABAC: Check district
    district = case_node.get("metadata", {}).get("district")
    if district:
        verify_district_access(current_user, district)

    target_id = case_node["id"]
    connected_nodes = {target_id}
    connected_links = []

    for link in links:
        if link["source"] == target_id or link["target"] == target_id:
            connected_links.append(link)
            connected_nodes.add(link["source"])
            connected_nodes.add(link["target"])

    filtered_nodes = [n for n in nodes if n["id"] in connected_nodes]

    # Mask if necessary
    has_sensitive_access = check_permission(current_user["role"], Permission.SENSITIVE_CASE_ACCESS)
    if not has_sensitive_access:
        for node in filtered_nodes:
            if node.get("kind") in ("accused", "victim"):
                node["label"] = mask_name(node["label"])

    return {
        "nodes": filtered_nodes,
        "links": connected_links,
        "case": case_node,
    }


@router.get("/community")
async def get_network_communities(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get criminal gang communities detected via modularity.
    """
    # Requires GANG_DETECTION permission
    check_perm = require_permission(Permission.GANG_DETECTION)
    await check_perm(current_user)

    service = GraphService(db)
    data = await service.get_criminal_network_data()
    return {"communities": data["communities"]}


@router.get("/repeat-offenders")
async def get_repeat_offenders(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get list of repeat offenders with computed risk scores.
    """
    check_perm = require_permission(Permission.CRIMINAL_NETWORK)
    await check_perm(current_user)

    service = GraphService(db)
    data = await service.get_criminal_network_data()

    # Mask if necessary
    has_sensitive_access = check_permission(current_user["role"], Permission.SENSITIVE_CASE_ACCESS)
    offenders = data["repeat_offenders"]
    if not has_sensitive_access:
        for o in offenders:
            o["name"] = mask_name(o["name"])

    return {"repeat_offenders": offenders}


@router.get("/analytics")
async def get_network_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get detailed graph centrality and structural density analytics.
    """
    check_perm = require_permission(Permission.CRIMINAL_NETWORK)
    await check_perm(current_user)

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
