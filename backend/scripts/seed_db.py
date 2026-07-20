import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import datetime
import random
from decimal import Decimal
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db.session import SessionLocal
from app.db.seed_data.faker_generator import generate_realistic_network
from app.db.seed_data.financial_seed import seed_financial_crime_records


async def seed_data():
    async with SessionLocal() as db:
        await generate_realistic_network(db)
        await seed_financial_crime_records(db)


if __name__ == "__main__":
    asyncio.run(seed_data())
