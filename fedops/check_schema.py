from fedops_core.db.engine import AsyncSessionLocal
from sqlalchemy import text
import asyncio

async def check_schema():
    async with AsyncSessionLocal() as session:
        # Check alembic version
        try:
            result = await session.execute(text("SELECT version_num FROM alembic_version"))
            version = result.scalar()
            print(f"Current alembic version: {version}")
        except Exception as e:
            print(f"Error checking alembic version: {e}")
        
        # Check opportunity_teams
        result = await session.execute(text("SELECT to_regclass('public.opportunity_teams')"))
        table_exists = result.scalar()
        print(f"opportunity_teams table exists: {table_exists is not None}")
        
        # Check entities columns
        result = await session.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'entities'"))
        columns = [row[0] for row in result.fetchall()]
        new_cols = ['revenue', 'capabilities', 'locations', 'web_addresses', 'personnel_count', 'business_types']
        for col in new_cols:
            print(f"Column {col} exists in entities: {col in columns}")

if __name__ == "__main__":
    asyncio.run(check_schema())
