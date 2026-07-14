import asyncio
import sys
import pytest
from unittest.mock import MagicMock, patch

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import SessionLocal

# Import modules to test
from app.services.analytics.analytics_utils import (
    haversine,
    perform_dbscan_clustering,
    calculate_forecast,
    detect_anomalies
)
from app.services.analytics.analytics_service import AnalyticsService
from app.agents.pattern_agent.pattern_agent import PatternAgent

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def db_session():
    async with SessionLocal() as session:
        yield session


# ─── Unit Tests for Math & Algorithms ────────────────────────────────────────

def test_haversine_distance():
    # Test distance between Whitefield PS and Koramangala PS (~4.8 km)
    dist = haversine(12.9716, 77.5946, 12.9348, 77.6189)
    assert 4.0 <= dist <= 6.0



def test_dbscan_clustering():
    # Construct test coordinates forming 2 clusters and 1 noise point
    # Cluster 1: Near Bengaluru (3 points)
    # Cluster 2: Near Mysuru (2 points)
    # Noise: Far away (1 point)
    test_coords = [
        {"latitude": 12.9716, "longitude": 77.5946, "crime_type": "Theft", "gravity": 2, "district": "Bengaluru Urban"},
        {"latitude": 12.9720, "longitude": 77.5950, "crime_type": "Theft", "gravity": 3, "district": "Bengaluru Urban"},
        {"latitude": 12.9710, "longitude": 77.5940, "crime_type": "Robbery", "gravity": 1, "district": "Bengaluru Urban"},
        
        {"latitude": 12.3051, "longitude": 76.6552, "crime_type": "Cyber Fraud", "gravity": 2, "district": "Mysuru"},
        {"latitude": 12.3060, "longitude": 76.6560, "crime_type": "Cyber Fraud", "gravity": 2, "district": "Mysuru"},
        
        {"latitude": 15.0000, "longitude": 74.0000, "crime_type": "Murder", "gravity": 3, "district": "Belagavi"}  # Noise
    ]
    
    # Run DBSCAN with eps = 10km, min_samples = 2
    clusters = perform_dbscan_clustering(test_coords, eps_km=10.0, min_samples=2)
    
    assert len(clusters) == 2
    # First cluster should be Bengaluru Urban (3 points)
    assert clusters[0]["cases"] == 3
    assert clusters[0]["district"] == "Bengaluru Urban"
    assert clusters[0]["dominant"] == "Theft"
    
    # Second cluster should be Mysuru (2 points)
    assert clusters[1]["cases"] == 2
    assert clusters[1]["district"] == "Mysuru"


def test_linear_regression_forecasting():
    # Test linear trend: 10, 20, 30, 40, 50
    history = [10, 20, 30, 40, 50]
    res = calculate_forecast(history)
    assert res["prediction"] == 60.0  # (next term)
    assert res["confidence"] > 0.90
    assert res["method"] == "linear_regression"


def test_anomaly_detection_z_score():
    # Stable counts with a massive spike at the end
    history = [10, 11, 10, 12, 10, 11, 10, 45]
    dates = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug"]
    
    anomalies = detect_anomalies(history, dates)
    assert len(anomalies) == 1
    assert anomalies[0]["time_period"] == "Aug"
    assert anomalies[0]["count"] == 45
    assert anomalies[0]["z_score"] > 2.0


# ─── Integration Tests with Database ──────────────────────────────────────────

async def test_analytics_service_trends(db_session: AsyncSession):
    service = AnalyticsService(db_session)
    trends = await service.get_trends()
    
    assert "time_series" in trends
    assert "top_crimes" in trends
    assert "district_ranking" in trends
    assert trends["total_cases"] > 0


async def test_analytics_service_hotspots(db_session: AsyncSession):
    service = AnalyticsService(db_session)
    hotspots = await service.get_hotspots()
    
    assert "dbscan_clusters" in hotspots
    assert "district_hotspots" in hotspots
    assert len(hotspots["district_hotspots"]) > 0


async def test_analytics_service_distribution(db_session: AsyncSession):
    service = AnalyticsService(db_session)
    dist = await service.get_distribution()
    
    assert "status_breakdown" in dist
    assert "temporal_distribution" in dist
    assert "demographics" in dist
    assert "crime_heat_index" in dist
    assert len(dist["demographics"]["byAge"]) > 0


# ─── Integration Test for PatternAgent and LLM ───────────────────────────────

@patch("app.services.llm.llm_service.genai.Client")
async def test_pattern_agent_pipeline_success(mock_genai, db_session: AsyncSession):

    # Mock Gemini provider response
    mock_client = MagicMock()
    mock_genai.return_value = mock_client
    
    mock_response = MagicMock()
    mock_candidate = MagicMock()
    mock_candidate.content.parts = [
        MagicMock(text="Mysuru district has experienced an increase in vehicle theft. DBSCAN identified emerging hotspots.")
    ]
    mock_candidate.finish_reason = "STOP"
    mock_response.candidates = [mock_candidate]
    mock_response.usage_metadata = MagicMock(
        prompt_token_count=100, candidates_token_count=50
    )
    mock_client.models.generate_content.return_value = mock_response
    
    agent = PatternAgent()
    res = await agent.analyze_patterns(db_session)
    
    assert res["status"] == "success"
    assert "details" in res
    assert "trends" in res["details"]
    assert "hotspots" in res["details"]
    assert "summary" in res
    assert "vehicle theft" in res["summary"].lower()
