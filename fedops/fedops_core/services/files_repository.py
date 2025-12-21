"""
Files Repository

Repository for StoredFile collection operations in Appwrite.
Integrates with Appwrite Storage for file uploads.
"""

from typing import Optional, List, Dict, Any, BinaryIO
from appwrite.query import Query
from appwrite.id import ID
from appwrite.input_file import InputFile
from appwrite.exception import AppwriteException
from fedops_core.services.appwrite_repository import AppwriteRepository
from fedops_core.db.appwrite_client import storage, STORAGE_BUCKET_ID
import logging
import os

logger = logging.getLogger(__name__)


class FilesRepository(AppwriteRepository):
    """Repository for stored file documents and Appwrite Storage operations."""
    
    def __init__(self):
        super().__init__("stored_files")
        self.bucket_id = STORAGE_BUCKET_ID or "fedops-files"
    
    async def get_by_opportunity(
        self, 
        opportunity_id: str, 
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get all files for an opportunity."""
        return await self.list(
            queries=[Query.equal("opportunity_id", opportunity_id)],
            limit=limit
        )
    
    async def get_by_filename(self, filename: str) -> Optional[Dict[str, Any]]:
        """Find file by filename."""
        return await self.find_by_field("filename", filename)
    
    async def upload_file(
        self,
        file_path: str,
        opportunity_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Upload a file to Appwrite Storage and create a document record.
        
        Args:
            file_path: Local path to the file
            opportunity_id: Optional opportunity ID to associate with
            metadata: Additional metadata for the document
            
        Returns:
            Created stored_files document
        """
        filename = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        file_type = os.path.splitext(filename)[1].lower().strip('.')
        
        try:
            # Upload to Appwrite Storage
            with open(file_path, 'rb') as f:
                storage_file = storage.create_file(
                    bucket_id=self.bucket_id,
                    file_id=ID.unique(),
                    file=InputFile.from_bytes(f.read(), filename)
                )
            
            storage_file_id = storage_file.get("$id")
            logger.info(f"Uploaded file to storage: {storage_file_id}")
            
            # Create document record
            doc_data = {
                "filename": filename,
                "file_path": file_path,
                "storage_file_id": storage_file_id,
                "file_type": file_type,
                "file_size": file_size,
                "opportunity_id": opportunity_id,
                **(metadata or {})
            }
            
            return await self.create(doc_data)
            
        except AppwriteException as e:
            logger.error(f"Error uploading file {filename}: {e}")
            raise
    
    async def upload_from_bytes(
        self,
        content: bytes,
        filename: str,
        opportunity_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Upload file from bytes to Appwrite Storage.
        
        Args:
            content: File content as bytes
            filename: Name for the file
            opportunity_id: Optional opportunity ID
            metadata: Additional metadata
            
        Returns:
            Created stored_files document
        """
        file_type = os.path.splitext(filename)[1].lower().strip('.')
        file_size = len(content)
        
        try:
            storage_file = storage.create_file(
                bucket_id=self.bucket_id,
                file_id=ID.unique(),
                file=InputFile.from_bytes(content, filename)
            )
            
            storage_file_id = storage_file.get("$id")
            
            doc_data = {
                "filename": filename,
                "file_path": "",  # No local path for uploaded bytes
                "storage_file_id": storage_file_id,
                "file_type": file_type,
                "file_size": file_size,
                "opportunity_id": opportunity_id,
                **(metadata or {})
            }
            
            return await self.create(doc_data)
            
        except AppwriteException as e:
            logger.error(f"Error uploading file {filename}: {e}")
            raise
    
    async def download_file(self, document_id: str) -> Optional[bytes]:
        """
        Download file content from Appwrite Storage.
        
        Args:
            document_id: The stored_files document ID
            
        Returns:
            File content as bytes or None
        """
        doc = await self.get(document_id)
        if not doc or not doc.get("storage_file_id"):
            return None
        
        try:
            result = storage.get_file_download(
                bucket_id=self.bucket_id,
                file_id=doc["storage_file_id"]
            )
            return result
        except AppwriteException as e:
            logger.error(f"Error downloading file: {e}")
            return None
    
    async def get_file_url(self, document_id: str) -> Optional[str]:
        """
        Get a view URL for a file.
        
        Args:
            document_id: The stored_files document ID
            
        Returns:
            File view URL or None
        """
        doc = await self.get(document_id)
        if not doc or not doc.get("storage_file_id"):
            return None
        
        try:
            result = storage.get_file_view(
                bucket_id=self.bucket_id,
                file_id=doc["storage_file_id"]
            )
            return result
        except AppwriteException as e:
            logger.error(f"Error getting file URL: {e}")
            return None
    
    async def delete_with_storage(self, document_id: str) -> bool:
        """
        Delete a file document and its storage file.
        
        Args:
            document_id: The stored_files document ID
            
        Returns:
            True if deleted successfully
        """
        doc = await self.get(document_id)
        if not doc:
            return False
        
        # Delete from storage if exists
        if doc.get("storage_file_id"):
            try:
                storage.delete_file(
                    bucket_id=self.bucket_id,
                    file_id=doc["storage_file_id"]
                )
            except AppwriteException as e:
                logger.warning(f"Could not delete storage file: {e}")
        
        # Delete document
        return await self.delete(document_id)
