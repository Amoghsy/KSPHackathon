import networkx as nx
from app.agents.network_agent.network_models import GraphResponse, LinkModel, NodeModel


class NetworkResponseFormatter:
    """
    Formatter class that maps NetworkX structures (Graphs, DiGraphs)
    to frontend-compliant GraphResponse Pydantic schemas.
    """

    @staticmethod
    def format_graph(G: nx.Graph | nx.DiGraph) -> GraphResponse:
        """Transforms a NetworkX graph into a serialized GraphResponse."""
        nodes = []
        for node_id, data in G.nodes(data=True):
            # Fallback kind to location if not provided
            kind = data.get("kind", "location")

            # Extract any bank information for accounts
            metadata = data.get("metadata", {}).copy()
            if "bank" in data:
                metadata["bank"] = data["bank"]

            nodes.append(
                NodeModel(
                    id=node_id,
                    label=data.get("label", node_id),
                    kind=kind,
                    metadata=metadata,
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
