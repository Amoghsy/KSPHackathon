import datetime
import random
from decimal import Decimal
import logging
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
import networkx as nx

from app.models.police_station import PoliceStation
from app.models.crime_type import CrimeType
from app.models.case import CaseMaster
from app.models.accused import AccusedMaster
from app.models.victim import VictimMaster
from app.models.financial_transaction import FinancialTransaction
from app.services.graph.graph_utils import normalize_name
from app.models.user import User
from app.models.district_assignment import UserDistrictAssignment
from app.models.access_request import DistrictAccessRequest, TemporaryDistrictPermission
from app.core.security import get_password_hash

logger = logging.getLogger(__name__)

# Predefined Karnataka Districts and Police Stations with geolocations
KARNATAKA_DISTRICTS = {
    "Bengaluru Urban": [("Whitefield PS", 12.9716, 77.5946), ("Koramangala PS", 12.9348, 77.6189), ("Jayanagar PS", 12.9299, 77.5824)],
    "Bengaluru Rural": [("Doddaballapura PS", 13.2923, 77.5432), ("Devanahalli PS", 13.2484, 77.7126)],
    "Mysuru": [("Mysuru Town PS", 12.3051, 76.6552), ("Mysuru West PS", 12.3121, 76.6124)],
    "Hubballi-Dharwad": [("Hubballi North PS", 15.3647, 75.1240), ("Dharwad Town PS", 15.4589, 75.0078)],
    "Belagavi": [("Belagavi Central PS", 15.8497, 74.4977), ("Belagavi North PS", 15.8670, 74.5200)],
    "Kalaburagi": [("Kalaburagi Station Bazar PS", 17.3291, 76.8341), ("Kalaburagi Chowk PS", 17.3450, 76.8500)],
    "Ballari": [("Ballari Town PS", 15.1394, 76.9214), ("Ballari Rural PS", 15.1500, 76.9000)],
    "Shivamogga": [("Shivamogga Town PS", 13.9299, 75.5681), ("Shivamogga Rural PS", 13.9500, 75.5800)],
    "Tumakuru": [("Tumakuru Town PS", 13.3379, 77.1006), ("Tumakuru Rural PS", 13.3500, 77.0800)],
    "Udupi": [("Udupi Town PS", 13.3409, 74.7421), ("Manipal PS", 13.3524, 74.7845)]
}

CRIME_TYPES = [
    "Theft",
    "Robbery",
    "Cyber Fraud",
    "Murder",
    "Assault",
    "Kidnapping",
    "Vehicle Theft",
    "Drug Trafficking",
    "Financial Fraud",
    "Human Trafficking"
]

# Realistic Kannada/Indian names to avoid generic Faker placeholders
INDIAN_FIRST_NAMES_MALE = [
    "Suresh", "Ravi", "Karthik", "Manoj", "Vikram", "Anand", "Ramesh", "Deepak",
    "Sandesh", "Manjunath", "Basavaraj", "Prakash", "Vijay", "Shivanand", "Raghu",
    "Kiran", "Santhosh", "Satish", "Ganesh", "Puneeth", "Prashanth", "Arjun",
    "Darshan", "Yash", "Vinay", "Harish", "Pradeep", "Raghavendra", "Shankar",
    "Venkatesh"
]

INDIAN_FIRST_NAMES_FEMALE = [
    "Sunitha", "Geetha", "Kavitha", "Shwetha", "Asha", "Roopa", "Jyothi", "Latha",
    "Lakshmi", "Radha", "Pooja", "Divya", "Priyanka", "Deepa", "Anitha", "Rekha",
    "Suma", "Vidya", "Meena", "Rashmi"
]

INDIAN_LAST_NAMES = [
    "Kumar", "Rao", "Patil", "Shetty", "Naik", "Gowda", "Hegde", "Bhat", "Joshi",
    "Kulkarni", "Reddy", "Nayak", "Pujari", "Desai", "Shastry", "Acharya", "Chavan",
    "Siddappa", "Hiremath", "Meti"
]

def generate_indian_name(gender_id=1):
    first = random.choice(INDIAN_FIRST_NAMES_MALE if gender_id == 1 else INDIAN_FIRST_NAMES_FEMALE)
    last = random.choice(INDIAN_LAST_NAMES)
    return f"{first} {last}"

