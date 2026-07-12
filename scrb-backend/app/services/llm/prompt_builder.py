"""
app/services/llm/prompt_builder.py — Reusable prompt template builder.

Composes structured prompts by injecting schema context, few-shot examples,
business rules, and user questions — no manual string concatenation.

Usage:
    from app.services.llm.prompt_builder import PromptBuilder

    builder = PromptBuilder()
    system, user = builder.build_nl2sql_prompt("Show theft cases in Mysuru")
"""

from __future__ import annotations

import logging
from string import Template

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

_NL2SQL_SYSTEM_TEMPLATE = Template("""\
You are an expert PostgreSQL SQL generator for the SCRB Intelligence Platform \
(Karnataka State Police crime analytics system).

STRICT RULES:
1. Generate PostgreSQL-compatible SQL ONLY.
2. Use ONLY the tables and columns from the supplied schema.
3. NEVER invent tables or columns.
4. NEVER use DELETE, UPDATE, INSERT, DROP, ALTER, TRUNCATE, or CREATE.
5. Prefer explicit JOINs over implicit joins.
6. Always qualify column names with table aliases when joining.
7. Always include LIMIT 100 unless the user explicitly requests more.
8. Return ONLY the raw SQL statement.
9. Do NOT include markdown, code fences, explanations, or comments.
10. If you cannot generate valid SQL for the request, respond with exactly: CANNOT_GENERATE_SQL

$schema_context

$examples

$business_rules
""")

_NL2SQL_USER_TEMPLATE = Template("""\
Convert the following natural-language question into a PostgreSQL SQL query.

Question: $question

SQL:""")

_SUMMARIZER_SYSTEM_TEMPLATE = Template("""\
You are a data analyst for the SCRB Intelligence Platform \
(Karnataka State Police crime analytics system).

RULES:
1. Summarise ONLY from the supplied data rows. Do NOT invent facts.
2. If no rows are provided or the result set is empty, respond with: \
"No matching records were found."
3. Keep summaries concise — 2-4 sentences for simple queries, up to a short \
paragraph for complex results.
4. Use natural language. Do not output raw SQL, JSON, or code.
5. Mention key numbers, names, and dates from the data.
6. If data contains aggregates, highlight the most significant findings.
""")

_SUMMARIZER_USER_TEMPLATE = Template("""\
The user asked: "$question"

The following SQL was executed:
$sql

Results ($row_count rows):
$rows_text

Provide a concise natural-language summary of these results.
""")


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------

class PromptBuilder:
    """
    Builds structured prompts for NL→SQL and result summarisation.

    Each method returns a ``(system_prompt, user_prompt)`` tuple ready
    for the LLM provider.
    """

    def __init__(
        self,
        *,
        schema_context: str = "",
        examples: str = "",
        business_rules: str = "",
    ) -> None:
        self._schema_context = schema_context
        self._examples = examples
        self._business_rules = business_rules or self._default_business_rules()

    # ------------------------------------------------------------------
    # NL → SQL prompt
    # ------------------------------------------------------------------

    def build_nl2sql_prompt(self, question: str) -> tuple[str, str]:
        """
        Build system + user prompts for NL→SQL generation.

        Returns
        -------
        (system_prompt, user_prompt)
        """
        system = _NL2SQL_SYSTEM_TEMPLATE.safe_substitute(
            schema_context=self._schema_context,
            examples=self._examples,
            business_rules=self._business_rules,
        )
        user = _NL2SQL_USER_TEMPLATE.safe_substitute(question=question)
        return system.strip(), user.strip()

    # ------------------------------------------------------------------
    # Result summariser prompt
    # ------------------------------------------------------------------

    def build_summary_prompt(
        self,
        question: str,
        sql: str,
        rows: list[dict],
        row_count: int,
    ) -> tuple[str, str]:
        """
        Build system + user prompts for result summarisation.

        Returns
        -------
        (system_prompt, user_prompt)
        """
        # Truncate rows for the prompt (first 30 rows max to stay in context).
        display_rows = rows[:30]
        rows_text = self._format_rows(display_rows) if display_rows else "(empty result set)"

        system = _SUMMARIZER_SYSTEM_TEMPLATE.safe_substitute()
        user = _SUMMARIZER_USER_TEMPLATE.safe_substitute(
            question=question,
            sql=sql,
            row_count=row_count,
            rows_text=rows_text,
        )
        return system.strip(), user.strip()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _format_rows(rows: list[dict]) -> str:
        """Format rows as a compact text table for the LLM prompt."""
        if not rows:
            return "(no data)"
        # Header from first row keys.
        headers = list(rows[0].keys())
        lines = [" | ".join(headers)]
        lines.append("-+-".join("-" * len(h) for h in headers))
        for row in rows:
            lines.append(" | ".join(str(row.get(h, "")) for h in headers))
        return "\n".join(lines)

    @staticmethod
    def _default_business_rules() -> str:
        return (
            "=== BUSINESS RULES ===\n"
            "- crime_no is the FIR number (e.g. '001/2025').\n"
            "- case_no is the court case number (may be NULL if not yet filed).\n"
            "- police_station.district contains the district name (e.g. 'Bengaluru Urban').\n"
            "- Use ILIKE for case-insensitive text matching.\n"
            "- Dates are stored as DATE or TIMESTAMP; use standard PostgreSQL date functions.\n"
            "- financial_transaction.is_suspicious is a boolean flag.\n"
            "- financial_transaction.amount is stored in INR (Indian Rupees).\n"
            "- 1 lakh = 100000, 1 crore = 10000000.\n"
        )
