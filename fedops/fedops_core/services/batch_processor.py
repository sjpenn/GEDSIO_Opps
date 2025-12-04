"""
Batch Processor - Parallel document extraction with progress tracking.

Provides batch processing capabilities for multiple documents with:
- Parallel processing with configurable concurrency
- Progress tracking and reporting
- Retry logic for failed extractions
- Rate limiting for API calls
- Result aggregation
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


@dataclass
class BatchResult:
    """Result from batch processing"""
    batch_id: str
    total_files: int
    successful: int
    failed: int
    results: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]
    duration: float
    started_at: float
    completed_at: float
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        return (self.successful / self.total_files * 100) if self.total_files > 0 else 0


@dataclass
class BatchProgress:
    """Progress tracking for batch processing"""
    batch_id: str
    total_files: int
    processed: int = 0
    successful: int = 0
    failed: int = 0
    current_file: Optional[str] = None
    started_at: float = field(default_factory=time.time)
    
    @property
    def progress_percent(self) -> float:
        """Calculate progress percentage"""
        return (self.processed / self.total_files * 100) if self.total_files > 0 else 0
    
    @property
    def elapsed_time(self) -> float:
        """Calculate elapsed time in seconds"""
        return time.time() - self.started_at
    
    @property
    def estimated_remaining(self) -> float:
        """Estimate remaining time in seconds"""
        if self.processed == 0:
            return 0
        avg_time_per_file = self.elapsed_time / self.processed
        remaining_files = self.total_files - self.processed
        return avg_time_per_file * remaining_files


class BatchProcessor:
    """Service for batch processing multiple documents"""
    
    def __init__(
        self,
        document_extractor,
        max_concurrent: int = 5,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        rate_limit_delay: float = 0.5
    ):
        """
        Initialize batch processor.
        
        Args:
            document_extractor: DocumentExtractor instance
            max_concurrent: Maximum concurrent extractions
            max_retries: Maximum retry attempts for failed extractions
            retry_delay: Delay between retries in seconds
            rate_limit_delay: Delay between API calls in seconds
        """
        self.extractor = document_extractor
        self.max_concurrent = max_concurrent
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.rate_limit_delay = rate_limit_delay
        
        # Track active batches
        self.active_batches: Dict[str, BatchProgress] = {}
        
        logger.info(f"BatchProcessor initialized (max_concurrent={max_concurrent})")
    
    async def process_batch(
        self,
        files: List[Dict[str, str]],
        max_concurrent: Optional[int] = None
    ) -> BatchResult:
        """
        Process multiple documents in parallel.
        
        Args:
            files: List of file dictionaries with 'file_path' and 'filename'
            max_concurrent: Override default max concurrent extractions
            
        Returns:
            BatchResult with aggregated results
        """
        batch_id = str(uuid.uuid4())
        started_at = time.time()
        
        # Initialize progress tracking
        progress = BatchProgress(
            batch_id=batch_id,
            total_files=len(files)
        )
        self.active_batches[batch_id] = progress
        
        logger.info(f"Starting batch {batch_id} with {len(files)} files")
        
        # Use provided concurrency or default
        concurrency = max_concurrent or self.max_concurrent
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(concurrency)
        
        # Process files
        tasks = [
            self._process_file_with_retry(file_info, semaphore, progress)
            for file_info in files
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Aggregate results
        successful_results = []
        errors = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                errors.append({
                    "file": files[i].get("filename", "unknown"),
                    "error": str(result)
                })
            elif result.get("error"):
                errors.append({
                    "file": files[i].get("filename", "unknown"),
                    "error": result["error"]
                })
            else:
                successful_results.append(result)
        
        completed_at = time.time()
        duration = completed_at - started_at
        
        # Create batch result
        batch_result = BatchResult(
            batch_id=batch_id,
            total_files=len(files),
            successful=len(successful_results),
            failed=len(errors),
            results=successful_results,
            errors=errors,
            duration=duration,
            started_at=started_at,
            completed_at=completed_at
        )
        
        # Clean up progress tracking
        del self.active_batches[batch_id]
        
        logger.info(
            f"Batch {batch_id} complete: {batch_result.successful}/{batch_result.total_files} "
            f"successful ({batch_result.success_rate:.1f}%) in {duration:.2f}s"
        )
        
        return batch_result
    
    async def _process_file_with_retry(
        self,
        file_info: Dict[str, str],
        semaphore: asyncio.Semaphore,
        progress: BatchProgress
    ) -> Dict[str, Any]:
        """
        Process a single file with retry logic.
        
        Args:
            file_info: File information dictionary
            semaphore: Semaphore for concurrency control
            progress: Progress tracking object
            
        Returns:
            Extraction result or error dictionary
        """
        file_path = file_info.get("file_path")
        filename = file_info.get("filename", file_path)
        
        async with semaphore:
            # Update progress
            progress.current_file = filename
            
            # Retry loop
            last_error = None
            for attempt in range(self.max_retries):
                try:
                    # Rate limiting
                    if self.rate_limit_delay > 0:
                        await asyncio.sleep(self.rate_limit_delay)
                    
                    # Extract document
                    result = await self.extractor.extract_all_documents([file_info])
                    
                    # Update progress
                    progress.processed += 1
                    progress.successful += 1
                    
                    logger.debug(f"Successfully processed: {filename}")
                    
                    return {
                        "file": filename,
                        "result": result,
                        "attempts": attempt + 1
                    }
                    
                except Exception as e:
                    last_error = e
                    logger.warning(
                        f"Attempt {attempt + 1}/{self.max_retries} failed for {filename}: {e}"
                    )
                    
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay * (attempt + 1))
            
            # All retries failed
            progress.processed += 1
            progress.failed += 1
            
            logger.error(f"Failed to process {filename} after {self.max_retries} attempts")
            
            return {
                "file": filename,
                "error": str(last_error),
                "attempts": self.max_retries
            }
    
    async def process_with_progress(
        self,
        files: List[Dict[str, str]],
        callback: Callable[[BatchProgress], None],
        callback_interval: float = 1.0
    ) -> BatchResult:
        """
        Process batch with progress callbacks.
        
        Args:
            files: List of file dictionaries
            callback: Function to call with progress updates
            callback_interval: Seconds between progress callbacks
            
        Returns:
            BatchResult
        """
        batch_id = str(uuid.uuid4())
        
        # Initialize progress
        progress = BatchProgress(
            batch_id=batch_id,
            total_files=len(files)
        )
        self.active_batches[batch_id] = progress
        
        # Start progress callback task
        async def progress_updater():
            while batch_id in self.active_batches:
                callback(progress)
                await asyncio.sleep(callback_interval)
        
        progress_task = asyncio.create_task(progress_updater())
        
        try:
            # Process batch
            result = await self.process_batch(files)
            return result
        finally:
            # Stop progress updates
            progress_task.cancel()
            try:
                await progress_task
            except asyncio.CancelledError:
                pass
    
    def get_batch_status(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of active batch.
        
        Args:
            batch_id: Batch identifier
            
        Returns:
            Status dictionary or None if batch not found
        """
        progress = self.active_batches.get(batch_id)
        if not progress:
            return None
        
        return {
            "batch_id": batch_id,
            "total_files": progress.total_files,
            "processed": progress.processed,
            "successful": progress.successful,
            "failed": progress.failed,
            "current_file": progress.current_file,
            "progress_percent": f"{progress.progress_percent:.1f}%",
            "elapsed_time": f"{progress.elapsed_time:.1f}s",
            "estimated_remaining": f"{progress.estimated_remaining:.1f}s"
        }
    
    def get_all_batch_statuses(self) -> List[Dict[str, Any]]:
        """Get status of all active batches"""
        return [
            self.get_batch_status(batch_id)
            for batch_id in self.active_batches.keys()
        ]
