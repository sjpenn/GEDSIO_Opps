import asyncio
import sys
import os
from sqlalchemy import select, func

# Add the project root to the python path
sys.path.append(os.getcwd())

from fedops_core.db.engine import AsyncSessionLocal
from fedops_core.db.models import (
    Opportunity, 
    OpportunityPipeline, 
    OpportunityScore, 
    Proposal, 
    ProposalVolume, 
    ProposalRequirement, 
    DocumentArtifact,
    AgentActivityLog
)

async def verify_storage():
    async with AsyncSessionLocal() as db:
        print("=== Verifying DB Storage ===")
        
        # 1. Pipeline Opportunities
        print("\n--- Pipeline Opportunities ---")
        result = await db.execute(select(OpportunityPipeline))
        pipelines = result.scalars().all()
        print(f"Total Pipeline Items: {len(pipelines)}")
        for p in pipelines:
            print(f"  - Opportunity ID: {p.opportunity_id}, Stage: {p.stage}, Status: {p.status}")
            
        # 2. Analysis Results
        print("\n--- Analysis Results ---")
        result = await db.execute(select(OpportunityScore))
        scores = result.scalars().all()
        print(f"Total Analyzed Opportunities: {len(scores)}")
        for s in scores:
            print(f"  - Opportunity ID: {s.opportunity_id}, Score: {s.weighted_score}, Decision: {s.go_no_go_decision}")
            
        # 3. Proposal Workspace
        print("\n--- Proposal Workspaces ---")
        result = await db.execute(select(Proposal))
        proposals = result.scalars().all()
        print(f"Total Proposals: {len(proposals)}")
        for p in proposals:
            print(f"  - Proposal ID: {p.id} (Opp ID: {p.opportunity_id}), Version: {p.version}")
            
            # Check volumes
            vol_res = await db.execute(select(func.count(ProposalVolume.id)).where(ProposalVolume.proposal_id == p.id))
            vol_count = vol_res.scalar()
            
            # Check requirements
            req_res = await db.execute(select(func.count(ProposalRequirement.id)).where(ProposalRequirement.proposal_id == p.id))
            req_count = req_res.scalar()
            
            # Check artifacts
            art_res = await db.execute(select(func.count(DocumentArtifact.id)).where(DocumentArtifact.proposal_id == p.id))
            art_count = art_res.scalar()
            
            print(f"    - Volumes: {vol_count}")
            print(f"    - Requirements: {req_count}")
            print(f"    - Artifacts: {art_count}")

        # 4. Agent Activity Logs
        print("\n--- Agent Activity Logs ---")
        result = await db.execute(select(func.count(AgentActivityLog.id)))
        log_count = result.scalar()
        print(f"Total Activity Logs: {log_count}")

if __name__ == "__main__":
    asyncio.run(verify_storage())
