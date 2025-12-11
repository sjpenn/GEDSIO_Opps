import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from fedops_core.db.engine import engine, Base
from fedops_core.db.models import Resume

async def create_table():
    print("Creating tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created (if not existed).")

if __name__ == "__main__":
    asyncio.run(create_table())
