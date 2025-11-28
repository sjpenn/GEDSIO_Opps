
import asyncio
from sqlalchemy import select
from fedops_core.db.engine import AsyncSessionLocal
from fedops_core.db.models import StoredFile, Opportunity

async def check_files():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(StoredFile).limit(10))
        files = result.scalars().all()
        print(f"Found {len(files)} files:")
        for f in files:
            print(f"ID: {f.id}, Filename: {f.filename}, Opp ID: {f.opportunity_id}, Content Len: {len(f.parsed_content) if f.parsed_content else 0}")
            
            if f.opportunity_id:
                opp_result = await db.execute(select(Opportunity).where(Opportunity.id == f.opportunity_id))
                opp = opp_result.scalar_one_or_none()
                if opp:
                    print(f"  Opportunity: {opp.title} (ID: {opp.id})")

if __name__ == "__main__":
    asyncio.run(check_files())
