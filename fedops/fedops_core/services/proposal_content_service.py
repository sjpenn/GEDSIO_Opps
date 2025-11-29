"""
Proposal Content Service
Handles proposal content generation, editing, and management for Phase 4.
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fedops_core.db.models import Proposal, ProposalVolume
from fedops_core.services.proposal_content_generator import ProposalContentGenerator
from fedops_core.services.page_limit_extractor import PageLimitExtractor
import uuid
import json


class ProposalContentService:
    """Service for managing proposal content in Phase 4"""
    
    @staticmethod
    async def get_proposal_content(db: AsyncSession, proposal_id: int) -> Dict[str, Any]:
        """Get full proposal structure with all volumes and blocks"""
        result = await db.execute(
            select(Proposal).where(Proposal.id == proposal_id)
        )
        proposal = result.scalar_one_or_none()
        
        if not proposal:
            raise ValueError(f"Proposal {proposal_id} not found")
        
        # Get all volumes
        volumes_result = await db.execute(
            select(ProposalVolume)
            .where(ProposalVolume.proposal_id == proposal_id)
            .order_by(ProposalVolume.order)
        )
        volumes = volumes_result.scalars().all()
        
        return {
            "proposal": {
                "id": proposal.id,
                "opportunity_id": proposal.opportunity_id,
                "version": proposal.version,
                "shipley_phase": proposal.shipley_phase,
            },
            "volumes": [
                {
                    "id": vol.id,
                    "title": vol.title,
                    "order": vol.order,
                    "blocks": vol.blocks or []
                }
                for vol in volumes
            ]
        }
    
    @staticmethod
    async def create_section(
        db: AsyncSession,
        proposal_id: int,
        volume_id: int,
        title: str,
        content: str = "",
        order: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create a new section (block) in a volume"""
        # Get the volume and proposal
        result = await db.execute(
            select(ProposalVolume).where(ProposalVolume.id == volume_id)
        )
        volume = result.scalar_one_or_none()
        
        if not volume or volume.proposal_id != proposal_id:
            raise ValueError(f"Volume {volume_id} not found for proposal {proposal_id}")
        
        # Get proposal to get opportunity_id
        proposal_result = await db.execute(
            select(Proposal).where(Proposal.id == proposal_id)
        )
        proposal = proposal_result.scalar_one_or_none()
        
        # Get current blocks
        blocks = list(volume.blocks or [])
        
        # Determine order
        if order is None:
            order = len(blocks)
        
        # Try to extract page limit from solicitation
        page_limit = None
        page_limit_source = None
        
        if proposal:
            try:
                extractor = PageLimitExtractor()
                page_limits = await extractor.extract_page_limits(db, proposal.opportunity_id)
                
                # Match this section title to extracted limits
                limit_data = extractor.match_to_section_title(title, page_limits)
                if limit_data:
                    page_limit = limit_data.get('limit')
                    page_limit_source = limit_data.get('source')
            except Exception as e:
                print(f"Error extracting page limit for section '{title}': {e}")
        
        # Create new block with page limit info
        new_block = {
            "id": str(uuid.uuid4()),
            "title": title,
            "content": content,
            "order": order
        }
        
        # Add page limit fields if available
        if page_limit is not None:
            new_block["page_limit"] = page_limit
        if page_limit_source:
            new_block["page_limit_source"] = page_limit_source
        
        blocks.append(new_block)
        volume.blocks = blocks
        
        await db.commit()
        await db.refresh(volume)
        
        return new_block
    
    @staticmethod
    async def update_section(
        db: AsyncSession,
        proposal_id: int,
        volume_id: int,
        block_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        order: Optional[int] = None
    ) -> Dict[str, Any]:
        """Update an existing section (block)"""
        # Get the volume
        result = await db.execute(
            select(ProposalVolume).where(ProposalVolume.id == volume_id)
        )
        volume = result.scalar_one_or_none()
        
        if not volume or volume.proposal_id != proposal_id:
            raise ValueError(f"Volume {volume_id} not found for proposal {proposal_id}")
        
        # Get current blocks
        blocks = list(volume.blocks or [])
        
        # Find and update the block
        updated = False
        for block in blocks:
            if block.get("id") == block_id:
                if title is not None:
                    block["title"] = title
                if content is not None:
                    block["content"] = content
                if order is not None:
                    block["order"] = order
                updated = True
                break
        
        if not updated:
            raise ValueError(f"Block {block_id} not found in volume {volume_id}")
        
        # Re-sort blocks by order
        blocks.sort(key=lambda b: b.get("order", 0))
        volume.blocks = blocks
        
        await db.commit()
        await db.refresh(volume)
        
        return next(b for b in blocks if b.get("id") == block_id)
    
    @staticmethod
    async def delete_section(
        db: AsyncSession,
        proposal_id: int,
        volume_id: int,
        block_id: str
    ) -> bool:
        """Delete a section (block)"""
        # Get the volume
        result = await db.execute(
            select(ProposalVolume).where(ProposalVolume.id == volume_id)
        )
        volume = result.scalar_one_or_none()
        
        if not volume or volume.proposal_id != proposal_id:
            raise ValueError(f"Volume {volume_id} not found for proposal {proposal_id}")
        
        # Get current blocks
        blocks = list(volume.blocks or [])
        
        # Filter out the block
        new_blocks = [b for b in blocks if b.get("id") != block_id]
        
        if len(new_blocks) == len(blocks):
            raise ValueError(f"Block {block_id} not found in volume {volume_id}")
        
        volume.blocks = new_blocks
        
        await db.commit()
        
        return True
    
    @staticmethod
    async def generate_content(
        db: AsyncSession,
        proposal_id: int,
        volume_id: int,
        block_id: str,
        prompt: Optional[str] = None
    ) -> str:
        """Generate content for a section using AI"""
        # Get the volume and block
        result = await db.execute(
            select(ProposalVolume).where(ProposalVolume.id == volume_id)
        )
        volume = result.scalar_one_or_none()
        
        if not volume or volume.proposal_id != proposal_id:
            raise ValueError(f"Volume {volume_id} not found for proposal {proposal_id}")
        
        blocks = volume.blocks or []
        block = next((b for b in blocks if b.get("id") == block_id), None)
        
        if not block:
            raise ValueError(f"Block {block_id} not found in volume {volume_id}")
        
        # Use the ProposalContentGenerator to generate real content
        generator = ProposalContentGenerator(db)
        
        # Get section title for context
        section_title = block.get('title', 'Section')
        
        # Generate content
        result = await generator.generate_section_content(
            proposal_id=proposal_id,
            section_title=section_title,
            prompt_instructions=prompt
        )
        
        if result["status"] == "error":
            raise ValueError(result["message"])
            
        generated_content = result["content"]
        
        return generated_content
    
    @staticmethod
    async def reorder_sections(
        db: AsyncSession,
        proposal_id: int,
        volume_id: int,
        block_orders: List[Dict[str, Any]]  # [{"id": "uuid", "order": 0}, ...]
    ) -> List[Dict[str, Any]]:
        """Reorder sections in a volume"""
        # Get the volume
        result = await db.execute(
            select(ProposalVolume).where(ProposalVolume.id == volume_id)
        )
        volume = result.scalar_one_or_none()
        
        if not volume or volume.proposal_id != proposal_id:
            raise ValueError(f"Volume {volume_id} not found for proposal {proposal_id}")
        
        # Get current blocks
        blocks = list(volume.blocks or [])
        
        # Update orders
        order_map = {item["id"]: item["order"] for item in block_orders}
        for block in blocks:
            if block.get("id") in order_map:
                block["order"] = order_map[block["id"]]
        
        # Sort by new order
        blocks.sort(key=lambda b: b.get("order", 0))
        volume.blocks = blocks
        
        await db.commit()
        await db.refresh(volume)
        
        return blocks
