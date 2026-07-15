"""
app/services/nl2sql/schema_context.py — Generate a compact schema description.

Dynamically extracts table names, columns, primary keys, foreign keys and
relationships from the SQLAlchemy ORM models and renders them as a concise
text block suitable for LLM prompts.

Usage:
    from app.services.nl2sql.schema_context import get_schema_context

    schema_text = get_schema_context()
"""

from __future__ import annotations

import logging
from typing import Any

# Force all models to register with Base.metadata.
import app.models  # noqa: F401
from app.db.base import Base

logger = logging.getLogger(__name__)


def _get_table_info(table_name: str, metadata: Any) -> dict:
    """Extract column / key / FK info for a single table from SA metadata."""
    table = metadata.tables.get(table_name)
    if table is None:
        return {}

    columns = []
    for col in table.columns:
        col_info: dict[str, Any] = {
            "name": col.name,
            "type": str(col.type),
            "nullable": col.nullable,
            "primary_key": col.primary_key,
        }
        columns.append(col_info)

    foreign_keys = []
    for fk_constraint in table.foreign_key_constraints:
        for fk in fk_constraint.elements:
            foreign_keys.append(
                {
                    "column": fk.parent.name,
                    "references": f"{fk.column.table.name}.{fk.column.name}",
                }
            )

    primary_keys = [col.name for col in table.primary_key.columns]

    return {
        "table": table_name,
        "columns": columns,
        "primary_keys": primary_keys,
        "foreign_keys": foreign_keys,
    }


def get_schema_dict() -> list[dict]:
    """Return structured schema info for every registered ORM table."""
    metadata = Base.metadata
    tables = []
    for table_name in sorted(metadata.tables.keys()):
        info = _get_table_info(table_name, metadata)
        if info:
            tables.append(info)
    return tables


def get_schema_context() -> str:
    """
    Generate a compact, LLM-friendly schema description.

    Returns a multi-line string suitable for injection into system prompts.
    """
    tables = get_schema_dict()
    if not tables:
        logger.warning("No tables found in SQLAlchemy metadata.")
        return "No database schema available."

    lines: list[str] = ["=== DATABASE SCHEMA ===", ""]

    for tbl in tables:
        lines.append(f"TABLE: {tbl['table']}")
        lines.append(f"  Primary Key(s): {', '.join(tbl['primary_keys'])}")

        for col in tbl["columns"]:
            pk_marker = " [PK]" if col["primary_key"] else ""
            null_marker = " (nullable)" if col["nullable"] else " (NOT NULL)"
            lines.append(f"  - {col['name']}: {col['type']}{pk_marker}{null_marker}")

        if tbl["foreign_keys"]:
            for fk in tbl["foreign_keys"]:
                lines.append(f"  FK: {fk['column']} → {fk['references']}")

        lines.append("")  # blank separator

    # Add relationship summary.
    lines.append("=== RELATIONSHIPS ===")
    lines.append("case_master.police_station_id → police_station.police_station_id")
    lines.append("case_master.crime_type_id → crime_type.crime_type_id")
    lines.append("accused_master.case_master_id → case_master.case_master_id")
    lines.append("victim_master.case_master_id → case_master.case_master_id")
    lines.append("financial_transaction.case_master_id → case_master.case_master_id")
    lines.append(
        "financial_transaction.accused_master_id → accused_master.accused_master_id"
    )
    lines.append("")

    result = "\n".join(lines)
    logger.debug(
        "Schema context generated (%d chars, %d tables)", len(result), len(tables)
    )
    return result
