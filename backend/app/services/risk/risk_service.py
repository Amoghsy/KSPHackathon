import hashlib
import json
import logging
import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.core.redis import get_redis_client
from app.core.permissions import get_user_authorized_districts, resolve_authorized_districts
from app.core.rbac import normalize_role, check_permission, Permission
from app.utils.masking import mask_name
from app.repositories.risk_repository import RiskRepository
from app.agents.risk_agent.risk_models import OffenderRiskProfile
from app.agents.risk_agent.risk_scoring import RiskScoringEngine
from app.agents.risk_agent.behavioral_tagging import BehavioralTagger
from app.agents.network_agent.graph_builder import GraphBuilder
from app.agents.network_agent.graph_analyzer import GraphAnalyzer
from app.services.graph.graph_utils import normalize_name

logger = logging.getLogger(__name__)

class RiskService:
    """
    Service class responsible for coordinating offender risk intelligence profiling,
    ABAC security containment, and Redis caching.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_offenders_risk_profiles(
        self,
        current_user: dict | None,
        district: str | None = None,
        minimum_score: float | None = None,
        risk_level: str | None = None,
        limit: int = 50,
        offset: int = 0
    ) -> list[OffenderRiskProfile]:
        """
        Calculate offender risk intelligence profiles restricted by authorized districts.
        """
        # 1. Check permissions / RBAC
        # Platform administrators are denied access to individual offender profiles
        if current_user:
            role = normalize_role(current_user.get("role"))
            if role == "ADMINISTRATOR":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Administrators do not have permission to view investigative offender risk profiles."
                )

        # 2. Get authorized districts under ABAC
        auth_districts_raw = await get_user_authorized_districts(current_user, self.db)
        auth_districts = resolve_authorized_districts(auth_districts_raw)

        # 3. Check Redis cache first
        auth_str = ",".join(sorted(auth_districts)) if auth_districts else "__ALL__"
        scope_data = {
            "auth_districts": auth_str,
            "district": district,
            "minimum_score": minimum_score,
            "risk_level": risk_level,
            "limit": limit,
            "offset": offset
        }
        scope_hash = hashlib.sha256(json.dumps(scope_data, sort_keys=True).encode()).hexdigest()
        cache_key = f"risk:offenders:{scope_hash}"

        try:
            redis_client = get_redis_client()
            cached_raw = await redis_client.get(cache_key)
            if cached_raw:
                logger.info("RiskService CACHE HIT key=%s", cache_key)
                cached_list = json.loads(cached_raw)
                return [OffenderRiskProfile.model_validate(p) for p in cached_list]
        except Exception as exc:
            logger.warning("Redis read error in RiskService (non-fatal): %s", exc)

        # 4. Fetch data from DB
        repo = RiskRepository(self.db, authorized_districts=auth_districts)
        
        # We need the full graph to compute centralities and communities accurately
        cases, accused, victims, transactions = await repo.get_authorized_cases_with_relations(district)
        
        # Build network graph
        G = GraphBuilder.build_criminal_network(cases, accused, victims, transactions)
        centrality = GraphAnalyzer.calculate_centrality(G)
        pageranks = centrality.get("pagerank", {})
        communities = GraphAnalyzer.detect_communities(G, pageranks)

        # Group accused records by person_id or name
        offenders_raw = await repo.get_authorized_offenders_data(district)
        grouped_offenders = {}
        for acc in offenders_raw:
            pid = acc.person_id or f"A_{normalize_name(acc.accused_name)}"
            if pid not in grouped_offenders:
                grouped_offenders[pid] = {
                    "person_id": pid,
                    "name": acc.accused_name,
                    "accused_records": [],
                    "cases": set(),
                    "transactions": set(),
                    "suspicious_transactions": set(),
                    "crime_types": set(),
                    "districts": set(),
                    "max_gravity": None,
                    "recently_active": False,
                }
            
            grouped_offenders[pid]["accused_records"].append(acc)
            if acc.case:
                case = acc.case
                grouped_offenders[pid]["cases"].add(case.case_master_id)
                if case.gravity_offence_id is not None:
                    if grouped_offenders[pid]["max_gravity"] is None or case.gravity_offence_id > grouped_offenders[pid]["max_gravity"]:
                        grouped_offenders[pid]["max_gravity"] = case.gravity_offence_id
                
                # Check recent activity (180 days)
                if case.crime_registered_date:
                    # Convert to datetime if it's not
                    reg_date = case.crime_registered_date
                    if isinstance(reg_date, str):
                        reg_date = datetime.datetime.fromisoformat(reg_date)
                    days_diff = (datetime.datetime.utcnow() - reg_date).days
                    if days_diff <= 180:
                        grouped_offenders[pid]["recently_active"] = True
                
                if case.police_station:
                    grouped_offenders[pid]["districts"].add(case.police_station.district)
                
                if case.crime_type:
                    grouped_offenders[pid]["crime_types"].add(case.crime_type.name)

            for tx in acc.financial_transactions:
                grouped_offenders[pid]["transactions"].add(tx.financial_transaction_id)
                if tx.is_suspicious:
                    grouped_offenders[pid]["suspicious_transactions"].add(tx.financial_transaction_id)

        # Process each offender profile
        profiles = []
        has_sensitive_access = False
        if current_user:
            role = normalize_role(current_user.get("role"))
            has_sensitive_access = check_permission(role, Permission.SENSITIVE_CASE_ACCESS)

        for pid, data in grouped_offenders.items():
            case_count = len(data["cases"])
            unique_districts_count = len(data["districts"])
            network_degree = G.degree(pid) if pid in G else 0
            transaction_count = len(data["transactions"])
            suspicious_transaction_count = len(data["suspicious_transactions"])
            crime_types_count = len(data["crime_types"])
            recently_active = data["recently_active"]
            
            # Community gang membership
            is_in_community = any(pid in comm["member_ids"] for comm in communities if len(comm["member_ids"]) >= 3)

            # Score computation
            score, factors, level = RiskScoringEngine.calculate_score(
                case_count=case_count,
                max_gravity_offence_id=data["max_gravity"],
                unique_districts_count=unique_districts_count,
                network_degree=network_degree,
                transaction_count=transaction_count,
                suspicious_transaction_count=suspicious_transaction_count,
                crime_types_count=crime_types_count
            )

            # Check filters
            if minimum_score is not None and score < minimum_score:
                continue
            if risk_level is not None and level.upper() != risk_level.upper():
                continue

            # Tag generation
            tags = BehavioralTagger.generate_tags(
                case_count=case_count,
                unique_districts_count=unique_districts_count,
                network_degree=network_degree,
                transaction_count=transaction_count,
                suspicious_transaction_count=suspicious_transaction_count,
                crime_types_count=crime_types_count,
                recently_active=recently_active,
                is_in_community=is_in_community,
                districts=list(data["districts"])
            )

            # Name masking based on permissions
            name = data["name"]
            if not has_sensitive_access:
                name = mask_name(name)

            profiles.append(
                OffenderRiskProfile(
                    person_id=pid,
                    name=name,
                    risk_score=score,
                    risk_level=level,
                    risk_factors=factors,
                    behavioral_tags=tags,
                    district=list(data["districts"])[0] if data["districts"] else "Unknown",
                    case_count=case_count
                )
            )

        # Sort profiles by risk score descending
        profiles.sort(key=lambda p: p.risk_score, reverse=True)

        # Cache all compiled profiles
        try:
            redis_client = get_redis_client()
            await redis_client.set(cache_key, json.dumps([p.model_dump() for p in profiles]), ex=300)
            logger.info("RiskService CACHE SET key=%s", cache_key)
        except Exception as exc:
            logger.warning("Redis write error in RiskService (non-fatal): %s", exc)

        # Apply limit / offset
        return profiles[offset : offset + limit]

    async def get_offender_risk_profile(
        self,
        current_user: dict | None,
        accused_id: str
    ) -> OffenderRiskProfile | None:
        """
        Retrieve risk profile for a single offender by person_id / node ID.
        """
        # Load all profiles for the user's authorized scope
        profiles = await self.get_offenders_risk_profiles(current_user=current_user, limit=5000)
        for p in profiles:
            if p.person_id == accused_id:
                return p
        return None

    async def get_risk_summary(
        self,
        current_user: dict | None,
        district: str | None = None
    ) -> dict:
        """
        Return aggregates of risk distribution (Policy Makers / Analysts read-only view).
        """
        # Load profiles
        profiles = await self.get_offenders_risk_profiles(current_user=current_user, district=district, limit=5000)
        
        distribution = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
        for p in profiles:
            distribution[p.risk_level] = distribution.get(p.risk_level, 0) + 1

        return {
            "total_offenders_analyzed": len(profiles),
            "risk_distribution": distribution
        }