async def generate_realistic_network(db: AsyncSession):
    # Set seed for reproducibility
    random.seed(42)

    print("Cleaning up old database records...")
    # Delete child tables first to respect FK constraints
    await db.execute(delete(TemporaryDistrictPermission))
    await db.execute(delete(DistrictAccessRequest))
    await db.execute(delete(UserDistrictAssignment))
    await db.execute(delete(User))
    await db.execute(delete(FinancialTransaction))
    await db.execute(delete(VictimMaster))
    await db.execute(delete(AccusedMaster))
    await db.execute(delete(CaseMaster))
    await db.execute(delete(CrimeType))
    await db.execute(delete(PoliceStation))
    await db.commit()

    # 1. Insert Police Stations & Districts
    stations_map = {}
    stations_db = []
    for district, ps_list in KARNATAKA_DISTRICTS.items():
        for name, lat, lng in ps_list:
            ps = PoliceStation(name=name, district=district)
            db.add(ps)
            stations_db.append((ps, lat, lng))
    await db.flush()
    for ps, lat, lng in stations_db:
        stations_map[ps.name] = {
            "id": ps.police_station_id,
            "district": ps.district,
            "lat": lat,
            "lng": lng
        }
    print(f"Inserted {len(stations_map)} Police Stations")

    # 2. Insert Crime Types
    crime_type_map = {}
    for ct_name in CRIME_TYPES:
        ct = CrimeType(name=ct_name)
        db.add(ct)
        await db.flush()
        crime_type_map[ct_name] = ct.crime_type_id
    print(f"Inserted {len(crime_type_map)} Crime Types")

    # 3. Define Criminal Network Actors
    # 4 Gangs (5-8 accused each)
    # Gang 1: Dandupalya Cyber Gang (6 members: G1_1 to G1_6)
    # Gang 2: Kolar Sand Mafia (6 members: G2_1 to G2_6)
    # Gang 3: Coastal Drug Syndicate (6 members: G3_1 to G3_6)
    # Gang 4: Deccan Cartel (6 members: G4_1 to G4_6)
    # 3 Bridge Offenders: B1, B2, B3
    # 3 Loose Repeat Offenders: R1, R2, R3
    # 5 Isolated Offenders: I1 to I5

    persons = {}
    
    # Pre-generate unique details for actors
    def create_person(pid, role_label, gender=1):
        name = generate_indian_name(gender)
        persons[pid] = {
            "person_id": pid,
            "name": name,
            "gender": gender,
            "age": random.randint(22, 58),
            "role": role_label,
            "accounts": [f"ACC-{pid}-1", f"ACC-{pid}-2"]
        }

    # Generate Gang 1
    for i in range(1, 7):
        create_person(f"G1_{i}", "Gang 1 Member", gender=random.choice([1, 1, 1, 2]))
    # Generate Gang 2
    for i in range(1, 7):
        create_person(f"G2_{i}", "Gang 2 Member", gender=1)
    # Generate Gang 3
    for i in range(1, 7):
        create_person(f"G3_{i}", "Gang 3 Member", gender=random.choice([1, 1, 2]))
    # Generate Gang 4
    for i in range(1, 7):
        create_person(f"G4_{i}", "Gang 4 Member", gender=1)
    
    # Generate Bridge Offenders
    create_person("B1", "Bridge 1 (G1 <-> G2)", gender=1)
    create_person("B2", "Bridge 2 (G2 <-> G3)", gender=1)
    create_person("B3", "Bridge 3 (G3 <-> G4)", gender=1)

    # Generate Loose Repeat Offenders
    create_person("R1", "Repeat Offender 1", gender=2)
    create_person("R2", "Repeat Offender 2", gender=1)
    create_person("R3", "Repeat Offender 3", gender=1)

    # Generate Isolated Offenders
    for i in range(1, 6):
        create_person(f"I{i}", f"Isolated Offender {i}", gender=random.choice([1, 2]))

    # Predefined shared bank accounts for gangs
    shared_accounts = {
        "ACC_SHARED_G1": ["G1_1", "G1_2"],
        "ACC_SHARED_G2": ["G2_1", "G2_2"],
        "ACC_SHARED_G3": ["G3_1", "G3_2"],
        "ACC_SHARED_G4": ["G4_1", "G4_2"]
    }

    # 4. Generate Case Specifications (Exactly 50 cases)
    # We map accused person_ids to cases.
    cases_spec = []

    # Cases 1 to 5: Isolated cases (1 accused each, no associates)
    cases_spec.append({"id": 1, "accused": ["I1"], "crime": "Theft", "district": "Udupi"})
    cases_spec.append({"id": 2, "accused": ["I2"], "crime": "Assault", "district": "Tumakuru"})
    cases_spec.append({"id": 3, "accused": ["I3"], "crime": "Cyber Fraud", "district": "Mysuru"})
    cases_spec.append({"id": 4, "accused": ["I4"], "crime": "Vehicle Theft", "district": "Hubballi-Dharwad"})
    cases_spec.append({"id": 5, "accused": ["I5"], "crime": "Murder", "district": "Kalaburagi"})

    # Cases 6 to 15: Gang 1 Cases (Dandupalya Gang) - primary in Bengaluru Urban/Rural
    cases_spec.append({"id": 6, "accused": ["G1_1", "G1_2"], "crime": "Cyber Fraud", "district": "Bengaluru Urban"})
    cases_spec.append({"id": 7, "accused": ["G1_2", "G1_3"], "crime": "Cyber Fraud", "district": "Bengaluru Urban"})
    cases_spec.append({"id": 8, "accused": ["G1_1", "G1_4"], "crime": "Theft", "district": "Bengaluru Rural"})
    cases_spec.append({"id": 9, "accused": ["G1_5"], "crime": "Cyber Fraud", "district": "Bengaluru Urban"})
    cases_spec.append({"id": 10, "accused": ["G1_1", "B1"], "crime": "Theft", "district": "Bengaluru Urban"})
    cases_spec.append({"id": 11, "accused": ["G1_6", "B1"], "crime": "Cyber Fraud", "district": "Bengaluru Rural"})
    cases_spec.append({"id": 12, "accused": ["G1_1", "R1"], "crime": "Cyber Fraud", "district": "Bengaluru Urban"})
    cases_spec.append({"id": 13, "accused": ["R1"], "crime": "Theft", "district": "Hubballi-Dharwad"})
    cases_spec.append({"id": 14, "accused": ["G1_3"], "crime": "Theft", "district": "Bengaluru Rural"})
    cases_spec.append({"id": 15, "accused": ["G1_4", "G1_6"], "crime": "Cyber Fraud", "district": "Bengaluru Urban"})

    # Cases 16 to 25: Gang 2 Cases (Kolar Sand Mafia) - primary in Tumakuru/Mysuru
    cases_spec.append({"id": 16, "accused": ["G2_1", "G2_2"], "crime": "Robbery", "district": "Tumakuru"})
    cases_spec.append({"id": 17, "accused": ["G2_2", "G2_3"], "crime": "Assault", "district": "Mysuru"})
    cases_spec.append({"id": 18, "accused": ["G2_1", "G2_4"], "crime": "Robbery", "district": "Tumakuru"})
    cases_spec.append({"id": 19, "accused": ["G2_5"], "crime": "Kidnapping", "district": "Mysuru"})
    cases_spec.append({"id": 20, "accused": ["G2_1", "B1"], "crime": "Robbery", "district": "Tumakuru"})
    cases_spec.append({"id": 21, "accused": ["G2_6", "B1"], "crime": "Assault", "district": "Bengaluru Urban"})
    cases_spec.append({"id": 22, "accused": ["G2_1", "B2"], "crime": "Robbery", "district": "Mysuru"})
    cases_spec.append({"id": 23, "accused": ["B2"], "crime": "Assault", "district": "Tumakuru"})
    cases_spec.append({"id": 24, "accused": ["G2_3"], "crime": "Kidnapping", "district": "Tumakuru"})
    cases_spec.append({"id": 25, "accused": ["G2_4", "G2_5"], "crime": "Assault", "district": "Mysuru"})

    # Cases 26 to 35: Gang 3 Cases (Coastal Syndicate) - primary in Udupi/Shivamogga
    cases_spec.append({"id": 26, "accused": ["G3_1", "G3_2"], "crime": "Drug Trafficking", "district": "Udupi"})
    cases_spec.append({"id": 27, "accused": ["G3_2", "G3_3"], "crime": "Financial Fraud", "district": "Shivamogga"})
    cases_spec.append({"id": 28, "accused": ["G3_1", "G3_4"], "crime": "Drug Trafficking", "district": "Udupi"})
    cases_spec.append({"id": 29, "accused": ["G3_5"], "crime": "Financial Fraud", "district": "Shivamogga"})
    cases_spec.append({"id": 30, "accused": ["G3_1", "B2"], "crime": "Drug Trafficking", "district": "Udupi"})
    cases_spec.append({"id": 31, "accused": ["G3_6", "B2"], "crime": "Financial Fraud", "district": "Shivamogga"})
    cases_spec.append({"id": 32, "accused": ["G3_1", "B3"], "crime": "Drug Trafficking", "district": "Udupi"})
    cases_spec.append({"id": 33, "accused": ["B3"], "crime": "Financial Fraud", "district": "Shivamogga"})
    cases_spec.append({"id": 34, "accused": ["G3_3"], "crime": "Drug Trafficking", "district": "Udupi"})
    cases_spec.append({"id": 35, "accused": ["G3_4", "G3_5"], "crime": "Financial Fraud", "district": "Shivamogga"})

    # Cases 36 to 45: Gang 4 Cases (Deccan Cartel) - primary in Kalaburagi/Ballari/Belagavi
    cases_spec.append({"id": 36, "accused": ["G4_1", "G4_2"], "crime": "Human Trafficking", "district": "Kalaburagi"})
    cases_spec.append({"id": 37, "accused": ["G4_2", "G4_3"], "crime": "Murder", "district": "Ballari"})
    cases_spec.append({"id": 38, "accused": ["G4_1", "G4_4"], "crime": "Human Trafficking", "district": "Belagavi"})
    cases_spec.append({"id": 39, "accused": ["G4_5"], "crime": "Murder", "district": "Kalaburagi"})
    cases_spec.append({"id": 40, "accused": ["G4_1", "B3"], "crime": "Human Trafficking", "district": "Kalaburagi"})
    cases_spec.append({"id": 41, "accused": ["G4_6", "B3"], "crime": "Murder", "district": "Ballari"})
    cases_spec.append({"id": 42, "accused": ["G4_1", "R3"], "crime": "Human Trafficking", "district": "Belagavi"})
    cases_spec.append({"id": 43, "accused": ["R3"], "crime": "Murder", "district": "Kalaburagi"})
    cases_spec.append({"id": 44, "accused": ["G4_3"], "crime": "Human Trafficking", "district": "Ballari"})
    cases_spec.append({"id": 45, "accused": ["G4_4", "G4_6"], "crime": "Murder", "district": "Belagavi"})

    # Cases 46 to 50: Cross-District and Repeat Offender cases
    cases_spec.append({"id": 46, "accused": ["B1", "B2", "R2"], "crime": "Vehicle Theft", "district": "Hubballi-Dharwad"})
    cases_spec.append({"id": 47, "accused": ["B2", "B3", "R2"], "crime": "Vehicle Theft", "district": "Shivamogga"})
    cases_spec.append({"id": 48, "accused": ["R1", "R2"], "crime": "Robbery", "district": "Belagavi"})
    cases_spec.append({"id": 49, "accused": ["R2", "B1"], "crime": "Theft", "district": "Hubballi-Dharwad"})
    cases_spec.append({"id": 50, "accused": ["R3", "B3"], "crime": "Kidnapping", "district": "Ballari"})

    # 5. Shared Victims Setup
    # SV1: Gang 1 cases (Cases 6 & 8)
    # SV2: Gang 1 & Gang 2 cases (Cases 10 & 20)
    # SV3: Gang 2 & Gang 3 cases (Cases 22 & 30)
    # SV4: Gang 3 & Gang 4 cases (Cases 32 & 40)
    # SV5: Repeat offender cases (Cases 12 & 48)
    shared_victims = {
        6: "SV1", 8: "SV1",
        10: "SV2", 20: "SV2",
        22: "SV3", 30: "SV3",
        32: "SV4", 40: "SV4",
        12: "SV5", 48: "SV5"
    }

    shared_victim_names = {
        "SV1": generate_indian_name(gender_id=2),
        "SV2": generate_indian_name(gender_id=1),
        "SV3": generate_indian_name(gender_id=2),
        "SV4": generate_indian_name(gender_id=1),
        "SV5": generate_indian_name(gender_id=2)
    }

    # Helper function to generate coordinate offsets around PS center
    def get_offset_coords(lat, lng):
        offset_lat = Decimal(f"{lat + random.uniform(-0.015, 0.015):.6f}")
        offset_lng = Decimal(f"{lng + random.uniform(-0.015, 0.015):.6f}")
        return offset_lat, offset_lng

    # 6. Insert Cases, Accused, and Victims
    cases_db = {}
    accused_db = []
    victims_inserted_count = 0
    accused_inserted_count = 0
    cases_inserted_count = 0

    for spec in cases_spec:
        # Resolve Police Station in specified District
        ps_choices = KARNATAKA_DISTRICTS[spec["district"]]
        ps_name, ps_lat, ps_lng = random.choice(ps_choices)
        ps_id = stations_map[ps_name]["id"]

        # Date distribution: 2022 to 2026. More recent = more frequent.
        year_weight = random.choices([2022, 2023, 2024, 2025, 2026], weights=[10, 15, 20, 25, 30])[0]
        month = random.randint(1, 12)
        day = random.randint(1, 28)
        reg_date = datetime.date(year_weight, month, day)
        incident_time = datetime.datetime.combine(reg_date, datetime.time(random.randint(0, 23), random.randint(0, 59)))

        lat, lng = get_offset_coords(ps_lat, ps_lng)
        
        c_no = f"1044300062026{100000 + spec['id']}"
        case_no = f"CC/{2200 + spec['id']}/{year_weight}"

        case = CaseMaster(
            crime_no=c_no,
            case_no=case_no,
            crime_registered_date=reg_date,
            incident_from_date=incident_time - datetime.timedelta(hours=random.randint(1, 24)),
            incident_to_date=incident_time,
            info_received_ps_date=incident_time + datetime.timedelta(hours=random.randint(1, 6)),
            latitude=lat,
            longitude=lng,
            brief_facts=f"Coordinated {spec['crime']} incident reported at {ps_name} in district {spec['district']}. Evidence collected and suspect analysis ongoing.",
            police_station_id=ps_id,
            crime_type_id=crime_type_map[spec["crime"]],
            police_person_id=random.randint(1, 100),
            case_category_id=random.randint(1, 8),
            gravity_offence_id=random.randint(1, 4),
            crime_major_head_id=random.randint(1, 15),
            crime_minor_head_id=random.randint(1, 30),
            case_status_id=random.randint(1, 4),
            court_id=random.randint(1, 10),
        )
        db.add(case)
        await db.flush()
        cases_db[spec["id"]] = case.case_master_id
        cases_inserted_count += 1

        # Link Accused
        for pid in spec["accused"]:
            person = persons[pid]
            acc = AccusedMaster(
                case_master_id=case.case_master_id,
                accused_name=person["name"],
                age_year=person["age"],
                gender_id=person["gender"],
                person_id=pid
            )
            db.add(acc)
            accused_db.append((pid, acc))
            accused_inserted_count += 1

        # Link Victims
        if spec["id"] in shared_victims:
            v_ref = shared_victims[spec["id"]]
            v_name = shared_victim_names[v_ref]
            vic = VictimMaster(
                case_master_id=case.case_master_id,
                victim_name=v_name,
                age_year=random.randint(25, 60),
                gender_id=random.choice([1, 2]),
                victim_police=False
            )
            db.add(vic)
            victims_inserted_count += 1
        else:
            # Generate 1 unique victim for this case
            v_gender = random.choice([1, 2])
            vic = VictimMaster(
                case_master_id=case.case_master_id,
                victim_name=generate_indian_name(v_gender),
                age_year=random.randint(18, 75),
                gender_id=v_gender,
                victim_police=False
            )
            db.add(vic)
            victims_inserted_count += 1

            # Sometime add another victim to reach around 60 total
            if spec["id"] % 4 == 0:
                v_gender2 = random.choice([1, 2])
                vic2 = VictimMaster(
                    case_master_id=case.case_master_id,
                    victim_name=generate_indian_name(v_gender2),
                    age_year=random.randint(18, 75),
                    gender_id=v_gender2,
                    victim_police=False
                )
                db.add(vic2)
                victims_inserted_count += 1

    await db.flush()
    print(f"Inserted {cases_inserted_count} Cases")
    print(f"Inserted {accused_inserted_count} Accused")
    print(f"Inserted {victims_inserted_count} Victims")

    # Map accused_master_ids to person_ids for referencing in transactions
    person_accused_ids = {}
    for pid, acc in accused_db:
        if pid not in person_accused_ids:
            person_accused_ids[pid] = []
        person_accused_ids[pid].append(acc.accused_master_id)

    # 7. Generate Financial Transactions (Exactly 150+ transactions)
    # We will build cycles, chains, and bridge flows.
    banks = ["SBI", "HDFC", "ICICI", "Axis", "Canara"]
    reasons = [
        "Rapid layering transfer between gang accounts",
        "Structuring threshold warning: transaction split detected",
        "Suspicious circular flow matching round-tripping pattern",
        "Large transaction anomaly: transfer between known criminal associates",
        "Money mule account incoming transfer"
    ]

    transactions_db = []

    # Helper function to generate transaction
    def add_tx(src_acc, dest_acc, src_pid, amount, date_offset=0, susp_chance=0.25):
        # Resolve linked case and accused master id for the sender
        case_id = None
        acc_master_id = None
        if src_pid and src_pid in person_accused_ids:
            acc_master_id = person_accused_ids[src_pid][0]
            # Get case master id
            for pid, acc in accused_db:
                if acc.accused_master_id == acc_master_id:
                    case_id = acc.case_master_id
                    break

        tx_date = datetime.datetime.now() - datetime.timedelta(days=date_offset)
        amt_decimal = Decimal(f"{amount:.2f}")
        is_susp = amount > 300000 or random.random() < susp_chance

        tx = FinancialTransaction(
            source_account=src_acc,
            destination_account=dest_acc,
            bank_name=random.choice(banks),
            amount=amt_decimal,
            transaction_date=tx_date,
            is_suspicious=is_susp,
            reason=random.choice(reasons) if is_susp else None,
            case_master_id=case_id,
            accused_master_id=acc_master_id
        )
        db.add(tx)
        transactions_db.append(tx)

    # A. Cycles (4 gangs, each has 1 cycle of 3 nodes repeated 5 times = 15 tx * 4 = 60 tx)
    for i in range(1, 5):
        for run in range(5):
            days_ago = run * 10 + random.randint(1, 5)
            # Flow 1 -> 2
            add_tx(f"ACC-G{i}_1-1", f"ACC-G{i}_2-1", f"G{i}_1", random.uniform(50000, 450000), days_ago, susp_chance=0.4)
            # Flow 2 -> 3
            add_tx(f"ACC-G{i}_2-1", f"ACC-G{i}_3-1", f"G{i}_2", random.uniform(50000, 450000), days_ago - 2, susp_chance=0.4)
            # Flow 3 -> 1
            add_tx(f"ACC-G{i}_3-1", f"ACC-G{i}_1-1", f"G{i}_3", random.uniform(50000, 450000), days_ago - 4, susp_chance=0.4)

    # B. Chains with Shared Accounts and Money Mules (4 gangs, 4 steps each, repeated 5 times = 20 tx * 4 = 80 tx)
    for i in range(1, 5):
        for run in range(5):
            days_ago = run * 12 + random.randint(1, 5)
            # Step 1
            add_tx(f"ACC-G{i}_4-1", f"ACC-G{i}_5-1", f"G{i}_4", random.uniform(20000, 150000), days_ago, susp_chance=0.1)
            # Step 2 (to Shared Account, G{i}_5 is the sender)
            add_tx(f"ACC-G{i}_5-1", f"ACC_SHARED_G{i}", f"G{i}_5", random.uniform(20000, 150000), days_ago - 1, susp_chance=0.3)
            # Step 3 (from Shared Account, alternate owner between G{i}_1 and G{i}_2)
            sender_pid = f"G{i}_1" if run % 2 == 0 else f"G{i}_2"
            add_tx(f"ACC_SHARED_G{i}", f"ACC-G{i}_6-1", sender_pid, random.uniform(15000, 140000), days_ago - 2, susp_chance=0.2)
            # Step 4
            add_tx(f"ACC-G{i}_6-1", f"ACC-G{i}_1-1", f"G{i}_6", random.uniform(10000, 120000), days_ago - 3, susp_chance=0.1)

    # C. Bridge Flows (Connects Gangs together, 3 bridges, each repeated 3 times = 6 tx * 3 = 18 tx)
    bridge_steps = [
        ("G1_1", "ACC-G1_1-1", "B1", "ACC-B1-1", "G2_1", "ACC-G2_1-1"),
        ("G2_1", "ACC-G2_1-1", "B2", "ACC-B2-1", "G3_1", "ACC-G3_1-1"),
        ("G3_1", "ACC-G3_1-1", "B3", "ACC-B3-1", "G4_1", "ACC-G4_1-1")
    ]
    for src_pid, src_acc, br_pid, br_acc, dest_pid, dest_acc in bridge_steps:
        for run in range(3):
            days_ago = run * 15 + random.randint(1, 5)
            # Flow from Gang to Bridge
            add_tx(src_acc, br_acc, src_pid, random.uniform(80000, 250000), days_ago, susp_chance=0.5)
            # Flow from Bridge to next Gang
            add_tx(br_acc, dest_acc, br_pid, random.uniform(70000, 240000), days_ago - 1, susp_chance=0.5)

    await db.flush()
    print(f"Inserted {len(transactions_db)} Financial Transactions")
    await db.commit()

    # 8. Automated Verification and Graph Validation Suite
    print("---------------------------------------------------------")
    print("Verifying database generation and graph properties...")
    print("---------------------------------------------------------")
    await run_automated_validation(db)


