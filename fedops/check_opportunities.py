
import asyncio
from sqlalchemy import select
from fedops_core.db.engine import AsyncSessionLocal
from fedops_core.db.models import Opportunity

async def check_opportunities():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Opportunity))
        opps = result.scalars().all()
        print(f"Found {len(opps)} opportunities:")
        for o in opps:
            print(f"ID: {o.id}, Title: {o.title}")

if __name__ == "__main__":
    asyncio.run(check_opportunities())
