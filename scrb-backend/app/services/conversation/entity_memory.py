"""
app/services/conversation/entity_memory.py — Entity memory representation.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


class EntityMemory:
    """
    Manages the entity memory of a conversation.
    Tracks context such as the last referenced case, accused, victim, etc.
    """

    def __init__(
        self,
        last_case: Optional[str] = None,
        last_accused: Optional[str] = None,
        last_victim: Optional[str] = None,
        last_station: Optional[str] = None,
        last_district: Optional[str] = None,
        last_crime_type: Optional[str] = None,
        last_date_range: Optional[str] = None,
    ) -> None:
        self.last_case = last_case
        self.last_accused = last_accused
        self.last_victim = last_victim
        self.last_station = last_station
        self.last_district = last_district
        self.last_crime_type = last_crime_type
        self.last_date_range = last_date_range

    def to_dict(self) -> Dict[str, Optional[str]]:
        """Serialize entity memory to a dictionary."""
        return {
            "last_case": self.last_case,
            "last_accused": self.last_accused,
            "last_victim": self.last_victim,
            "last_station": self.last_station,
            "last_district": self.last_district,
            "last_crime_type": self.last_crime_type,
            "last_date_range": self.last_date_range,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EntityMemory:
        """Create EntityMemory instance from dictionary data."""
        return cls(
            last_case=data.get("last_case") or data.get("case_id"),
            last_accused=data.get("last_accused") or data.get("accused_id"),
            last_victim=data.get("last_victim") or data.get("victim_id"),
            last_station=data.get("last_station") or data.get("police_station"),
            last_district=data.get("last_district") or data.get("district"),
            last_crime_type=data.get("last_crime_type") or data.get("crime_type"),
            last_date_range=data.get("last_date_range") or data.get("date_range"),
        )

    def update(self, new_entities: Dict[str, Any]) -> None:
        """
        Update entity memory with new entity values.
        Only overwrites values if they are provided and not None.
        """
        mappings = {
            "case": ["last_case", "case_id", "case"],
            "accused": ["last_accused", "accused_id", "accused"],
            "victim": ["last_victim", "victim_id", "victim"],
            "station": ["last_station", "police_station", "station"],
            "district": ["last_district", "district"],
            "crime_type": ["last_crime_type", "crime_type"],
            "date_range": ["last_date_range", "date_range"],
        }
        for attr, keys in mappings.items():
            for key in keys:
                val = new_entities.get(key)
                if val is not None:
                    setattr(self, f"last_{attr}", str(val))
                    break
