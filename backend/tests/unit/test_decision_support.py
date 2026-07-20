import pytest
from app.agents.decision_support_agent.similar_case_search import SimilarityEngine
from app.agents.decision_support_agent.evidence_gap_analyzer import EvidenceGapAnalyzer
from app.agents.decision_support_agent.lead_generator import LeadGenerator

def test_similarity_engine_calculations():
    case_a = {
        "case_id": 1,
        "crime_type_id": 10,
        "crime_type": "Robbery",
        "crime_major_head_id": 2,
        "district": "Mysuru",
        "police_station_id": 5,
        "police_station": "Vijayanagar",
        "crime_registered_date": "2026-03-01T00:00:00",
        "latitude": 12.30,
        "longitude": 76.60,
        "accused": [{"person_id": "P101", "accused_name": "Ravi"}],
        "victims": [{"victim_name": "Suresh"}],
        "financial_transactions": [{"source_account": "ACC001", "destination_account": "ACC002"}]
    }

    # Highly similar case (identical type, accused, and district)
    case_b = {
        "case_id": 2,
        "crime_type_id": 10,
        "crime_type": "Robbery",
        "crime_major_head_id": 2,
        "district": "Mysuru",
        "police_station_id": 5,
        "police_station": "Vijayanagar",
        "crime_registered_date": "2026-03-05T00:00:00",
        "latitude": 12.31,
        "longitude": 76.61, # very close
        "accused": [{"person_id": "P101", "accused_name": "Ravi"}],
        "victims": [{"victim_name": "Suresh"}],
        "financial_transactions": [{"source_account": "ACC001", "destination_account": "ACC003"}]
    }

    res = SimilarityEngine.calculate_similarity(case_a, case_b)
    score = res["similarity_score"]
    reasons = res["reasons"]
    
    assert score > 80
    assert score <= 100
    assert any("Same crime type" in r for r in reasons)
    assert any("Shared accused" in r for r in reasons)

    # Completely unrelated case
    case_c = {
        "case_id": 3,
        "crime_type_id": 20,
        "crime_type": "Cyber Fraud",
        "crime_major_head_id": 5,
        "district": "Mandya",
        "police_station_id": 9,
        "police_station": "Mandya Town",
        "crime_registered_date": "2026-06-01T00:00:00",
        "latitude": 12.52,
        "longitude": 76.90,
        "accused": [{"person_id": "P999", "accused_name": "Somu"}],
        "victims": [{"victim_name": "John"}],
        "financial_transactions": []
    }

    res_c = SimilarityEngine.calculate_similarity(case_a, case_c)
    assert res_c["similarity_score"] == 0
    assert len(res_c["reasons"]) == 0


def test_evidence_gap_analyzer():
    # Case with missing victims, coordinates, and no financial data for a financial crime
    case_summary = {
        "crime_type_id": 12,
        "crime_type": "Financial Fraud",
        "latitude": None,
        "longitude": None,
        "victims": [],
        "financial_transactions": []
    }
    
    gaps = EvidenceGapAnalyzer.analyze(case_summary, is_repeat_offender=True)
    gap_types = [g["type"] for g in gaps]
    
    assert "MISSING_VICTIM_DATA" in gap_types
    assert "MISSING_GEOSPATIAL_DATA" in gap_types
    assert "MISSING_FINANCIAL_DATA" in gap_types
    assert "CROSS_CASE_REVIEW_INCOMPLETE" in gap_types


def test_lead_generator():
    case_summary = {
        "crime_type_id": 10,
        "crime_type": "Robbery",
        "accused": [{"person_id": "P101", "accused_name": "Ravi"}],
        "financial_transactions": [{"is_suspicious": True, "financial_transaction_id": 101, "amount": 50000}]
    }

    similar_cases = [
        {
            "case_master_id": 204,
            "similarity_score": 85,
            "reasons": ["Same crime type: Robbery", "Shared accused person_id: P101"]
        }
    ]

    leads = LeadGenerator.generate_leads(
        case_summary=case_summary,
        similar_cases=similar_cases,
        is_repeat_offender=True,
        network_community_id=3,
        highest_risk_score=82.0,
        unauthorized_districts_with_signals=["Mandya"]
    )

    lead_types = [l["type"] for l in leads]
    assert "CROSS_CASE_LINK" in lead_types
    assert "FINANCIAL_RELATIONSHIP" in lead_types
    assert "HIGH_RISK_SUSPECT" in lead_types
    assert "CROSS_DISTRICT_SIGNAL" in lead_types

    # Verify critical priorities
    critical_leads = [l for l in leads if l["priority"] == "CRITICAL"]
    assert len(critical_leads) >= 1
