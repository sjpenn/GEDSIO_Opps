from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fedops_agents.base_agent import BaseAgent
from fedops_core.db.models import Proposal
from fedops_core.services.ai_service import AIService
from fedops_core.prompts import CONTENT_REVIEW_PROMPT

class ReviewerAgent(BaseAgent):
    def __init__(self, db: AsyncSession):
        super().__init__("ReviewerAgent", db)
        self.ai_service = AIService()

    async def execute(self, opportunity_id: int, **kwargs) -> Dict[str, Any]:
        """
        Executes a review cycle for a specific proposal section or the entire proposal.
        
        kwargs:
            proposal_id (int): Required.
            section_id (str, optional): If provided, review only this section.
            review_type (str, optional): "compliance", "quality", "full". Default "full".
        """
        proposal_id = kwargs.get('proposal_id')
        section_id = kwargs.get('section_id')
        review_type = kwargs.get('review_type', 'full')

        if not proposal_id:
            raise ValueError("proposal_id is required for ReviewerAgent")

        await self.log_activity(opportunity_id, "START_REVIEW", "IN_PROGRESS", {"section_id": section_id})

        try:
            # Fetch Proposal
            result = await self.db.execute(select(Proposal).where(Proposal.id == proposal_id))
            proposal = result.scalar_one_or_none()
            if not proposal:
                raise ValueError(f"Proposal {proposal_id} not found")

            # Determine scope
            sections_to_review = []
            if section_id:
                 # Fetch specific block/content. 
                 # Note: ProposalContentSection might not map directly if we are using JSON blocks in Volume.
                 # Assuming for now we are reviewing text content passed or retrieving it from DB models.
                 # Ideally we should look up the section content.
                 pass 
                 # For MVP, assuming we pass content directly or fetch all blocks and filter.
            else:
                # Review all available content (MVP: limit to first few or specific active ones)
                pass

            # Mocking content retrieval for now if not implemented in models fully for granular access
            # In a real scenario, we'd query ProposalContent or similar.
            
            # For this implementation, let's assume we are reviewing a specific text provided in kwargs
            # or fetching from a conceptual ProposalSection model.
            
            content_to_review = kwargs.get('content')
            context = kwargs.get('context', '') # Requirements etc.

            if not content_to_review:
                 return {"status": "skipped", "message": "No content to review"}

            # AI Review
            prompt = CONTENT_REVIEW_PROMPT.format(
                content=content_to_review,
                requirements=context
            )
            
            review_result = await self.ai_service.analyze_opportunity(prompt) # Using analyze_opportunity as generic JSON extractor
            
            # Store Review
            # review_entry = ProposalReview(...)
            # self.db.add(review_entry)
            # await self.db.commit()

            await self.log_activity(opportunity_id, "REVIEW_COMPLETE", "SUCCESS", {"score": review_result.get("score")})

            return {
                "status": "success",
                "review": review_result
            }

        except Exception as e:
            await self.log_activity(opportunity_id, "REVIEW_ERROR", "FAILURE", {"error": str(e)})
            return {"status": "error", "message": str(e)}
