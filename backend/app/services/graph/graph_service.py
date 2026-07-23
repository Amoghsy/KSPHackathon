import logging
import traceback
from fastapi import HTTPException
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
        authorized_districts: list[str] | None = None,
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

        # 0. Check if Level 1 Dashboard View (no focus ID, no active filters)
        is_level1 = not (
            (district and district != "All")
            or (crime_type and crime_type != "All")
            or (police_station and police_station != "All")
            or (time_period and time_period != "All")
            or focus_id
        )
        if is_level1:
            if authorized_districts is None:
                cached_stats = await self.cache.get("dashboard_stats", {})
                if cached_stats:
                    return {
                        "graph": {"nodes": [], "links": []},
                        **cached_stats
                    }

            # If not cached, let's load all cases to compute stats
            cases = await self.repository.get_filtered_cases(authorized_districts=authorized_districts)
            case_ids = [c.case_master_id for c in cases]
            accused = await self.repository.get_accused_for_cases(case_ids)
            accused_ids = [a.accused_master_id for a in accused]
            victims = await self.repository.get_victims_for_cases(case_ids)
            transactions = await self.repository.get_financial_transactions(
                case_ids=case_ids, accused_ids=accused_ids
            )

            try:
                G_full = GraphBuilder.build_criminal_network(cases, accused, victims, transactions)
            except Exception as exc:
                logger.error("Error in stage 'Graph Construction': %s: %s\nTraceback:\n%s", type(exc).__name__, exc, traceback.format_exc())
                raise HTTPException(status_code=500, detail="Internal server error during graph analytics.")

            try:
                centrality = GraphAnalyzer.calculate_centrality(G_full)
            except Exception as exc:
                logger.error("Error in stage 'Centrality Calculation': %s: %s\nTraceback:\n%s", type(exc).__name__, exc, traceback.format_exc())
                raise HTTPException(status_code=500, detail="Internal server error during graph analytics.")

            try:
                communities = GraphAnalyzer.detect_communities(G_full, centrality["pagerank"])
            except Exception as exc:
                logger.error("Error in stage 'Community Detection': %s: %s\nTraceback:\n%s", type(exc).__name__, exc, traceback.format_exc())
                raise HTTPException(status_code=500, detail="Internal server error during graph analytics.")

            try:
                repeat_offenders = GraphAnalyzer.detect_repeat_offenders(G_full, centrality["degree"])
            except Exception as exc:
                logger.error("Error in stage 'Repeat Offender Detection': %s: %s\nTraceback:\n%s", type(exc).__name__, exc, traceback.format_exc())
                raise HTTPException(status_code=500, detail="Internal server error during graph analytics.")

            node_degrees = dict(G_full.degree())
            degree_values = list(node_degrees.values())
            avg_degree = sum(degree_values) / len(degree_values) if degree_values else 0.0

            most_connected = [
                G_full.nodes[node].get("label", node)
                for node, deg in node_degrees.items()
                if deg > avg_degree and G_full.nodes[node].get("kind") == "accused"
            ]

            sorted_bet = sorted(
                centrality["betweenness"].items(), key=lambda x: x[1], reverse=True
            )
            bridge_nodes = [
                G_full.nodes[node].get("label", node)
                for node, bet in sorted_bet[:5]
                if bet > 0.0 and G_full.nodes[node].get("kind") == "accused"
            ]

            station_nodes = [
                (node, deg) for node, deg in node_degrees.items()
                if G_full.nodes[node].get("kind") == "location" 
                and G_full.nodes[node].get("metadata", {}).get("type") == "police_station"
            ]
            most_connected_station = "Unknown Station"
            if station_nodes:
                best_station_node = max(station_nodes, key=lambda x: x[1])[0]
                most_connected_station = G_full.nodes[best_station_node].get("label", "Unknown Station")

            stats = {
                "degree_centrality": centrality["degree"],
                "betweenness_centrality": centrality["betweenness"],
                "closeness_centrality": centrality["closeness"],
                "pagerank": centrality["pagerank"],
                "communities": communities[:5],  # Top 5
                "repeat_offenders": repeat_offenders[:10],  # Top 10
                "density": round(nx.density(G_full), 5),
                "node_count": G_full.number_of_nodes(),
                "edge_count": G_full.number_of_edges(),
                "most_connected": most_connected[:10],
                "bridge_nodes": bridge_nodes,
                "crime_clusters": [c["members"] for c in communities if len(c["members"]) > 1],
                "most_connected_police_station": most_connected_station,
                "focus_reason": "Dashboard loaded. Choose investigation target.",
                "center_node": None,
            }
            if authorized_districts is None:
                await self.cache.set("dashboard_stats", {}, stats)
            return {
                "graph": {"nodes": [], "links": []},
                **stats
            }

        # Level 2: Target-focused Subgraph Extraction
        # Try to retrieve from Cache (resolve focus_kind first for cache key)
        cases_sample = []
        if focus_id:
            cases_sample = await self.repository.get_cases_by_focus_id(focus_id, authorized_districts=authorized_districts)
        if cases_sample:
            # We build a temp graph to figure out focus_kind for caching
            temp_G = GraphBuilder.build_criminal_network(cases_sample[:1], [], [], [])
            focus_clean = focus_id.strip()
            focus_kind = "target"
            if focus_clean in temp_G:
                focus_kind = temp_G.nodes[focus_clean].get("kind", "target")
            else:
                for n, d in temp_G.nodes(data=True):
                    if d.get("label", "").lower() == focus_clean.lower():
                        focus_kind = d.get("kind", "target")
                        break
            filters["focus_kind"] = focus_kind

        if authorized_districts is None:
            cached_data = await self.cache.get("criminal_network", filters)
            if cached_data:
                return cached_data

        # 1. Fetch live targeted data
        if focus_id:
            cases = await self.repository.get_cases_by_focus_id(focus_id, authorized_districts=authorized_districts)
            if district and district != "All":
                cases = [c for c in cases if c.police_station and c.police_station.district == district]
            if police_station and police_station != "All":
                cases = [c for c in cases if c.police_station and c.police_station.name == police_station]
            if crime_type and crime_type != "All":
                cases = [c for c in cases if c.crime_type and c.crime_type.name == crime_type]
        else:
            cases = await self.repository.get_filtered_cases(
                district=district,
                crime_type=crime_type,
                police_station=police_station,
                time_period=time_period,
                authorized_districts=authorized_districts,
            )

        case_ids = [c.case_master_id for c in cases]
        accused = await self.repository.get_accused_for_cases(case_ids)
        accused_ids = [a.accused_master_id for a in accused]
        victims = await self.repository.get_victims_for_cases(case_ids)
        transactions = await self.repository.get_financial_transactions(
            case_ids=case_ids, accused_ids=accused_ids
        )

        from app.services.graph.graph_utils import normalize_name

        # 2. Build graph using NetworkX
        G_full = GraphBuilder.build_criminal_network(
            cases, accused, victims, transactions
        )

        # 2.5 Resolve center node
        center_node = None
        focus_reason = ""

        if focus_id:
            focus_id_clean = focus_id.strip()
            if focus_id_clean in G_full:
                center_node = focus_id_clean
            else:
                for node, ndata in G_full.nodes(data=True):
                    lbl = ndata.get("label", "")
                    meta = ndata.get("metadata", {})
                    if (
                        focus_id_clean.lower() in lbl.lower()
                        or focus_id_clean.lower() == str(node).lower()
                        or focus_id_clean.lower() == str(meta.get("person_id", "")).lower()
                    ):
                        center_node = node
                        break

            if center_node:
                lbl = G_full.nodes[center_node].get("label", center_node)
                kind = G_full.nodes[center_node].get("kind", "entity")
                focus_reason = f"Focused investigation on {kind}: {lbl}"
            else:
                focus_reason = f"Focused investigation: {focus_id}"
        elif district and district != "All":
            dist_id = f"D_{normalize_name(district)}"
            if dist_id in G_full:
                center_node = dist_id
                focus_reason = f"Focused investigation on District: {district}"
        elif police_station and police_station != "All":
            for node, ndata in G_full.nodes(data=True):
                if (
                    ndata.get("kind") == "location"
                    and ndata.get("metadata", {}).get("type") == "police_station"
                    and police_station.lower() in ndata.get("label", "").lower()
                ):
                    center_node = node
                    focus_reason = f"Focused investigation around Police Station: {ndata.get('label')}"
                    break

        if not center_node and G_full.number_of_nodes() > 0:
            accused_nodes = [
                n for n, ndata in G_full.nodes(data=True) if ndata.get("kind") == "accused"
            ]
            if accused_nodes:
                center_node = max(accused_nodes, key=lambda n: G_full.degree(n))
                lbl = G_full.nodes[center_node].get("label", "Unknown Accused")
                focus_reason = f"Centered investigation on top repeat offender: {lbl}"

        # 3. Enforce Strict Graph Trimming limits (max 40 nodes, 75 edges)
        G = self._trim_graph(G_full, center_node, max_nodes=40, max_edges=75)

        # 4. Calculate centralities on trimmed graph
        try:
            centrality = GraphAnalyzer.calculate_centrality(G)
        except Exception as exc:
            logger.error("Error in stage 'Centrality Calculation': %s: %s\nTraceback:\n%s", type(exc).__name__, exc, traceback.format_exc())
            raise HTTPException(status_code=500, detail="Internal server error during graph analytics.")

        try:
            communities = GraphAnalyzer.detect_communities(G, centrality["pagerank"])
        except Exception as exc:
            logger.error("Error in stage 'Community Detection': %s: %s\nTraceback:\n%s", type(exc).__name__, exc, traceback.format_exc())
            raise HTTPException(status_code=500, detail="Internal server error during graph analytics.")

        try:
            repeat_offenders = GraphAnalyzer.detect_repeat_offenders(G, centrality["degree"])
        except Exception as exc:
            logger.error("Error in stage 'Repeat Offender Detection': %s: %s\nTraceback:\n%s", type(exc).__name__, exc, traceback.format_exc())
            raise HTTPException(status_code=500, detail="Internal server error during graph analytics.")

        # 5. Format Graph Response
        formatted_graph = NetworkResponseFormatter.format_graph(G, centrality, communities, repeat_offenders)

        # 6. Find Bridge Nodes and Most Connected
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

        # 7. Assemble results
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
        if authorized_districts is None:
            await self.cache.set("criminal_network", filters, results)
        return results

    def _trim_graph(self, G: nx.Graph, center_node: str | None, max_nodes: int = 40, max_edges: int = 75) -> nx.Graph:
        """Enforces limits on graph size prioritizing closeness to target node."""
        if G.number_of_nodes() <= max_nodes and G.number_of_edges() <= max_edges:
            return G

        # 1. Select the top nodes to keep
        if center_node and center_node in G:
            try:
                lengths = nx.single_source_shortest_path_length(G, center_node)
            except Exception:
                lengths = {n: 999 for n in G.nodes}
            deg_centrality = nx.degree_centrality(G)
            
            sorted_nodes = sorted(
                G.nodes,
                key=lambda n: (lengths.get(n, 999), -deg_centrality.get(n, 0.0))
            )
            nodes_to_keep = sorted_nodes[:max_nodes]
        else:
            deg_centrality = nx.degree_centrality(G)
            sorted_nodes = sorted(G.nodes, key=lambda n: -deg_centrality.get(n, 0.0))
            nodes_to_keep = sorted_nodes[:max_nodes]

        # Induced subgraph
        G_trimmed = G.subgraph(nodes_to_keep).copy()

        # 2. Trim edges if they exceed max_edges
        if G_trimmed.number_of_edges() > max_edges:
            sorted_edges = sorted(
                G_trimmed.edges(data=True),
                key=lambda e: e[2].get("weight", 1.0),
                reverse=True
            )
            G_trimmed.clear_edges()
            for u, v, data in sorted_edges[:max_edges]:
                G_trimmed.add_edge(u, v, **data)

        return G_trimmed

    async def get_node_expansion_data(self, node_id: str, kind: str, authorized_districts: list[str] | None = None) -> dict:
        """
        Retrieves 1-degree neighbors and links for a specific node for lazy loading.
        """
        # Fetch relevant cases for this node
        cases = await self.repository.get_cases_by_focus_id(node_id, authorized_districts=authorized_districts)
        case_ids = [c.case_master_id for c in cases]
        
        # Fetch accused, victims, transactions
        accused = await self.repository.get_accused_for_cases(case_ids)
        accused_ids = [a.accused_master_id for a in accused]
        victims = await self.repository.get_victims_for_cases(case_ids)
        transactions = await self.repository.get_financial_transactions(
            case_ids=case_ids, accused_ids=accused_ids
        )
        
        # Build network graph
        if kind == "account":
            G = GraphBuilder.build_financial_network(transactions, cases)
        else:
            G = GraphBuilder.build_criminal_network(cases, accused, victims, transactions)
            
        # Extract 1-degree neighborhood (ego graph radius=1)
        center_node = None
        if node_id in G:
            center_node = node_id
        else:
            # Fallback to label match
            for n, data in G.nodes(data=True):
                if data.get("label", "").lower() == node_id.lower():
                    center_node = n
                    break
                    
        if center_node:
            G_sub = nx.ego_graph(G, center_node, radius=1)
        else:
            G_sub = G
            
        # Calculate local centralities and format
        try:
            centrality = GraphAnalyzer.calculate_centrality(G_sub)
        except Exception as exc:
            logger.error("Error in stage 'Centrality Calculation': %s: %s\nTraceback:\n%s", type(exc).__name__, exc, traceback.format_exc())
            raise HTTPException(status_code=500, detail="Internal server error during graph analytics.")

        try:
            communities = GraphAnalyzer.detect_communities(G_sub, centrality["pagerank"])
        except Exception as exc:
            logger.error("Error in stage 'Community Detection': %s: %s\nTraceback:\n%s", type(exc).__name__, exc, traceback.format_exc())
            raise HTTPException(status_code=500, detail="Internal server error during graph analytics.")

        try:
            repeat_offenders = GraphAnalyzer.detect_repeat_offenders(G_sub, centrality["degree"])
        except Exception as exc:
            logger.error("Error in stage 'Repeat Offender Detection': %s: %s\nTraceback:\n%s", type(exc).__name__, exc, traceback.format_exc())
            raise HTTPException(status_code=500, detail="Internal server error during graph analytics.")
        
        formatted = NetworkResponseFormatter.format_graph(G_sub, centrality, communities, repeat_offenders)
        return formatted.model_dump()

    async def get_financial_network_data(
        self,
        district: str | None = None,
        crime_type: str | None = None,
        police_station: str | None = None,
        time_period: str | None = None,
        focus_id: str | None = None,
        authorized_districts: list[str] | None = None,
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
            "focus_id": focus_id,
        }

        # Check Cache
        if authorized_districts is None:
            cached_data = await self.cache.get("financial_network", filters)
            if cached_data:
                return cached_data

        # 1. Fetch filtered cases
        if focus_id:
            cases = await self.repository.get_cases_by_focus_id(focus_id, authorized_districts=authorized_districts)
            if district and district != "All":
                cases = [c for c in cases if c.police_station and c.police_station.district == district]
            if police_station and police_station != "All":
                cases = [c for c in cases if c.police_station and c.police_station.name == police_station]
            if crime_type and crime_type != "All":
                cases = [c for c in cases if c.crime_type and c.crime_type.name == crime_type]
        else:
            cases = await self.repository.get_filtered_cases(
                district=district,
                crime_type=crime_type,
                police_station=police_station,
                time_period=time_period,
                authorized_districts=authorized_districts,
            )
        case_ids = [c.case_master_id for c in cases]
        accused = await self.repository.get_accused_for_cases(case_ids)
        accused_ids = [a.accused_master_id for a in accused]

        # Fetch connected transactions
        transactions = await self.repository.get_financial_transactions(
            case_ids=case_ids, accused_ids=accused_ids
        )

        # 2. Build financial graph using NetworkX
        try:
            G_fin = GraphBuilder.build_financial_network(transactions, cases)
        except Exception as exc:
            logger.error("Error in stage 'Financial Graph Construction': %s: %s\nTraceback:\n%s", type(exc).__name__, exc, traceback.format_exc())
            raise HTTPException(status_code=500, detail="Internal server error during graph analytics.")

        # 3. Detect financial patterns (cycles, high-value transfers, shared accounts)
        try:
            patterns = GraphAnalyzer.detect_financial_patterns(G_fin)
        except Exception as exc:
            logger.error("Error in stage 'Financial Pattern Detection': %s: %s\nTraceback:\n%s", type(exc).__name__, exc, traceback.format_exc())
            raise HTTPException(status_code=500, detail="Internal server error during graph analytics.")

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
        if authorized_districts is None:
            await self.cache.set("financial_network", filters, results)

        return results
