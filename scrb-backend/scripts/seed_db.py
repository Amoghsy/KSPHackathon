import asyncio
import datetime
import random
import sys
from decimal import Decimal
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from faker import Faker
from sqlalchemy import delete

from app.db.session import SessionLocal
from app.models.police_station import PoliceStation
from app.models.crime_type import CrimeType
from app.models.case import CaseMaster
from app.models.accused import AccusedMaster
from app.models.victim import VictimMaster
from app.models.financial_transaction import FinancialTransaction


async def seed_data():
    fake = Faker()
    # Set seed for reproducibility
    Faker.seed(42)
    random.seed(42)

    async with SessionLocal() as db:
        print("Cleaning up old database records...")
        # Delete in order of dependencies (child tables first)
        await db.execute(delete(FinancialTransaction))
        await db.execute(delete(VictimMaster))
        await db.execute(delete(AccusedMaster))
        await db.execute(delete(CaseMaster))
        await db.execute(delete(CrimeType))
        await db.execute(delete(PoliceStation))
        await db.commit()

        # -------------------------------------------------------------
        # 1. Seed 15 Police Stations
        # -------------------------------------------------------------
        districts = ["Bengaluru", "Mysuru", "Hubballi", "Belagavi", "Mangaluru", "Tumakuru", "Shivamogga"]
        station_names = [
            ("Whitefield PS", "Bengaluru"),
            ("Koramangala PS", "Bengaluru"),
            ("Jayanagar PS", "Bengaluru"),
            ("Indiranagar PS", "Bengaluru"),
            ("Malleshwaram PS", "Bengaluru"),
            ("Mysuru Town PS", "Mysuru"),
            ("Mysuru West PS", "Mysuru"),
            ("Hubballi North PS", "Hubballi"),
            ("Hubballi South PS", "Hubballi"),
            ("Belagavi Central PS", "Belagavi"),
            ("Belagavi North PS", "Belagavi"),
            ("Mangaluru Town PS", "Mangaluru"),
            ("Mangaluru East PS", "Mangaluru"),
            ("Tumakuru PS", "Tumakuru"),
            ("Shivamogga PS", "Shivamogga")
        ]
        
        stations = []
        for name, dist in station_names:
            ps = PoliceStation(name=name, district=dist)
            db.add(ps)
            stations.append(ps)
        await db.flush()
        print(f"Inserted {len(stations)} Stations")

        # -------------------------------------------------------------
        # 2. Seed 20 Crime Types
        # -------------------------------------------------------------
        crime_names = [
            "Theft", "Robbery", "Burglary", "Assault", "Cheating",
            "Cybercrime", "Narcotics", "Vehicle Theft", "Kidnapping", "Fraud",
            "Murder", "Extortion", "Gambling", "Riot", "Arson",
            "Smuggling", "Trespass", "Forgery", "Bribery", "Homicide"
        ]
        crime_types = []
        for name in crime_names:
            ct = CrimeType(name=name)
            db.add(ct)
            crime_types.append(ct)
        await db.flush()
        print(f"Inserted {len(crime_types)} Crime Types")

        # -------------------------------------------------------------
        # 3. Seed Criminal Network (4-5 accused shared across 3+ cases)
        # -------------------------------------------------------------
        # 5 repeat offenders forming a cluster
        network_accused_names = ["Suresh Naik", "Ravi Kumar", "Karthik Rao", "Manoj Patil", "Vikram Shetty"]
        # 4 cases shared across the cluster
        network_cases = []
        cluster_crime_nos = ["104430006202600201", "104430006202600204", "104430006202600219", "104430006202600231"]
        cluster_case_nos = ["CC/2201/2026", "CC/2204/2026", "CC/2219/2026", "CC/2231/2026"]
        
        robbery_crime_type = next(c for c in crime_types if c.name == "Robbery")
        whitefield_ps = next(s for s in stations if s.name == "Whitefield PS")

        for idx, (c_no, case_no) in enumerate(zip(cluster_crime_nos, cluster_case_nos)):
            days_ago = random.randint(10, 180)
            reg_date = datetime.date.today() - datetime.timedelta(days=days_ago)
            case_time = datetime.datetime.combine(reg_date, datetime.time(random.randint(0, 23), random.randint(0, 59)))
            
            # Lat/Long in Whitefield bounding box
            lat = Decimal(f"{random.uniform(12.95, 12.99):.6f}")
            lng = Decimal(f"{random.uniform(77.70, 77.76):.6f}")
            
            case = CaseMaster(
                crime_no=c_no,
                case_no=case_no,
                crime_registered_date=reg_date,
                incident_from_date=case_time - datetime.timedelta(hours=random.randint(1, 12)),
                incident_to_date=case_time,
                info_received_ps_date=case_time + datetime.timedelta(hours=random.randint(1, 4)),
                latitude=lat,
                longitude=lng,
                brief_facts=f"Coordinated robbery case linked to gang activity in Whitefield, involving theft of cash and electronics under threat.",
                police_station_id=whitefield_ps.police_station_id,
                crime_type_id=robbery_crime_type.crime_type_id,
                # Random lookup placeholders
                police_person_id=random.randint(1, 50),
                case_category_id=random.randint(1, 5),
                gravity_offence_id=3,  # Grievous/High
                crime_major_head_id=random.randint(1, 10),
                crime_minor_head_id=random.randint(1, 20),
                case_status_id=random.randint(1, 3),
                court_id=random.randint(1, 5)
            )
            db.add(case)
            network_cases.append(case)
        await db.flush()

        # Insert network accused and link them across cases
        # Suresh Naik (Accused 1) in Cases 0, 1, 3
        # Ravi Kumar (Accused 2) in Cases 0, 1, 2
        # Karthik Rao (Accused 3) in Cases 0, 2, 3
        # Manoj Patil (Accused 4) in Cases 1, 2, 3
        # Vikram Shetty (Accused 5) in Cases 0, 1, 2, 3
        network_accused_objs = []
        sharing_matrix = {
            "Suresh Naik": [0, 1, 3],
            "Ravi Kumar": [0, 1, 2],
            "Karthik Rao": [0, 2, 3],
            "Manoj Patil": [1, 2, 3],
            "Vikram Shetty": [0, 1, 2, 3]
        }
        
        accused_instances = []
        for name in network_accused_names:
            case_indices = sharing_matrix[name]
            person_id = f"A{random.randint(100, 999)}"
            for c_idx in case_indices:
                case = network_cases[c_idx]
                acc = AccusedMaster(
                    case_master_id=case.case_master_id,
                    accused_name=name,
                    age_year=random.randint(22, 45),
                    gender_id=1,  # Male
                    person_id=person_id
                )
                db.add(acc)
                accused_instances.append(acc)
        await db.flush()

        # -------------------------------------------------------------
        # 4. Seed Financial Transactions (ONLY for the network cluster)
        # -------------------------------------------------------------
        banks = ["SBI", "HDFC", "ICICI", "Axis", "Canara"]
        # Generate accounts for our 5 network members
        accounts = {}
        for name in network_accused_names:
            accounts[name] = f"ACC-{random.randint(5000, 9999)}"

        transaction_count = 0
        reasons = [
            "Structuring threshold warning: transaction split detected",
            "Rapid layering transfer between gang accounts",
            "Suspicious cash withdrawal immediately after theft incident",
            "Anomalous large amount transfer from unknown third-party account"
        ]

        # Generate transaction links between these cluster members
        for _ in range(12):
            source_name = random.choice(network_accused_names)
            dest_name = random.choice([n for n in network_accused_names if n != source_name])
            
            amount = Decimal(f"{random.uniform(10000, 750000):.2f}")
            is_susp = amount > 300000 or random.random() > 0.7
            
            # Find one of the cases this source accused is involved in
            source_acc_insts = [a for a in accused_instances if a.accused_name == source_name]
            linked_case_id = random.choice(source_acc_insts).case_master_id if source_acc_insts else None
            linked_acc_id = source_acc_insts[0].accused_master_id if source_acc_insts else None
            
            days_ago = random.randint(5, 170)
            tx_date = datetime.datetime.now() - datetime.timedelta(days=days_ago)

            tx = FinancialTransaction(
                source_account=accounts[source_name],
                destination_account=accounts[dest_name],
                bank_name=random.choice(banks),
                amount=amount,
                transaction_date=tx_date,
                is_suspicious=is_susp,
                reason=random.choice(reasons) if is_susp else None,
                case_master_id=linked_case_id,
                accused_master_id=linked_acc_id
            )
            db.add(tx)
            transaction_count += 1
        await db.flush()
        print(f"Inserted {transaction_count} Financial Transactions")

        # -------------------------------------------------------------
        # 5. Seed remaining Cases (to reach 250 Cases)
        # -------------------------------------------------------------
        total_cases_needed = 250
        current_cases_count = len(network_cases)
        cases_to_create = total_cases_needed - current_cases_count

        all_cases = list(network_cases)

        for i in range(cases_to_create):
            # Create realistic Karnataka district & station
            ps = random.choice(stations)
            ct = random.choice(crime_types)
            
            days_ago = random.randint(1, 365)
            reg_date = datetime.date.today() - datetime.timedelta(days=days_ago)
            case_time = datetime.datetime.combine(reg_date, datetime.time(random.randint(0, 23), random.randint(0, 59)))
            
            # Bounding box of Karnataka: ~11.5–18.5°N, 74–78.5°E
            lat = Decimal(f"{random.uniform(11.5, 18.5):.6f}")
            lng = Decimal(f"{random.uniform(74.0, 78.5):.6f}")
            

            c_no = f"1044300062026{random.randint(100000, 999999)}"
            case_no = f"CC/{2000 + i}/2026"

            case = CaseMaster(
                crime_no=c_no,
                case_no=case_no,
                crime_registered_date=reg_date,
                incident_from_date=case_time - datetime.timedelta(hours=random.randint(1, 24)),
                incident_to_date=case_time,
                info_received_ps_date=case_time + datetime.timedelta(hours=random.randint(1, 6)),
                latitude=lat,
                longitude=lng,
                brief_facts=f"Incident of {ct.name} reported at {ps.name} in {ps.district}. Investigation in progress.",
                police_station_id=ps.police_station_id,
                crime_type_id=ct.crime_type_id,
                # Random lookup placeholders
                police_person_id=random.randint(1, 100),
                case_category_id=random.randint(1, 8),
                gravity_offence_id=random.randint(1, 4),
                crime_major_head_id=random.randint(1, 15),
                crime_minor_head_id=random.randint(1, 30),
                case_status_id=random.randint(1, 4),
                court_id=random.randint(1, 10)
            )
            db.add(case)
            all_cases.append(case)
        await db.flush()
        print(f"Inserted {len(all_cases)} Cases")

        # -------------------------------------------------------------
        # 6. Seed remaining Accused (to reach 500 Accused)
        # -------------------------------------------------------------
        total_accused_needed = 500
        current_accused_count = len(accused_instances)
        accused_to_create = total_accused_needed - current_accused_count

        for i in range(accused_to_create):
            # Select random case from the general pool (not the network cases to avoid modifying the network structure)
            case = random.choice(all_cases[current_cases_count:])
            acc = AccusedMaster(
                case_master_id=case.case_master_id,
                accused_name=fake.name(),
                age_year=random.randint(18, 70),
                gender_id=random.choice([1, 2]), # 1: Male, 2: Female
                person_id=f"A{random.randint(1000, 9999)}"
            )
            db.add(acc)
        await db.flush()
        print(f"Inserted {total_accused_needed} Accused")

        # -------------------------------------------------------------
        # 7. Seed Victims (to reach 400 Victims)
        # -------------------------------------------------------------
        total_victims_needed = 400
        for i in range(total_victims_needed):
            case = random.choice(all_cases)
            vic = VictimMaster(
                case_master_id=case.case_master_id,
                victim_name=fake.name(),
                age_year=random.randint(5, 80),
                gender_id=random.choice([1, 2]),
                victim_police=random.choice([True, False]) if random.random() > 0.9 else False
            )
            db.add(vic)
        await db.flush()
        print(f"Inserted {total_victims_needed} Victims")

        await db.commit()
        print("Database seeding completed successfully!")


if __name__ == "__main__":
    asyncio.run(seed_data())
