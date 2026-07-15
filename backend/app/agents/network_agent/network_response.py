import networkx as nx
from app.agents.network_agent.network_models import GraphResponse, LinkModel, NodeModel


class NetworkResponseFormatter:
    """
    Formatter class that maps NetworkX structures (Graphs, DiGraphs)
    to frontend-compliant GraphResponse Pydantic schemas.
    """

    @staticmethod
    def format_graph(
        G: nx.Graph | nx.DiGraph,
        centrality: dict | None = None,
        communities: list | None = None,
        repeat_offenders: list | None = None,
    ) -> GraphResponse:
        """Transforms a NetworkX graph into a serialized GraphResponse with computed sizes and colors."""
        from app.agents.network_agent.graph_analyzer import GraphAnalyzer

        if not centrality:
            centrality = GraphAnalyzer.calculate_centrality(G)
        if not communities:
            communities = GraphAnalyzer.detect_communities(G, centrality.get("pagerank", {}))
        if not repeat_offenders:
            repeat_offenders = GraphAnalyzer.detect_repeat_offenders(G, centrality.get("degree", {}))

        # Build community mappings
        node_to_community = {}
        leaders = set()
        for comm in communities:
            comm_id = comm.get("community_id")
            leader_name = comm.get("leader")
            for m_id in comm.get("member_ids", []):
                node_to_community[m_id] = comm_id
                # Match leader by label or ID
                if G.nodes[m_id].get("label") == leader_name or m_id == leader_name:
                    leaders.add(m_id)

        repeat_offender_ids = {o.get("id") for o in repeat_offenders}

        nodes = []
        for node_id, data in G.nodes(data=True):
            kind = data.get("kind", "location")
            metadata = data.get("metadata", {}).copy()
            if "bank" in data:
                metadata["bank"] = data["bank"]

            # 1. Size node by degree centrality
            # We scale the raw degree for a stable visual size
            raw_degree = G.degree(node_id) if hasattr(G, "degree") else 1
            node_size = min(25.0, max(4.0, 4.0 + raw_degree * 1.5))

            # 2. Color node by priority
            node_color = "#64748B"  # Default gray for Case/neutral
            if node_id in repeat_offender_ids:
                node_color = "#EF4444"  # Red for repeat offenders
            elif node_id in leaders:
                node_color = "#F97316"  # Orange for community leaders
            elif kind == "victim":
                node_color = "#10B981"  # Green for victims
            elif kind == "location" and metadata.get("type") == "police_station":
                node_color = "#3B82F6"  # Blue for police stations
            elif kind == "account":
                node_color = "#8B5CF6"  # Purple for financial accounts
            elif kind == "accused":
                comm_id = node_to_community.get(node_id)
                if comm_id:
                    # High quality community colors palette
                    COMMUNITY_COLORS = [
                        "#EC4899", "#06B6D4", "#14B8A6", "#10B981", "#6366F1",
                        "#8B5CF6", "#A855F7", "#F59E0B", "#EAB308", "#84CC16"
                    ]
                    node_color = COMMUNITY_COLORS[(comm_id - 1) % len(COMMUNITY_COLORS)]
                else:
                    node_color = "#1F3864"  # Default dark blue
            elif kind == "location":
                node_color = "#475569"  # Slate for other locations

            nodes.append(
                NodeModel(
                    id=node_id,
                    label=data.get("label", node_id),
                    kind=kind,
                    metadata=metadata,
                    color=node_color,
                    val=node_size,
                )
            )

        links = []
        for u, v, data in G.edges(data=True):
            links.append(
                LinkModel(
                    source=u,
                    target=v,
                    label=data.get("label"),
                    weight=data.get("weight"),
                    amount=data.get("amount"),
                    suspicious=data.get("suspicious"),
                    reason=data.get("reason"),
                )
            )

        return GraphResponse(nodes=nodes, links=links)
