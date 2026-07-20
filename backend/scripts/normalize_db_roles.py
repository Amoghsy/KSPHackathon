import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.user import User
from app.core.rbac import normalize_role

async def run_normalization():
    print("Connecting to database to normalize roles...")
    async with SessionLocal() as db:
        try:
            stmt = select(User)
            result = await db.execute(stmt)
            users = result.scalars().all()
            
            updated_count = 0
            for user in users:
                normalized = normalize_role(user.role)
                if user.role != normalized:
                    print(f"User '{user.username}': role '{user.role}' -> '{normalized}'")
                    user.role = normalized
                    updated_count += 1
            
            if updated_count > 0:
                await db.commit()
                print(f"Successfully normalized roles for {updated_count} user(s).")
            else:
                print("All user roles are already normalized.")
                
        except Exception as e:
            print("Error during role normalization:", e)
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(run_normalization())
