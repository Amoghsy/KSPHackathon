import math
from datetime import date
from typing import Any

def haversine_distance(lat1: float | None, lon1: float | None, lat2: float | None, lon2: float | None) -> float | None:
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return None
    try:
        # Radius of Earth in kilometers
        R = 6371.0
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        
        a = math.sin(delta_phi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return R * c
    except Exception:
        return None

def date_diff_days(date_str1: str | None, date_str2: str | None) -> int:
    if not date_str1 or not date_str2:
        return 9999
    try:
        d1 = date.fromisoformat(date_str1.split("T")[0])
        d2 = date.fromisoformat(date_str2.split("T")[0])
        return abs((d1 - d2).days)
    except Exception:
        return 9999

class SimilarityEngine:
    """
    Computes explainable, deterministic similarity between two case summaries.
    """
    @staticmethod
    def calculate_similarity(case_a: dict[str, Any], case_b: dict[str, Any]) -> dict[str, Any]:
        score = 0
        reasons = []
        
        # 1. Same Crime Type (+25)
        if case_a.get("crime_type_id") == case_b.get("crime_type_id") and case_a.get("crime_type_id") is not None:
            score += 25
            reasons.append(f"Same crime type: {case_a.get('crime_type')}")
            
        # 2. Same Crime Head / Modus Operandi (+20)
        if case_a.get("crime_major_head_id") == case_b.get("crime_major_head_id") and case_a.get("crime_major_head_id") is not None:
            score += 20
            reasons.append("Same major crime head (similar Modus Operandi category)")
            
        # 3. Shared Accused / Person ID (+30)
        pids_a = {acc["person_id"] for acc in case_a.get("accused", []) if acc.get("person_id")}
        pids_b = {acc["person_id"] for acc in case_b.get("accused", []) if acc.get("person_id")}
        shared_pids = pids_a.intersection(pids_b)
        if shared_pids:
            score += 30
            reasons.append(f"Shared accused person(s): {', '.join(shared_pids)}")
            
        # 4. Shared Financial Account (+25)
        accounts_a = set()
        for tx in case_a.get("financial_transactions", []):
            if tx.get("source_account"): accounts_a.add(tx["source_account"])
            if tx.get("destination_account"): accounts_a.add(tx["destination_account"])
            
        accounts_b = set()
        for tx in case_b.get("financial_transactions", []):
            if tx.get("source_account"): accounts_b.add(tx["source_account"])
            if tx.get("destination_account"): accounts_b.add(tx["destination_account"])
            
        shared_accounts = accounts_a.intersection(accounts_b)
        if shared_accounts:
            score += 25
            reasons.append(f"Shared financial account: {', '.join(shared_accounts)}")
            
        # 5. Same or Nearby Location (+10)
        dist = haversine_distance(
            case_a.get("latitude"), case_a.get("longitude"),
            case_b.get("latitude"), case_b.get("longitude")
        )
        if dist is not None and dist <= 5.0:
            score += 10
            reasons.append(f"Geographical proximity: cases occurred within {dist:.2f} km of each other")
            
        # 6. Same District (+5)
        if case_a.get("district") == case_b.get("district") and case_a.get("district") not in (None, "Unknown"):
            score += 5
            reasons.append(f"Both cases occurred in {case_a.get('district')} district")
            
        # 7. Same Police Station (+5)
        if case_a.get("police_station_id") == case_b.get("police_station_id") and case_a.get("police_station_id") is not None:
            score += 5
            reasons.append(f"Both cases occurred in same police station area: {case_a.get('police_station')}")
            
        # 8. Similar Time Pattern (+10)
        days = date_diff_days(case_a.get("crime_registered_date"), case_b.get("crime_registered_date"))
        if days <= 30:
            score += 10
            reasons.append(f"Temporal proximity: registered within {days} days of each other")
            
        # 9. Shared Victim (+15)
        victims_a = {v["victim_name"].strip().lower() for v in case_a.get("victims", []) if v.get("victim_name")}
        victims_b = {v["victim_name"].strip().lower() for v in case_b.get("victims", []) if v.get("victim_name")}
        shared_victims = victims_a.intersection(victims_b)
        if shared_victims:
            score += 15
            # Retrieve original capitalization
            shared_names = []
            for v in case_a.get("victims", []):
                if v.get("victim_name", "").strip().lower() in shared_victims:
                    shared_names.append(v["victim_name"])
            reasons.append(f"Shared victim(s): {', '.join(set(shared_names))}")
            
        # Normalize
        final_score = min(100, score)
        
        return {
            "similarity_score": final_score,
            "reasons": reasons
        }
