"""
app/services/nl2sql/sql_validator.py — Validate AI-generated SQL.

Ensures that only safe, read-only SQL is passed to the database layer.
Uses sqlparse for AST-level parsing and validates against the known schema.

Usage:
    from app.services.nl2sql.sql_validator import SQLValidator

    validator = SQLValidator()
    result = validator.validate("SELECT * FROM case_master LIMIT 10")
    if result.valid:
        ...  # safe to execute
    else:
        print(result.errors)
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

import sqlparse
from sqlparse.sql import Identifier, IdentifierList, Parenthesis, Where
from sqlparse.tokens import DDL, DML, Keyword
from app.core.rbac import check_permission, Permission, normalize_role

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Structured response
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Outcome of SQL validation."""

    valid: bool
    """True if the SQL is safe to execute."""

    sql: str = ""
    """The (possibly normalised) SQL that was validated."""

    errors: list[str] = field(default_factory=list)
    """List of human-readable validation failure reasons."""


# ---------------------------------------------------------------------------
# Schema registry — known tables and columns
# ---------------------------------------------------------------------------

# Derived from the Day 1 SQLAlchemy models.  Kept as a plain dict so it is
# easy to auto-generate from metadata introspection later.
_KNOWN_SCHEMA: dict[str, set[str]] = {
    "case_master": {
        "case_master_id",
        "crime_no",
        "case_no",
        "crime_registered_date",
        "police_station_id",
        "crime_type_id",
        "police_person_id",
        "case_category_id",
        "gravity_offence_id",
        "crime_major_head_id",
        "crime_minor_head_id",
        "case_status_id",
        "court_id",
        "incident_from_date",
        "incident_to_date",
        "info_received_ps_date",
        "latitude",
        "longitude",
        "brief_facts",
    },
    "police_station": {
        "police_station_id",
        "name",
        "district",
    },
    "crime_type": {
        "crime_type_id",
        "name",
    },
    "accused_master": {
        "accused_master_id",
        "case_master_id",
        "accused_name",
        "age_year",
        "gender_id",
        "person_id",
    },
    "victim_master": {
        "victim_master_id",
        "case_master_id",
        "victim_name",
        "age_year",
        "gender_id",
        "victim_police",
    },
    "financial_transaction": {
        "financial_transaction_id",
        "source_account",
        "destination_account",
        "bank_name",
        "amount",
        "transaction_date",
        "is_suspicious",
        "reason",
        "case_master_id",
        "accused_master_id",
    },
    "users": {
        "id",
        "username",
        "hashed_password",
        "role",
    },
}

# Flat set of all known table names (lowered).
_KNOWN_TABLES: set[str] = {t.lower() for t in _KNOWN_SCHEMA}

# Flat set of all known column names across all tables (lowered).
_KNOWN_COLUMNS: set[str] = {
    col.lower() for cols in _KNOWN_SCHEMA.values() for col in cols
}

# ---------------------------------------------------------------------------
# Allowed / blocked statement types
# ---------------------------------------------------------------------------

_ALLOWED_STATEMENT_TYPES: set[str] = {"SELECT"}

_BLOCKED_KEYWORDS: set[str] = {
    "DROP",
    "DELETE",
    "UPDATE",
    "INSERT",
    "ALTER",
    "TRUNCATE",
    "CREATE",
}

