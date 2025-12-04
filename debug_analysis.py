#!/usr/bin/env python3
"""
Debug script to test the analysis workflow and identify issues.
Usage: python debug_analysis.py <opportunity_id>
"""

import asyncio
import sys
import os

# Add fedops to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'fedops'))

from fedops_core.db.engine import get_db_context
from fedops_agents.capability_agent import CapabilityMappingAgent
from fedops_agents.past_performance_agent import PastPerformanceAgent
from fedops_agents.personnel_agent import PersonnelAgent
from sqlalchemy import select
from fedops_core.db.models import Opportunity, StoredFile

async def debug_analysis(opportunity_id: int):
    print(f"{'='*60}")
    print(f"Debugging Analysis for Opportunity ID: {opportunity_id}")
    print(f"{'='*60}\n")
    
    async with get_db_context() as db:
        # 1. Check Opportunity exists
        print("1. Checking Opportunity...")
        result = await db.execute(select(Opportunity).where(Opportunity.id == opportunity_id))
        opp = result.scalar_one_or_none()
        
        if not opp:
            print(f"❌ Opportunity {opportunity_id} not found!")
            return
        
        print(f"✓ Found: {opp.title}")
        print(f"  Department: {opp.department}")
        print(f"  Description: {opp.description[:100] if opp.description else 'None'}...")
        
        # 2. Check Files
        print("\n2. Checking Files...")
        files_result = await db.execute(select(StoredFile).where(StoredFile.opportunity_id == opportunity_id))
        files = files_result.scalars().all()
        
        print(f"  Found {len(files)} files:")
        for file in files:
            has_parsed = "✓" if file.parsed_content else "✗"
            exists = "✓" if os.path.exists(file.file_path) else "✗"
            print(f"    {has_parsed} Parsed | {exists} Exists | {file.filename}")
        
        if not files:
            print("  ⚠️  No files found - agents will use description only")
        
        # 3. Test PersonnelAgent
        print("\n3. Testing PersonnelAgent...")
        try:
            personnel_agent = PersonnelAgent(db)
            personnel_result = await personnel_agent.execute(opportunity_id)
            print(f"  ✓ Success")
            print(f"  Summary: {personnel_result.get('summary', 'N/A')[:100]}...")
            if 'key_personnel' in personnel_result:
                print(f"  Key Personnel: {len(personnel_result['key_personnel'])} found")
            if 'labor_categories' in personnel_result:
                print(f"  Labor Categories: {len(personnel_result['labor_categories'])} found")
        except Exception as e:
            print(f"  ❌ Failed: {str(e)}")
        
        # 4. Test PastPerformanceAgent
        print("\n4. Testing PastPerformanceAgent...")
        try:
            past_perf_agent = PastPerformanceAgent(db)
            past_perf_result = await past_perf_agent.execute(opportunity_id)
            print(f"  ✓ Success")
            print(f"  Summary: {past_perf_result.get('summary', 'N/A')[:100]}...")
            if 'requirements' in past_perf_result:
                print(f"  Requirements: {len(past_perf_result['requirements'])} found")
        except Exception as e:
            print(f"  ❌ Failed: {str(e)}")
        
        # 5. Test Full CapabilityMappingAgent
        print("\n5. Testing CapabilityMappingAgent (Full)...")
        try:
            cap_agent = CapabilityMappingAgent(db)
            cap_result = await cap_agent.execute(opportunity_id)
            print(f"  ✓ Success")
            print(f"  Status: {cap_result.get('status', 'unknown')}")
            print(f"  Strategic Score: {cap_result.get('strategic_alignment_score', 'N/A')}")
            print(f"  Capacity Score: {cap_result.get('internal_capacity_score', 'N/A')}")
            
            if 'personnel_details' in cap_result:
                print(f"  Personnel Details: {cap_result['personnel_details'].get('summary', 'N/A')[:80]}...")
            if 'past_performance_details' in cap_result:
                print(f"  Past Perf Details: {cap_result['past_performance_details'].get('summary', 'N/A')[:80]}...")
        except Exception as e:
            print(f"  ❌ Failed: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print(f"\n{'='*60}")
        print("Debug Complete")
        print(f"{'='*60}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_analysis.py <opportunity_id>")
        sys.exit(1)
    
    opportunity_id = int(sys.argv[1])
    asyncio.run(debug_analysis(opportunity_id))
