from typing import Any

class LeadGenerator:
    """
    Generates deterministic, traceable, evidence-backed investigative leads.
    """
    @staticmethod
    def generate_leads(
        case_summary: dict[str, Any],
        similar_cases: list[dict[str, Any]],
        is_repeat_offender: bool = False,
        network_community_id: int | None = None,
        highest_risk_score: float = 0.0,
        unauthorized_districts_with_signals: list[str] | None = None
    ) -> list[dict[str, Any]]:
        leads = []
        lead_counter = 1
        
        # Helper to format lead dict
        def make_lead(lead_type: str, title: str, description: str, priority: str, confidence: float, evidence: dict, source_modules: list[str]) -> dict:
            nonlocal lead_counter
            lead_id = f"LEAD-{lead_counter:03d}"
            lead_counter += 1
            return {
                "lead_id": lead_id,
                "type": lead_type,
                "title": title,
                "description": description,
                "priority": priority,
                "confidence": confidence,
                "evidence": evidence,
                "source_modules": source_modules,
                "required_permissions": [],
                "status": "PENDING"
            }

        # Rule 1: Repeat Offender
        # If the same person_id appears in multiple cases (or is marked as repeat offender)
        pids = [acc["person_id"] for acc in case_summary.get("accused", []) if acc.get("person_id")]
        if is_repeat_offender and pids:
            # Find similar cases that share these pids
            linked_case_ids = []
            for sc in similar_cases:
                # Check if it mentions shared accused in reasons
                if any("shared accused" in r.lower() for r in sc.get("reasons", [])) and sc.get("case_master_id"):
                    linked_case_ids.append(sc["case_master_id"])
                    
            leads.append(make_lead(
                lead_type="CROSS_CASE_LINK",
                title="Review linked FIRs involving the same recorded person",
                description=f"Accused person(s) in this case ({', '.join(pids)}) have historical records in other cases.",
                priority="CRITICAL" if highest_risk_score >= 75.0 else "HIGH",
                confidence=0.95,
                evidence={
                    "person_ids": pids,
                    "linked_cases": linked_case_ids or "See similar cases list"
                },
                source_modules=["Case Intelligence", "Network Intelligence"]
            ))

        # Rule 2: Financial Transactions connection
        txs = case_summary.get("financial_transactions", [])
        suspicious_txs = [tx for tx in txs if tx.get("is_suspicious")]
        if suspicious_txs:
            leads.append(make_lead(
                lead_type="FINANCIAL_RELATIONSHIP",
                title="Review verified financial relationships between linked accused",
                description=f"Detected {len(suspicious_txs)} suspicious financial transaction records linked to the accused in this case.",
                priority="HIGH",
                confidence=0.95,
                evidence={
                    "transaction_ids": [tx["financial_transaction_id"] for tx in suspicious_txs],
                    "total_suspicious_amount": sum(tx["amount"] for tx in suspicious_txs)
                },
                source_modules=["Case Intelligence", "Financial Crime"]
            ))

        # Rule 3: Crime pattern MO similarity
        # If cases share crime type + location + time pattern
        high_similarity_cases = [sc for sc in similar_cases if sc.get("similarity_score", 0) >= 60]
        mo_case_ids = []
        for sc in high_similarity_cases:
            reasons_lower = [r.lower() for r in sc.get("reasons", [])]
            has_mo_clues = any("crime type" in r or "modus operandi" in r or "proximity" in r for r in reasons_lower)
            if has_mo_clues and sc.get("case_master_id"):
                mo_case_ids.append(sc["case_master_id"])
                
        if mo_case_ids:
            leads.append(make_lead(
                lead_type="PATTERN_COMPARISON",
                title="Compare cases for a possible repeated modus-operandi pattern",
                description=f"Identified {len(mo_case_ids)} candidate case(s) with high structural similarity (score >= 60%).",
                priority="HIGH" if len(mo_case_ids) >= 2 else "MEDIUM",
                confidence=0.75,
                evidence={
                    "similar_case_ids": mo_case_ids,
                    "crime_type": case_summary.get("crime_type")
                },
                source_modules=["Pattern Intelligence", "Case Similarity"]
            ))

        # Rule 4: Shared Network Community
        if network_community_id is not None:
            leads.append(make_lead(
                lead_type="NETWORK_COMMUNITY",
                title="Review the detected network community for verified cross-case relationships",
                description=f"Accused in this case are associated with detected criminal network community ID: {network_community_id}.",
                priority="MEDIUM",
                confidence=0.85,
                evidence={
                    "community_id": network_community_id
                },
                source_modules=["Network Intelligence"]
            ))

        # Rule 5: High Risk Offender
        if highest_risk_score >= 70.0:
            leads.append(make_lead(
                lead_type="HIGH_RISK_SUSPECT",
                title="Review recorded history and verified network relationships of high-priority suspect",
                description=f"One or more suspects linked to this case have critical behavioral risk ratings (highest risk score: {highest_risk_score:.1f}).",
                priority="CRITICAL" if highest_risk_score >= 80.0 else "HIGH",
                confidence=0.90,
                evidence={
                    "highest_risk_score": highest_risk_score
                },
                source_modules=["Risk Intelligence"]
            ))

        # Rule 6: Cross-District Signals
        if unauthorized_districts_with_signals:
            for dist in unauthorized_districts_with_signals:
                leads.append(make_lead(
                    lead_type="CROSS_DISTRICT_SIGNAL",
                    title=f"Potential related intelligence exists in {dist} district",
                    description=f"Decision Support has detected matching patterns/similar cases in {dist} district outside your authorized scope.",
                    priority="HIGH",
                    confidence=0.80,
                    evidence={
                        "restricted_district": dist,
                        "action_required": "Request temporary district access under Day 7 workflow to view case details."
                    },
                    source_modules=["Case Intelligence", "District ABAC"]
                ))

        return leads
