"""
Extraction Progress Tracker

Simple in-memory progress tracker for requirement extraction operations.
Stores progress by proposal_id to enable real-time status updates.
"""

from typing import Dict, Optional
from datetime import datetime
from threading import Lock


class ExtractionProgress:
    """Tracks progress of requirement extraction operations"""
    
    def __init__(self):
        self._progress: Dict[int, Dict] = {}
        self._lock = Lock()
    
    def start(self, proposal_id: int, total_files: int):
        """Initialize progress tracking for a proposal"""
        with self._lock:
            self._progress[proposal_id] = {
                "status": "running",
                "total_files": total_files,
                "processed_files": 0,
                "current_file": None,
                "filenames": [],
                "started_at": datetime.utcnow().isoformat(),
                "completed_at": None,
                "error": None
            }
    
    def update(self, proposal_id: int, filename: str):
        """Update progress with current file being processed"""
        with self._lock:
            if proposal_id in self._progress:
                progress = self._progress[proposal_id]
                progress["current_file"] = filename
                progress["processed_files"] += 1
                progress["filenames"].append(filename)
    
    def complete(self, proposal_id: int, requirements_count: int, artifacts_count: int):
        """Mark extraction as complete"""
        with self._lock:
            if proposal_id in self._progress:
                progress = self._progress[proposal_id]
                progress["status"] = "completed"
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
                progress["error"] = error
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
