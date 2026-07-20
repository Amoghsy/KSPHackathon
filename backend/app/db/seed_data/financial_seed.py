import datetime
import random
from decimal import Decimal
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.police_station import PoliceStation
from app.models.crime_type import CrimeType
from app.models.case import CaseMaster
from app.models.accused import AccusedMaster
from app.models.victim import VictimMaster
from app.models.financial_transaction import FinancialTransaction

logger = logging.getLogger(__name__)

# New financial crime accused to insert
FINANCIAL_ACCUSED = [
    {"person_id": "FC_1", "name": "Aditya Hegde", "age": 34, "gender": 1},
    {"person_id": "FC_2", "name": "Vikram Desai", "age": 41, "gender": 1},
    {"person_id": "FC_3", "name": "Neha Kulkarni", "age": 29, "gender": 2},
    {"person_id": "FC_4", "name": "Rajesh Gowda", "age": 48, "gender": 1},
    {"person_id": "FC_5", "name": "Sanjay Naik", "age": 38, "gender": 1},
    {"person_id": "FC_6", "name": "Priyanka Rao", "age": 32, "gender": 2},
]

async def seed_financial_crime_records(db: AsyncSession):
    logger.info("Checking for existing financial crime seed records...")
    
    # Check if we already have the FC_1 accused
    stmt = select(AccusedMaster).where(AccusedMaster.person_id == "FC_1")
    result = await db.execute(stmt)
    if result.scalars().first() is not None:
        logger.info("Financial crime seed records already exist. Skipping insertion.")
        return

    logger.info("Seeding new financial crime records...")

    # 1. Resolve Crime Types
    crime_types = {}
    for ct_name in ["Financial Fraud", "Cyber Fraud"]:
        stmt = select(CrimeType).where(CrimeType.name == ct_name)
        result = await db.execute(stmt)
        ct = result.scalar_one_or_none()
        if not ct:
            ct = CrimeType(name=ct_name)
            db.add(ct)
            await db.flush()
        crime_types[ct_name] = ct.crime_type_id

    # 2. Get Police Stations
    stmt = select(PoliceStation)
    result = await db.execute(stmt)
    stations = result.scalars().all()
    if not stations:
        logger.error("No police stations found! Please run the main database seed script first.")
        return

    # Map police stations by district
    stations_by_district = {}
    for ps in stations:
        if ps.district not in stations_by_district:
            stations_by_district[ps.district] = []
        stations_by_district[ps.district].append(ps)

    # Helper to get random station
    def get_station_for_district(dist_name):
        opts = stations_by_district.get(dist_name, stations)
        return random.choice(opts)

    # 3. Create Case Specifications (10 new cases)
    cases_spec = [
        {"id": 101, "accused": ["FC_1"], "crime": "Financial Fraud", "district": "Bengaluru Urban", "facts": "Multi-crore Ponzi scheme targeting senior citizens in Koramangala."},
        {"id": 102, "accused": ["FC_2"], "crime": "Financial Fraud", "district": "Bengaluru Urban", "facts": "Invoice manipulation and shell company laundering operation."},
        {"id": 103, "accused": ["FC_1", "FC_2"], "crime": "Cyber Fraud", "district": "Bengaluru Urban", "facts": "Coordinated phishing and corporate bank account takeover."},
        {"id": 104, "accused": ["FC_3"], "crime": "Financial Fraud", "district": "Mysuru", "facts": "Embezzlement of cooperative society funds via fake vendor payments."},
        {"id": 105, "accused": ["FC_4"], "crime": "Financial Fraud", "district": "Hubballi-Dharwad", "facts": "Real estate investment scam inflating land values via dummy brokers."},
        {"id": 106, "accused": ["FC_5"], "crime": "Cyber Fraud", "district": "Mysuru", "facts": "Cryptocurrency investment portal hacking and ransomware payout laundering."},
        {"id": 107, "accused": ["FC_4", "FC_5"], "crime": "Financial Fraud", "district": "Hubballi-Dharwad", "facts": "Coordinated loan fraud scam using forged agricultural bills."},
        {"id": 108, "accused": ["FC_6"], "crime": "Financial Fraud", "district": "Bengaluru Urban", "facts": "Stock market pump-and-dump scheme run from Whitefield tech parks."},
        {"id": 109, "accused": ["FC_3", "FC_6"], "crime": "Cyber Fraud", "district": "Mysuru", "facts": "Fake identity banking portal redirecting transaction commission fees."},
        {"id": 110, "accused": ["FC_1", "FC_3", "FC_5"], "crime": "Financial Fraud", "district": "Bengaluru Urban", "facts": "Cross-district money laundering syndicate spanning Bengaluru and Mysuru."},
    ]

    # Create cases
    cases_db = {}
    accused_db = []
    
    for idx, spec in enumerate(cases_spec):
        ps = get_station_for_district(spec["district"])
        
        reg_date = datetime.date(2025, 11, idx + 1)
        incident_time = datetime.datetime.combine(reg_date, datetime.time(10, 0))
        
        # coordinate offset
        lat = Decimal(f"12.9716") + Decimal(f"{random.uniform(-0.01, 0.01):.6f}")
        lng = Decimal(f"77.5946") + Decimal(f"{random.uniform(-0.01, 0.01):.6f}")
        
        c_no = f"2044300062026{200000 + spec['id']}"
        case_no = f"CC/{3200 + spec['id']}/2025"

        case = CaseMaster(
            crime_no=c_no,
            case_no=case_no,
            crime_registered_date=reg_date,
            incident_from_date=incident_time - datetime.timedelta(hours=6),
            incident_to_date=incident_time,
            info_received_ps_date=incident_time + datetime.timedelta(hours=2),
            latitude=lat,
            longitude=lng,
            brief_facts=spec["facts"],
            police_station_id=ps.police_station_id,
            crime_type_id=crime_types[spec["crime"]],
            police_person_id=random.randint(1, 100),
            case_category_id=1,
            gravity_offence_id=1,
            crime_major_head_id=1,
            crime_minor_head_id=1,
            case_status_id=1,
            court_id=1,
        )
        db.add(case)
        await db.flush()
        cases_db[spec["id"]] = case.case_master_id

        # Accused linking
        for p_id in spec["accused"]:
            acc_details = next(a for a in FINANCIAL_ACCUSED if a["person_id"] == p_id)
            acc = AccusedMaster(
                case_master_id=case.case_master_id,
                accused_name=acc_details["name"],
                age_year=acc_details["age"],
                gender_id=acc_details["gender"],
                person_id=p_id
            )
            db.add(acc)
            accused_db.append((p_id, acc))
            
        # Add a victim
        vic = VictimMaster(
            case_master_id=case.case_master_id,
            victim_name=f"Victim of {spec['id']}",
            age_year=random.randint(25, 65),
            gender_id=random.choice([1, 2]),
            victim_police=False
        )
        db.add(vic)

    await db.flush()
    logger.info(f"Seeded {len(cases_db)} financial crime cases.")

    # Accused id mapping
    person_accused_ids = {}
    for p_id, acc in accused_db:
        if p_id not in person_accused_ids:
            person_accused_ids[p_id] = []
        person_accused_ids[p_id].append(acc.accused_master_id)

    # 4. Generate transaction network patterns
    banks = ["HDFC", "ICICI", "SBI", "Axis Bank", "Kotak"]
    reasons = [
        "Suspicious round-tripping transfer",
        "Layering network split transfer",
        "High-value structured transaction",
        "Shell company distribution flow",
        "Money laundering transfer chain",
    ]

    tx_count = 0

    def add_tx(src_acc, dest_acc, p_id, amount, is_susp=False, reason=None, days_ago=10):
        nonlocal tx_count
        case_id = None
        acc_master_id = None
        
        if p_id and p_id in person_accused_ids:
            acc_master_id = person_accused_ids[p_id][0]
            # find linked case
            for pid, acc in accused_db:
                if acc.accused_master_id == acc_master_id:
                    case_id = acc.case_master_id
                    break
        
        tx_date = datetime.datetime.now() - datetime.timedelta(days=days_ago)
        
        tx = FinancialTransaction(
            source_account=src_acc,
            destination_account=dest_acc,
            bank_name=random.choice(banks),
            amount=Decimal(f"{amount:.2f}"),
            transaction_date=tx_date,
            is_suspicious=is_susp,
            reason=reason if is_susp else None,
            case_master_id=case_id,
            accused_master_id=acc_master_id
        )
        db.add(tx)
        tx_count += 1

    # Pattern A: Circular Flow 1 (FC_1 -> FC_2 -> FC_3 -> FC_1)
    for run in range(4):
        days = 20 - run * 3
        amt = 620000.00 + run * 15000.00
        # Hop 1: FC_1 (ACC-FC1-1) -> FC_2 (ACC-FC2-1)
        add_tx("ACC-FC1-1", "ACC-FC2-1", "FC_1", amt, is_susp=True, reason="Suspicious round-tripping transfer", days_ago=days)
        # Hop 2: FC_2 (ACC-FC2-1) -> FC_3 (ACC-FC3-1)
        add_tx("ACC-FC2-1", "ACC-FC3-1", "FC_2", amt, is_susp=True, reason="Suspicious round-tripping transfer", days_ago=days - 1)
        # Hop 3: FC_3 (ACC-FC3-1) -> FC_1 (ACC-FC1-1)
        add_tx("ACC-FC3-1", "ACC-FC1-1", "FC_3", amt, is_susp=True, reason="Suspicious round-tripping transfer", days_ago=days - 2)

    # Pattern B: Circular Flow 2 (FC_4 -> FC_5 -> FC_6 -> FC_4)
    for run in range(4):
        days = 25 - run * 4
        amt = 850000.00 - run * 20000.00
        # Hop 1: FC_4 (ACC-FC4-1) -> FC_5 (ACC-FC5-1)
        add_tx("ACC-FC4-1", "ACC-FC5-1", "FC_4", amt, is_susp=True, reason="Suspicious round-tripping transfer", days_ago=days)
        # Hop 2: FC_5 (ACC-FC5-1) -> FC_6 (ACC-FC6-1)
        add_tx("ACC-FC5-1", "ACC-FC6-1", "FC_5", amt, is_susp=True, reason="Suspicious round-tripping transfer", days_ago=days - 1)
        # Hop 3: FC_6 (ACC-FC6-1) -> FC_4 (ACC-FC4-1)
        add_tx("ACC-FC6-1", "ACC-FC4-1", "FC_6", amt, is_susp=True, reason="Suspicious round-tripping transfer", days_ago=days - 2)

    # Pattern C: Shared Account (ACC-SHARED-FC)
    for run in range(5):
        days = 15 - run * 2
        # FC_1 -> ACC-SHARED-FC
        add_tx("ACC-FC1-2", "ACC-SHARED-FC", "FC_1", 240000.00, is_susp=True, reason="Shared account funding deposit", days_ago=days)
        # FC_2 -> ACC-SHARED-FC
        add_tx("ACC-FC2-2", "ACC-SHARED-FC", "FC_2", 310000.00, is_susp=True, reason="Shared account funding deposit", days_ago=days)
        # ACC-SHARED-FC -> FC_3
        add_tx("ACC-SHARED-FC", "ACC-FC3-2", "FC_1", 500000.00, is_susp=True, reason="Shared account payout distribution", days_ago=days - 1)

    # Pattern D: High-Value Transfers (₹10L+)
    add_tx("ACC-FC1-1", "ACC-FC4-2", "FC_1", 1250000.00, is_susp=True, reason="Large transaction anomaly: over ₹10 Lakhs threshold", days_ago=5)
    add_tx("ACC-FC3-2", "ACC-FC5-1", "FC_3", 1580000.00, is_susp=True, reason="Large transaction anomaly: over ₹10 Lakhs threshold", days_ago=7)
    add_tx("ACC-FC6-2", "ACC-FC2-1", "FC_6", 2100000.00, is_susp=True, reason="Large transaction anomaly: over ₹10 Lakhs threshold", days_ago=9)

    # E. Some normal transactions to round it out
    for i in range(1, 7):
        for run in range(3):
            src = f"ACC-FC{i}-1"
            dest = f"ACC-NORMAL-{i}-{run}"
            add_tx(src, dest, f"FC_{i}", random.uniform(15000.00, 85000.00), is_susp=False, days_ago=30 - run*5)

    await db.commit()
    logger.info(f"Seeded {tx_count} financial transactions successfully.")
