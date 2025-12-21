"""
Opportunities Repository

Repository for Opportunity collection operations in Appwrite.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from appwrite.query import Query
from fedops_core.services.appwrite_repository import AppwriteRepository
import logging

logger = logging.getLogger(__name__)


class OpportunitiesRepository(AppwriteRepository):
    """Repository for opportunity documents."""
    
    def __init__(self):
        super().__init__("opportunities")
    
    async def get_by_notice_id(self, notice_id: str) -> Optional[Dict[str, Any]]:
        """Find opportunity by SAM.gov notice ID."""
        return await self.find_by_field("notice_id", notice_id)
    
    async def search(
        self,
        keyword: Optional[str] = None,
        naics_code: Optional[str] = None,
        department: Optional[str] = None,
        set_aside: Optional[str] = None,
        posted_from: Optional[datetime] = None,
        posted_to: Optional[datetime] = None,
        active: Optional[str] = None,
        limit: int = 25,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Search opportunities with various filters.
        
        Returns dict with 'documents' and 'total'.
        """
        queries = []
        
        if keyword:
            # Appwrite fulltext search on title
            queries.append(Query.search("title", keyword))
        
        if naics_code:
            queries.append(Query.equal("naics_code", naics_code))
        
        if department:
            queries.append(Query.equal("department", department))
        
        if set_aside:
            queries.append(Query.equal("type_of_set_aside", set_aside))
        
        if posted_from:
            queries.append(Query.greater_than_equal("posted_date", posted_from.isoformat()))
        
        if posted_to:
            queries.append(Query.less_than_equal("posted_date", posted_to.isoformat()))
        
        if active:
            queries.append(Query.equal("active", active))
        
        # Default ordering by posted_date desc
        queries.append(Query.order_desc("posted_date"))
        
        return await self.list(queries=queries, limit=limit, offset=offset)
    
    async def get_by_source(
        self, 
        source: str, 
        limit: int = 25, 
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get opportunities by source (SAM.gov, Manual, etc)."""
        return await self.list(
            queries=[Query.equal("source", source)],
            limit=limit,
            offset=offset
        )
    
    async def get_active(
        self, 
        limit: int = 25, 
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get active opportunities."""
        return await self.list(
            queries=[
                Query.equal("active", "Yes"),
                Query.order_desc("posted_date")
            ],
            limit=limit,
            offset=offset
        )
    
    async def get_by_naics(
        self, 
        naics_codes: List[str], 
        limit: int = 25
    ) -> Dict[str, Any]:
        """Get opportunities matching any of the NAICS codes."""
        return await self.list(
            queries=[Query.equal("naics_code", naics_codes)],
            limit=limit
        )
    
    async def update_resource_files(
        self, 
        document_id: str, 
        resource_files: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Update the resolved resource files for an opportunity."""
        return await self.update(document_id, {"resource_files": resource_files})
