import pytest
from app.agents.risk_agent.risk_scoring import RiskScoringEngine
from app.agents.risk_agent.behavioral_tagging import BehavioralTagger
from app.services.forecasting.arima_model import forecast_arima_or_fallback

def test_risk_scoring_engine_low():
    # Test low risk calculation
    score, factors, level = RiskScoringEngine.calculate_score(
        case_count=1,
        max_gravity_offence_id=1,
        unique_districts_count=1,
        network_degree=0,
        transaction_count=0,
        suspicious_transaction_count=0,
        crime_types_count=1
    )
    assert level == "LOW"
    assert score == 2.0  # gravity=2.0 (low offence), others 0
    assert len(factors) == 7

def test_risk_scoring_engine_critical():
    # Test high case counts and severity
    score, factors, level = RiskScoringEngine.calculate_score(
        case_count=6,  # repeat=25
        max_gravity_offence_id=4,  # severity=15
        unique_districts_count=4,  # cross_district=15
        network_degree=10,  # network=15
        transaction_count=4,  # financial=15
        suspicious_transaction_count=2,  # suspicious=10
        crime_types_count=3  # diversity=5
    )
    # total score: 25 + 15 + 15 + 15 + 15 + 10 + 5 = 100
    assert level == "CRITICAL"
    assert score == 100.0

def test_behavioral_tagger():
    tags = BehavioralTagger.generate_tags(
        case_count=4,
        unique_districts_count=3,
        network_degree=6,
        transaction_count=2,
        suspicious_transaction_count=1,
        crime_types_count=2,
        recently_active=True,
        is_in_community=True,
        districts=["Mysuru", "Mandya", "Bengaluru"]
    )
    codes = {t.code for t in tags}
    assert "REPEAT_OFFENDER" in codes
    assert "CROSS_DISTRICT" in codes
    assert "HIGHLY_CONNECTED" in codes
    assert "NETWORK_SIGNIFICANT" in codes
    assert "FINANCIAL_LINKED" in codes
    assert "SUSPICIOUS_FINANCIAL_ACTIVITY" in codes
    assert "MULTI_CRIME_PATTERN" in codes
    assert "RECENTLY_ACTIVE" in codes
    assert "POSSIBLE_GANG_ASSOCIATION" in codes

def test_forecasting_fallback():
    # Test WMA fallback when history is short
    history = [10, 20, 30]
    res = forecast_arima_or_fallback(history, periods=2)
    assert res["method"] == "weighted_moving_average"
    assert len(res["forecast"]) == 2
    assert res["confidence"] == 0.65
