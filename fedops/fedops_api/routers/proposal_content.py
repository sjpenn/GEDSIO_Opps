"""
Proposal Content API Router
Handles API endpoints for Phase 4 proposal content management.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from fedops_core.db.engine import get_db
from fedops_core.services.proposal_content_service import ProposalContentService
from fedops_core.services.file_storage_service import FileStorageService

router = APIRouter(prefix="/proposal-content", tags=["proposal-content"])


# Pydantic models
class SectionCreate(BaseModel):
    title: str
    content: str = ""
    order: Optional[int] = None


class SectionUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    order: Optional[int] = None


class ContentGenerationRequest(BaseModel):
    prompt: Optional[str] = None


class ReorderRequest(BaseModel):
    block_orders: List[Dict[str, Any]]  # [{"id": "uuid", "order": 0}, ...]


class ExportRequest(BaseModel):
    format: str = "markdown"  # markdown, pdf, docx


@router.get("/proposals/{proposal_id}/content")
async def get_proposal_content(
    proposal_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get full proposal structure with all volumes and blocks"""
    try:
        content = await ProposalContentService.get_proposal_content(db, proposal_id)
        return content
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/proposals/{proposal_id}/volumes/{volume_id}/sections")
async def create_section(
    proposal_id: int,
    volume_id: int,
    request: SectionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new section in a volume"""
    try:
        section = await ProposalContentService.create_section(
            db=db,
            proposal_id=proposal_id,
            volume_id=volume_id,
            title=request.title,
            content=request.content,
            order=request.order
        )
        return section
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/proposals/{proposal_id}/volumes/{volume_id}/sections/{block_id}")
async def update_section(
    proposal_id: int,
    volume_id: int,
    block_id: str,
    request: SectionUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing section"""
    try:
        section = await ProposalContentService.update_section(
            db=db,
            proposal_id=proposal_id,
            volume_id=volume_id,
            block_id=block_id,
            title=request.title,
            content=request.content,
            order=request.order
        )
        return section
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/proposals/{proposal_id}/volumes/{volume_id}/sections/{block_id}")
async def delete_section(
    proposal_id: int,
    volume_id: int,
    block_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a section"""
    try:
        success = await ProposalContentService.delete_section(
            db=db,
            proposal_id=proposal_id,
            volume_id=volume_id,
            block_id=block_id
        )
        return {"success": success}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/proposals/{proposal_id}/volumes/{volume_id}/sections/{block_id}/generate")
async def generate_content(
    proposal_id: int,
    volume_id: int,
    block_id: str,
    request: ContentGenerationRequest,
    db: AsyncSession = Depends(get_db)
):
    """Generate AI content for a section"""
    try:
        content = await ProposalContentService.generate_content(
            db=db,
            proposal_id=proposal_id,
            volume_id=volume_id,
            block_id=block_id,
            prompt=request.prompt
        )
        return {"content": content}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/proposals/{proposal_id}/volumes/{volume_id}/reorder")
async def reorder_sections(
    proposal_id: int,
    volume_id: int,
    request: ReorderRequest,
    db: AsyncSession = Depends(get_db)
):
    """Reorder sections in a volume"""
    try:
        blocks = await ProposalContentService.reorder_sections(
            db=db,
            proposal_id=proposal_id,
            volume_id=volume_id,
            block_orders=request.block_orders
        )
        return {"blocks": blocks}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/proposals/{proposal_id}/export")
async def export_proposal(
    proposal_id: int,
    request: ExportRequest,
    db: AsyncSession = Depends(get_db)
):
    """Export proposal to file"""
    try:
        # Get proposal content
        content_data = await ProposalContentService.get_proposal_content(db, proposal_id)
        
        # Format as markdown
        markdown_content = _format_as_markdown(content_data)
        
        # Save to file storage
        storage = FileStorageService()
        filepath = storage.save_proposal_export(
            proposal_id=proposal_id,
            content=markdown_content,
            extension="md"
        )
        
        return {
            "success": True,
            "filepath": filepath,
            "format": "markdown"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _format_as_markdown(content_data: Dict[str, Any]) -> str:
    """Format proposal content as markdown"""
    lines = []
    
    # Title
    lines.append(f"# Proposal {content_data['proposal']['id']}")
    lines.append("")
    lines.append(f"**Version:** {content_data['proposal']['version']}")
    lines.append(f"**Phase:** {content_data['proposal']['shipley_phase']}")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Volumes
    for volume in content_data['volumes']:
        lines.append(f"## {volume['title']}")
        lines.append("")
        
        # Blocks/Sections
        for block in sorted(volume['blocks'], key=lambda b: b.get('order', 0)):
            lines.append(f"### {block.get('title', 'Untitled Section')}")
            lines.append("")
            lines.append(block.get('content', ''))
            lines.append("")
    
    return "\n".join(lines)


@router.post("/proposals/{proposal_id}/generate-sources-sought")
async def generate_sources_sought(
    proposal_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Generate a Sources Sought / RFI response"""
    try:
        result = await ProposalContentService.generate_sources_sought(db, proposal_id)
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