_BLOCKED_PATTERN = re.compile(
    r"\b(" + "|".join(_BLOCKED_KEYWORDS) + r")\b",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------


class SQLValidator:
    """
    Validates AI-generated SQL before it reaches the database.

    Checks performed (in order):
        1. Non-empty input
        2. Single statement only (no semicolon-separated batches)
        3. Statement type is SELECT (via sqlparse)
        4. No blocked keywords (DROP, DELETE, etc.)
        5. Referenced tables exist in the schema
        6. Referenced columns exist in the schema
        7. SQL parses without errors (well-formed)
    """

    def __init__(
        self,
        *,
        schema: dict[str, set[str]] | None = None,
        strict_columns: bool = True,
    ) -> None:
        """
        Parameters
        ----------
        schema : dict, optional
            Override the built-in schema registry (useful for tests).
        strict_columns : bool
            When True, reject queries referencing unknown column names.
            Set to False if you only want table-level validation.
        """
        schema = schema or _KNOWN_SCHEMA
        self._schema = {k.lower(): {c.lower() for c in v} for k, v in schema.items()}
        self._tables = {t.lower() for t in self._schema}
        self._columns = {c for cols in self._schema.values() for c in cols}
        self._strict_columns = strict_columns

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def validate(self, sql: str, current_user: dict | None = None) -> ValidationResult:
        """
        Validate the given SQL string.

        Parameters
        ----------
        sql : str
            The SQL statement to validate.
        current_user : dict, optional
            The authenticated user context for RBAC checks.

        Returns
        -------
        ValidationResult
            `.valid` is True if the SQL passes all checks.
            `.errors` contains a list of failure reasons (if any).
        """
        errors: list[str] = []

        # 1. Non-empty
        if not sql or not sql.strip():
            return ValidationResult(
                valid=False, sql="", errors=["Empty SQL statement."]
            )

        normalised = sql.strip().rstrip(";").strip()

        # 2. Parse with sqlparse
        try:
            parsed_statements = sqlparse.parse(normalised)
        except Exception as exc:  # noqa: BLE001
            return ValidationResult(
                valid=False,
                sql=normalised,
                errors=[f"SQL parse error: {exc}"],
            )

        if not parsed_statements:
            return ValidationResult(
                valid=False,
                sql=normalised,
                errors=["SQL parse returned no statements."],
            )

        # Only allow a single statement.
        if len(parsed_statements) > 1:
            errors.append(
                f"Multiple statements detected ({len(parsed_statements)}). "
                "Only a single SELECT is allowed."
            )
            return ValidationResult(valid=False, sql=normalised, errors=errors)

        stmt = parsed_statements[0]

        # 3. Statement type must be SELECT (or DML SELECT via CTE/WITH).
        stmt_type = stmt.get_type()
        if stmt_type and stmt_type.upper() not in _ALLOWED_STATEMENT_TYPES:
            errors.append(
                f"Statement type '{stmt_type}' is not allowed. Only SELECT is permitted."
            )

        # Fallback: check leading keyword for WITH … SELECT (CTEs).
        first_token_value = self._first_keyword(stmt)
        if first_token_value and first_token_value.upper() not in {"SELECT", "WITH"}:
            errors.append(
                f"Leading keyword '{first_token_value}' is not allowed. "
                "Only SELECT / WITH (CTE) queries are permitted."
            )

        # 4. Blocked keyword scan (on raw text, after stripping comments).
        cleaned = self._strip_comments(normalised)
        blocked_match = _BLOCKED_PATTERN.search(cleaned)
        if blocked_match:
            kw = blocked_match.group(1).upper()
            errors.append(f"Blocked keyword detected: {kw}.")

        # If we already have fatal errors, return early before schema checks.
        if errors:
            return ValidationResult(valid=False, sql=normalised, errors=errors)

        # 5. Table validation
        cte_aliases = self._extract_cte_aliases(normalised)
        referenced_tables = self._extract_tables(stmt)
        unknown_tables = referenced_tables - self._tables - cte_aliases
        if unknown_tables:
            errors.append(
                f"Unknown table(s): {', '.join(sorted(unknown_tables))}. "
                f"Known tables: {', '.join(sorted(self._tables))}."
            )

        # 6. Column validation (optional strict mode)
        if self._strict_columns:
            referenced_columns = self._extract_columns(stmt, cte_aliases)
            # Only flag columns that are definitely not in the schema and not
            # SQL functions / aliases / *.
            unknown_columns = referenced_columns - self._columns
            if unknown_columns:
                errors.append(
                    f"Unknown column(s): {', '.join(sorted(unknown_columns))}."
                )

        # 7. User-level RBAC & Permission validation (if user context is provided)
        if current_user:
            role = normalize_role(current_user.get("role"))
            
            # Users table: Admin only
            if "users" in referenced_tables:
                if role != "ADMINISTRATOR":
                    errors.append(f"Permission denied. Role '{role}' is not allowed to access user accounts.")
                    
            # Financial transactions: Requires FINANCIAL_CRIME permission
            if "financial_transaction" in referenced_tables:
                if not check_permission(role, Permission.FINANCIAL_CRIME):
                    errors.append(f"Permission denied. Role '{role}' is not allowed to access financial transaction records.")
                    
            # Complainant/Victim names: Requires SENSITIVE_CASE_ACCESS permission
            # Check if columns is strict, or fallback to name scanning
            referenced_columns = self._extract_columns(stmt, cte_aliases)
            has_sensitive_access = check_permission(role, Permission.SENSITIVE_CASE_ACCESS)
            
            if not has_sensitive_access:
                # Crime Analyst and Policy Maker cannot access victim identities
                if "victim_name" in referenced_columns or "victim_master" in referenced_tables:
                    if "victim_name" in referenced_columns or "*" in referenced_columns:
                        errors.append("You do not have permission to access victim identities.")
                # Investigator/Analyst/Policymaker can have individual restrictions:
                if role in ("POLICY_MAKER", "ANALYST"):
                    if "victim_name" in referenced_columns or "complainant" in referenced_columns or "accused_name" in referenced_columns:
                        errors.append("You do not have permission to access personal identifiable information (PII) such as complainant, accused or victim names.")
                    if "source_account" in referenced_columns or "destination_account" in referenced_columns:
                        errors.append("You do not have permission to access financial bank accounts.")

        # 8. Well-formed check (sqlparse does not throw on *most* malformed SQL,
        #    but we can flag obvious issues like unmatched parentheses).
        if normalised.count("(") != normalised.count(")"):
            errors.append("Mismatched parentheses in SQL statement.")

        valid = len(errors) == 0
        if not valid:
            logger.warning("SQL validation failed: %s — SQL=%.300s", errors, normalised)
        else:
            logger.debug("SQL validation OK: %.200s", normalised)

        return ValidationResult(valid=valid, sql=normalised, errors=errors)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _strip_comments(sql: str) -> str:
        """Remove single-line and block comments."""
        sql = re.sub(r"--[^\n]*", "", sql)
        sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
        return sql

    @staticmethod
    def _first_keyword(stmt: sqlparse.sql.Statement) -> str | None:
        """Return the first keyword token value."""
        for token in stmt.tokens:
            if token.ttype in (DML, DDL, Keyword):
                return token.normalized
            if not token.is_whitespace:
                return token.normalized
        return None

    @staticmethod
    def _extract_cte_aliases(sql: str) -> set[str]:
        """
        Extract CTE alias names from WITH clauses.

        Matches patterns like:  WITH cte_name AS (...)  and
        WITH RECURSIVE cte_name AS (...)
        """
        aliases: set[str] = set()
        # Match 'WITH [RECURSIVE] name AS' and subsequent ', name AS'
        pattern = re.compile(
            r"(?:\bWITH\b(?:\s+RECURSIVE)?\s+|,\s*)"
            r"([a-zA-Z_][a-zA-Z0-9_]*)\s+AS\s*\(",
            re.IGNORECASE,
        )
        for m in pattern.finditer(sql):
            aliases.add(m.group(1).lower())
        return aliases

    def _extract_tables(self, stmt: sqlparse.sql.Statement) -> set[str]:
        """
        Extract table names referenced in the SQL statement.

        Handles:  FROM table, JOIN table, FROM table AS alias,
                  FROM (subquery) — skipped, sub-select tables extracted
        """
        tables: set[str] = set()
        self._walk_for_tables(stmt.tokens, tables)
        return tables

    def _walk_for_tables(self, tokens: list, tables: set[str]) -> None:
        """Recursively walk tokens after FROM / JOIN to collect table names."""
        expect_table = False
        for token in tokens:
            # Skip whitespace and comments.
            if token.is_whitespace or token.ttype in sqlparse.tokens.Comment:
                continue

            # After FROM / JOIN, next meaningful token(s) are table identifiers.
            if token.ttype is Keyword and token.normalized.upper() in {
                "FROM",
                "JOIN",
                "INNER JOIN",
                "LEFT JOIN",
                "RIGHT JOIN",
                "FULL JOIN",
                "CROSS JOIN",
                "LEFT OUTER JOIN",
                "RIGHT OUTER JOIN",
                "FULL OUTER JOIN",
                "NATURAL JOIN",
            }:
                expect_table = True
                continue

            if expect_table:
                if isinstance(token, IdentifierList):
                    for identifier in token.get_identifiers():
                        name = self._table_name_from_identifier(identifier)
                        if name:
                            tables.add(name.lower())
                    expect_table = False
                elif isinstance(token, Identifier):
                    name = self._table_name_from_identifier(token)
                    if name:
                        tables.add(name.lower())
                    expect_table = False
                elif isinstance(token, Parenthesis):
                    # Subquery — recurse into it.
                    self._walk_for_tables(token.tokens, tables)
                    expect_table = False
                elif token.ttype is not None:
                    # Bare name without Identifier wrapper.
                    tables.add(token.normalized.lower())
                    expect_table = False
                continue

            # Recurse into sub-statements (subqueries in WHERE, etc.).
            if hasattr(token, "tokens"):
                self._walk_for_tables(token.tokens, tables)

    @staticmethod
    def _table_name_from_identifier(identifier: Identifier) -> str | None:
        """Extract the real table name from a sqlparse Identifier (handles aliases)."""
        # identifier.get_real_name() returns the base name before AS alias.
        name = identifier.get_real_name()
        if name and not name.startswith("("):
            return name
        return None

    def _extract_columns(
        self,
        stmt: sqlparse.sql.Statement,
        cte_aliases: set[str] | None = None,
    ) -> set[str]:
        """
        Best-effort extraction of column names from the SQL.

        Returns only simple identifiers (no functions, *, aliases with AS).
        CTE aliases are excluded so they aren't flagged as columns.
        """
        columns: set[str] = set()
        self._walk_for_columns(stmt.tokens, columns)
        # Remove CTE alias names that might have been picked up.
        if cte_aliases:
            columns -= cte_aliases
        return columns

    def _walk_for_columns(self, tokens: list, columns: set[str]) -> None:
        """Walk tokens to collect column-like identifiers."""
        for token in tokens:
            if token.is_whitespace:
                continue

            if isinstance(token, Identifier):
                real = token.get_real_name()
                if real and real != "*" and real.lower() not in self._tables:
                    # Skip function calls (real_name followed by parenthesis).
                    if not any(isinstance(t, Parenthesis) for t in token.tokens):
                        # Handle table.column notation.
                        parts = real.split(".")
                        col_name = parts[-1].lower()
                        columns.add(col_name)

            elif isinstance(token, IdentifierList):
                for ident in token.get_identifiers():
                    if isinstance(ident, Identifier):
                        real = ident.get_real_name()
                        if real and real != "*" and real.lower() not in self._tables:
                            if not any(
                                isinstance(t, Parenthesis) for t in ident.tokens
                            ):
                                parts = real.split(".")
                                col_name = parts[-1].lower()
                                columns.add(col_name)

            elif isinstance(token, (Where, Parenthesis)):
                self._walk_for_columns(token.tokens, columns)

            elif hasattr(token, "tokens"):
                self._walk_for_columns(token.tokens, columns)
