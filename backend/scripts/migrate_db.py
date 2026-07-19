import asyncio
import logging
from sqlalchemy import create_engine, text
from app.core.security import get_password_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql+psycopg://scrb_user:scrb_pass@localhost:5432/scrb_dev"

async def run_migration():
    engine = create_engine(DATABASE_URL)
    
    with engine.begin() as conn:
        logger.info("Starting database schema updates...")
        
        # 1. Update users table
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS districts VARCHAR(255);"))
        logger.info("Updated users table with 'districts' column.")
        
        # 2. Update audit_log table
        conn.execute(text("ALTER TABLE audit_log ADD COLUMN IF NOT EXISTS username VARCHAR(100);"))
        conn.execute(text("ALTER TABLE audit_log ADD COLUMN IF NOT EXISTS role VARCHAR(50);"))
        conn.execute(text("ALTER TABLE audit_log ADD COLUMN IF NOT EXISTS api VARCHAR(255);"))
        conn.execute(text("ALTER TABLE audit_log ADD COLUMN IF NOT EXISTS response_size INTEGER;"))
        conn.execute(text("ALTER TABLE audit_log ADD COLUMN IF NOT EXISTS ip_address VARCHAR(45);"))
        conn.execute(text("ALTER TABLE audit_log ADD COLUMN IF NOT EXISTS status VARCHAR(50);"))
        logger.info("Updated audit_log table with new tracking columns.")
        
        # 3. Create investigation_history table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS investigation_history (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                timestamp TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() at time zone 'utc') NOT NULL,
                investigation_name VARCHAR(255) NOT NULL,
                entity_type VARCHAR(50) NOT NULL,
                entity_id VARCHAR(100) NOT NULL
            );
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_investigation_history_user_id ON investigation_history(user_id);"))
        logger.info("Created investigation_history table and index.")
        
        # 4. Seed test users
        hashed_pw = get_password_hash("password123")
        users_to_seed = [
            # username, role, districts
            ("insp_mysuru", "INVESTIGATOR", "Mysuru"),
            ("insp_bengaluru", "INVESTIGATOR", "Bengaluru"),
            ("senior_sp", "SENIOR_INVESTIGATOR", "Mysuru,Bengaluru"),
            ("analyst_priya", "ANALYST", "Mysuru,Bengaluru,Mangaluru"),
            ("supervisor_ramesh", "SUPERVISOR", None),
            ("policymaker_anitha", "POLICY_MAKER", None),
        ]
        
        for username, role, districts in users_to_seed:
            # Check if user already exists
            res = conn.execute(text("SELECT id FROM users WHERE username = :u"), {"u": username}).fetchone()
            if not res:
                conn.execute(text("""
                    INSERT INTO users (username, hashed_password, role, districts)
                    VALUES (:u, :p, :r, :d)
                """), {"u": username, "p": hashed_pw, "r": role, "d": districts})
                logger.info(f"Seeded test user: {username} ({role}, districts={districts})")
            else:
                conn.execute(text("""
                    UPDATE users SET role = :r, districts = :d WHERE username = :u
                """), {"u": username, "r": role, "d": districts})
                logger.info(f"Updated existing test user: {username} ({role}, districts={districts})")

        logger.info("Database migration and seeding completed successfully.")

if __name__ == "__main__":
    asyncio.run(run_migration())
