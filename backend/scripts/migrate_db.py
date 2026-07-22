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
        
        # 1. Update users table (no legacy districts column added)
        logger.info("Skipped adding legacy districts column to users table.")
        
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
            ("insp_bengaluru", "INVESTIGATOR", "Bengaluru Urban"),
            ("senior_sp", "SENIOR_INVESTIGATOR", "Mysuru,Bengaluru Urban"),
            ("analyst_priya", "ANALYST", "Mysuru,Bengaluru Urban,Mangaluru"),
            ("supervisor_ramesh", "SUPERVISOR", None),
            ("policymaker_anitha", "POLICY_MAKER", None),
        ]
        
        for username, role, districts in users_to_seed:
            # Check if user already exists
            res = conn.execute(text("SELECT id FROM users WHERE username = :u"), {"u": username}).fetchone()
            if not res:
                res_insert = conn.execute(text("""
                    INSERT INTO users (username, hashed_password, role, email, employee_id, full_name, must_change_password, account_status)
                    VALUES (:u, :p, :r, :email, :emp, :name, FALSE, 'ACTIVE')
                    RETURNING id
                """), {
                    "u": username,
                    "p": hashed_pw,
                    "r": role,
                    "email": f"{username}@ksp.gov.in",
                    "emp": f"KSP-{10000 + hash(username)%1000}",
                    "name": username.replace("_", " ").title()
                })
                user_id = res_insert.fetchone()[0]
                logger.info(f"Seeded test user: {username} ({role})")
            else:
                user_id = res[0]
                conn.execute(text("""
                    UPDATE users SET role = :r WHERE id = :user_id
                """), {"r": role, "user_id": user_id})
                logger.info(f"Updated existing test user: {username} ({role})")

            # Seed district assignments idempotently
            if districts:
                for d_name in districts.split(","):
                    d_name = d_name.strip()
                    if d_name:
                        # Check if active assignment already exists
                        chk = conn.execute(text("""
                            SELECT id FROM user_district_assignments
                            WHERE user_id = :user_id AND district = :d AND is_active = TRUE
                        """), {"user_id": user_id, "d": d_name}).fetchone()
                        if not chk:
                            conn.execute(text("""
                                INSERT INTO user_district_assignments (user_id, district, is_active, assigned_at)
                                VALUES (:user_id, :d, TRUE, NOW())
                            """), {"user_id": user_id, "d": d_name})
                            logger.info(f"Assigned user {username} to district {d_name}")

        logger.info("Database migration and seeding completed successfully.")

if __name__ == "__main__":
    asyncio.run(run_migration())
