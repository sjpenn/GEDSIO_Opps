"""
Extraction Progress Tracker

Enhanced in-memory progress tracker for analysis operations.
Tracks stages, operations, documents, and DB/Vector store activity.
"""

from typing import Dict, Optional, List
from datetime import datetime
from threading import Lock


class ExtractionProgress:
    """Tracks progress of extraction and analysis operations with granular detail"""
    
    def __init__(self):
        self._progress: Dict[int, Dict] = {}
        self._lock = Lock()
    
    def start(self, proposal_id: int, total_files: int = 0, message: str = "Starting analysis..."):
        """Initialize progress tracking for a proposal/opportunity"""
        with self._lock:
            self._progress[proposal_id] = {
                "status": "running",
                "total_files": total_files,
                "processed_files": 0,
                "current_file": None,
                "message": message,
                "percent": 0,
                "filenames": [],
                "started_at": datetime.utcnow().isoformat(),
                "completed_at": None,
                "error": None,
                # Enhanced tracking fields
                "stage": "initialization",  # initialization, ingestion, extraction, analysis, finalization
                "current_operation": None,  # extracting, chunking, embedding, analyzing, summarizing, storing
                "operation_target": None,   # e.g., "RFP.pdf", "Section L", "compliance_agent"
                "documents": [],            # List of {"name": str, "status": str}
                "db_operations": {"writes": 0, "reads": 0},
                "vector_operations": {"writes": 0, "reads": 0},
            }
    
    def update(self, proposal_id: int, filename: str = None, message: str = None, percent: int = None):
        """Update progress with current file being processed or general status message"""
        with self._lock:
            if proposal_id in self._progress:
                progress = self._progress[proposal_id]
                if filename:
                    progress["current_file"] = filename
                    progress["processed_files"] += 1
                    progress["filenames"].append(filename)
                
                if message:
                    progress["message"] = message
                    
                if percent is not None:
                    progress["percent"] = percent
                elif filename and progress["total_files"] > 0:
                    # Auto-calculate per file if not explicit
                    progress["percent"] = int((progress["processed_files"] / progress["total_files"]) * 100)
    
    def set_stage(self, proposal_id: int, stage: str, message: str = None, percent: int = None):
        """
        Set the current analysis stage.
        
        Stages: initialization, ingestion, extraction, analysis, finalization
        """
        with self._lock:
            if proposal_id in self._progress:
                progress = self._progress[proposal_id]
                progress["stage"] = stage
                if message:
                    progress["message"] = message
                if percent is not None:
                    progress["percent"] = percent
    
    def set_operation(
        self, 
        proposal_id: int, 
        operation: str, 
        target: str = None, 
        message: str = None,
        percent: int = None
    ):
        """
        Set current operation with optional target.
        
        Operations: extracting, chunking, embedding, analyzing, summarizing, storing
        Target: Document name, section, or agent name
        """
        with self._lock:
            if proposal_id in self._progress:
                progress = self._progress[proposal_id]
                progress["current_operation"] = operation
                progress["operation_target"] = target
                
                # Auto-generate message if not provided
                if message:
                    progress["message"] = message
                elif target:
                    op_emoji = {
                        "extracting": "📄",
                        "chunking": "✂️",
                        "embedding": "🔢",
                        "analyzing": "🔍",
                        "summarizing": "📊",
                        "storing": "💾"
                    }
                    emoji = op_emoji.get(operation, "⏳")
                    progress["message"] = f"{emoji} {operation.capitalize()}: {target}"
                
                if percent is not None:
                    progress["percent"] = percent
    
    def track_document(self, proposal_id: int, doc_name: str, status: str):
        """
        Track status of individual documents.
        
        Status: pending, extracting, chunking, complete, error
        """
        with self._lock:
            if proposal_id in self._progress:
                progress = self._progress[proposal_id]
                # Find and update existing doc or add new
                for doc in progress["documents"]:
                    if doc["name"] == doc_name:
                        doc["status"] = status
                        return
                progress["documents"].append({"name": doc_name, "status": status})
    
    def track_db_operation(self, proposal_id: int, op_type: str = "write"):
        """Track database operation (read/write)"""
        with self._lock:
            if proposal_id in self._progress:
                if op_type == "write":
                    self._progress[proposal_id]["db_operations"]["writes"] += 1
                else:
                    self._progress[proposal_id]["db_operations"]["reads"] += 1
    
    def track_vector_operation(self, proposal_id: int, op_type: str = "write"):
        """Track vector store operation (read/write)"""
        with self._lock:
            if proposal_id in self._progress:
                if op_type == "write":
                    self._progress[proposal_id]["vector_operations"]["writes"] += 1
                else:
                    self._progress[proposal_id]["vector_operations"]["reads"] += 1
    
    def complete(self, proposal_id: int, requirements_count: int = 0, artifacts_count: int = 0):
        """Mark extraction as complete"""
        with self._lock:
            if proposal_id in self._progress:
                progress = self._progress[proposal_id]
                progress["status"] = "completed"
                progress["stage"] = "complete"
                progress["current_operation"] = None
                progress["percent"] = 100
                progress["message"] = "✅ Analysis complete!"
                progress["current_file"] = None
                progress["completed_at"] = datetime.utcnow().isoformat()
                progress["requirements_count"] = requirements_count
                progress["artifacts_count"] = artifacts_count
    
    def fail(self, proposal_id: int, error: str):
        """Mark extraction as failed"""
        with self._lock:
            if proposal_id in self._progress:
                progress = self._progress[proposal_id]
                progress["status"] = "failed"
                progress["stage"] = "error"
                progress["error"] = error
                progress["message"] = f"❌ Error: {error[:100]}"
                progress["completed_at"] = datetime.utcnow().isoformat()
    
    def get(self, proposal_id: int) -> Optional[Dict]:
        """Get current progress for a proposal"""
        with self._lock:
            return self._progress.get(proposal_id)
    
    def clear(self, proposal_id: int):
        """Clear progress data for a proposal"""
        with self._lock:
            if proposal_id in self._progress:
                del self._progress[proposal_id]


# Global singleton instance
extraction_progress = ExtractionProgress()

