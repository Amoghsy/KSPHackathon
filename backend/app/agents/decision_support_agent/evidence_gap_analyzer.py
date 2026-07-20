from typing import Any

class EvidenceGapAnalyzer:
    """
    Analyzes case summaries to identify missing metadata, lack of evidence, or classification gaps.
    """
    @staticmethod
    def analyze(case_summary: dict[str, Any], is_repeat_offender: bool = False) -> list[dict[str, Any]]:
        gaps = []
        
        # 1. Check crime type classification
        if not case_summary.get("crime_type_id") or case_summary.get("crime_type") == "Unknown":
            gaps.append({
                "type": "MISSING_CRIME_CLASSIFICATION",
                "severity": "HIGH",
                "description": "No crime category type classification is assigned to this record.",
                "impact": "Core analysis, trends, and pattern matching are restricted."
            })
            
        # 2. Check victim data
        if not case_summary.get("victims"):
            gaps.append({
                "type": "MISSING_VICTIM_DATA",
                "severity": "MEDIUM",
                "description": "No victim details or profiles are recorded for this case.",
                "impact": "Victim association and profiling analysis cannot be executed."
            })
            
        # 3. Check geospatial data
        lat = case_summary.get("latitude")
        lon = case_summary.get("longitude")
        if lat is None or lon is None or lat == 0.0 or lon == 0.0:
            gaps.append({
                "type": "MISSING_GEOSPATIAL_DATA",
                "severity": "MEDIUM",
                "description": "Geospatial coordinates (latitude/longitude) are missing or invalid.",
                "impact": "Geographic hotspot detection and GIS mapping are unavailable for this case."
            })
            
        # 4. Check financial transaction logs for financial crimes
        crime_name = str(case_summary.get("crime_type", "")).lower()
        is_financial_crime = any(kw in crime_name for kw in ("financial", "fraud", "money", "laundering", "cyber", "theft", "robbery", "bribery"))
        if is_financial_crime and not case_summary.get("financial_transactions"):
            gaps.append({
                "type": "MISSING_FINANCIAL_DATA",
                "severity": "HIGH",
                "description": "No financial transaction logs are linked to this financial or property crime case.",
                "impact": "Money laundering flow, account tracing, and financial relationship analysis are disabled."
            })
            
        # 5. Check case status
        if not case_summary.get("case_status_id"):
            gaps.append({
                "type": "MISSING_CASE_STATUS",
                "severity": "LOW",
                "description": "No operational case status is recorded for this file.",
                "impact": "Tracking progress of the investigation and timeline status updates is limited."
            })
            
        # 6. Check cross-case review notes for repeat offenders
        brief_facts = str(case_summary.get("brief_facts", "")).lower()
        has_cross_notes = any(kw in brief_facts for kw in ("linked", "similar", "repeat", "associated case", "fir", "cr-"))
        if is_repeat_offender and not has_cross_notes:
            gaps.append({
                "type": "CROSS_CASE_REVIEW_INCOMPLETE",
                "severity": "MEDIUM",
                "description": "Offender is linked to other cases, but cross-case intelligence notes are missing from facts.",
                "impact": "Investigating officers may lack awareness of Modus Operandi links across historical files."
            })
            
        return gaps
