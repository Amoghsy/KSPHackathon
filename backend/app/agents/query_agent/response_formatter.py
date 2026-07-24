"""
app/agents/query_agent/response_formatter.py — Format Query Agent responses.

Converts internal pipeline results into a standardised JSON-serialisable dict.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


import re
import decimal


def to_numeric(val: Any) -> float | int:
    if val is None:
        return 0
    if isinstance(val, (int, float)):
        return val
    if isinstance(val, decimal.Decimal):
        return float(val)
    try:
        val_str = str(val).replace(",", "").replace("%", "").strip()
        if "." in val_str:
            return float(val_str)
        else:
            return int(val_str)
    except ValueError:
        return 0


def generate_statistics_from_results(question: str, columns: list[str], rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    # 1. Check if question contains a statistics-related term
    stats_terms = {
        "statistic", "statistics", "stats", "chart", "graph", "plot", "average", "avg",
        "total", "sum", "count", "distribution", "trend", "percentage", "pct", "analytics",
        "correlation", "metrics", "rate"
    }
    question_lower = question.lower()
    has_stats_term = any(term in question_lower for term in stats_terms)
    if not has_stats_term:
        return None

    if not rows or not columns:
        return None

    # 2. Analyze column types based on the first few rows
    numeric_cols = []
    categorical_cols = []
    
    first_row = rows[0]
    for col in columns:
        val = first_row.get(col)
        if val is None:
            # check subsequent rows if the first row has None
            for row in rows[1:5]:
                if row.get(col) is not None:
                    val = row.get(col)
                    break
        
        col_lower = col.lower()
        is_dimension = False
        if col_lower == "id" or col_lower.endswith("_id") or col_lower.startswith("id_"):
            is_dimension = True
        elif any(t in col_lower for t in ["year", "month", "date", "day", "time", "created_at"]):
            is_dimension = True

        if val is None:
            categorical_cols.append(col)
            continue
            
        # Check if it's numeric or can be parsed as numeric
        is_num = False
        if not is_dimension:
            if isinstance(val, (int, float, decimal.Decimal)) and not isinstance(val, bool):
                is_num = True
            elif isinstance(val, str):
                try:
                    float(val.replace(",", "").replace("%", "").strip())
                    is_num = True
                except ValueError:
                    pass
        
        if is_num:
            numeric_cols.append(col)
        else:
            categorical_cols.append(col)

    # 3. Choose statistics presentation based on the analyzed columns
    # Scenario A: Single cell / Single value (e.g. COUNT or SUM)
    if len(rows) == 1 and len(numeric_cols) >= 1:
        val_col = numeric_cols[0]
        val = first_row.get(val_col)
        num_val = to_numeric(val)
        
        title = val_col.replace("_", " ").title()
        title_lower = title.lower()
        if "avg" in title_lower or "average" in title_lower:
            pass
        elif "average" in question_lower or "avg" in question_lower:
            title = f"Average {title}"
            
        if "total" in title_lower:
            pass
        elif "total" in question_lower:
            title = f"Total {title}"
        elif "count" in title_lower:
            pass
        elif "count" in question_lower:
            title = f"Count of {title}"
            
        return {
            "kind": "stat",
            "title": title,
            "value": num_val,
        }

    # Scenario B: Multiple rows, at least one numeric and one categorical column (Chart)
    if len(rows) > 1 and len(numeric_cols) >= 1:
        val_col = numeric_cols[0]
        # Choose the best categorical column
        label_col = categorical_cols[0] if categorical_cols else columns[0]
        if label_col == val_col and len(columns) > 1:
            label_col = [c for c in columns if c != val_col][0]
            
        chart_data = []
        for r in rows:
            label_val = r.get(label_col)
            if label_val is None:
                label_str = "None"
            else:
                label_str = str(label_val)
                if len(label_str) > 10 and (label_str[4] == '-' or label_str[10] == 'T'):
                    label_str = label_str[:10]
            
            val_val = r.get(val_col)
            num_val = to_numeric(val_val)
                
            chart_data.append({
                "label": label_str,
                "value": num_val
            })
            
        chart_kind = "bar"
        label_col_lower = label_col.lower()
        if any(t in label_col_lower for t in ["date", "year", "month", "day", "time", "created_at"]):
            chart_kind = "line"
            
        title = f"{val_col.replace('_', ' ').title()} by {label_col.replace('_', ' ').title()}"
        return {
            "kind": "chart",
            "title": title,
            "chartKind": chart_kind,
            "chartData": chart_data
        }
        
    # Scenario C: Multiple rows but no numeric columns - calculate counts of the categorical values
    if len(rows) > 1 and not numeric_cols:
        group_col = columns[0]
        counts = {}
        for r in rows:
            val = r.get(group_col)
            val_str = str(val) if val is not None else "None"
            counts[val_str] = counts.get(val_str, 0) + 1
            
        chart_data = [{"label": k, "value": v} for k, v in counts.items()]
        chart_data = sorted(chart_data, key=lambda x: x["value"], reverse=True)[:10]
        
        title = f"Distribution of {group_col.replace('_', ' ').title()}"
        return {
            "kind": "chart",
            "title": title,
            "chartKind": "bar",
            "chartData": chart_data
        }

    return None


def extract_tables(sql: str) -> list[str]:
    """Extract table names from SQL FROM and JOIN clauses."""
    matches = re.findall(r"\b(?:from|join)\s+([a-zA-Z_0-9]+)", sql, re.IGNORECASE)
    return list(set(matches))


def format_success(
    *,
    question: str,
    generated_sql: str,
    rows: list[dict[str, Any]],
    columns: list[str],
    row_count: int,
    execution_time_ms: float,
    summary: str,
    confidence: float,
) -> dict[str, Any]:
    """
    Build the standard success response payload.
    """
    tables = extract_tables(generated_sql)
    sources = f"PostgreSQL: {', '.join(tables)}" if tables else "PostgreSQL Database"
    
    # Calculate confidence score (0-100)
    conf_pct = int(confidence * 100) if confidence <= 1.0 else int(confidence)

    explain_block = {
        "sql": generated_sql,
        "sources": sources,
        "algorithms": "NL-to-SQL Semantic Translation, Relational Database Execution",
        "confidence": conf_pct,
        "execution_time": f"{round(execution_time_ms, 2)}ms",
        "summary": summary
    }

    statistics_block = generate_statistics_from_results(question, columns, rows)

    return {
        "status": "success",
        "question": question,
        "generated_sql": generated_sql,
        "row_count": row_count,
        "execution_time_ms": round(execution_time_ms, 2),
        "summary": summary,
        "rows": rows,
        "columns": columns,
        "confidence": confidence,
        "explain": explain_block,
        "statistics": statistics_block
    }



def format_error(
    *,
    question: str,
    error: str,
    error_type: str,
    generated_sql: str | None = None,
    retryable: bool = False,
) -> dict[str, Any]:
    """
    Build the standard error response payload.

    No stack traces. Structured, user-friendly errors.
    """
    return {
        "status": "error",
        "question": question,
        "error": error,
        "error_type": error_type,
        "generated_sql": generated_sql,
        "retryable": retryable,
    }


def compute_confidence(
    *,
    sql_valid: bool,
    rows_returned: int,
    execution_ok: bool,
    summary_ok: bool,
) -> float:
    """
    Compute a heuristic confidence score (0.0 – 1.0).

    Does NOT call the LLM — purely deterministic.

    Scoring:
        +0.30  valid SQL generated
        +0.30  query executed without errors
        +0.20  rows were returned (non-empty result)
        +0.10  more than 0 but ≤ 1000 rows (reasonable result set)
        +0.10  summary generated successfully
    """
    score = 0.0

    if sql_valid:
        score += 0.30

    if execution_ok:
        score += 0.30

    if rows_returned > 0:
        score += 0.20
        if rows_returned <= 1000:
            score += 0.10

    if summary_ok:
        score += 0.10

    return min(score, 1.0)
