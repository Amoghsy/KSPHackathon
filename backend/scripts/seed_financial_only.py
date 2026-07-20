import asyncio
import sys
from pathlib import Path

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db.session import SessionLocal
from app.db.seed_data.financial_seed import seed_financial_crime_records

async def main():
    print("Starting financial crime seeding only (existing database will NOT be wiped)...")
    async with SessionLocal() as db:
        await seed_financial_crime_records(db)
    print("Financial crime seeding completed.")

if __name__ == "__main__":
    asyncio.run(main())
