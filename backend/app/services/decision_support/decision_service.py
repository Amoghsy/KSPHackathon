import datetime
import hashlib
import json
import logging
from typing import Any
from fastapi import HTTPException, status
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.case import CaseMaster
from app.models.police_station import PoliceStation
from app.models.crime_type import CrimeType
from app.models.accused import AccusedMaster
from app.models.financial_transaction import FinancialTransaction
from app.core.permissions import get_user_authorized_districts, resolve_authorized_districts, verify_district_access
from app.core.rbac import check_permission, normalize_role, Permission
from app.core.redis import get_redis_client
from app.agents.audit_agent.audit_agent import AuditAgent

from app.agents.decision_support_agent.case_summary import CaseSummaryBuilder
from app.agents.decision_support_agent.similar_case_search import SimilarityEngine
from app.agents.decision_support_agent.evidence_gap_analyzer import EvidenceGapAnalyzer
from app.agents.decision_support_agent.lead_generator import LeadGenerator
from app.agents.decision_support_agent.decision_support_agent import DecisionSupportAgent

# Import Day 5, 6, 8 services
from app.services.graph.graph_service import GraphService
from app.services.analytics.analytics_service import AnalyticsService
from app.services.risk.risk_service import RiskService

logger = logging.getLogger(__name__)

def get_scope_hash(current_user: dict, authorized_districts: list[str] | None) -> str:
    role = current_user.get("role", "")
    dist_str = ",".join(sorted(authorized_districts)) if authorized_districts else "__ALL__"
    data = {
        "role": role,
        "districts": dist_str
    }
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

