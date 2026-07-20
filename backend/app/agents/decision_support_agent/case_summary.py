import datetime
from decimal import Decimal
from typing import Any
from app.models.case import CaseMaster

class CaseSummaryBuilder:
    """
    Builds a deterministic structured summary of a case from a CaseMaster model.
    Converts Decimals, Dates, and Datetimes into JSON-serializable types.
    """
    
    @staticmethod
    def build(case: CaseMaster, has_sensitive_access: bool = True) -> dict[str, Any]:
        """
        Builds a structured dictionary of case facts.
        If has_sensitive_access is False, masks victim names and brief facts.
        """
        from app.utils.masking import mask_name, mask_brief_facts
        
        accused_list = []
        for acc in case.accused:
            acc_name = acc.accused_name
            if not has_sensitive_access:
                acc_name = mask_name(acc_name)
            accused_list.append({
                "accused_master_id": acc.accused_master_id,
                "accused_name": acc_name,
                "age_year": acc.age_year,
                "gender_id": acc.gender_id,
                "person_id": acc.person_id
            })
            
        victims_list = []
        for vic in case.victims:
            vic_name = vic.victim_name
            if not has_sensitive_access:
                vic_name = mask_name(vic_name)
            victims_list.append({
                "victim_master_id": vic.victim_master_id,
                "victim_name": vic_name,
                "age_year": vic.age_year,
                "gender_id": vic.gender_id,
                "victim_police": vic.victim_police
            })
            
        financial_list = []
        for tx in case.financial_transactions:
            from app.utils.masking import mask_account
            src_acc = tx.source_account
            dst_acc = tx.destination_account
            if not has_sensitive_access:
                src_acc = mask_account(src_acc) if src_acc else None
                dst_acc = mask_account(dst_acc) if dst_acc else None
                
            financial_list.append({
                "financial_transaction_id": tx.financial_transaction_id,
                "source_account": src_acc,
                "destination_account": dst_acc,
                "bank_name": tx.bank_name,
                "amount": float(tx.amount) if isinstance(tx.amount, (Decimal, float)) else tx.amount,
                "transaction_date": tx.transaction_date.isoformat() if isinstance(tx.transaction_date, (datetime.datetime, datetime.date)) else tx.transaction_date,
                "is_suspicious": tx.is_suspicious,
                "reason": tx.reason
            })
            
        brief_facts = case.brief_facts
        if not has_sensitive_access and brief_facts:
            brief_facts = mask_brief_facts(brief_facts)
            
        return {
            "case_id": case.case_master_id,
            "crime_number": case.crime_no,
            "case_no": case.case_no,
            "crime_type": case.crime_type.name if case.crime_type else "Unknown",
            "crime_type_id": case.crime_type_id,
            "crime_registered_date": case.crime_registered_date.isoformat() if isinstance(case.crime_registered_date, (datetime.date, datetime.datetime)) else str(case.crime_registered_date),
            "incident_from_date": case.incident_from_date.isoformat() if isinstance(case.incident_from_date, (datetime.datetime, datetime.date)) else str(case.incident_from_date) if case.incident_from_date else None,
            "incident_to_date": case.incident_to_date.isoformat() if isinstance(case.incident_to_date, (datetime.datetime, datetime.date)) else str(case.incident_to_date) if case.incident_to_date else None,
            "police_station": case.police_station.name if case.police_station else "Unknown",
            "police_station_id": case.police_station_id,
            "district": case.police_station.district if case.police_station else "Unknown",
            "latitude": float(case.latitude) if isinstance(case.latitude, Decimal) else case.latitude,
            "longitude": float(case.longitude) if isinstance(case.longitude, Decimal) else case.longitude,
            "brief_facts": brief_facts,
            "accused": accused_list,
            "victims": victims_list,
            "financial_transactions": financial_list,
            "gravity_offence_id": case.gravity_offence_id,
            "case_status_id": case.case_status_id,
            "court_id": case.court_id,
            "crime_major_head_id": case.crime_major_head_id,
            "crime_minor_head_id": case.crime_minor_head_id
        }
