#!/usr/bin/env python3
import asyncio
import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'fedops'))

from sqlalchemy import select
from fedops_core.db.engine import get_db_context
from fedops_core.db.models import Proposal, Opportunity, StoredFile

async def check_documents(opportunity_id):
    async with get_db_context() as db:
        # Get opportunity
        result = await db.execute(select(Opportunity).where(Opportunity.id == opportunity_id))
        opp = result.scalar_one_or_none()
        
        if not opp:
            print(f"❌ Opportunity {opportunity_id} not found!")
            return
        
        print(f"✅ Opportunity found: {opp.title}")
        
        # Get stored files
        result = await db.execute(select(StoredFile).where(StoredFile.opportunity_id == opportunity_id))
        files = result.scalars().all()
        
        print(f"\n📁 Found {len(files)} stored files:")
        for f in files:
            print(f"\n  File: {f.filename}")
            print(f"    ID: {f.id}")
            print(f"    Path: {f.file_path}")
            print(f"    File exists: {os.path.exists(f.file_path) if f.file_path else 'No path'}")
            print(f"    Parsed content length: {len(f.parsed_content) if f.parsed_content else 0}")
            
            if f.parsed_content:
                print(f"    First 200 chars: {f.parsed_content[:200]}")

if __name__ == "__main__":
    opp_id = int(sys.argv[1]) if len(sys.argv) > 1 else 3509
    asyncio.run(check_documents(opp_id))