class DecisionSupportService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.audit = AuditAgent()

    async def get_authorized_case(self, case_id: int, current_user: dict) -> CaseMaster:
        """
        Retrieves the case and enforces district ABAC.
        Raises 404 if not found, 403 if unauthorized.
        """
        stmt = (
            select(CaseMaster)
            .where(CaseMaster.case_master_id == case_id)
            .options(
                selectinload(CaseMaster.police_station),
                selectinload(CaseMaster.crime_type),
                selectinload(CaseMaster.accused),
                selectinload(CaseMaster.victims),
                selectinload(CaseMaster.financial_transactions).selectinload(
                    FinancialTransaction.accused
                )
            )
        )
        result = await self.db.execute(stmt)
        case = result.scalar_one_or_none()
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Case with ID {case_id} not found."
            )
            
        # Enforce ABAC
        case_district = case.police_station.district if case.police_station else None
        await verify_district_access(current_user, case_district, self.db)
        return case

    async def get_similar_cases(self, case_id: int, current_user: dict, limit: int = 5, min_score: float = 0.0) -> list[dict[str, Any]]:
        """
        Calculates similarity for cases. Enforces ABAC by masking cases outside authorized scope.
        """
        role = normalize_role(current_user.get("role"))
        # Deny ADMINISTRATOR and POLICY_MAKER
        if role == "ADMINISTRATOR":
            raise HTTPException(status_code=403, detail="Administrators do not have permission to view similar cases.")
        if role == "POLICY_MAKER":
            raise HTTPException(status_code=403, detail="Policy makers are restricted from case-specific similarity views.")

        # Get authorized districts
        auth_districts_raw = await get_user_authorized_districts(current_user, self.db)
        auth_districts = resolve_authorized_districts(auth_districts_raw)
        
        scope_hash = get_scope_hash(current_user, auth_districts)
        cache_key = f"similar:{case_id}:{scope_hash}:{limit}:{min_score}"
        
        # Try Cache
        try:
            redis_client = get_redis_client()
            cached = await redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning("Redis read error in DecisionSupportService (non-fatal): %s", e)

        # Load source case
        source_case = await self.get_authorized_case(case_id, current_user)
        has_sensitive_access = check_permission(current_user["role"], Permission.SENSITIVE_CASE_ACCESS)
        source_summary = CaseSummaryBuilder.build(source_case, has_sensitive_access=has_sensitive_access)
        
        # Retrieve candidate cases
        # To avoid O(N^2), prefilter cases sharing same crime type, or same district, or same accused person_id
        accused_pids = [a.person_id for a in source_case.accused if a.person_id]
        
        candidate_stmt = select(CaseMaster).options(
            selectinload(CaseMaster.police_station),
            selectinload(CaseMaster.crime_type),
            selectinload(CaseMaster.accused),
            selectinload(CaseMaster.victims),
            selectinload(CaseMaster.financial_transactions)
        ).where(CaseMaster.case_master_id != case_id)
        
        # Build pre-filtering conditions in SQL
        conditions = [CaseMaster.crime_type_id == source_case.crime_type_id]
        if source_case.police_station and source_case.police_station.district:
            # Match district (join PoliceStation)
            candidate_stmt = candidate_stmt.join(CaseMaster.police_station)
            conditions.append(PoliceStation.district == source_case.police_station.district)
            
        if accused_pids:
            # Match accused person_id
            conditions.append(CaseMaster.accused.any(AccusedMaster.person_id.in_(accused_pids)))
            
        candidate_stmt = candidate_stmt.where(or_(*conditions))
        
        res = await self.db.execute(candidate_stmt)
        candidates = res.unique().scalars().all()
        
        similar_list = []
        for cand in candidates:
            # Enforce district containment BEFORE returning details
            cand_district = cand.police_station.district if cand.police_station else None
            is_cand_authorized = True
            
            if auth_districts is not None:
                is_cand_authorized = cand_district in auth_districts
                
            cand_summary = CaseSummaryBuilder.build(cand, has_sensitive_access=has_sensitive_access)
            sim_res = SimilarityEngine.calculate_similarity(source_summary, cand_summary)
            
            score = sim_res["similarity_score"]
            if score < min_score:
                continue
                
            reasons = sim_res["reasons"]
            
            # Mask details if candidate case is unauthorized
            if not is_cand_authorized:
                similar_list.append({
                    "case_master_id": None,
                    "crime_no": "RESTRICTED",
                    "case_no": "RESTRICTED",
                    "crime_type": cand.crime_type.name if cand.crime_type else "Unknown",
                    "district": cand_district or "Restricted District",
                    "police_station": "RESTRICTED",
                    "similarity_score": score,
                    "reasons": [
                        "Potential related intelligence exists in restricted district scope.",
                        f"District: {cand_district}. Additional authorization required."
                    ],
                    "is_authorized": False,
                    "access_required": True
                })
            else:
                similar_list.append({
                    "case_master_id": cand.case_master_id,
                    "crime_no": cand.crime_no,
                    "case_no": cand.case_no,
                    "crime_type": cand.crime_type.name if cand.crime_type else "Unknown",
                    "district": cand_district or "Unknown",
                    "police_station": cand.police_station.name if cand.police_station else "Unknown",
                    "similarity_score": score,
                    "reasons": reasons,
                    "is_authorized": True,
                    "access_required": False
                })
                
        # Sort and limit
        similar_list.sort(key=lambda x: x["similarity_score"], reverse=True)
        results = similar_list[:limit]
        
        # Cache
        try:
            redis_client = get_redis_client()
            await redis_client.set(cache_key, json.dumps(results), ex=300)
        except Exception as e:
            logger.warning("Redis write error in DecisionSupportService (non-fatal): %s", e)
            
        return results

    async def get_evidence_gaps(self, case_id: int, current_user: dict) -> list[dict[str, Any]]:
        """
        Identifies missing components in the current case context.
        """
        source_case = await self.get_authorized_case(case_id, current_user)
        has_sensitive = check_permission(current_user["role"], Permission.SENSITIVE_CASE_ACCESS)
        summary = CaseSummaryBuilder.build(source_case, has_sensitive_access=has_sensitive)
        
        # Determine if repeat offender to trigger specific gaps
        is_repeat = False
        accused_pids = [a.person_id for a in source_case.accused if a.person_id]
        if accused_pids:
            # Query if these accused exist in other cases
            stmt = select(AccusedMaster).where(
                AccusedMaster.person_id.in_(accused_pids),
                AccusedMaster.case_master_id != case_id
            )
            res = await self.db.execute(stmt)
            if res.scalars().all():
                is_repeat = True
                
        return EvidenceGapAnalyzer.analyze(summary, is_repeat_offender=is_repeat)

    async def get_timeline(self, case_id: int, current_user: dict) -> list[dict[str, Any]]:
        """
        Builds a chronology of facts using actual timestamps.
        """
        source_case = await self.get_authorized_case(case_id, current_user)
        
        events = []
        # 1. Crime incident occurred
        if source_case.incident_from_date:
            events.append({
                "date": source_case.incident_from_date.isoformat(),
                "event": "Crime incident occurred (Commencement)",
                "details": f"Location coordinates: {source_case.latitude}, {source_case.longitude}" if source_case.latitude else ""
            })
        if source_case.incident_to_date:
            events.append({
                "date": source_case.incident_to_date.isoformat(),
                "event": "Crime incident concluded",
                "details": ""
            })
            
        # 2. Crime registered / FIR Filed
        events.append({
            "date": source_case.crime_registered_date.isoformat(),
            "event": "FIR Registered",
            "details": f"Crime No: {source_case.crime_no} at Police Station: {source_case.police_station.name if source_case.police_station else 'Unknown'}"
        })
        
        # 3. Accused identified
        for acc in source_case.accused:
            events.append({
                "date": source_case.crime_registered_date.isoformat(), # Defaulting to registration date
                "event": f"Accused identified: {acc.accused_name}",
                "details": f"Person ID: {acc.person_id or 'Not recorded'}"
            })
            
        # 4. Financial transactions logged
        for tx in source_case.financial_transactions:
            events.append({
                "date": tx.transaction_date.isoformat(),
                "event": f"Suspicious transaction recorded" if tx.is_suspicious else "Financial transaction logged",
                "details": f"Amount: ₹{tx.amount:.2f} (Bank: {tx.bank_name or 'Unknown'}). Link: {tx.source_account} -> {tx.destination_account}"
            })
            
        # Sort events chronologically
        events.sort(key=lambda x: x["date"])
        return events

    async def get_leads(self, case_id: int, current_user: dict) -> list[dict[str, Any]]:
        """
        Evaluates leads based on rules and composed permissions.
        """
        source_case = await self.get_authorized_case(case_id, current_user)
        has_sensitive = check_permission(current_user["role"], Permission.SENSITIVE_CASE_ACCESS)
        summary = CaseSummaryBuilder.build(source_case, has_sensitive_access=has_sensitive)
        
        # Retrieve similar cases
        sim_cases = await self.get_similar_cases(case_id, current_user, limit=5, min_score=0.0)
        
        # Check cross-district signals
        unauth_districts = []
        for sc in sim_cases:
            if not sc.get("is_authorized") and sc.get("district"):
                unauth_districts.append(sc["district"])
        unauth_districts = list(set(unauth_districts))
        
        # Get highest risk score for any accused (Day 8 Risk integration)
        highest_risk = 0.0
        is_repeat = False
        
        # Enforce composition: if user has risk access
        # In KSP, supervisors, senior investigators and investigators have risk access (investigators subject to district ABAC)
        # Administrators and Policy Makers are checked at service entry, so they don't call this
        try:
            risk_service = RiskService(self.db)
            for acc in source_case.accused:
                pid = acc.person_id or f"A_{acc.accused_name}"
                prof = await risk_service.get_offender_risk_profile(current_user, pid)
                if prof:
                    if prof.risk_score > highest_risk:
                        highest_risk = prof.risk_score
                    if prof.case_count > 1:
                        is_repeat = True
        except Exception as e:
            logger.warning("Failed to fetch risk profile for lead generator (non-fatal): %s", e)
            
        # Get community ID (Day 5 Network integration)
        community_id = None
        try:
            # Let's call GraphService to search focus_id
            graph_service = GraphService(self.db)
            net_data = await graph_service.get_criminal_network_data(focus_id=source_case.crime_no)
            # Find the nodes belonging to this case's accused and see if they share a community
            pids = [acc.person_id or f"A_{acc.accused_name}" for acc in source_case.accused]
            for comm in net_data.get("communities", []):
                # Check intersection of members
                comm_members = comm.get("members", [])
                if any(m in comm_members for m in pids):
                    community_id = comm.get("id")
                    break
        except Exception as e:
            logger.warning("Failed to fetch network communities for lead generator (non-fatal): %s", e)

        leads = LeadGenerator.generate_leads(
            case_summary=summary,
            similar_cases=sim_cases,
            is_repeat_offender=is_repeat,
            network_community_id=community_id,
            highest_risk_score=highest_risk,
            unauthorized_districts_with_signals=unauth_districts
        )
        
        # Composition filtering: remove financial leads if lacking permission
        has_fin_permission = check_permission(current_user["role"], Permission.FINANCIAL_CRIME)
        if not has_fin_permission:
            leads = [l for l in leads if l["type"] != "FINANCIAL_RELATIONSHIP"]
            
        return leads

    async def get_investigation_brief(self, case_id: int, current_user: dict, generate_ai_summary: bool = True) -> dict[str, Any]:
        """
        Orchestrates and builds the complete structured investigation brief + Gemini narrative summary.
        Caches the unified brief in Redis.
        """
        role = normalize_role(current_user.get("role"))
        # Deny ADMINISTRATOR and POLICY_MAKER
        if role == "ADMINISTRATOR":
            raise HTTPException(status_code=403, detail="Administrators do not have permission to view investigation briefs.")
        if role == "POLICY_MAKER":
            raise HTTPException(status_code=403, detail="Policy makers are restricted from case-specific briefs.")

        auth_districts_raw = await get_user_authorized_districts(current_user, self.db)
        auth_districts = resolve_authorized_districts(auth_districts_raw)
        
        scope_hash = get_scope_hash(current_user, auth_districts)
        cache_key = f"brief:{case_id}:{scope_hash}"
        
        # Try Cache
        try:
            redis_client = get_redis_client()
            cached = await redis_client.get(cache_key)
            if cached:
                # Log AUDIT log event for cache hit
                import uuid
                await self.audit.log_action(
                    self.db,
                    user_id=current_user.get("id"),
                    username=current_user.get("username"),
                    role=current_user.get("role"),
                    api=f"/api/v1/decision-support/case/{case_id}/brief",
                    request_id=f"brief-cache-{uuid.uuid4()}",
                    action="DECISION_SUPPORT_ACCESSED",
                    case_id=case_id,
                    district_id=auth_districts[0] if auth_districts else "All",
                    summary="Accessed cached investigation brief."
                )
                return json.loads(cached)
        except Exception as e:
            logger.warning("Redis read error in DecisionSupportService (non-fatal): %s", e)

        # 1. Fetch authorized case
        case = await self.get_authorized_case(case_id, current_user)
        has_sensitive = check_permission(current_user["role"], Permission.SENSITIVE_CASE_ACCESS)
        summary = CaseSummaryBuilder.build(case, has_sensitive_access=has_sensitive)
        
        # 2. Gather sub-modules
        similar = await self.get_similar_cases(case_id, current_user, limit=5, min_score=0.0)
        leads = await self.get_leads(case_id, current_user)
        gaps = await self.get_evidence_gaps(case_id, current_user)
        timeline = await self.get_timeline(case_id, current_user)
        
        # 3. Network findings composition
        network_findings = {}
        has_network_perm = check_permission(current_user["role"], Permission.CRIMINAL_NETWORK)
        if has_network_perm:
            try:
                graph_service = GraphService(self.db)
                net_data = await graph_service.get_criminal_network_data(focus_id=case.crime_no)
                network_findings = {
                    "node_count": net_data.get("node_count", 0),
                    "edge_count": net_data.get("edge_count", 0),
                    "density": net_data.get("density", 0.0),
                    "bridge_suspects": net_data.get("bridge_nodes", []),
                    "most_connected": net_data.get("most_connected", []),
                    "repeat_offenders_count": len(net_data.get("repeat_offenders", []))
                }
            except Exception as e:
                logger.warning("Failed network composition: %s", e)
                
        # 4. Risk findings composition
        risk_findings = {}
        try:
            risk_service = RiskService(self.db)
            highest_score = 0.0
            critical_count = 0
            behavioral_tags = []
            for acc in case.accused:
                pid = acc.person_id or f"A_{acc.accused_name}"
                prof = await risk_service.get_offender_risk_profile(current_user, pid)
                if prof:
                    if prof.risk_score > highest_score:
                        highest_score = prof.risk_score
                    if prof.risk_level == "CRITICAL":
                        critical_count += 1
                    for t in prof.behavioral_tags:
                        if t.label not in behavioral_tags:
                            behavioral_tags.append(t.label)
                            
            risk_findings = {
                "highest_risk_score": highest_score,
                "critical_offenders_count": critical_count,
                "behavioral_tags": behavioral_tags
            }
        except Exception as e:
            logger.warning("Failed risk composition: %s", e)
            
        # 5. Financial findings composition (Strict permission control)
        financial_findings = {}
        has_fin_permission = check_permission(current_user["role"], Permission.FINANCIAL_CRIME)
        if has_fin_permission:
            susp_count = sum(1 for tx in summary.get("financial_transactions", []) if tx.get("is_suspicious"))
            tot_val = sum(tx.get("amount", 0.0) for tx in summary.get("financial_transactions", []))
            financial_findings = {
                "total_transactions": len(summary.get("financial_transactions", [])),
                "suspicious_transactions_count": susp_count,
                "total_transaction_value": tot_val
            }
        else:
            # Strip financial transactions from summary before brief construction
            summary["financial_transactions"] = []

        # 6. Pattern findings composition
        pattern_findings = {}
        try:
            analytics_service = AnalyticsService(self.db, authorized_districts=auth_districts)
            anom = await analytics_service.get_anomalies(district=case.police_station.district, crime_type=case.crime_type.name if case.crime_type else None)
            pattern_findings = {
                "district_anomalies_count": len(anom),
                "district": case.police_station.district
            }
        except Exception as e:
            logger.warning("Failed pattern composition: %s", e)

        # Assemble unified brief
        brief = {
            "case": summary,
            "network_findings": network_findings,
            "risk_findings": risk_findings,
            "financial_findings": financial_findings,
            "pattern_findings": pattern_findings,
            "similar_cases": similar,
            "leads": leads,
            "evidence_gaps": gaps,
            "timeline": timeline
        }
        
        # 7. Narrative AI Briefing (Google Gemini summary with fallback)
        ai_summary = "AI narrative summary temporarily unavailable."
        if generate_ai_summary:
            agent = DecisionSupportAgent()
            ai_summary = await agent.generate_summary(brief)
            
        brief["ai_summary"] = ai_summary
        
        # 8. Redis Cache Set
        try:
            redis_client = get_redis_client()
            await redis_client.set(cache_key, json.dumps(brief), ex=300)
        except Exception as e:
            logger.warning("Redis write error in DecisionSupportService (non-fatal): %s", e)
            
        # 9. Audit log security trail
        import uuid
        case_dist = case.police_station.district if case.police_station else "Unknown"
        cross_district_signal_detected = any(l.get("type") == "CROSS_DISTRICT_SIGNAL" for l in leads)
        
        await self.audit.log_action(
            self.db,
            user_id=current_user.get("id"),
            username=current_user.get("username"),
            role=current_user.get("role"),
            api=f"/api/v1/decision-support/case/{case_id}/brief",
            request_id=f"brief-gen-{uuid.uuid4()}",
            action="INVESTIGATION_BRIEF_GENERATED",
            case_id=case_id,
            district_id=case_dist,
            summary=f"Generated brief and decision support profile for case {case.crime_no}."
        )
        
        if cross_district_signal_detected:
            await self.audit.log_action(
                self.db,
                user_id=current_user.get("id"),
                username=current_user.get("username"),
                role=current_user.get("role"),
                api=f"/api/v1/decision-support/case/{case_id}/brief",
                request_id=f"cross-sig-{uuid.uuid4()}",
                action="CROSS_DISTRICT_SIGNAL_DETECTED",
                case_id=case_id,
                district_id=case_dist,
                summary=f"Cross-district similarity signals detected for case {case.crime_no}."
            )
            
        return brief
