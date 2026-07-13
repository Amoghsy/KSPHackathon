import logging
import networkx as nx

from app.models.case import CaseMaster
from app.models.accused import AccusedMaster
from app.models.victim import VictimMaster
from app.models.financial_transaction import FinancialTransaction
from app.services.graph.graph_utils import normalize_name

logger = logging.getLogger(__name__)


class GraphBuilder:
    """
    Builder class using NetworkX to construct investigation graphs
    from SQLAlchemy database entities.
    """

    @staticmethod
    def build_criminal_network(
        cases: list[CaseMaster],
        accused: list[AccusedMaster],
        victims: list[VictimMaster],
        transactions: list[FinancialTransaction],
    ) -> nx.Graph:
        """
        Builds a comprehensive undirected network graph.
        Nodes represent Cases, Accused (persons), Victims, Police Stations, and Crime Types.
        Edges represent relationships (Committed, Victim Of, Occurred At) and discovered
        co-offending or suspect link weights.
        """
        G = nx.Graph()

        # 1. Add Case Nodes
        case_map = {}
        for c in cases:
            case_id = f"C{c.case_master_id}"
            case_map[c.case_master_id] = case_id
            G.add_node(
                case_id,
                label=c.case_no or c.crime_no,
                kind="case",
                metadata={
                    "case_master_id": c.case_master_id,
                    "crime_no": c.crime_no,
                    "case_no": c.case_no,
                    "registered_date": str(c.crime_registered_date),
                    "brief_facts": c.brief_facts,
                    "gravity_offence_id": c.gravity_offence_id,
                },
            )

        # 2. Add Accused Nodes (grouped by person_id or normalised name)
        accused_by_person = {}
        for acc in accused:
            pid = acc.person_id or f"A_{normalize_name(acc.accused_name)}"
            if pid not in accused_by_person:
                accused_by_person[pid] = {
                    "id": pid,
                    "name": acc.accused_name,
                    "age": acc.age_year,
                    "gender": acc.gender_id,
                    "cases": [],
                    "accused_master_ids": [],
                }
            accused_by_person[pid]["cases"].append(acc.case_master_id)
            accused_by_person[pid]["accused_master_ids"].append(acc.accused_master_id)

        for pid, data in accused_by_person.items():
            G.add_node(
                pid,
                label=data["name"],
                kind="accused",
                metadata={
                    "person_id": pid,
                    "age": data["age"],
                    "gender": data["gender"],
                    "case_count": len(data["cases"]),
                    "accused_master_ids": data["accused_master_ids"],
                },
            )

            # Link Accused to their Cases
            for case_id in data["cases"]:
                if case_id in case_map:
                    G.add_edge(
                        pid,
                        case_map[case_id],
                        label="committed",
                        weight=5.0,
                        relationship="committed",
                    )

        # 3. Add Victim Nodes
        victim_by_name = {}
        for vic in victims:
            norm_name = normalize_name(vic.victim_name)
            vid = f"V_{norm_name}"
            if vid not in victim_by_name:
                victim_by_name[vid] = {
                    "id": vid,
                    "name": vic.victim_name,
                    "age": vic.age_year,
                    "gender": vic.gender_id,
                    "cases": [],
                }
            victim_by_name[vid]["cases"].append(vic.case_master_id)

        for vid, data in victim_by_name.items():
            G.add_node(
                vid,
                label=data["name"],
                kind="victim",
                metadata={
                    "age": data["age"],
                    "gender": data["gender"],
                    "case_count": len(data["cases"]),
                },
            )

            # Link Victims to their Cases
            for case_id in data["cases"]:
                if case_id in case_map:
                    G.add_edge(
                        vid,
                        case_map[case_id],
                        label="victim of",
                        weight=2.0,
                        relationship="victim of",
                    )

        # 4. Add Police Station & District Location Nodes
        for c in cases:
            case_id = f"C{c.case_master_id}"
            if c.police_station:
                ps = c.police_station
                ps_id = f"PS_{ps.police_station_id}"

                # Police Station node
                if ps_id not in G:
                    G.add_node(
                        ps_id,
                        label=ps.name,
                        kind="location",
                        metadata={
                            "police_station_id": ps.police_station_id,
                            "district": ps.district,
                            "type": "police_station",
                        },
                    )
                G.add_edge(
                    case_id,
                    ps_id,
                    label="occurred at",
                    weight=3.0,
                    relationship="occurred at",
                )

                # District node
                if ps.district:
                    dist_id = f"D_{normalize_name(ps.district)}"
                    if dist_id not in G:
                        G.add_node(
                            dist_id,
                            label=ps.district,
                            kind="location",
                            metadata={"type": "district", "name": ps.district},
                        )
                    G.add_edge(
                        ps_id,
                        dist_id,
                        label="in district",
                        weight=1.0,
                        relationship="in district",
                    )

            # Crime Type node
            if c.crime_type:
                ct = c.crime_type
                ct_id = f"CT_{ct.crime_type_id}"
                if ct_id not in G:
                    G.add_node(
                        ct_id,
                        label=ct.name,
                        kind="location",
                        metadata={"type": "crime_type", "crime_type_id": ct.crime_type_id},
                    )
                G.add_edge(
                    case_id,
                    ct_id,
                    label="crime category",
                    weight=1.0,
                    relationship="crime category",
                )

        # 5. Relationship Discovery & Accused-Accused Weighted Links (Part 4)
        accused_ids = list(accused_by_person.keys())
        for i in range(len(accused_ids)):
            for j in range(i + 1, len(accused_ids)):
                pid_a = accused_ids[i]
                pid_b = accused_ids[j]
                data_a = accused_by_person[pid_a]
                data_b = accused_by_person[pid_b]

                weight = 0.0
                shared_reasons = []

                # Same Case (co-accused): +5
                shared_cases = set(data_a["cases"]).intersection(set(data_b["cases"]))
                if shared_cases:
                    weight += 5.0 * len(shared_cases)
                    shared_reasons.append("co-accused")

                # Same Victim: +2
                vic_names_a = {
                    normalize_name(v.victim_name)
                    for v in victims
                    if v.case_master_id in data_a["cases"]
                }
                vic_names_b = {
                    normalize_name(v.victim_name)
                    for v in victims
                    if v.case_master_id in data_b["cases"]
                }
                shared_vics = vic_names_a.intersection(vic_names_b)
                if shared_vics:
                    weight += 2.0 * len(shared_vics)
                    shared_reasons.append("shared victim")

                # Same Police Station: +3
                ps_ids_a = {
                    c.police_station_id
                    for c in cases
                    if c.case_master_id in data_a["cases"] and c.police_station_id
                }
                ps_ids_b = {
                    c.police_station_id
                    for c in cases
                    if c.case_master_id in data_b["cases"] and c.police_station_id
                }
                shared_ps = ps_ids_a.intersection(ps_ids_b)
                if shared_ps:
                    weight += 3.0 * len(shared_ps)
                    shared_reasons.append("shared police station")

                # Same Financial Account (Accused linked via transaction): +10
                # Check if there is a transaction between any account of A and B
                has_tx = False
                for tx in transactions:
                    if tx.accused_master_id in data_a["accused_master_ids"]:
                        # check if dest account is owned by B (we will infer ownership or direct transaction)
                        pass
                # We will check if they have any transactions where they are explicitly linked or co-occurring
                # A direct co-accused transaction is handled in build_financial_network,
                # but we can check if they share transactions in our database:
                tx_ids_a = {tx.financial_transaction_id for tx in transactions if tx.accused_master_id in data_a["accused_master_ids"]}
                tx_ids_b = {tx.financial_transaction_id for tx in transactions if tx.accused_master_id in data_b["accused_master_ids"]}
                # Also check direct transfers:
                # If they have a transaction linking their account details
                # We can pre-calculate account owners
                accounts_a = {tx.source_account for tx in transactions if tx.accused_master_id in data_a["accused_master_ids"]}
                accounts_b = {tx.source_account for tx in transactions if tx.accused_master_id in data_b["accused_master_ids"]}
                
                # Check transfers between A's accounts and B's accounts
                direct_tx = [
                    tx for tx in transactions
                    if (tx.source_account in accounts_a and tx.destination_account in accounts_b) or
                       (tx.source_account in accounts_b and tx.destination_account in accounts_a)
                ]
                if direct_tx:
                    weight += 10.0 * len(direct_tx)
                    shared_reasons.append("financial transaction")

                # Cross-District Crimes (connected but span multiple districts): +6
                if weight > 0:
                    districts_a = {
                        c.police_station.district
                        for c in cases
                        if c.case_master_id in data_a["cases"] and c.police_station and c.police_station.district
                    }
                    districts_b = {
                        c.police_station.district
                        for c in cases
                        if c.case_master_id in data_b["cases"] and c.police_station and c.police_station.district
                    }
                    if districts_a and districts_b and districts_a != districts_b:
                        weight += 6.0
                        shared_reasons.append("cross-district crimes")

                # Add link if there is any shared connection
                if weight > 0:
                    G.add_edge(
                        pid_a,
                        pid_b,
                        label=", ".join(shared_reasons),
                        weight=weight,
                        relationship="suspect_link",
                    )

        return G

    @staticmethod
    def build_financial_network(
        transactions: list[FinancialTransaction],
        cases: list[CaseMaster],
    ) -> nx.DiGraph:
        """
        Builds a directed financial transaction graph.
        Nodes represent Accused, Bank Accounts, Cases, and Police Station Locations.
        Edges represent ownership (Accused -> Account) and transfers (Account -> Account).
        """
        G_fin = nx.DiGraph()

        # Track account banks and owners
        account_owners = {}
        account_banks = {}
        case_map = {c.case_master_id: c for c in cases}

        for tx in transactions:
            if tx.source_account:
                account_banks[tx.source_account] = tx.bank_name
                if tx.accused:
                    pid = tx.accused.person_id or f"A_{normalize_name(tx.accused.accused_name)}"
                    account_owners[tx.source_account] = {
                        "id": pid,
                        "name": tx.accused.accused_name,
                        "bank": tx.bank_name,
                    }
            if tx.destination_account:
                if tx.destination_account not in account_banks:
                    account_banks[tx.destination_account] = tx.bank_name

        # 1. Add Accused nodes
        for acc_no, owner in account_owners.items():
            pid = owner["id"]
            if pid not in G_fin:
                G_fin.add_node(
                    pid,
                    label=owner["name"],
                    kind="accused",
                    metadata={"person_id": pid},
                )

        # 2. Add Account nodes
        for acc_no, bank in account_banks.items():
            if acc_no not in G_fin:
                # Format account label like the mock "SBI ••5001" or just Account number
                short_acc = acc_no.split("-")[-1] if "-" in acc_no else acc_no
                label = f"{bank or 'Bank'} ••{short_acc}"
                G_fin.add_node(
                    acc_no,
                    label=label,
                    kind="account",
                    bank=bank or "Unknown Bank",
                    metadata={"account_number": acc_no, "bank": bank},
                )

            # Link Accused owner to Account
            if acc_no in account_owners:
                pid = account_owners[acc_no]["id"]
                G_fin.add_edge(pid, acc_no, label="owns", relationship="owns")

        # 3. Add Transaction edges & link to cases
        # We consolidate multiple transactions between the same source and destination
        # to keep the graph display clean on the frontend.
        consolidated_transfers = {}
        for tx in transactions:
            if not tx.source_account or not tx.destination_account:
                continue

            edge_key = (tx.source_account, tx.destination_account)
            if edge_key not in consolidated_transfers:
                consolidated_transfers[edge_key] = {
                    "amount": 0.0,
                    "suspicious": False,
                    "reasons": [],
                }

            consolidated_transfers[edge_key]["amount"] += float(tx.amount)
            if tx.is_suspicious:
                consolidated_transfers[edge_key]["suspicious"] = True
                if tx.reason:
                    consolidated_transfers[edge_key]["reasons"].append(tx.reason)


        # Add transfer links to G_fin
        for (src, dest), data in consolidated_transfers.items():
            reasons = list(set(data["reasons"]))
            reason_str = "; ".join(reasons) if reasons else None
            G_fin.add_edge(
                src,
                dest,
                label="transfer",
                amount=data["amount"],
                suspicious=data["suspicious"],
                reason=reason_str,
                relationship="transfer",
            )

        return G_fin
