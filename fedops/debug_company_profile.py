
import asyncio
import os
import sys
import json
from sqlalchemy import select

# Add project root to path
sys.path.append(os.getcwd())

from fedops_core.db.engine import AsyncSessionLocal
from fedops_core.db.models import Entity, CompanyProfile

async def debug_company_profile():
    print("--- Starting Debug ---")
    async with AsyncSessionLocal() as db:
        # 1. Check Primary Entity
        result = await db.execute(select(Entity).where(Entity.is_primary == True))
        primary = result.scalar_one_or_none()
        
        if not primary:
            print("ERROR: No primary entity found.")
            return

        print(f"Primary Entity: {primary.legal_business_name} (UEI: {primary.uei})")
        
        # 2. Check full_response for NAICS
        if primary.full_response:
            try:
                assertions = primary.full_response.get("assertions", {})
                goods = assertions.get("goodsAndServices", {})
                naics_list = goods.get("naicsList", [])
                print(f"Entities Raw NAICS Count: {len(naics_list)}")
                if naics_list:
                    print(f"First 3 NAICS in Raw Data: {[n.get('naicsCode') for n in naics_list[:3]]}")
            except Exception as e:
                print(f"Error reading full_response: {e}")
        else:
            print("WARNING: Primary entity has no full_response data.")

        # 3. Check Company Profile
        result = await db.execute(select(CompanyProfile).where(CompanyProfile.uei == primary.uei))
        profile = result.scalars().first()
        
        if not profile:
            print("ERROR: No CompanyProfile found for primary entity.")
        else:
            print(f"Company Profile Found: {profile.company_name}")
            print(f"Profile Target NAICS: {profile.target_naics}")
            print(f"Profile Target Set Asides: {profile.target_set_asides}")

if __name__ == "__main__":
    asyncio.run(debug_company_profile())
