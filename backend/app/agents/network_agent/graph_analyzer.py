import logging
import networkx as nx
from networkx.algorithms.community import greedy_modularity_communities

logger = logging.getLogger(__name__)


class GraphAnalyzer:
    """
    Service class executing NetworkX graph analytics algorithms.
    """

    @staticmethod
    def calculate_centrality(G: nx.Graph) -> dict:
        """
        Calculates Degree, Betweenness, Closeness, and PageRank centralities for all nodes.
        """
        if G.number_of_nodes() == 0:
            return {
                "degree": {},
                "betweenness": {},
                "closeness": {},
                "pagerank": {},
            }

        # 1. Degree Centrality
        deg = nx.degree_centrality(G)

        # 2. Betweenness Centrality
        try:
            bet = nx.betweenness_centrality(G)
        except Exception as exc:
            logger.warning("Betweenness calculation failed, using zeros: %s", exc)
            bet = {n: 0.0 for n in G.nodes}

        # 3. Closeness Centrality
        try:
            close = nx.closeness_centrality(G)
        except Exception as exc:
            logger.warning("Closeness calculation failed, using zeros: %s", exc)
            close = {n: 0.0 for n in G.nodes}

        # 4. PageRank Centrality
        try:
            pr = nx.pagerank(G, alpha=0.85)
        except Exception as exc:
            logger.warning("PageRank convergence failed (e.g. missing scipy), using Python power iteration: %s", exc)
            # Pure-python PageRank power iteration fallback to avoid requiring SciPy package
            n_count = G.number_of_nodes()
            if n_count == 0:
                pr = {}
            else:
                # Initialize uniform ranks
                pr = dict.fromkeys(G, 1.0 / n_count)
                p = dict.fromkeys(G, 1.0 / n_count)
                max_iter = 100
                tol = 1.0e-6
                for _ in range(max_iter):
                    xlast = pr
                    pr = dict.fromkeys(xlast, 0.0)
                    # Handle dangling nodes (nodes with out-degree 0 in directed, or degree 0 in undirected)
                    dangling_sum = sum(xlast[node] for node in xlast if G.degree(node) == 0)
                    for node in xlast:
                        deg = G.degree(node)
                        if deg > 0:
                            for neighbor in G[node]:
                                pr[neighbor] += 0.85 * xlast[node] / deg
                        pr[node] += (1.0 - 0.85) * p[node] + 0.85 * dangling_sum / n_count
                    # Check convergence
                    err = sum(abs(pr[node] - xlast[node]) for node in pr)
                    if err < tol:
                        break

        return {
            "degree": deg,
            "betweenness": bet,
            "closeness": close,
            "pagerank": pr,
        }

    @staticmethod
    def detect_communities(G: nx.Graph, pageranks: dict[str, float]) -> list[dict]:
        """
        Runs community detection on the Accused-only subgraph to detect criminal gangs.
        Uses Greedy Modularity community detection algorithm.
        """
        accused_nodes = [
            n for n, data in G.nodes(data=True) if data.get("kind") == "accused"
        ]
        if not accused_nodes:
            return []

        subgraph = G.subgraph(accused_nodes)

        if subgraph.number_of_edges() == 0:
            raw_communities = [{n} for n in accused_nodes]
        else:
            try:
                raw_communities = list(greedy_modularity_communities(subgraph))
            except Exception as exc:
                logger.warning(
                    "Greedy modularity failed, using connected components: %s", exc
                )
                raw_communities = list(nx.connected_components(subgraph))

        communities = []
        for idx, comm in enumerate(raw_communities):
            members = list(comm)
            if not members:
                continue

            # Leader is the member with the highest PageRank in the community
            leader_node = max(members, key=lambda m: pageranks.get(m, 0.0))
            leader_name = G.nodes[leader_node].get("label", leader_node)

            # Calculate internal connections count within the community
            comm_subgraph = G.subgraph(members)
            internal_edges = comm_subgraph.number_of_edges()

            # Confidence score based on internal density
            num_members = len(members)
            if num_members > 1:
                possible_edges = num_members * (num_members - 1) / 2
                density = internal_edges / possible_edges if possible_edges > 0 else 0.0
                confidence = 0.5 + (density * 0.5)
            else:
                confidence = 1.0

            communities.append(
                {
                    "community_id": idx + 1,
                    "members": [G.nodes[m].get("label", m) for m in members],
                    "member_ids": members,
                    "leader": leader_name,
                    "confidence_score": round(confidence * 100, 2),
                    "internal_connections": internal_edges,
                }
            )

        return communities

    @staticmethod
    def detect_repeat_offenders(
        G: nx.Graph, degree_centralities: dict[str, float]
    ) -> list[dict]:
        """
        Detects repeat offenders using multi-FIR, multi-district, multi-station,
        and transaction history criteria.
        """
        offenders = []
        accused_nodes = [
            n for n, data in G.nodes(data=True) if data.get("kind") == "accused"
        ]

        for u in accused_nodes:
            name = G.nodes[u].get("label", u)

            # 1. Find connected Cases
            cases_u = [v for v in G.neighbors(u) if G.nodes[v].get("kind") == "case"]
            case_labels = [G.nodes[c].get("label", c) for c in cases_u]

            # 2. Extract locations (Stations, Districts) and crime types
            districts_u = set()
            stations_u = set()
            crime_types_u = set()

            for c in cases_u:
                for nbr in G.neighbors(c):
                    nbr_data = G.nodes[nbr]
                    if nbr_data.get("kind") == "location":
                        meta = nbr_data.get("metadata", {})
                        nbr_type = meta.get("type")
                        if nbr_type == "police_station":
                            stations_u.add(nbr_data.get("label", nbr))
                            if meta.get("district"):
                                districts_u.add(meta.get("district"))
                        elif nbr_type == "crime_type":
                            crime_types_u.add(nbr_data.get("label", nbr))

            # 3. Find known associates (other accused nodes sharing co-offending links)
            associates = [
                G.nodes[v].get("label", v)
                for v in G.neighbors(u)
                if G.nodes[v].get("kind") == "accused"
            ]

            crime_count = len(cases_u)
            num_districts = len(districts_u)
            num_stations = len(stations_u)
            num_crime_categories = len(crime_types_u)

            # Check financial links count
            financial_links_count = 0
            for v in G.neighbors(u):
                if G.nodes[v].get("kind") == "accused":
                    edge_data = G[u][v]
                    if "financial transaction" in edge_data.get("label", ""):
                        financial_links_count += 1

            # Criteria: 3+ FIRs OR cases in multiple districts OR multiple stations
            # OR has financial links OR multiple crime categories
            is_repeat = (
                crime_count >= 3
                or num_districts > 1
                or num_stations > 1
                or num_crime_categories > 1
                or financial_links_count > 0
            )

            if is_repeat:
                # Risk score out of 100
                risk_score = (
                    (crime_count * 15)
                    + (num_districts * 15)
                    + (num_stations * 10)
                    + (num_crime_categories * 10)
                    + (financial_links_count * 15)
                )
                risk_score = min(100.0, float(risk_score))

                offenders.append(
                    {
                        "id": u,
                        "name": name,
                        "crime_count": crime_count,
                        "cases": case_labels,
                        "risk_score": risk_score,
                        "network_degree": round(degree_centralities.get(u, 0.0), 4),
                        "known_associates": associates,
                    }
                )

        # Sort repeat offenders by risk score descending
        offenders.sort(key=lambda o: o["risk_score"], reverse=True)
        return offenders

    @staticmethod
    def detect_financial_patterns(G_fin: nx.DiGraph) -> dict:
        """
        Runs financial intelligence algorithms on the directed financial transaction graph.
        Detects circular flow cycles, high-value transfers, and shared account owners.
        """
        patterns = {
            "circular_flows": [],
            "high_value_transfers": [],
            "shared_accounts": [],
        }

        # 1. Circular Flow Detection (Simple Cycles)
        account_nodes = [
            n for n, data in G_fin.nodes(data=True) if data.get("kind") == "account"
        ]
        if len(account_nodes) >= 2:
            G_accounts = nx.DiGraph()
            for u, v, edge_data in G_fin.edges(data=True):
                if (
                    G_fin.nodes[u].get("kind") == "account"
                    and G_fin.nodes[v].get("kind") == "account"
                ):
                    G_accounts.add_edge(u, v, **edge_data)

            try:
                cycles = list(nx.simple_cycles(G_accounts))
                for cycle in cycles:
                    if len(cycle) >= 2:
                        flow_labels = [
                            G_fin.nodes[acc].get("label", acc) for acc in cycle
                        ] + [G_fin.nodes[cycle[0]].get("label", cycle[0])]
                        patterns["circular_flows"].append(
                            {
                                "flow": " -> ".join(flow_labels),
                                "accounts": cycle,
                                "length": len(cycle),
                            }
                        )

            except Exception as exc:  # noqa: BLE001
                logger.warning("Error running simple_cycles: %s", exc)

        # 2. Shared Accounts (Accounts with >1 owner)
        for node in account_nodes:
            owners = [
                u
                for u, v, d in G_fin.in_edges(node, data=True)
                if d.get("relationship") == "owns"
            ]
            if len(owners) > 1:
                patterns["shared_accounts"].append(
                    {
                        "account": node,
                        "label": G_fin.nodes[node].get("label", node),
                        "owners": [G_fin.nodes[o].get("label", o) for o in owners],
                    }
                )

        # 3. High Value & Suspicious Transfers
        for u, v, data in G_fin.edges(data=True):
            if data.get("relationship") == "transfer":
                amount = data.get("amount", 0.0)
                if amount > 300000.0 or data.get("suspicious"):
                    patterns["high_value_transfers"].append(
                        {
                            "source": G_fin.nodes[u].get("label", u),
                            "target": G_fin.nodes[v].get("label", v),
                            "amount": amount,
                            "suspicious": data.get("suspicious", False),
                            "reason": data.get("reason"),
                        }
                    )

        return patterns
