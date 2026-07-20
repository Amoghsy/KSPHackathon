from app.agents.risk_agent.risk_models import RiskFactorModel

class RiskScoringEngine:
    """
    Deterministic risk scoring engine that calculates the Prioritization Score (0-100)
    using only verified indicators.
    """

    @staticmethod
    def calculate_score(
        case_count: int,
        max_gravity_offence_id: int | None,
        unique_districts_count: int,
        network_degree: int,
        transaction_count: int,
        suspicious_transaction_count: int,
        crime_types_count: int
    ) -> tuple[float, list[RiskFactorModel], str]:
        factors = []

        # 1. Repeat case links (Max 25)
        repeat_score = 0.0
        if case_count == 1:
            repeat_score = 0.0
        elif case_count == 2:
            repeat_score = 8.0
        elif case_count == 3:
            repeat_score = 15.0
        elif case_count == 4:
            repeat_score = 20.0
        elif case_count >= 5:
            repeat_score = 25.0
        
        factors.append(RiskFactorModel(
            name="repeat_offending",
            label="Repeat Offending (Max 25)",
            score=repeat_score,
            max_score=25.0,
            reason=f"Linked to {case_count} recorded FIR/case records."
        ))

        # 2. Crime Severity (Max 15)
        severity_score = 0.0
        reason_severity = "No severity information on record."
        if max_gravity_offence_id is not None:
            # 4=Grievous, 3=High, 2=Medium, 1=Low
            if max_gravity_offence_id == 4:
                severity_score = 15.0
                reason_severity = "Linked to grievous offence record."
            elif max_gravity_offence_id == 3:
                severity_score = 10.0
                reason_severity = "Linked to high gravity offence record."
            elif max_gravity_offence_id == 2:
                severity_score = 5.0
                reason_severity = "Linked to medium gravity offence record."
            elif max_gravity_offence_id == 1:
                severity_score = 2.0
                reason_severity = "Linked to low gravity offence record."
            else:
                reason_severity = "Unknown severity level."
        
        factors.append(RiskFactorModel(
            name="crime_severity",
            label="Crime Severity (Max 15)",
            score=severity_score,
            max_score=15.0,
            reason=reason_severity
        ))

        # 3. Cross-district activity (Max 15)
        district_score = 0.0
        if unique_districts_count == 1:
            district_score = 0.0
        elif unique_districts_count == 2:
            district_score = 6.0
        elif unique_districts_count == 3:
            district_score = 10.0
        elif unique_districts_count >= 4:
            district_score = 15.0

        factors.append(RiskFactorModel(
            name="cross_district_activity",
            label="Cross-District Activity (Max 15)",
            score=district_score,
            max_score=15.0,
            reason=f"Recorded case activity across {unique_districts_count} districts."
        ))

        # 4. Network influence (Max 15)
        network_score = 0.0
        if network_degree >= 8:
            network_score = 15.0
        elif network_degree >= 5:
            network_score = 12.0
        elif network_degree >= 3:
            network_score = 8.0
        elif network_degree >= 2:
            network_score = 5.0
        elif network_degree == 1:
            network_score = 2.0

        factors.append(RiskFactorModel(
            name="network_influence",
            label="Network Influence (Max 15)",
            score=network_score,
            max_score=15.0,
            reason=f"Has {network_degree} connections within the intelligence network."
        ))

        # 5. Financial links (Max 15)
        fin_score = 0.0
        if transaction_count == 1:
            fin_score = 5.0
        elif transaction_count == 2:
            fin_score = 10.0
        elif transaction_count >= 3:
            fin_score = 15.0

        factors.append(RiskFactorModel(
            name="financial_links",
            label="Financial Links (Max 15)",
            score=fin_score,
            max_score=15.0,
            reason=f"Linked to {transaction_count} transaction records in financial graph."
        ))

        # 6. Suspicious transactions (Max 10)
        susp_score = 0.0
        if suspicious_transaction_count == 1:
            susp_score = 5.0
        elif suspicious_transaction_count >= 2:
            susp_score = 10.0

        factors.append(RiskFactorModel(
            name="suspicious_transactions",
            label="Suspicious Transactions (Max 10)",
            score=susp_score,
            max_score=10.0,
            reason=f"Flagged with {suspicious_transaction_count} suspicious transaction indicators."
        ))

        # 7. Crime-type diversity (Max 5)
        diversity_score = 0.0
        if crime_types_count == 2:
            diversity_score = 3.0
        elif crime_types_count >= 3:
            diversity_score = 5.0

        factors.append(RiskFactorModel(
            name="crime_type_diversity",
            label="Crime-Type Diversity (Max 5)",
            score=diversity_score,
            max_score=5.0,
            reason=f"Operates across {crime_types_count} distinct categories of crime."
        ))

        # Compute total
        total_score = sum(f.score for f in factors)
        total_score = min(100.0, max(0.0, total_score))

        # Classify risk level
        if total_score >= 80:
            level = "CRITICAL"
        elif total_score >= 60:
            level = "HIGH"
        elif total_score >= 35:
            level = "MEDIUM"
        else:
            level = "LOW"

        return total_score, factors, level
