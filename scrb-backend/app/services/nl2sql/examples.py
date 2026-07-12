"""
app/services/nl2sql/examples.py — Few-shot NL→SQL examples.

These examples are injected into the Gemini prompt so the model learns
the expected SQL style, table/column names, and query patterns.

Keep examples separate from code — easy to update without touching logic.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class NLSQLExample:
    """A single natural-language → SQL example."""

    question: str
    sql: str


# ---------------------------------------------------------------------------
# Curated examples  (15 realistic queries against the SCRB schema)
# ---------------------------------------------------------------------------

FEW_SHOT_EXAMPLES: list[NLSQLExample] = [
    # 1. Simple filter by crime type and location
    NLSQLExample(
        question="Show all theft cases in Mysuru during 2025.",
        sql=(
            "SELECT cm.case_master_id, cm.crime_no, cm.crime_registered_date, "
            "ps.name AS police_station, ct.name AS crime_type "
            "FROM case_master cm "
            "JOIN police_station ps ON cm.police_station_id = ps.police_station_id "
            "JOIN crime_type ct ON cm.crime_type_id = ct.crime_type_id "
            "WHERE ct.name ILIKE '%theft%' "
            "AND ps.district ILIKE '%Mysuru%' "
            "AND cm.crime_registered_date >= '2025-01-01' "
            "AND cm.crime_registered_date < '2026-01-01' "
            "ORDER BY cm.crime_registered_date DESC "
            "LIMIT 100"
        ),
    ),
    # 2. Repeat offenders
    NLSQLExample(
        question="Which accused appeared in more than three FIRs?",
        sql=(
            "SELECT am.accused_name, COUNT(DISTINCT am.case_master_id) AS fir_count "
            "FROM accused_master am "
            "GROUP BY am.accused_name "
            "HAVING COUNT(DISTINCT am.case_master_id) > 3 "
            "ORDER BY fir_count DESC "
            "LIMIT 100"
        ),
    ),
    # 3. Recent robberies in a city
    NLSQLExample(
        question="Show robbery cases reported in Bengaluru last month.",
        sql=(
            "SELECT cm.case_master_id, cm.crime_no, cm.crime_registered_date, "
            "ps.name AS police_station "
            "FROM case_master cm "
            "JOIN police_station ps ON cm.police_station_id = ps.police_station_id "
            "JOIN crime_type ct ON cm.crime_type_id = ct.crime_type_id "
            "WHERE ct.name ILIKE '%robbery%' "
            "AND ps.district ILIKE '%Bengaluru%' "
            "AND cm.crime_registered_date >= (CURRENT_DATE - INTERVAL '1 month') "
            "ORDER BY cm.crime_registered_date DESC "
            "LIMIT 100"
        ),
    ),
    # 4. Case count by district
    NLSQLExample(
        question="How many cases were registered per district in 2025?",
        sql=(
            "SELECT ps.district, COUNT(*) AS case_count "
            "FROM case_master cm "
            "JOIN police_station ps ON cm.police_station_id = ps.police_station_id "
            "WHERE cm.crime_registered_date >= '2025-01-01' "
            "AND cm.crime_registered_date < '2026-01-01' "
            "GROUP BY ps.district "
            "ORDER BY case_count DESC "
            "LIMIT 100"
        ),
    ),
    # 5. Suspicious financial transactions
    NLSQLExample(
        question="Show all suspicious financial transactions above 1 lakh.",
        sql=(
            "SELECT ft.financial_transaction_id, ft.source_account, "
            "ft.destination_account, ft.amount, ft.transaction_date, ft.reason "
            "FROM financial_transaction ft "
            "WHERE ft.is_suspicious = TRUE "
            "AND ft.amount > 100000 "
            "ORDER BY ft.amount DESC "
            "LIMIT 100"
        ),
    ),
    # 6. Victim demographics
    NLSQLExample(
        question="List all victims under 18 years old.",
        sql=(
            "SELECT vm.victim_name, vm.age_year, cm.crime_no, ps.name AS police_station "
            "FROM victim_master vm "
            "JOIN case_master cm ON vm.case_master_id = cm.case_master_id "
            "JOIN police_station ps ON cm.police_station_id = ps.police_station_id "
            "WHERE vm.age_year < 18 "
            "ORDER BY vm.age_year "
            "LIMIT 100"
        ),
    ),
    # 7. Cases with coordinates (geo queries)
    NLSQLExample(
        question="Find cases with GPS coordinates near latitude 12.97, longitude 77.59.",
        sql=(
            "SELECT cm.case_master_id, cm.crime_no, cm.latitude, cm.longitude, "
            "cm.brief_facts "
            "FROM case_master cm "
            "WHERE cm.latitude BETWEEN 12.95 AND 12.99 "
            "AND cm.longitude BETWEEN 77.57 AND 77.61 "
            "ORDER BY cm.crime_registered_date DESC "
            "LIMIT 100"
        ),
    ),
    # 8. Crime type breakdown
    NLSQLExample(
        question="What are the top 10 most common crime types?",
        sql=(
            "SELECT ct.name AS crime_type, COUNT(*) AS case_count "
            "FROM case_master cm "
            "JOIN crime_type ct ON cm.crime_type_id = ct.crime_type_id "
            "GROUP BY ct.name "
            "ORDER BY case_count DESC "
            "LIMIT 10"
        ),
    ),
    # 9. Accused linked to financial transactions
    NLSQLExample(
        question="Show accused persons involved in suspicious transactions.",
        sql=(
            "SELECT DISTINCT am.accused_name, ft.amount, ft.source_account, "
            "ft.destination_account, ft.transaction_date "
            "FROM accused_master am "
            "JOIN financial_transaction ft "
            "ON am.accused_master_id = ft.accused_master_id "
            "WHERE ft.is_suspicious = TRUE "
            "ORDER BY ft.amount DESC "
            "LIMIT 100"
        ),
    ),
    # 10. Police station workload
    NLSQLExample(
        question="Which police stations have the most cases this year?",
        sql=(
            "SELECT ps.name AS police_station, ps.district, "
            "COUNT(*) AS case_count "
            "FROM case_master cm "
            "JOIN police_station ps ON cm.police_station_id = ps.police_station_id "
            "WHERE cm.crime_registered_date >= DATE_TRUNC('year', CURRENT_DATE) "
            "GROUP BY ps.name, ps.district "
            "ORDER BY case_count DESC "
            "LIMIT 100"
        ),
    ),
    # 11. Cases without accused
    NLSQLExample(
        question="Find cases that have no accused persons linked.",
        sql=(
            "SELECT cm.case_master_id, cm.crime_no, cm.crime_registered_date "
            "FROM case_master cm "
            "LEFT JOIN accused_master am ON cm.case_master_id = am.case_master_id "
            "WHERE am.accused_master_id IS NULL "
            "ORDER BY cm.crime_registered_date DESC "
            "LIMIT 100"
        ),
    ),
    # 12. Monthly crime trend
    NLSQLExample(
        question="Show the monthly crime count for 2025.",
        sql=(
            "SELECT DATE_TRUNC('month', cm.crime_registered_date) AS month, "
            "COUNT(*) AS case_count "
            "FROM case_master cm "
            "WHERE cm.crime_registered_date >= '2025-01-01' "
            "AND cm.crime_registered_date < '2026-01-01' "
            "GROUP BY DATE_TRUNC('month', cm.crime_registered_date) "
            "ORDER BY month "
            "LIMIT 100"
        ),
    ),
    # 13. Total transaction value per case
    NLSQLExample(
        question="What is the total transaction amount per case?",
        sql=(
            "SELECT cm.crime_no, SUM(ft.amount) AS total_amount "
            "FROM financial_transaction ft "
            "JOIN case_master cm ON ft.case_master_id = cm.case_master_id "
            "GROUP BY cm.crime_no "
            "ORDER BY total_amount DESC "
            "LIMIT 100"
        ),
    ),
    # 14. Cases by gender of accused
    NLSQLExample(
        question="How many accused persons are there by gender?",
        sql=(
            "SELECT am.gender_id, COUNT(*) AS accused_count "
            "FROM accused_master am "
            "GROUP BY am.gender_id "
            "ORDER BY accused_count DESC "
            "LIMIT 100"
        ),
    ),
    # 15. Search by brief facts keyword
    NLSQLExample(
        question="Find cases mentioning 'kidnapping' in brief facts.",
        sql=(
            "SELECT cm.case_master_id, cm.crime_no, cm.brief_facts, "
            "cm.crime_registered_date "
            "FROM case_master cm "
            "WHERE cm.brief_facts ILIKE '%kidnapping%' "
            "ORDER BY cm.crime_registered_date DESC "
            "LIMIT 100"
        ),
    ),
]


def format_examples_for_prompt() -> str:
    """Render all examples as a prompt-injectable text block."""
    lines: list[str] = ["=== FEW-SHOT EXAMPLES ===", ""]
    for i, ex in enumerate(FEW_SHOT_EXAMPLES, 1):
        lines.append(f"Example {i}:")
        lines.append(f"  Question: {ex.question}")
        lines.append(f"  SQL: {ex.sql}")
        lines.append("")
    return "\n".join(lines)
