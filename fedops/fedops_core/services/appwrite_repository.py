"""
Appwrite Base Repository

Provides base CRUD operations for Appwrite collections.
All entity-specific repositories inherit from this class.
"""

# Suppress Appwrite SDK deprecation warnings relating to Documents->Rows rename
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*deprecated.*")

from typing import TypeVar, Generic, Optional, List, Dict, Any
from datetime import datetime
from appwrite.id import ID
from appwrite.query import Query
from appwrite.exception import AppwriteException
from fedops_core.db.appwrite_client import (
    databases, 
    DATABASE_ID, 
    get_collection_id
)
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=Dict[str, Any])


class AppwriteRepository(Generic[T]):
    """
    Base repository class for Appwrite database operations.
    
    Provides standard CRUD operations that can be extended by
    entity-specific repositories.
    """
    
    def __init__(self, collection_name: str):
        """
        Initialize repository for a specific collection.
        
        Args:
            collection_name: Name of the collection (used to look up collection ID)
        """
        self.collection_name = collection_name
        self.collection_id = get_collection_id(collection_name)
        self.database_id = DATABASE_ID
    
    def _add_timestamps(self, data: Dict[str, Any], is_update: bool = False) -> Dict[str, Any]:
        """Add created_at/updated_at timestamps to data."""
        now = datetime.utcnow().isoformat()
        if not is_update and "created_at" not in data:
            data["created_at"] = now
        data["updated_at"] = now
        return data
    
    def _clean_response(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean Appwrite response by extracting document data.
        Preserves the $id field as 'id' for compatibility.
        """
        if not document:
            return None
        
        result = dict(document)
        # Map Appwrite's $id to 'id' for consistency
        if "$id" in result:
            result["id"] = result.pop("$id")
        # Remove other Appwrite metadata if needed
        result.pop("$collectionId", None)
        result.pop("$databaseId", None)
        result.pop("$permissions", None)
        result.pop("$createdAt", None)
        result.pop("$updatedAt", None)
        return result
    
    async def create(
        self, 
        data: Dict[str, Any], 
        document_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new document in the collection.
        
        Args:
            data: Document data
            document_id: Optional custom document ID (uses UUID if not provided)
            
        Returns:
            Created document with ID
        """
        try:
            doc_id = document_id or ID.unique()
            data = self._add_timestamps(data.copy())
            
            # Filter out None values - Appwrite doesn't accept null for non-nullable fields
            clean_data = {k: v for k, v in data.items() if v is not None}
            
            result = databases.create_document(
                database_id=self.database_id,
                collection_id=self.collection_id,
                document_id=doc_id,
                data=clean_data
            )
            logger.debug(f"Created document {doc_id} in {self.collection_name}")
            return self._clean_response(result)
        except AppwriteException as e:
            logger.error(f"Error creating document in {self.collection_name}: {e}")
            raise
    
    async def get(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a document by ID.
        
        Args:
            document_id: Document ID
            
        Returns:
            Document data or None if not found
        """
        try:
            result = databases.get_document(
                database_id=self.database_id,
                collection_id=self.collection_id,
                document_id=document_id
            )
            return self._clean_response(result)
        except AppwriteException as e:
            if e.code == 404:
                return None
            logger.error(f"Error getting document {document_id} from {self.collection_name}: {e}")
            raise
    
    async def update(
        self, 
        document_id: str, 
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a document.
        
        Args:
            document_id: Document ID
            data: Fields to update
            
        Returns:
            Updated document
        """
        try:
            data = self._add_timestamps(data.copy(), is_update=True)
            
            # Filter out None values for update
            clean_data = {k: v for k, v in data.items() if v is not None}
            
            result = databases.update_document(
                database_id=self.database_id,
                collection_id=self.collection_id,
                document_id=document_id,
                data=clean_data
            )
            logger.debug(f"Updated document {document_id} in {self.collection_name}")
            return self._clean_response(result)
        except AppwriteException as e:
            logger.error(f"Error updating document {document_id} in {self.collection_name}: {e}")
            raise
    
    async def delete(self, document_id: str) -> bool:
        """
        Delete a document.
        
        Args:
            document_id: Document ID
            
        Returns:
            True if deleted successfully
        """
        try:
            databases.delete_document(
                database_id=self.database_id,
                collection_id=self.collection_id,
                document_id=document_id
            )
            logger.debug(f"Deleted document {document_id} from {self.collection_name}")
            return True
        except AppwriteException as e:
            if e.code == 404:
                return False
            logger.error(f"Error deleting document {document_id} from {self.collection_name}: {e}")
            raise
    
    async def list(
        self, 
        queries: Optional[List[str]] = None, 
        limit: int = 25,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        List documents with optional filtering.
        
        Args:
            queries: List of Appwrite Query strings
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            
        Returns:
            Dict with 'documents' list and 'total' count
        """
        try:
            query_list = queries or []
            query_list.append(Query.limit(limit))
            query_list.append(Query.offset(offset))
            
            result = databases.list_documents(
                database_id=self.database_id,
                collection_id=self.collection_id,
                queries=query_list
            )
            
            return {
                "documents": [self._clean_response(doc) for doc in result["documents"]],
                "total": result["total"]
            }
        except AppwriteException as e:
            logger.error(f"Error listing documents from {self.collection_name}: {e}")
            raise
    
    async def find_one(self, queries: List[str]) -> Optional[Dict[str, Any]]:
        """
        Find a single document matching the queries.
        
        Args:
            queries: List of Appwrite Query strings
            
        Returns:
            First matching document or None
        """
        result = await self.list(queries=queries, limit=1)
        documents = result.get("documents", [])
        return documents[0] if documents else None
    
    async def find_by_field(
        self, 
        field: str, 
        value: Any
    ) -> Optional[Dict[str, Any]]:
        """
        Find a single document by field value.
        
        Args:
            field: Field name to search
            value: Value to match
            
        Returns:
            First matching document or None
        """
        return await self.find_one([Query.equal(field, value)])
    
    async def count(self, queries: Optional[List[str]] = None) -> int:
        """
        Count documents matching the queries.
        
        Args:
            queries: Optional list of Appwrite Query strings
            
        Returns:
            Count of matching documents
        """
        result = await self.list(queries=queries, limit=1)
        return result.get("total", 0)
    
    async def exists(self, document_id: str) -> bool:
        """
        Check if a document exists.
        
        Args:
            document_id: Document ID
            
        Returns:
            True if document exists
        """
        doc = await self.get(document_id)
        return doc is not None
    
    async def upsert(
        self, 
        document_id: str, 
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create or update a document.
        
        Args:
            document_id: Document ID
            data: Document data
            
        Returns:
            Created or updated document
        """
        if await self.exists(document_id):
            return await self.update(document_id, data)
        else:
            return await self.create(data, document_id=document_id)
    
    async def bulk_create(
        self, 
        documents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Create multiple documents.
        
        Args:
            documents: List of document data dicts
            
        Returns:
            List of created documents
        """
        results = []
        for doc in documents:
            try:
                result = await self.create(doc)
                results.append(result)
            except AppwriteException as e:
                logger.warning(f"Error in bulk create: {e}")
                # Continue with other documents
        return results
    
    async def delete_many(self, queries: List[str]) -> int:
        """
        Delete multiple documents matching the queries.
        
        Args:
            queries: List of Appwrite Query strings
            
        Returns:
            Count of deleted documents
        """
        deleted = 0
        result = await self.list(queries=queries, limit=100)
        
        for doc in result.get("documents", []):
            doc_id = doc.get("id")
            if doc_id and await self.delete(doc_id):
                deleted += 1
        
        return deleted
