"""
Test batch processor functionality.
"""

import pytest
import asyncio
from fedops_core.services.batch_processor import BatchProcessor, BatchResult, BatchProgress


class MockDocumentExtractor:
    """Mock extractor for testing"""
    
    def __init__(self, fail_rate=0.0, delay=0.1):
        self.fail_rate = fail_rate
        self.delay = delay
        self.call_count = 0
    
    async def extract_all_documents(self, files):
        """Mock extraction"""
        self.call_count += 1
        await asyncio.sleep(self.delay)
        
        # Simulate failures based on fail_rate
        import random
        if random.random() < self.fail_rate:
            raise Exception("Simulated extraction failure")
        
        return {
            "section_b": {"test": "data"},
            "source_documents": files
        }


class TestBatchProcessor:
    """Test batch processing functionality"""
    
    @pytest.mark.asyncio
    async def test_batch_processor_initialization(self):
        """Test batch processor initialization"""
        extractor = MockDocumentExtractor()
        processor = BatchProcessor(extractor, max_concurrent=3)
        
        assert processor.max_concurrent == 3
        assert processor.max_retries == 3
        assert len(processor.active_batches) == 0
    
    @pytest.mark.asyncio
    async def test_process_batch_success(self):
        """Test successful batch processing"""
        extractor = MockDocumentExtractor(fail_rate=0.0, delay=0.05)
        processor = BatchProcessor(extractor, max_concurrent=2)
        
        files = [
            {"file_path": f"/test/file{i}.pdf", "filename": f"file{i}.pdf"}
            for i in range(5)
        ]
        
        result = await processor.process_batch(files)
        
        assert result.total_files == 5
        assert result.successful == 5
        assert result.failed == 0
        assert result.success_rate == 100.0
        assert len(result.results) == 5
        assert len(result.errors) == 0
    
    @pytest.mark.asyncio
    async def test_process_batch_with_failures(self):
        """Test batch processing with some failures"""
        extractor = MockDocumentExtractor(fail_rate=0.3, delay=0.05)
        processor = BatchProcessor(extractor, max_concurrent=2, max_retries=1)
        
        files = [
            {"file_path": f"/test/file{i}.pdf", "filename": f"file{i}.pdf"}
            for i in range(10)
        ]
        
        result = await processor.process_batch(files)
        
        assert result.total_files == 10
        assert result.successful + result.failed == 10
        assert len(result.results) == result.successful
        assert len(result.errors) == result.failed
    
    @pytest.mark.asyncio
    async def test_progress_tracking(self):
        """Test progress tracking"""
        progress = BatchProgress("test-batch", total_files=10)
        
        assert progress.progress_percent == 0.0
        assert progress.processed == 0
        
        progress.processed = 5
        progress.successful = 4
        progress.failed = 1
        
        assert progress.progress_percent == 50.0
        assert progress.elapsed_time > 0
    
    @pytest.mark.asyncio
    async def test_batch_result(self):
        """Test batch result properties"""
        result = BatchResult(
            batch_id="test-123",
            total_files=10,
            successful=8,
            failed=2,
            results=[],
            errors=[],
            duration=5.0,
            started_at=100.0,
            completed_at=105.0
        )
        
        assert result.success_rate == 80.0
        assert result.total_files == 10
    
    @pytest.mark.asyncio
    async def test_concurrent_processing(self):
        """Test that concurrent processing is faster than sequential"""
        import time
        
        extractor = MockDocumentExtractor(delay=0.1)
        
        files = [
            {"file_path": f"/test/file{i}.pdf", "filename": f"file{i}.pdf"}
            for i in range(5)
        ]
        
        # Sequential (max_concurrent=1)
        processor_seq = BatchProcessor(extractor, max_concurrent=1, rate_limit_delay=0)
        start = time.time()
        await processor_seq.process_batch(files)
        sequential_time = time.time() - start
        
        # Parallel (max_concurrent=5)
        processor_par = BatchProcessor(extractor, max_concurrent=5, rate_limit_delay=0)
        start = time.time()
        await processor_par.process_batch(files)
        parallel_time = time.time() - start
        
        # Parallel should be significantly faster
        assert parallel_time < sequential_time * 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
