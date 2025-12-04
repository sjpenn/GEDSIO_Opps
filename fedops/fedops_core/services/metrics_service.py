"""
Metrics Service - Extraction performance tracking and reporting.

Collects metrics on extraction success rates, OCR usage, processing times,
schema validation, and cache performance.
"""

import logging
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import json

logger = logging.getLogger(__name__)


@dataclass
class ExtractionMetric:
    """Single extraction metric"""
    section: str
    success: bool
    duration: float
    ocr_used: bool
    timestamp: float
    error: Optional[str] = None


@dataclass
class ValidationMetric:
    """Schema validation metric"""
    section: str
    success: bool
    timestamp: float
    error: Optional[str] = None


@dataclass
class CacheMetric:
    """Cache operation metric"""
    cache_type: str
    operation: str  # 'hit' or 'miss'
    timestamp: float


class MetricsService:
    """Service for tracking extraction performance metrics"""
    
    def __init__(self, max_metrics: int = 10000):
        self.max_metrics = max_metrics
        
        # Metric storage
        self.extraction_metrics: List[ExtractionMetric] = []
        self.validation_metrics: List[ValidationMetric] = []
        self.cache_metrics: List[CacheMetric] = []
        
        # Counters
        self.extraction_counts = defaultdict(lambda: {"success": 0, "failure": 0})
        self.validation_counts = defaultdict(lambda: {"success": 0, "failure": 0})
        self.cache_counts = defaultdict(lambda: {"hits": 0, "misses": 0})
        self.ocr_usage_count = 0
        
        logger.info("MetricsService initialized")
    
    def record_extraction(
        self,
        section: str,
        success: bool,
        duration: float,
        ocr_used: bool = False,
        error: Optional[str] = None
    ):
        """
        Record extraction attempt.
        
        Args:
            section: Section type (e.g., 'section_b')
            success: Whether extraction succeeded
            duration: Processing time in seconds
            ocr_used: Whether OCR was used
            error: Error message if failed
        """
        metric = ExtractionMetric(
            section=section,
            success=success,
            duration=duration,
            ocr_used=ocr_used,
            timestamp=time.time(),
            error=error
        )
        
        self.extraction_metrics.append(metric)
        
        # Update counters
        if success:
            self.extraction_counts[section]["success"] += 1
        else:
            self.extraction_counts[section]["failure"] += 1
        
        if ocr_used:
            self.ocr_usage_count += 1
        
        # Trim if over max
        if len(self.extraction_metrics) > self.max_metrics:
            self.extraction_metrics = self.extraction_metrics[-self.max_metrics:]
        
        logger.debug(f"Recorded extraction: {section} success={success} duration={duration:.2f}s")
    
    def record_validation(
        self,
        section: str,
        success: bool,
        error: Optional[str] = None
    ):
        """
        Record schema validation attempt.
        
        Args:
            section: Section type
            success: Whether validation succeeded
            error: Validation error message
        """
        metric = ValidationMetric(
            section=section,
            success=success,
            timestamp=time.time(),
            error=error
        )
        
        self.validation_metrics.append(metric)
        
        # Update counters
        if success:
            self.validation_counts[section]["success"] += 1
        else:
            self.validation_counts[section]["failure"] += 1
        
        # Trim if over max
        if len(self.validation_metrics) > self.max_metrics:
            self.validation_metrics = self.validation_metrics[-self.max_metrics:]
    
    def record_cache_hit(self, cache_type: str):
        """Record cache hit"""
        metric = CacheMetric(
            cache_type=cache_type,
            operation="hit",
            timestamp=time.time()
        )
        
        self.cache_metrics.append(metric)
        self.cache_counts[cache_type]["hits"] += 1
        
        # Trim if over max
        if len(self.cache_metrics) > self.max_metrics:
            self.cache_metrics = self.cache_metrics[-self.max_metrics:]
    
    def record_cache_miss(self, cache_type: str):
        """Record cache miss"""
        metric = CacheMetric(
            cache_type=cache_type,
            operation="miss",
            timestamp=time.time()
        )
        
        self.cache_metrics.append(metric)
        self.cache_counts[cache_type]["misses"] += 1
        
        # Trim if over max
        if len(self.cache_metrics) > self.max_metrics:
            self.cache_metrics = self.cache_metrics[-self.max_metrics:]
    
    def get_metrics_summary(self, time_range: str = "24h") -> Dict[str, Any]:
        """
        Get summary of metrics for specified time range.
        
        Args:
            time_range: Time range ('1h', '24h', '7d', 'all')
            
        Returns:
            Dictionary with metric summaries
        """
        # Calculate time threshold
        now = time.time()
        if time_range == "1h":
            threshold = now - 3600
        elif time_range == "24h":
            threshold = now - 86400
        elif time_range == "7d":
            threshold = now - 604800
        else:  # 'all'
            threshold = 0
        
        # Filter metrics by time range
        recent_extractions = [m for m in self.extraction_metrics if m.timestamp >= threshold]
        recent_validations = [m for m in self.validation_metrics if m.timestamp >= threshold]
        recent_cache = [m for m in self.cache_metrics if m.timestamp >= threshold]
        
        # Calculate extraction stats
        total_extractions = len(recent_extractions)
        successful_extractions = sum(1 for m in recent_extractions if m.success)
        failed_extractions = total_extractions - successful_extractions
        
        extraction_success_rate = (
            (successful_extractions / total_extractions * 100)
            if total_extractions > 0 else 0
        )
        
        # Calculate average processing time
        avg_duration = (
            sum(m.duration for m in recent_extractions) / total_extractions
            if total_extractions > 0 else 0
        )
        
        # OCR usage
        ocr_used_count = sum(1 for m in recent_extractions if m.ocr_used)
        ocr_usage_rate = (
            (ocr_used_count / total_extractions * 100)
            if total_extractions > 0 else 0
        )
        
        # Validation stats
        total_validations = len(recent_validations)
        successful_validations = sum(1 for m in recent_validations if m.success)
        validation_success_rate = (
            (successful_validations / total_validations * 100)
            if total_validations > 0 else 0
        )
        
        # Cache stats
        total_cache_ops = len(recent_cache)
        cache_hits = sum(1 for m in recent_cache if m.operation == "hit")
        cache_hit_rate = (
            (cache_hits / total_cache_ops * 100)
            if total_cache_ops > 0 else 0
        )
        
        # Per-section breakdown
        section_stats = {}
        for section in set(m.section for m in recent_extractions):
            section_metrics = [m for m in recent_extractions if m.section == section]
            section_success = sum(1 for m in section_metrics if m.success)
            section_total = len(section_metrics)
            section_avg_duration = sum(m.duration for m in section_metrics) / section_total
            
            section_stats[section] = {
                "total": section_total,
                "success": section_success,
                "failure": section_total - section_success,
                "success_rate": f"{(section_success / section_total * 100):.2f}%",
                "avg_duration": f"{section_avg_duration:.2f}s"
            }
        
        return {
            "time_range": time_range,
            "summary": {
                "total_extractions": total_extractions,
                "successful_extractions": successful_extractions,
                "failed_extractions": failed_extractions,
                "extraction_success_rate": f"{extraction_success_rate:.2f}%",
                "avg_processing_time": f"{avg_duration:.2f}s",
                "ocr_usage_count": ocr_used_count,
                "ocr_usage_rate": f"{ocr_usage_rate:.2f}%",
                "total_validations": total_validations,
                "validation_success_rate": f"{validation_success_rate:.2f}%",
                "cache_operations": total_cache_ops,
                "cache_hit_rate": f"{cache_hit_rate:.2f}%"
            },
            "by_section": section_stats,
            "cache_by_type": dict(self.cache_counts)
        }
    
    def export_metrics(self, format: str = "json") -> str:
        """
        Export metrics in specified format.
        
        Args:
            format: Export format ('json', 'csv')
            
        Returns:
            Formatted metrics string
        """
        if format == "json":
            summary = self.get_metrics_summary("all")
            return json.dumps(summary, indent=2)
        elif format == "csv":
            # Simple CSV export of extraction metrics
            lines = ["section,success,duration,ocr_used,timestamp,error"]
            for m in self.extraction_metrics:
                lines.append(
                    f"{m.section},{m.success},{m.duration},{m.ocr_used},"
                    f"{m.timestamp},{m.error or ''}"
                )
            return "\n".join(lines)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def reset_metrics(self):
        """Reset all metrics"""
        self.extraction_metrics.clear()
        self.validation_metrics.clear()
        self.cache_metrics.clear()
        self.extraction_counts.clear()
        self.validation_counts.clear()
        self.cache_counts.clear()
        self.ocr_usage_count = 0
        logger.info("Metrics reset")
    
    def get_recent_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent extraction errors.
        
        Args:
            limit: Maximum number of errors to return
            
        Returns:
            List of error dictionaries
        """
        failed_extractions = [
            m for m in reversed(self.extraction_metrics)
            if not m.success and m.error
        ][:limit]
        
        return [
            {
                "section": m.section,
                "error": m.error,
                "timestamp": datetime.fromtimestamp(m.timestamp).isoformat(),
                "duration": m.duration
            }
            for m in failed_extractions
        ]
