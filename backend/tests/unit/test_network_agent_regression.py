import pytest
import networkx as nx
import logging
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.agents.network_agent.graph_analyzer import GraphAnalyzer
from app.services.graph.graph_service import GraphService
from app.core.security import get_current_user
from app.core.rbac import Permission

# Configure logging to check for warnings
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Setup pytestmark for anyio
pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def supervisor_user():
    return {
        "id": 3,
        "username": "supervisor_ramesh",
        "role": "SUPERVISOR",
        "districts": "Bengaluru Urban,Mysuru,Tumakuru"
    }


def test_calculate_centrality_normal_and_fallback():
    # 1. Normal graph
    G = nx.Graph()
    G.add_edge("A", "B")
    G.add_edge("B", "C")
    
    # Calculate with default (which falls back to pure-Python pagerank if scipy is missing)
    centrality = GraphAnalyzer.calculate_centrality(G)
    assert isinstance(centrality, dict)
    assert "degree" in centrality
    assert isinstance(centrality["degree"], dict)
    assert centrality["degree"]["B"] == 1.0  # Normalized degree centrality for central node in line graph of 3 nodes
    
    # 2. Test explicit PageRank fallback path by mocking nx.pagerank to fail
    with patch("networkx.pagerank", side_effect=Exception("missing scipy simulated exception")):
        centrality_fallback = GraphAnalyzer.calculate_centrality(G)
        
        # Verify that degree centrality is a dictionary and NOT an integer
        assert isinstance(centrality_fallback, dict)
        assert "degree" in centrality_fallback
        assert isinstance(centrality_fallback["degree"], dict)
        assert centrality_fallback["degree"]["B"] == 1.0
        
        # Verify pagerank fallback computed successfully
        assert "pagerank" in centrality_fallback
        assert isinstance(centrality_fallback["pagerank"], dict)
        assert len(centrality_fallback["pagerank"]) == 3


def test_detect_repeat_offenders_normal():
    G = nx.Graph()
    # Add accused nodes
    G.add_node("U1", kind="accused", label="Ramesh")
    G.add_node("U2", kind="accused", label="Suresh")
    
    # Add case nodes
    G.add_node("C1", kind="case", label="FIR-001")
    G.add_node("C2", kind="case", label="FIR-002")
    G.add_node("C3", kind="case", label="FIR-003")
    
    # Add locations
    G.add_node("L1", kind="location", label="Mysuru", metadata={"type": "police_station", "district": "Mysuru"})
    G.add_node("L2", kind="location", label="Mandya", metadata={"type": "police_station", "district": "Mandya"})
    
    # Connect U1 to 3 cases (satisfying repeat offender criteria >= 3 cases)
    G.add_edge("U1", "C1")
    G.add_edge("U1", "C2")
    G.add_edge("U1", "C3")
    
    # Connect cases to locations
    G.add_edge("C1", "L1")
    G.add_edge("C2", "L2")
    
    # Connect U2 to 1 case (not repeat offender on case count alone, and not multi-district)
    G.add_edge("U2", "C1")
    
    degree_centrality = {"U1": 0.8, "U2": 0.2}
    
    offenders = GraphAnalyzer.detect_repeat_offenders(G, degree_centrality)
    
    assert len(offenders) == 1
    assert offenders[0]["id"] == "U1"
    assert offenders[0]["name"] == "Ramesh"
    assert offenders[0]["crime_count"] == 3
    assert offenders[0]["network_degree"] == 0.8


def test_detect_repeat_offenders_empty_and_defensive():
    # Empty Graph
    G_empty = nx.Graph()
    offenders_empty = GraphAnalyzer.detect_repeat_offenders(G_empty, {})
    assert offenders_empty == []
    
    # None Graph
    offenders_none_graph = GraphAnalyzer.detect_repeat_offenders(None, {})
    assert offenders_none_graph == []
    
    # None centrality
    G = nx.Graph()
    G.add_node("U1", kind="accused", label="Ramesh")
    G.add_node("C1", kind="case", label="FIR-001")
    G.add_edge("U1", "C1")
    # satisfies repeat offender if we give multi-district/station or financial links
    # Let's add location links
    G.add_node("L1", kind="location", label="Mysuru", metadata={"type": "police_station", "district": "Mysuru"})
    G.add_node("L2", kind="location", label="Mandya", metadata={"type": "police_station", "district": "Mandya"})
    G.add_edge("C1", "L1")
    # To have another district, we need another case or connection
    G.add_node("C2", kind="case", label="FIR-002")
    G.add_edge("U1", "C2")
    G.add_edge("C2", "L2")
    
    # degree_centralities is None
    offenders_none_cent = GraphAnalyzer.detect_repeat_offenders(G, None)
    assert len(offenders_none_cent) == 1
    assert offenders_none_cent[0]["network_degree"] == 0.0
    
    # degree_centralities is malformed (e.g. an integer, like the bug)
    offenders_int_cent = GraphAnalyzer.detect_repeat_offenders(G, 42)
    assert len(offenders_int_cent) == 1
    assert offenders_int_cent[0]["network_degree"] == 0.0

    # degree_centralities has string values (malformed values)
    offenders_str_val = GraphAnalyzer.detect_repeat_offenders(G, {"U1": "invalid-float-val"})
    assert len(offenders_str_val) == 1
    assert offenders_str_val[0]["network_degree"] == 0.0


def test_api_v1_network_endpoint_success(supervisor_user):
    client = TestClient(app)
    
    # Setup test graph
    G = nx.Graph()
    G.add_node("U1", kind="accused", label="Ramesh")
    G.add_node("C1", kind="case", label="FIR-001")
    G.add_edge("U1", "C1")
    
    # Mock GraphBuilder.build_criminal_network to return our custom graph
    with patch("app.services.graph.graph_service.GraphBuilder.build_criminal_network", return_value=G), \
         patch("app.services.graph.graph_service.GraphRepository") as mock_repo_class:
        
        # Mock repository methods
        mock_repo = mock_repo_class.return_value
        mock_repo.get_filtered_cases = AsyncMock(return_value=[])
        mock_repo.get_accused_for_cases = AsyncMock(return_value=[])
        mock_repo.get_victims_for_cases = AsyncMock(return_value=[])
        mock_repo.get_financial_transactions = AsyncMock(return_value=[])
        
        # Override current user dependency to supervisor
        app.dependency_overrides[get_current_user] = lambda: supervisor_user
        
        # Explicitly patch pagerank to fail to ensure fallback flow executes inside the API request
        with patch("networkx.pagerank", side_effect=Exception("missing scipy")):
            try:
                response = client.get("/api/v1/network/")
                assert response.status_code == 200
                data = response.json()
                
                # Check response shape is valid JSON and matches expected fields
                assert "nodes" in data
                assert "links" in data
                assert "repeat_offenders" in data
                assert "communities" in data
                
            finally:
                app.dependency_overrides.clear()
