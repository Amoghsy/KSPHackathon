from app.agents.query_agent.response_formatter import generate_statistics_from_results


def test_no_statistics_keywords():
    # If the user's question does not contain statistics-related words
    result = generate_statistics_from_results(
        question="Show theft cases in Bengaluru during 2025",
        columns=["case_id", "district"],
        rows=[{"case_id": 1, "district": "Bengaluru"}]
    )
    assert result is None


def test_statistics_kpi_stat_card():
    # If the user asks for count or total and query returns 1 row with numeric column
    result = generate_statistics_from_results(
        question="What is the total count of theft cases?",
        columns=["count_cases"],
        rows=[{"count_cases": 150}]
    )
    assert result is not None
    assert result["kind"] == "stat"
    assert result["value"] == 150
    assert "Total" in result["title"]


def test_statistics_chart_line():
    # If the label column looks like date/year/month and value is numeric
    result = generate_statistics_from_results(
        question="Show a trend chart of cases over the years",
        columns=["year", "case_count"],
        rows=[
            {"year": "2023", "case_count": 10},
            {"year": "2024", "case_count": 25},
            {"year": "2025", "case_count": 40}
        ]
    )
    assert result is not None
    assert result["kind"] == "chart"
    assert result["chartKind"] == "line"
    assert len(result["chartData"]) == 3
    assert result["chartData"][0]["label"] == "2023"
    assert result["chartData"][0]["value"] == 10.0


def test_statistics_chart_bar():
    # If category column is not time-series and value is numeric
    result = generate_statistics_from_results(
        question="Show statistics of cases by district",
        columns=["district", "cases_sum"],
        rows=[
            {"district": "Bengaluru", "cases_sum": "100"},
            {"district": "Mysuru", "cases_sum": "50"}
        ]
    )
    assert result is not None
    assert result["kind"] == "chart"
    assert result["chartKind"] == "bar"
    assert len(result["chartData"]) == 2
    assert result["chartData"][0]["label"] == "Bengaluru"
    assert result["chartData"][0]["value"] == 100.0


def test_statistics_distribution():
    # If there are no numeric columns, calculate distribution of the first column
    result = generate_statistics_from_results(
        question="Show analytics of status of the cases",
        columns=["status"],
        rows=[
            {"status": "Active"},
            {"status": "Closed"},
            {"status": "Active"},
            {"status": "Active"},
            {"status": "Closed"}
        ]
    )
    assert result is not None
    assert result["kind"] == "chart"
    assert result["chartKind"] == "bar"
    # Active: 3, Closed: 2
    assert len(result["chartData"]) == 2
    assert result["chartData"][0]["label"] == "Active"
    assert result["chartData"][0]["value"] == 3
    assert result["chartData"][1]["label"] == "Closed"
    assert result["chartData"][1]["value"] == 2
