from app.agents.risk_agent.risk_models import BehavioralTagModel

class BehavioralTagger:
    """
    Tagger class assigning deterministic intelligence tags based on raw indicators.
    """

    @staticmethod
    def generate_tags(
        case_count: int,
        unique_districts_count: int,
        network_degree: int,
        transaction_count: int,
        suspicious_transaction_count: int,
        crime_types_count: int,
        recently_active: bool,
        is_in_community: bool,
        districts: list[str]
    ) -> list[BehavioralTagModel]:
        tags = []

        # 1. REPEAT_OFFENDER
        if case_count >= 3:
            tags.append(BehavioralTagModel(
                code="REPEAT_OFFENDER",
                label="Repeat Offender",
                reason=f"Suspect is linked to {case_count} distinct cases on record.",
                evidence=f"Case count: {case_count}"
            ))

        # 2. CROSS_DISTRICT
        if unique_districts_count >= 2:
            tags.append(BehavioralTagModel(
                code="CROSS_DISTRICT",
                label="Cross-District Operations",
                reason=f"Suspect has active cases spanning multiple districts: {', '.join(districts)}.",
                evidence=f"Span: {unique_districts_count} districts"
            ))

        # 3. HIGHLY_CONNECTED
        if network_degree >= 5:
            tags.append(BehavioralTagModel(
                code="HIGHLY_CONNECTED",
                label="Highly Connected",
                reason=f"Suspect holds a highly connected position within the criminal network with {network_degree} links.",
                evidence=f"Network Degree: {network_degree}"
            ))

        # 4. NETWORK_SIGNIFICANT
        if case_count >= 3 and network_degree >= 3:
            tags.append(BehavioralTagModel(
                code="NETWORK_SIGNIFICANT",
                label="Network Significant",
                reason=f"Suspect is a repeat offender with significant network links (cases: {case_count}, degree: {network_degree}).",
                evidence=f"Cases: {case_count}, Degree: {network_degree}"
            ))

        # 5. FINANCIAL_LINKED
        if transaction_count >= 1:
            tags.append(BehavioralTagModel(
                code="FINANCIAL_LINKED",
                label="Financial Crime Linked",
                reason=f"Suspect is linked to financial transaction records in the transactions log.",
                evidence=f"Transactions: {transaction_count}"
            ))

        # 6. SUSPICIOUS_FINANCIAL_ACTIVITY
        if suspicious_transaction_count >= 1:
            tags.append(BehavioralTagModel(
                code="SUSPICIOUS_FINANCIAL_ACTIVITY",
                label="Suspicious Financial Activity",
                reason=f"Linked to {suspicious_transaction_count} transactions explicitly flagged as suspicious.",
                evidence=f"Suspicious transactions: {suspicious_transaction_count}"
            ))

        # 7. MULTI_CRIME_PATTERN
        if crime_types_count >= 2:
            tags.append(BehavioralTagModel(
                code="MULTI_CRIME_PATTERN",
                label="Multi-Crime Pattern",
                reason=f"Suspect's modus operandi spans {crime_types_count} distinct crime categories.",
                evidence=f"Categories count: {crime_types_count}"
            ))

        # 8. RECENTLY_ACTIVE
        if recently_active:
            tags.append(BehavioralTagModel(
                code="RECENTLY_ACTIVE",
                label="Recently Active",
                reason="Recorded activity has occurred within the last 180 days.",
                evidence="Has case registered in last 180 days"
            ))

        # 9. POSSIBLE_GANG_ASSOCIATION
        if is_in_community:
            tags.append(BehavioralTagModel(
                code="POSSIBLE_GANG_ASSOCIATION",
                label="Possible Gang Association",
                reason="Network cluster analysis places the suspect in a coordinated crime community/gang.",
                evidence="Community detection positive"
            ))

        return tags
