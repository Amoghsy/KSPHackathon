"""
app/services/conversation/entity_resolver.py — Deterministic entity extraction.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ResolvedEntity(BaseModel):
    """Container for resolved entities."""

    case_id: Optional[str] = Field(None, alias="last_case")
    accused_id: Optional[str] = Field(None, alias="last_accused")
    victim_id: Optional[str] = Field(None, alias="last_victim")
    police_station: Optional[str] = Field(None, alias="last_station")
    district: Optional[str] = Field(None, alias="last_district")
    crime_type: Optional[str] = Field(None, alias="last_crime_type")
    date_range: Optional[str] = Field(None, alias="last_date_range")

    class Config:
        populate_by_name = True


class EntityResolver:
    """
    Deterministic entity resolver that parses user questions and Query Agent response rows
    to extract and track relevant entities (cases, accused, victims, stations, districts, etc.).
    Do NOT use Gemini/AI.
    """

    # Common Karnataka Districts
    DISTRICTS = [
        "Mysuru",
        "Mysore",
        "Bengaluru",
        "Bangalore",
        "Belagavi",
        "Hubli",
        "Dharwad",
        "Mangaluru",
        "Mangalore",
        "Udupi",
        "Kolar",
        "Tumakuru",
        "Tumkur",
        "Mandya",
        "Chamarajanagar",
        "Hassan",
        "Shimoga",
        "Shivamogga",
        "Chikmagalur",
        "Davangere",
        "Bagalkot",
        "Bidar",
        "Vijayapura",
        "Bijapur",
        "Chitradurga",
        "Gadag",
        "Kalaburagi",
        "Gulbarga",
        "Koppal",
        "Raichur",
        "Ramanagara",
        "Yadgir",
    ]

    # Mapping of keywords to Crime Types
    CRIME_TYPES = {
        "theft": "Theft",
        "robbery": "Robbery",
        "cyber": "Cyber Crime",
        "cyber crime": "Cyber Crime",
        "cybercrime": "Cyber Crime",
        "murder": "Murder",
        "homicide": "Murder",
        "assault": "Assault",
        "extortion": "Extortion",
        "kidnap": "Kidnapping",
        "kidnapping": "Kidnapping",
        "burglary": "Burglary",
        "cheating": "Cheating",
        "forgery": "Forgery",
        "rape": "Rape / Sexual Assault",
        "sexual assault": "Rape / Sexual Assault",
        "dowry": "Dowry Deaths",
        "dacoity": "Dacoity",
        "riot": "Riots",
        "rioting": "Riots",
    }

    def resolve(
        self, question: str, response: Optional[Dict[str, Any]] = None
    ) -> ResolvedEntity:
        """
        Extract entities from user's question and/or Query Agent response.
        """
        entities = {}

        # 1. Parse user question
        # Case / FIR Number (e.g. FIR 123, Case #123, FIR-123)
        case_match = re.search(
            r"\b(?:FIR|case|no)\b[\s-]*#?([A-Za-z0-9_/]+)\b", question, re.IGNORECASE
        )
        if case_match:
            entities["case_id"] = case_match.group(1)
        else:
            # Fallback check: if there is a slash pattern like 12/2025
            slash_match = re.search(r"\b(\d+/\d+)\b", question)
            if slash_match:
                entities["case_id"] = slash_match.group(1)

        # Accused ID (A followed by digits, e.g., A102, A210)
        accused_match = re.search(r"\bA\d+\b", question, re.IGNORECASE)
        if accused_match:
            entities["accused_id"] = accused_match.group(0).upper()

        # Victim ID (V followed by digits, e.g., V102)
        victim_match = re.search(r"\bV\d+\b", question, re.IGNORECASE)
        if victim_match:
            entities["victim_id"] = victim_match.group(0).upper()

        # District
        for d in self.DISTRICTS:
            if re.search(rf"\b{d}\b", question, re.IGNORECASE):
                entities["district"] = d
                break

        # Crime Type
        for kw, ct in self.CRIME_TYPES.items():
            if re.search(rf"\b{kw}\b", question, re.IGNORECASE):
                entities["crime_type"] = ct
                break

        # Police Station name preceding "station" or "police station"
        station_match = re.search(
            r"\b([A-Za-z0-9\s]+?)\s+(?:police\s+)?station\b", question, re.IGNORECASE
        )
        if station_match:
            station_name = station_match.group(1).strip()
            # Clean up words like "at", "the", "in", "this", "that"
            clean_station = re.sub(
                r"\b(?:at|the|in|this|that|which|handled|by)\b",
                "",
                station_name,
                flags=re.IGNORECASE,
            ).strip()
            if clean_station:
                entities["police_station"] = clean_station

        # Date Range
        year_match = re.search(r"\b(20\d{2})\b", question)
        if year_match:
            entities["date_range"] = year_match.group(1)
        elif "this month" in question.lower():
            entities["date_range"] = "this month"
        elif "this year" in question.lower():
            entities["date_range"] = "this year"
        elif "last year" in question.lower():
            entities["date_range"] = "last year"

        # 2. Parse Query Agent Response rows if available
        if response and response.get("status") == "success" and response.get("rows"):
            rows: List[Dict[str, Any]] = response["rows"]
            # Look at the first row to extract entities
            first_row = rows[0]

            # Map common database keys to our entity attributes
            db_mappings = {
                "case_id": ["crime_no", "case_no", "case_master_id"],
                "accused_id": ["accused_name", "accused_id", "accused_no"],
                "victim_id": ["victim_name", "victim_id", "victim_no"],
                "police_station": [
                    "police_station",
                    "police_station_name",
                    "station_name",
                ],
                "district": ["district", "district_name", "unit_name"],
                "crime_type": ["crime_type", "crime_type_name", "crime_head"],
            }

            for attr, keys in db_mappings.items():
                if (
                    attr not in entities
                ):  # Only extract if not already found in question
                    for k in keys:
                        val = first_row.get(k)
                        if val is not None:
                            # Verify if accused/victim match patterns
                            if attr == "accused_id" and not re.match(
                                r"^A\d+$", str(val)
                            ):
                                continue
                            if attr == "victim_id" and not re.match(
                                r"^V\d+$", str(val)
                            ):
                                continue
                            entities[attr] = str(val)
                            break

        return ResolvedEntity(**entities)
