"""
Additional Appwrite Repositories

Repositories for remaining collections.
"""

from typing import Optional, List, Dict, Any
from appwrite.query import Query
from fedops_core.services.appwrite_repository import AppwriteRepository
import logging

logger = logging.getLogger(__name__)


class CompanyProfilesRepository(AppwriteRepository):
    """Repository for company profile documents."""
    
    def __init__(self):
        super().__init__("company_profiles")
    
    async def get_by_uei(self, uei: str) -> Optional[Dict[str, Any]]:
        """Find company profile by UEI."""
        return await self.find_by_field("uei", uei)


class CompanyProfileDocumentsRepository(AppwriteRepository):
    """Repository for company profile documents."""
    
    def __init__(self):
        super().__init__("company_profile_documents")
    
    async def get_by_company(
        self, 
        company_uei: str, 
        document_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get documents for a company profile."""
        queries = [Query.equal("company_uei", company_uei)]
        if document_type:
            queries.append(Query.equal("document_type", document_type))
        return await self.list(queries=queries, limit=100)


class EntityAwardsRepository(AppwriteRepository):
    """Repository for entity award documents."""
    
    def __init__(self):
        super().__init__("entity_awards")
    
    async def get_by_uei(
        self, 
        recipient_uei: str, 
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get awards for an entity."""
        return await self.list(
            queries=[Query.equal("recipient_uei", recipient_uei)],
            limit=limit
        )
    
    async def get_by_award_id(self, award_id: str) -> Optional[Dict[str, Any]]:
        """Find award by award_id."""
        return await self.find_by_field("award_id", award_id)


class OpportunityPipelinesRepository(AppwriteRepository):
    """Repository for opportunity pipeline documents."""
    
    def __init__(self):
        super().__init__("opportunity_pipelines")
    
    async def get_by_opportunity(
        self, 
        opportunity_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get pipeline for an opportunity."""
        return await self.find_by_field("opportunity_id", opportunity_id)
    
    async def get_or_create(
        self, 
        opportunity_id: str
    ) -> Dict[str, Any]:
        """Get existing pipeline or create new one."""
        existing = await self.get_by_opportunity(opportunity_id)
        if existing:
            return existing
        
        return await self.create({
            "opportunity_id": opportunity_id,
            "status": "WATCHING",
            "stage": "QUALIFICATION"
        })
    
    async def get_by_status(
        self, 
        status: str, 
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get pipelines by status."""
        return await self.list(
            queries=[
                Query.equal("status", status),
                Query.equal("archived", False)
            ],
            limit=limit
        )


class DocumentChunksRepository(AppwriteRepository):
    """Repository for document chunk documents."""
    
    def __init__(self):
        super().__init__("document_chunks")
    
    async def get_by_file(
        self, 
        stored_file_id: str
    ) -> Dict[str, Any]:
        """Get chunks for a stored file."""
        return await self.list(
            queries=[
                Query.equal("stored_file_id", stored_file_id),
                Query.order_asc("chunk_index")
            ],
            limit=1000
        )
    
    async def get_by_opportunity(
        self, 
        opportunity_id: str
    ) -> Dict[str, Any]:
        """Get all chunks for an opportunity."""
        return await self.list(
            queries=[Query.equal("opportunity_id", opportunity_id)],
            limit=1000
        )


class DoclingDocumentsRepository(AppwriteRepository):
    """Repository for docling document outputs."""
    
    def __init__(self):
        super().__init__("docling_documents")
    
    async def get_by_file(
        self, 
        stored_file_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get docling output for a stored file."""
        return await self.find_by_field("stored_file_id", stored_file_id)


class PastPerformancesRepository(AppwriteRepository):
    """Repository for past performance documents."""
    
    def __init__(self):
        super().__init__("past_performances")
    
    async def get_by_entity(
        self, 
        entity_uei: str
    ) -> Dict[str, Any]:
        """Get past performances for an entity."""
        return await self.list(
            queries=[Query.equal("entity_uei", entity_uei)],
            limit=100
        )
    
    async def get_by_status(
        self, 
        status: str
    ) -> Dict[str, Any]:
        """Get past performances by status."""
        return await self.list(
            queries=[Query.equal("status", status)],
            limit=100
        )


class ResumesRepository(AppwriteRepository):
    """Repository for resume documents."""
    
    def __init__(self):
        super().__init__("resumes")
    
    async def get_by_user(
        self, 
        user_id: str
    ) -> Dict[str, Any]:
        """Get resumes for a user."""
        return await self.list(
            queries=[Query.equal("user_id", user_id)],
            limit=100
        )


class DocumentSectionsRepository(AppwriteRepository):
    """Repository for document section documents."""
    
    def __init__(self):
        super().__init__("document_sections")
    
    async def get_by_file(
        self, 
        stored_file_id: str
    ) -> Dict[str, Any]:
        """Get sections for a stored file."""
        return await self.list(
            queries=[Query.equal("stored_file_id", stored_file_id)],
            limit=100
        )
    
    async def get_by_opportunity(
        self, 
        opportunity_id: str
    ) -> Dict[str, Any]:
        """Get all sections for an opportunity."""
        return await self.list(
            queries=[Query.equal("opportunity_id", opportunity_id)],
            limit=100
        )
    
    async def get_section(
        self, 
        opportunity_id: str, 
        section_letter: str
    ) -> Optional[Dict[str, Any]]:
        """Get a specific section for an opportunity."""
        result = await self.list(
            queries=[
                Query.equal("opportunity_id", opportunity_id),
                Query.equal("section_letter", section_letter)
            ],
            limit=1
        )
        docs = result.get("documents", [])
        return docs[0] if docs else None


class OpportunityCommentsRepository(AppwriteRepository):
    """Repository for opportunity comment documents."""
    
    def __init__(self):
        super().__init__("opportunity_comments")
    
    async def get_by_opportunity(
        self, 
        opportunity_id: str
    ) -> Dict[str, Any]:
        """Get comments for an opportunity."""
        return await self.list(
            queries=[
                Query.equal("opportunity_id", opportunity_id),
                Query.order_desc("created_at")
            ],
            limit=100
        )


class OpportunityScoresRepository(AppwriteRepository):
    """Repository for opportunity score documents."""
    
    def __init__(self):
        super().__init__("opportunity_scores")
    
    async def get_by_opportunity(
        self, 
        opportunity_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get score for an opportunity."""
        return await self.find_by_field("opportunity_id", opportunity_id)
    
    async def get_or_create(
        self, 
        opportunity_id: str
    ) -> Dict[str, Any]:
        """Get existing score or create new one."""
        existing = await self.get_by_opportunity(opportunity_id)
        if existing:
            return existing
        
        return await self.create({
            "opportunity_id": opportunity_id,
            "strategic_alignment_score": 0.0,
            "financial_viability_score": 0.0,
            "contract_risk_score": 0.0,
            "internal_capacity_score": 0.0,
            "data_integrity_score": 0.0,
            "weighted_score": 0.0
        })
