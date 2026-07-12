"""
app/services/conversation/context_injector.py — Deterministic context injection for follow-up questions.
"""

from __future__ import annotations

import re
from typing import Optional

from app.services.conversation.entity_memory import EntityMemory


class ContextInjector:
    """
    Deterministically resolves and rewrites follow-up questions using conversation state
    and entity memory. No AI or vector search.
    """

    def inject(
        self,
        question: str,
        entity_memory: EntityMemory,
        last_question: Optional[str] = None,
    ) -> str:
        """
        Inject conversation context into the current user question if it's a follow-up.
        """
        q_lower = question.lower().strip()

        # Extract entities from memory
        last_case = entity_memory.last_case
        last_accused = entity_memory.last_accused
        last_station = entity_memory.last_station
        last_district = entity_memory.last_district
        last_crime_type = entity_memory.last_crime_type

        # 1. Pronoun and specific reference replacement
        # "his victims" / "her victims"
        if re.search(r"\b(his|her|their)\s+victims\b", q_lower):
            if last_accused:
                return re.sub(
                    r"\b(his|her|their)\s+victims\b",
                    f"victims of accused {last_accused}",
                    question,
                    flags=re.IGNORECASE,
                )

        # "his previous cases" / "her previous cases"
        if re.search(r"\b(his|her|their)\s+previous\s+cases\b", q_lower):
            if last_accused:
                return re.sub(
                    r"\b(his|her|their)\s+previous\s+cases\b",
                    f"previous cases of accused {last_accused}",
                    question,
                    flags=re.IGNORECASE,
                )

        # "who is the accused" / "who's the accused"
        if q_lower in [
            "who is the accused",
            "who is the accused?",
            "who's the accused",
            "who's the accused?",
        ]:
            if last_case:
                return f"Who is the accused in FIR {last_case}"

        # "where did it happen" / "where did it happen?"
        if q_lower in ["where did it happen", "where did it happen?"]:
            if last_case:
                return f"Where did FIR {last_case} happen"

        # "which station?" / "which station"
        if q_lower in [
            "which station?",
            "which station",
            "which station handled it?",
            "which station handled it",
        ]:
            if last_case:
                return f"Which station handled FIR {last_case}"

        # "he", "she", "his", "her", "their", "those accused"
        if last_accused:
            # Replace pronouns referring to the accused
            question = re.sub(
                r"\b(he|she|those accused)\b",
                f"accused {last_accused}",
                question,
                flags=re.IGNORECASE,
            )
            question = re.sub(
                r"\b(his|her|their)\b",
                f"accused {last_accused}'s",
                question,
                flags=re.IGNORECASE,
            )

        if last_case:
            # Replace case references
            question = re.sub(
                r"\b(that case|this case)\b",
                f"FIR {last_case}",
                question,
                flags=re.IGNORECASE,
            )

        if last_station:
            question = re.sub(
                r"\b(this station|that station)\b",
                f"station {last_station}",
                question,
                flags=re.IGNORECASE,
            )

        if last_district:
            question = re.sub(
                r"\b(this district|that district)\b",
                f"district {last_district}",
                question,
                flags=re.IGNORECASE,
            )

        # Recalculate lower case after substitutions
        q_lower = question.lower().strip()

        # 2. General Short Follow-ups
        # Case 1: "Only solved ones"
        if q_lower in [
            "only solved ones",
            "only solved ones.",
            "only solved",
            "only solved cases",
        ]:
            # Reconstruct from last query/entities
            parts = ["solved"]
            if last_crime_type:
                parts.append(last_crime_type.lower())
            parts.append("cases")
            if last_district:
                parts.append(f"in {last_district}")
            if last_accused:
                parts.append(f"involving accused {last_accused}")
            return "Show " + " ".join(parts)

        # Case 2: "Show accused" (as a follow-up)
        if q_lower in [
            "show accused",
            "show accused.",
            "show the accused",
            "who are the accused",
        ]:
            parts = ["accused"]
            if last_crime_type or last_district or last_case:
                parts.append("in")
                if last_crime_type:
                    parts.append(f"{last_crime_type.lower()} cases")
                if last_district:
                    parts.append(f"in {last_district}")
                if last_case:
                    parts.append(f"FIR {last_case}")
                return "Show " + " ".join(parts)

        # Case 3: "Show only female victims"
        if q_lower in ["show only female victims", "show only female victims."]:
            if last_accused:
                return f"Show only female victims of accused {last_accused}"
            elif last_case:
                return f"Show only female victims in FIR {last_case}"

        # Case 4: Short "Only <something>" follow-ups
        only_match = re.match(r"^only\s+(.+)$", q_lower)
        if only_match:
            only_val = only_match.group(1).strip()

            # Check if only_val is a crime type
            if only_val in [
                "robbery",
                "theft",
                "murder",
                "cyber",
                "cyber crime",
                "cybercrime",
                "assault",
            ]:
                crime_mapped = only_val.title()
                if only_val in ["cyber", "cybercrime"]:
                    crime_mapped = "Cyber Crime"

                parts = [f"{crime_mapped} cases"]
                if last_accused:
                    parts.append(f"involving accused {last_accused}")
                if last_district:
                    parts.append(f"in {last_district}")
                return "Show " + " ".join(parts)

            # Check if only_val is a district
            matched_district = None
            from app.services.conversation.entity_resolver import EntityResolver

            for d in EntityResolver.DISTRICTS:
                if d.lower() == only_val.lower():
                    matched_district = d
                    break

            if matched_district:
                parts = ["cases"]
                if last_crime_type:
                    parts.insert(0, f"{last_crime_type.lower()}")
                parts.append(f"in {matched_district}")
                if last_accused:
                    parts.append(f"involving accused {last_accused}")
                return "Show " + " ".join(parts)

            # Check if only_val is a date range / year / month
            if only_val in ["this month", "this year", "last year"] or re.match(
                r"^(20\d{2})$", only_val
            ):
                date_str = only_val
                parts = ["cases"]
                if last_crime_type:
                    parts.insert(0, f"{last_crime_type.lower()}")
                if last_district:
                    parts.append(f"in {last_district}")
                if last_accused:
                    parts.append(f"involving accused {last_accused}")
                parts.append(f"during {date_str}")
                return "Show " + " ".join(parts)

        return question
