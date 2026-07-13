import logging
from sqlalchemy.ext.asyncio import AsyncSession
import networkx as nx

from app.services.graph.graph_repository import GraphRepository
from app.services.graph.graph_cache import GraphCache
from app.agents.network_agent.graph_builder import GraphBuilder
from app.agents.network_agent.graph_analyzer import GraphAnalyzer
from app.agents.network_agent.network_response import NetworkResponseFormatter

logger = logging.getLogger(__name__)


class GraphService:
    """
    Orchestration service for building, analyzing, and caching graphs.
    Reused by NetworkAgent, Financial endpoints, and future agents.
    """

    def __init__(self, db: AsyncSession):
        self.repository = GraphRepository(db)
        self.cache = GraphCache()

    async def get_criminal_network_data(
        self,
        district: str | None = None,
        crime_type: str | None = None,
        police_station: str | None = None,
        time_period: str | None = None,
        focus_id: str | None = None,
    ) -> dict:
        """
        Retrieves the criminal network graph and analytics.
        Uses Redis cache if available, else builds from PostgreSQL.
        """
        filters = {
            "district": district,
            "crime_type": crime_type,
            "police_station": police_station,
            "time_period": time_period,
            "focus_id": focus_id,
        }

        # Check Cache
        cached_data = await self.cache.get("criminal_network", filters)
        if cached_data:
            return cached_data

        # 1. Fetch live data
        cases = await self.repository.get_filtered_cases(
            district=district,
            crime_type=crime_type,
            police_station=police_station,
            time_period=time_period,
        )
        case_ids = [c.case_master_id for c in cases]

        accused = await self.repository.get_accused_for_cases(case_ids)
        accused_ids = []
        for a in accused:
            accused_ids.append(a.accused_master_id)

        victims = await self.repository.get_victims_for_cases(case_ids)
        transactions = await self.repository.get_financial_transactions(
            case_ids=case_ids, accused_ids=accused_ids
        )

        from app.services.graph.graph_utils import normalize_name

        # 2. Build graph using NetworkX
        G_full = GraphBuilder.build_criminal_network(
            cases, accused, victims, transactions
        )

        # 2.5 Subgraph Extraction (Focused Investigation Graphs)
        center_node = None
        focus_reason = ""

        # First priority: explicit focus_id
        if focus_id:
            focus_id_clean = focus_id.strip()
            if focus_id_clean in G_full:
                center_node = focus_id_clean
                lbl = G_full.nodes[focus_id_clean].get("label", focus_id_clean)
                kind = G_full.nodes[focus_id_clean].get("kind", "entity")
                focus_reason = f"Focused investigation on {kind}: {lbl} ({focus_id_clean})"
            else:
                # Search by label or metadata
                for node, ndata in G_full.nodes(data=True):
                    lbl = ndata.get("label", "")
                    kind = ndata.get("kind", "")
                    meta = ndata.get("metadata", {})
                    if (
                        focus_id_clean.lower() in lbl.lower()
                        or focus_id_clean.lower() == str(node).lower()
                        or focus_id_clean.lower() == str(meta.get("person_id", "")).lower()
                        or focus_id_clean.lower() == str(meta.get("case_no", "")).lower()
                        or focus_id_clean.lower() == str(meta.get("crime_no", "")).lower()
                    ):
                        center_node = node
                        focus_reason = f"Focused investigation on {kind}: {lbl}"
                        break

        # Second priority: filter-based center node (if no focus_id is provided but filters exist)
        if not center_node:
            if police_station:
                for node, ndata in G_full.nodes(data=True):
                    if (
                        ndata.get("kind") == "location"
                        and ndata.get("metadata", {}).get("type") == "police_station"
                        and police_station.lower() in ndata.get("label", "").lower()
                    ):
                        center_node = node
                        focus_reason = f"Focused investigation around Police Station: {ndata.get('label')}"
                        break
            
            if not center_node and district:
                dist_id = f"D_{normalize_name(district)}"
                if dist_id in G_full:
                    center_node = dist_id
                    focus_reason = f"Focused investigation on District: {district}"
                else:
                    for node, ndata in G_full.nodes(data=True):
                        if (
                            ndata.get("kind") == "location"
                            and ndata.get("metadata", {}).get("type") == "district"
                            and district.lower() in ndata.get("label", "").lower()
                        ):
                            center_node = node
                            focus_reason = f"Focused investigation on District: {ndata.get('label')}"
                            break

        # Third priority: if absolutely no filters and no focus_id, pick the highest risk/degree Accused
        if not center_node:
            accused_nodes = [
                n for n, ndata in G_full.nodes(data=True) if ndata.get("kind") == "accused"
            ]
            if accused_nodes:
                center_node = max(accused_nodes, key=lambda n: G_full.degree(n))
                lbl = G_full.nodes[center_node].get("label", "Unknown Accused")
                focus_reason = f"Centered investigation on top repeat offender: {lbl}"

        # Extract ego subgraph
        if center_node:
            kind = G_full.nodes[center_node].get("kind")
            meta_type = G_full.nodes[center_node].get("metadata", {}).get("type", "")
            
            # Districts get a radius of 3 (District -> Police Stations -> Cases -> Accused)
            # Other nodes (Accused, Case) get radius of 2 (e.g. Accused -> Case -> Victim/PS)
            radius = 3 if (kind == "location" and meta_type == "district") else 2
            G = nx.ego_graph(G_full, center_node, radius=radius)
        else:
            G = G_full
            focus_reason = "Displaying global criminal network graph."

        # 3. Calculate centralities
        centrality = GraphAnalyzer.calculate_centrality(G)

        # 4. Detect Communities (Gangs)
        communities = GraphAnalyzer.detect_communities(G, centrality["pagerank"])

        # 5. Detect Repeat Offenders
        repeat_offenders = GraphAnalyzer.detect_repeat_offenders(
            G, centrality["degree"]
        )

        # 6. Format Graph Response
        formatted_graph = NetworkResponseFormatter.format_graph(G)

        # 7. Find Bridge Nodes and Most Connected (Degree > mean)
        node_degrees = dict(G.degree())
        degree_values = list(node_degrees.values())
        avg_degree = sum(degree_values) / len(degree_values) if degree_values else 0.0

        most_connected = [
            G.nodes[node].get("label", node)
            for node, deg in node_degrees.items()
            if deg > avg_degree and G.nodes[node].get("kind") == "accused"
        ]

        sorted_bet = sorted(
            centrality["betweenness"].items(), key=lambda x: x[1], reverse=True
        )
        bridge_nodes = [
            G.nodes[node].get("label", node)
            for node, bet in sorted_bet[:5]
            if bet > 0.0 and G.nodes[node].get("kind") == "accused"
        ]

        # 8. Assemble results
        results = {
            "graph": formatted_graph.model_dump(),
            "degree_centrality": centrality["degree"],
            "betweenness_centrality": centrality["betweenness"],
            "closeness_centrality": centrality["closeness"],
            "pagerank": centrality["pagerank"],
            "communities": communities,
            "repeat_offenders": repeat_offenders,
            "density": round(nx.density(G), 5),
            "node_count": G.number_of_nodes(),
            "edge_count": G.number_of_edges(),
            "most_connected": most_connected[:10],
            "bridge_nodes": bridge_nodes,
            "crime_clusters": [c["members"] for c in communities if len(c["members"]) > 1],
            "focus_reason": focus_reason,
            "center_node": center_node,
        }

        # Write to Cache
        await self.cache.set("criminal_network", filters, results)

        return results


    async def get_financial_network_data(
        self,
        district: str | None = None,
        crime_type: str | None = None,
        police_station: str | None = None,
        time_period: str | None = None,
    ) -> dict:
        """
        Retrieves the financial network graph (accused, accounts, cases) and cycles.
        Uses Redis cache if available, else builds from PostgreSQL.
        """
        filters = {
            "district": district,
            "crime_type": crime_type,
            "police_station": police_station,
            "time_period": time_period,
        }

        # Check Cache
        cached_data = await self.cache.get("financial_network", filters)
        if cached_data:
            return cached_data

        # 1. Fetch filtered cases
        cases = await self.repository.get_filtered_cases(
            district=district,
            crime_type=crime_type,
            police_station=police_station,
            time_period=time_period,
        )
        case_ids = [c.case_master_id for c in cases]

        # Fetch connected transactions
        transactions = await self.repository.get_financial_transactions(
            case_ids=case_ids
        )

        # 2. Build financial graph using NetworkX
        G_fin = GraphBuilder.build_financial_network(transactions, cases)

        # 3. Detect financial patterns (cycles, high-value transfers, shared accounts)
        patterns = GraphAnalyzer.detect_financial_patterns(G_fin)

        # 4. Format Graph Response
        formatted_graph = NetworkResponseFormatter.format_graph(G_fin)

        # 5. Assemble results
        results = {
            "graph": formatted_graph.model_dump(),
            "patterns": patterns,
            "node_count": G_fin.number_of_nodes(),
            "edge_count": G_fin.number_of_edges(),
        }

        # Write to Cache
        await self.cache.set("financial_network", filters, results)

        return results
