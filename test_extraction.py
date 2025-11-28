#!/usr/bin/env python3
import asyncio
import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'fedops'))

from fedops_core.db.engine import get_db_context
from fedops_core.services.requirement_extraction_service import RequirementExtractionService

async def test_extraction(proposal_id):
    async with get_db_context() as db:
        service = RequirementExtractionService(db)
        result = await service.extract_requirements_from_proposal(proposal_id)
        print(f"Result: {result}")

if __name__ == "__main__":
    proposal_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    asyncio.run(test_extraction(proposal_id))