async def run_automated_validation(db: AsyncSession):
    # Retrieve all data from PostgreSQL
    res_cases = await db.execute(select(CaseMaster).options(
        selectinload(CaseMaster.police_station),
        selectinload(CaseMaster.crime_type)
    ))
    cases = list(res_cases.scalars().all())

    res_acc = await db.execute(select(AccusedMaster))
    accused = list(res_acc.scalars().all())

    res_vic = await db.execute(select(VictimMaster))
    victims = list(res_vic.scalars().all())

    res_tx = await db.execute(select(FinancialTransaction).options(
        selectinload(FinancialTransaction.accused),
        selectinload(FinancialTransaction.case)
    ))
    transactions = list(res_tx.scalars().all())

    res_ps = await db.execute(select(PoliceStation))
    stations = list(res_ps.scalars().all())

    # Build NetworkX graph exactly as the backend endpoints do
    from app.agents.network_agent.graph_builder import GraphBuilder
    G = GraphBuilder.build_criminal_network(cases, accused, victims, transactions)
    G_fin = GraphBuilder.build_financial_network(transactions, cases)

    # 1. Foreign Key Validation
    case_ids = {c.case_master_id for c in cases}
    ps_ids = {s.police_station_id for s in stations}
    for acc in accused:
        assert acc.case_master_id in case_ids, f"Accused {acc.accused_name} has invalid case_master_id {acc.case_master_id}"
    for vic in victims:
        assert vic.case_master_id in case_ids, f"Victim {vic.victim_name} has invalid case_master_id {vic.case_master_id}"
    for c in cases:
        assert c.police_station_id in ps_ids, f"Case {c.case_no} has invalid police_station_id {c.police_station_id}"
    print("[OK] Every foreign key is valid.")

    # 2. Verify gangs have multiple members
    from app.agents.network_agent.graph_analyzer import GraphAnalyzer
    centrality = GraphAnalyzer.calculate_centrality(G)
    communities = GraphAnalyzer.detect_communities(G, centrality["pagerank"])
    
    assert len(communities) >= 4, f"Expected at least 4 communities, found {len(communities)}"
    for comm in communities[:4]:
        assert len(comm["members"]) >= 5, f"Community {comm['community_id']} has fewer than 5 members: {comm['members']}"
    print("[OK] Every gang community has multiple members (5-8 accused).")
    print(f"[OK] Detected communities count: {len(communities)}")

    # 3. Verify repeat offenders exist
    repeat_offenders = GraphAnalyzer.detect_repeat_offenders(G, centrality["degree"])
    assert len(repeat_offenders) >= 10, f"Expected at least 10 repeat offenders, found {len(repeat_offenders)}"
    for o in repeat_offenders:
        assert o["crime_count"] >= 3 or o["risk_score"] > 50, f"Offender {o['name']} does not satisfy repeat offender criteria"
    print("[OK] Repeat offenders exist and have >= 3 cases or high risk scores.")

    # 4. Verify bridge offenders exist
    accused_nodes = [n for n, d in G.nodes(data=True) if d.get("kind") == "accused"]
    betweenness = centrality["betweenness"]
    sorted_betweenness = sorted(
        [(n, betweenness[n]) for n in accused_nodes],
        key=lambda x: x[1],
        reverse=True
    )
    top_accused_bet = [n for n, b in sorted_betweenness[:5]]
    assert any(b in top_accused_bet for b in ["B1", "B2", "B3"]), "Bridge offenders not detected in top betweenness centrality nodes"
    print("[OK] Bridge offenders exist and possess high betweenness centrality values.")

    # 5. Verify financial graph connected
    assert G_fin.number_of_nodes() > 0, "Financial graph is empty"
    assert G_fin.number_of_edges() >= 50, f"Expected >= 50 edges in financial network, found {G_fin.number_of_edges()}"
    assert len(transactions) >= 150, f"Expected >= 150 transactions in database, found {len(transactions)}"
    
    patterns = GraphAnalyzer.detect_financial_patterns(G_fin)
    assert len(patterns["circular_flows"]) > 0, "No circular flows detected"
    assert len(patterns["shared_accounts"]) > 0, "No shared accounts detected"
    assert len(patterns["high_value_transfers"]) > 0, "No high value transfers detected"
    print("[OK] Financial graph is connected and rich with cycles, chains, and shared accounts.")

    # 6. Verify shortest paths are available
    if "G1_1" in G and "G4_1" in G:
        has_path = nx.has_path(G, "G1_1", "G4_1")
        assert has_path, "No shortest path found between G1_1 and G4_1"
        path = nx.shortest_path(G, "G1_1", "G4_1")
        print(f"[OK] Shortest path available between gang leaders: {' -> '.join(path)}")
    else:
        print("[WARN] Gang leader nodes not found in graph.")

    # 7. District filters return data
    for dist in KARNATAKA_DISTRICTS.keys():
        cases_in_dist = [c for c in cases if c.police_station and c.police_station.district == dist]
        assert len(cases_in_dist) > 0, f"No cases found in district {dist}"
    print("[OK] District filters return data for all 10 districts.")

    # 8. Seed users, assignments, and access request scenarios
    print("Seeding deterministic users and ABAC district scopes...")
    hashed_pw = get_password_hash("password123")

    users_to_seed = [
        ("insp_mysuru", "Investigator", "Mysuru"),
        ("insp_bengaluru", "Investigator", "Bengaluru Urban"),
        ("senior_sp", "Senior Investigator", "Mysuru,Bengaluru Urban"),
        ("analyst_priya", "Analyst", "Mysuru,Bengaluru Urban,Mangaluru"),
        ("supervisor_ramesh", "Supervisor", None),
        ("policymaker_anitha", "Policy Maker", None),
        ("admin_system", "Administrator", None),
    ]

    user_objs = {}
    for username, role, legacy_districts in users_to_seed:
        user = User(
            username=username,
            hashed_password=hashed_pw,
            role=role,
            districts=legacy_districts
        )
        db.add(user)
        user_objs[username] = user
    await db.flush()

    assignments = [
        # Ramesh supervises Bengaluru Urban, Mysuru, Tumakuru
        UserDistrictAssignment(user_id=user_objs["supervisor_ramesh"].id, district="Bengaluru Urban", assigned_by=user_objs["admin_system"].id, is_active=True),
        UserDistrictAssignment(user_id=user_objs["supervisor_ramesh"].id, district="Mysuru", assigned_by=user_objs["admin_system"].id, is_active=True),
        UserDistrictAssignment(user_id=user_objs["supervisor_ramesh"].id, district="Tumakuru", assigned_by=user_objs["admin_system"].id, is_active=True),
        # permanent assignments for investigators/analysts
        UserDistrictAssignment(user_id=user_objs["insp_mysuru"].id, district="Mysuru", assigned_by=user_objs["supervisor_ramesh"].id, is_active=True),
        UserDistrictAssignment(user_id=user_objs["insp_bengaluru"].id, district="Bengaluru Urban", assigned_by=user_objs["supervisor_ramesh"].id, is_active=True),
        UserDistrictAssignment(user_id=user_objs["senior_sp"].id, district="Mysuru", assigned_by=user_objs["supervisor_ramesh"].id, is_active=True),
        UserDistrictAssignment(user_id=user_objs["senior_sp"].id, district="Bengaluru Urban", assigned_by=user_objs["supervisor_ramesh"].id, is_active=True),
        UserDistrictAssignment(user_id=user_objs["analyst_priya"].id, district="Mysuru", assigned_by=user_objs["supervisor_ramesh"].id, is_active=True),
        UserDistrictAssignment(user_id=user_objs["analyst_priya"].id, district="Bengaluru Urban", assigned_by=user_objs["supervisor_ramesh"].id, is_active=True),
        UserDistrictAssignment(user_id=user_objs["analyst_priya"].id, district="Hubballi-Dharwad", assigned_by=user_objs["supervisor_ramesh"].id, is_active=True),
    ]
    for asn in assignments:
        db.add(asn)
    await db.flush()

    # Seed different access request scenarios
    now = datetime.datetime.utcnow()

    # Scenario 1: PENDING request
    req_pending = DistrictAccessRequest(
        requester_id=user_objs["insp_mysuru"].id,
        requested_district="Bengaluru Urban",
        reason="Tracking Bengaluru accomplices of gang",
        duration_hours=24,
        status="PENDING",
        requested_at=now - datetime.timedelta(hours=2)
    )
    db.add(req_pending)

    # Scenario 2: APPROVED & ACTIVE request
    req_approved = DistrictAccessRequest(
        requester_id=user_objs["insp_mysuru"].id,
        requested_district="Bengaluru Urban",
        reason="Need access to Whitefield case records",
        duration_hours=48,
        status="APPROVED",
        requested_at=now - datetime.timedelta(days=1),
        reviewed_by=user_objs["supervisor_ramesh"].id,
        reviewed_at=now - datetime.timedelta(hours=23),
        review_comment="Approved for 48 hours."
    )
    db.add(req_approved)
    await db.flush()

    perm_active = TemporaryDistrictPermission(
        user_id=user_objs["insp_mysuru"].id,
        district="Bengaluru Urban",
        access_request_id=req_approved.id,
        approved_by=user_objs["supervisor_ramesh"].id,
        approved_at=now - datetime.timedelta(hours=23),
        expires_at=now + datetime.timedelta(hours=25),
        is_revoked=False
    )
    db.add(perm_active)

    # Scenario 3: EXPIRED request
    req_expired = DistrictAccessRequest(
        requester_id=user_objs["insp_mysuru"].id,
        requested_district="Bengaluru Urban",
        reason="Follow up on previous investigation",
        duration_hours=12,
        status="APPROVED",
        requested_at=now - datetime.timedelta(days=2),
        reviewed_by=user_objs["supervisor_ramesh"].id,
        reviewed_at=now - datetime.timedelta(days=2) + datetime.timedelta(minutes=10),
        review_comment="Approved for 12 hours."
    )
    db.add(req_expired)
    await db.flush()

    perm_expired = TemporaryDistrictPermission(
        user_id=user_objs["insp_mysuru"].id,
        district="Bengaluru Urban",
        access_request_id=req_expired.id,
        approved_by=user_objs["supervisor_ramesh"].id,
        approved_at=now - datetime.timedelta(days=2) + datetime.timedelta(minutes=10),
        expires_at=now - datetime.timedelta(days=1, hours=12),
        is_revoked=False
    )
    db.add(perm_expired)

    # Scenario 4: REVOKED request
    req_revoked = DistrictAccessRequest(
        requester_id=user_objs["insp_mysuru"].id,
        requested_district="Bengaluru Urban",
        reason="Access Koramangala station logs",
        duration_hours=24,
        status="APPROVED",
        requested_at=now - datetime.timedelta(hours=5),
        reviewed_by=user_objs["supervisor_ramesh"].id,
        reviewed_at=now - datetime.timedelta(hours=4)
    )
    db.add(req_revoked)
    await db.flush()

    perm_revoked = TemporaryDistrictPermission(
        user_id=user_objs["insp_mysuru"].id,
        district="Bengaluru Urban",
        access_request_id=req_revoked.id,
        approved_by=user_objs["supervisor_ramesh"].id,
        approved_at=now - datetime.timedelta(hours=4),
        expires_at=now + datetime.timedelta(hours=20),
        is_revoked=True,
        revoked_at=now - datetime.timedelta(hours=1),
        revoked_by=user_objs["supervisor_ramesh"].id,
        revocation_reason="Investigation concluded early"
    )
    db.add(perm_revoked)

    # Scenario 5: REJECTED request
    req_rejected = DistrictAccessRequest(
        requester_id=user_objs["insp_mysuru"].id,
        requested_district="Belagavi",
        reason="Check Belagavi gang connections",
        duration_hours=24,
        status="REJECTED",
        requested_at=now - datetime.timedelta(hours=10),
        reviewed_by=user_objs["supervisor_ramesh"].id,
        reviewed_at=now - datetime.timedelta(hours=9),
        review_comment="Insufficient justification."
    )
    db.add(req_rejected)
    await db.commit()

    # 9. Final Statistics Print
    print("---------------------------------------------------------")
    print("DATABASES SEEDED AND VALIDATED SUCCESSFULLY:")
    print(f"  - Cases: {len(cases)}")
    print(f"  - Accused: {len(accused)}")
    print(f"  - Victims: {len(victims)}")
    print(f"  - Transactions: {len(transactions)}")
    print(f"  - Repeat Offenders Found: {len(repeat_offenders)}")
    print(f"  - Communities Found: {len(communities)}")
    print(f"  - Financial Cycles Detected: {len(patterns['circular_flows'])}")
    print(f"  - Shared Accounts Found: {len(patterns['shared_accounts'])}")
    print(f"  - Users Seeded: {len(users_to_seed)}")
    print(f"  - District Assignments Seeded: {len(assignments)}")
    print("---------------------------------------------------------")

