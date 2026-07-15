from typing import Any
from pydantic import BaseModel


class NodeModel(BaseModel):
    id: str
    label: str
    kind: str  # 'accused', 'victim', 'location', 'case', 'account'
    metadata: dict[str, Any] = {}
    color: str | None = None
    val: float | None = None


class LinkModel(BaseModel):
    source: str
    target: str
    label: str | None = None
    weight: float | None = None
    amount: float | None = None
    suspicious: bool | None = None
    reason: str | None = None


class GraphResponse(BaseModel):
    nodes: list[NodeModel]
    links: list[LinkModel]


class OffenderModel(BaseModel):
    id: str
    name: str
    crime_count: int
    cases: list[str]
    risk_score: float
    network_degree: float
    known_associates: list[str]


class CommunityModel(BaseModel):
    community_id: int
    members: list[str]
    leader: str
    confidence_score: float


class AnalyticsModel(BaseModel):
    density: float
    node_count: int
    edge_count: int
    degree_centrality: dict[str, float]
    betweenness_centrality: dict[str, float]
    closeness_centrality: dict[str, float]
    pagerank: dict[str, float]
    most_connected: list[str]
    bridge_nodes: list[str]
    crime_clusters: list[list[str]]
    summary: str | None = None
