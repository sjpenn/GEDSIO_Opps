"""
Entity Profile Service
Manages entity profiles with associated documents and vector store data.
Enables quick switching between primary entities while preserving all data.
"""
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from fedops_core.db.models import Entity, CompanyProfile, CompanyProfileDocument
from fedops_core.services.vector_store import VectorStore

logger = logging.getLogger(__name__)


class EntityProfileService:
    """
    Manages entity profiles with associated documents and vector store data.
    
    Provides functionality for:
    - Activating/deactivating entities as primary
    - Getting entity document summaries
    - Managing vector store data per entity
    - Listing available entities with their stats
    """
    
    def __init__(self, vector_store: Optional[VectorStore] = None):
        self.vector_store = vector_store or VectorStore()
    
    async def activate_entity(self, db: AsyncSession, entity_uei: str) -> Dict[str, Any]:
        """
        Set an entity as the primary entity, preserving the previous entity's data.
        
        Args:
            db: Database session
            entity_uei: UEI of the entity to activate
            
        Returns:
            Dict with activation status and entity info
        """
        # 1. Get the entity to activate
        result = await db.execute(
            select(Entity).where(Entity.uei == entity_uei)
        )
        entity = result.scalar_one_or_none()
        
        if not entity:
            return {
                "success": False,
                "error": f"Entity with UEI {entity_uei} not found"
            }
        
        # 2. Get current primary entity (if any) and deactivate it
        current_primary_result = await db.execute(
            select(Entity).where(Entity.is_primary == True)
        )
        current_primary = current_primary_result.scalar_one_or_none()
        
        previous_entity_uei = None
        if current_primary and current_primary.uei != entity_uei:
            current_primary.is_primary = False
            previous_entity_uei = current_primary.uei
            db.add(current_primary)
            logger.info(f"Deactivated previous primary entity: {current_primary.legal_business_name}")
        
        # 3. Activate the new entity
        entity.is_primary = True
        entity.last_active_at = datetime.utcnow()
        db.add(entity)
        
        await db.commit()
        await db.refresh(entity)
        
        logger.info(f"Activated entity as primary: {entity.legal_business_name} ({entity_uei})")
        
        return {
            "success": True,
            "entity": {
                "uei": entity.uei,
                "legal_business_name": entity.legal_business_name,
                "cage_code": entity.cage_code,
                "logo_url": entity.logo_url,
                "is_primary": entity.is_primary,
                "last_active_at": entity.last_active_at.isoformat() if entity.last_active_at else None
            },
            "previous_entity_uei": previous_entity_uei,
            "message": f"Successfully activated {entity.legal_business_name} as primary entity"
        }
    
    async def deactivate_entity(self, db: AsyncSession, entity_uei: str) -> Dict[str, Any]:
        """
        Deactivate an entity without setting a new primary.
        
        This preserves all entity data but removes the primary flag.
        """
        result = await db.execute(
            select(Entity).where(Entity.uei == entity_uei)
        )
        entity = result.scalar_one_or_none()
        
        if not entity:
            return {
                "success": False,
                "error": f"Entity with UEI {entity_uei} not found"
            }
        
        if not entity.is_primary:
            return {
                "success": True,
                "message": "Entity is already not primary"
            }
        
        entity.is_primary = False
        db.add(entity)
        await db.commit()
        
        logger.info(f"Deactivated entity: {entity.legal_business_name}")
        
        return {
            "success": True,
            "message": f"Successfully deactivated {entity.legal_business_name}"
        }
    
    async def get_entity_documents(
        self, 
        db: AsyncSession, 
        entity_uei: str
    ) -> List[Dict[str, Any]]:
        """
        Get all documents for an entity.
        
        Returns list of documents with their metadata.
        """
        result = await db.execute(
            select(CompanyProfileDocument)
            .where(CompanyProfileDocument.company_uei == entity_uei)
            .order_by(CompanyProfileDocument.created_at.desc())
        )
        documents = result.scalars().all()
        
        return [
            {
                "id": doc.id,
                "title": doc.title,
                "document_type": doc.document_type,
                "description": doc.description,
                "file_path": doc.file_path,
                "file_size": doc.file_size,
                "status": doc.status,
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
                "updated_at": doc.updated_at.isoformat() if doc.updated_at else None
            }
            for doc in documents
        ]
    
    async def get_entity_document_summary(
        self, 
        db: AsyncSession, 
        entity_uei: str
    ) -> Dict[str, Any]:
        """
        Get document counts and types for an entity.
        
        Returns summary with total count and breakdown by type.
        """
        # Get counts by document type
        result = await db.execute(
            select(
                CompanyProfileDocument.document_type,
                func.count(CompanyProfileDocument.id).label('count')
            )
            .where(CompanyProfileDocument.company_uei == entity_uei)
            .group_by(CompanyProfileDocument.document_type)
        )
        type_counts = result.all()
        
        document_types = {row[0]: row[1] for row in type_counts}
        total_count = sum(document_types.values())
        
        return {
            "entity_uei": entity_uei,
            "total_documents": total_count,
            "by_type": document_types
        }
    
    async def get_entity_vector_stats(self, entity_uei: str) -> Dict[str, Any]:
        """
        Get vector store statistics for an entity.
        
        Returns stats including collection counts and total chunks.
        """
        return await self.vector_store.get_entity_stats(entity_uei)
    
    async def list_available_entities(
        self, 
        db: AsyncSession,
        include_document_counts: bool = True
    ) -> List[Dict[str, Any]]:
        """
        List all entities with their document counts and activation status.
        
        Returns list of entity profiles sorted by:
        1. Primary entity first
        2. Then by last_active_at (most recent first)
        3. Then by name
        """
        # Get all entities that have been used (have a company profile or are/were primary)
        result = await db.execute(
            select(Entity)
            .order_by(
                Entity.is_primary.desc(),
                Entity.last_active_at.desc().nulls_last(),
                Entity.legal_business_name
            )
        )
        entities = result.scalars().all()
        
        entity_profiles = []
        
        for entity in entities:
            profile_data = {
                "uei": entity.uei,
                "legal_business_name": entity.legal_business_name,
                "cage_code": entity.cage_code,
                "logo_url": entity.logo_url,
                "is_primary": entity.is_primary,
                "last_active_at": entity.last_active_at.isoformat() if entity.last_active_at else None,
                "entity_type": entity.entity_type,
                "document_count": 0,
                "document_types": {}
            }
            
            if include_document_counts:
                doc_summary = await self.get_entity_document_summary(db, entity.uei)
                profile_data["document_count"] = doc_summary["total_documents"]
                profile_data["document_types"] = doc_summary["by_type"]
            
            # Only include entities that have been activated or have documents
            if entity.is_primary or entity.last_active_at or profile_data["document_count"] > 0:
                entity_profiles.append(profile_data)
        
        return entity_profiles
    
    async def get_primary_entity(self, db: AsyncSession) -> Optional[Dict[str, Any]]:
        """
        Get the current primary entity with its document summary.
        """
        result = await db.execute(
            select(Entity).where(Entity.is_primary == True)
        )
        entity = result.scalar_one_or_none()
        
        if not entity:
            return None
        
        doc_summary = await self.get_entity_document_summary(db, entity.uei)
        vector_stats = await self.get_entity_vector_stats(entity.uei)
        
        return {
            "uei": entity.uei,
            "legal_business_name": entity.legal_business_name,
            "cage_code": entity.cage_code,
            "logo_url": entity.logo_url,
            "is_primary": True,
            "last_active_at": entity.last_active_at.isoformat() if entity.last_active_at else None,
            "document_summary": doc_summary,
            "vector_stats": vector_stats
        }
    
    async def switch_entity(
        self, 
        db: AsyncSession, 
        from_uei: str, 
        to_uei: str
    ) -> Dict[str, Any]:
        """
        Switch from one primary entity to another.
        
        Convenience method that deactivates the current and activates the new.
        All data for both entities is preserved.
        """
        # Verify both entities exist
        from_result = await db.execute(select(Entity).where(Entity.uei == from_uei))
        from_entity = from_result.scalar_one_or_none()
        
        to_result = await db.execute(select(Entity).where(Entity.uei == to_uei))
        to_entity = to_result.scalar_one_or_none()
        
        if not from_entity:
            return {
                "success": False,
                "error": f"Source entity {from_uei} not found"
            }
        
        if not to_entity:
            return {
                "success": False,
                "error": f"Target entity {to_uei} not found"
            }
        
        # Perform the switch
        activation_result = await self.activate_entity(db, to_uei)
        
        if activation_result["success"]:
            return {
                "success": True,
                "switched_from": {
                    "uei": from_entity.uei,
                    "legal_business_name": from_entity.legal_business_name
                },
                "switched_to": activation_result["entity"],
                "message": f"Successfully switched from {from_entity.legal_business_name} to {to_entity.legal_business_name}"
            }
        
        return activation_result


# Global instance for convenience
entity_profile_service = EntityProfileService()
