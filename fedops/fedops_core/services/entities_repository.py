"""
Entities Repository

Repository for Entity collection operations in Appwrite.
"""

from typing import Optional, List, Dict, Any
from appwrite.query import Query
from fedops_core.services.appwrite_repository import AppwriteRepository
import logging

logger = logging.getLogger(__name__)


class EntitiesRepository(AppwriteRepository):
    """Repository for entity documents."""
    
    def __init__(self):
        super().__init__("entities")
    
    async def get_by_uei(self, uei: str) -> Optional[Dict[str, Any]]:
        """Find entity by UEI."""
        return await self.find_by_field("uei", uei)
    
    async def get_primary_entity(self) -> Optional[Dict[str, Any]]:
        """Get the primary entity."""
        return await self.find_one([Query.equal("is_primary", True)])
    
    async def set_primary_entity(self, uei: str) -> Dict[str, Any]:
        """
        Set an entity as primary, unsetting any existing primary.
        
        Args:
            uei: UEI of the entity to set as primary
            
        Returns:
            Updated entity document
        """
        # First, unset any existing primary
        current_primary = await self.get_primary_entity()
        if current_primary and current_primary.get("uei") != uei:
            await self.update(current_primary["id"], {"is_primary": False})
        
        # Find the entity by UEI
        entity = await self.get_by_uei(uei)
        if not entity:
            raise ValueError(f"Entity with UEI {uei} not found")
        
        # Set as primary
        return await self.update(entity["id"], {"is_primary": True})
    
    async def get_by_entity_type(
        self, 
        entity_type: str, 
        limit: int = 25
    ) -> Dict[str, Any]:
        """Get entities by type (PARTNER, COMPETITOR, etc)."""
        return await self.list(
            queries=[Query.equal("entity_type", entity_type)],
            limit=limit
        )
    
    async def search_by_name(
        self, 
        name: str, 
        limit: int = 10
    ) -> Dict[str, Any]:
        """Search entities by business name."""
        return await self.list(
            queries=[Query.search("legal_business_name", name)],
            limit=limit
        )
    
    async def get_partners(self, limit: int = 25) -> Dict[str, Any]:
        """Get partner entities."""
        return await self.get_by_entity_type("PARTNER", limit)
    
    async def get_competitors(self, limit: int = 25) -> Dict[str, Any]:
        """Get competitor entities."""
        return await self.get_by_entity_type("COMPETITOR", limit)
