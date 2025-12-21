"""
Proposals Repository

Repository for Proposal and ProposalVolume collection operations.
"""

from typing import Optional, List, Dict, Any
from appwrite.query import Query
from fedops_core.services.appwrite_repository import AppwriteRepository
import logging

logger = logging.getLogger(__name__)


class ProposalsRepository(AppwriteRepository):
    """Repository for proposal documents."""
    
    def __init__(self):
        super().__init__("proposals")
    
    async def get_by_opportunity(
        self, 
        opportunity_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get proposal for an opportunity."""
        return await self.find_by_field("opportunity_id", opportunity_id)
    
    async def get_or_create(
        self, 
        opportunity_id: str
    ) -> Dict[str, Any]:
        """Get existing proposal or create new one."""
        existing = await self.get_by_opportunity(opportunity_id)
        if existing:
            return existing
        
        return await self.create({
            "opportunity_id": opportunity_id,
            "version": 1,
            "current_stage": "DISCOVERY",
            "stage_status": "IN_PROGRESS"
        })
    
    async def update_stage(
        self, 
        document_id: str, 
        stage: str, 
        status: str = "IN_PROGRESS"
    ) -> Dict[str, Any]:
        """Update proposal stage and status."""
        return await self.update(document_id, {
            "current_stage": stage,
            "stage_status": status
        })
    
    async def get_by_stage(
        self, 
        stage: str, 
        limit: int = 25
    ) -> Dict[str, Any]:
        """Get proposals by current stage."""
        return await self.list(
            queries=[Query.equal("current_stage", stage)],
            limit=limit
        )
    
    async def record_bid_decision(
        self, 
        document_id: str,
        decision: str,
        score: float,
        justification: str,
        decided_by: str
    ) -> Dict[str, Any]:
        """Record a bid decision on a proposal."""
        from datetime import datetime
        return await self.update(document_id, {
            "bid_decision_score": score,
            "bid_decision_justification": justification,
            "bid_decision_by": decided_by,
            "bid_decision_date": datetime.utcnow().isoformat(),
            "stage_status": decision  # GO, NO_GO, etc.
        })


class ProposalVolumesRepository(AppwriteRepository):
    """Repository for proposal volume documents."""
    
    def __init__(self):
        super().__init__("proposal_volumes")
    
    async def get_by_proposal(
        self, 
        proposal_id: str
    ) -> Dict[str, Any]:
        """Get all volumes for a proposal."""
        return await self.list(
            queries=[
                Query.equal("proposal_id", proposal_id),
                Query.order_asc("order")
            ],
            limit=100
        )
    
    async def create_volume(
        self,
        proposal_id: str,
        title: str,
        order: int = 0,
        blocks: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Create a new proposal volume."""
        return await self.create({
            "proposal_id": proposal_id,
            "title": title,
            "order": order,
            "blocks": blocks or []
        })
    
    async def update_blocks(
        self, 
        document_id: str, 
        blocks: List[Dict]
    ) -> Dict[str, Any]:
        """Update the content blocks for a volume."""
        return await self.update(document_id, {"blocks": blocks})
