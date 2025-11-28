
import asyncio
from sqlalchemy import select, func
from fedops_core.db.engine import AsyncSessionLocal
from fedops_core.db.models import Opportunity

async def check_max_opp_id():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(func.max(Opportunity.id)))
        max_id = result.scalar()
        print(f"Max Opportunity ID: {max_id}")
        
        # List last 5 IDs
        res = await db.execute(select(Opportunity.id).order_by(Opportunity.id.desc()).limit(5))
        ids = res.scalars().all()
        print(f"Last 5 IDs: {ids}")

if __name__ == "__main__":
    asyncio.run(check_max_opp_id())
