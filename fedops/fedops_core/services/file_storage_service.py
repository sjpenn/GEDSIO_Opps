"""
File Storage Service
Handles local file storage for proposal exports and documents.
"""
import os
from pathlib import Path
from typing import Optional
from datetime import datetime
import shutil


class FileStorageService:
    """Service for managing local file storage"""
    
    def __init__(self, storage_dir: str = "./storage"):
        self.storage_dir = Path(storage_dir)
        self.proposals_dir = self.storage_dir / "proposals"
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure storage directories exist"""
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.proposals_dir.mkdir(parents=True, exist_ok=True)
    
    def save_proposal_export(
        self,
        proposal_id: int,
        content: str,
        filename: Optional[str] = None,
        extension: str = "md"
    ) -> str:
        """
        Save a proposal export to local storage
        
        Args:
            proposal_id: ID of the proposal
            content: Content to save
            filename: Optional custom filename
            extension: File extension (default: md)
        
        Returns:
            Relative path to the saved file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"proposal_{proposal_id}_{timestamp}.{extension}"
        
        filepath = self.proposals_dir / filename
        
        # Write content to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Return relative path
        return str(filepath.relative_to(self.storage_dir))
    
    def get_proposal_export_path(self, relative_path: str) -> Path:
        """Get absolute path for a proposal export"""
        return self.storage_dir / relative_path
    
    def delete_proposal_export(self, relative_path: str) -> bool:
        """Delete a proposal export file"""
        filepath = self.storage_dir / relative_path
        if filepath.exists():
            filepath.unlink()
            return True
        return False
    
    def list_proposal_exports(self, proposal_id: Optional[int] = None) -> list:
        """List all proposal exports, optionally filtered by proposal_id"""
        files = []
        for filepath in self.proposals_dir.glob("*.md"):
            if proposal_id is None or f"proposal_{proposal_id}_" in filepath.name:
                files.append({
                    "filename": filepath.name,
                    "path": str(filepath.relative_to(self.storage_dir)),
                    "size": filepath.stat().st_size,
                    "modified": datetime.fromtimestamp(filepath.stat().st_mtime).isoformat()
                })
        return files
    
    def save_uploaded_file(
        self,
        file_content: bytes,
        filename: str,
        subdirectory: str = "uploads"
    ) -> str:
        """
        Save an uploaded file to storage
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            subdirectory: Subdirectory within storage (default: uploads)
        
        Returns:
            Relative path to the saved file
        """
        upload_dir = self.storage_dir / subdirectory
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename if needed
        filepath = upload_dir / filename
        counter = 1
        while filepath.exists():
            name, ext = os.path.splitext(filename)
            filepath = upload_dir / f"{name}_{counter}{ext}"
            counter += 1
        
        # Write file
        with open(filepath, 'wb') as f:
            f.write(file_content)
        
        return str(filepath.relative_to(self.storage_dir))
