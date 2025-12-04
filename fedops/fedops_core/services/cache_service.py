"""
Cache Service - Document extraction caching system.

Provides file hash-based caching for parsed documents, scanned PDF detection,
and extraction results with TTL-based expiration and LRU eviction.
"""

import hashlib
import logging
import time
from typing import Optional, Dict, Any
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import OrderedDict

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    value: Any
    created_at: float
    ttl: int  # Time to live in seconds
    hits: int = 0
    
    def is_expired(self) -> bool:
        """Check if entry has expired"""
        if self.ttl == 0:  # 0 means no expiration
            return False
        return time.time() - self.created_at > self.ttl
    
    def record_hit(self):
        """Record cache hit"""
        self.hits += 1


class LRUCache:
    """LRU cache with TTL support"""
    
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key not in self.cache:
            self.misses += 1
            return None
        
        entry = self.cache[key]
        
        # Check expiration
        if entry.is_expired():
            del self.cache[key]
            self.misses += 1
            return None
        
        # Move to end (most recently used)
        self.cache.move_to_end(key)
        entry.record_hit()
        self.hits += 1
        
        return entry.value
    
    def set(self, key: str, value: Any, ttl: int = 86400):
        """Set value in cache with TTL"""
        # Remove if exists
        if key in self.cache:
            del self.cache[key]
        
        # Add new entry
        entry = CacheEntry(
            value=value,
            created_at=time.time(),
            ttl=ttl
        )
        self.cache[key] = entry
        
        # Evict oldest if over max size
        if len(self.cache) > self.max_size:
            self.cache.popitem(last=False)
    
    def clear(self):
        """Clear all cache entries"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.2f}%",
            "total_requests": total_requests
        }


class CacheService:
    """Service for caching document extraction results"""
    
    def __init__(
        self,
        max_parsed_docs: int = 50,
        max_scanned_status: int = 200,
        max_extractions: int = 100,
        default_ttl: int = 86400  # 24 hours
    ):
        self.default_ttl = default_ttl
        
        # Separate caches for different data types
        self.parsed_docs_cache = LRUCache(max_size=max_parsed_docs)
        self.scanned_status_cache = LRUCache(max_size=max_scanned_status)
        self.extraction_cache = LRUCache(max_size=max_extractions)
        self.table_cache = LRUCache(max_size=max_extractions)
        
        logger.info(f"CacheService initialized with TTL={default_ttl}s")
    
    def _get_file_hash(self, file_path: str) -> str:
        """
        Generate MD5 hash of file content for cache key.
        
        Args:
            file_path: Path to file
            
        Returns:
            MD5 hash string
        """
        try:
            md5 = hashlib.md5()
            with open(file_path, 'rb') as f:
                # Read in chunks for large files
                for chunk in iter(lambda: f.read(8192), b''):
                    md5.update(chunk)
            return md5.hexdigest()
        except Exception as e:
            logger.error(f"Error hashing file {file_path}: {e}")
            # Fallback to file path + mtime
            stat = Path(file_path).stat()
            return hashlib.md5(f"{file_path}:{stat.st_mtime}".encode()).hexdigest()
    
    # Parsed Document Cache
    
    async def get_parsed_document(self, file_path: str) -> Optional[str]:
        """
        Get parsed document content from cache.
        
        Args:
            file_path: Path to document
            
        Returns:
            Cached markdown content or None
        """
        cache_key = self._get_file_hash(file_path)
        content = self.parsed_docs_cache.get(cache_key)
        
        if content:
            logger.debug(f"Cache HIT for parsed document: {Path(file_path).name}")
        else:
            logger.debug(f"Cache MISS for parsed document: {Path(file_path).name}")
        
        return content
    
    async def set_parsed_document(
        self,
        file_path: str,
        content: str,
        ttl: Optional[int] = None
    ):
        """
        Cache parsed document content.
        
        Args:
            file_path: Path to document
            content: Parsed markdown content
            ttl: Time to live in seconds (default: service default)
        """
        cache_key = self._get_file_hash(file_path)
        self.parsed_docs_cache.set(cache_key, content, ttl or self.default_ttl)
        logger.debug(f"Cached parsed document: {Path(file_path).name}")
    
    # Scanned Status Cache
    
    async def get_scanned_status(self, file_path: str) -> Optional[bool]:
        """
        Get scanned PDF status from cache.
        
        Args:
            file_path: Path to PDF
            
        Returns:
            Cached scanned status or None
        """
        cache_key = self._get_file_hash(file_path)
        return self.scanned_status_cache.get(cache_key)
    
    async def set_scanned_status(
        self,
        file_path: str,
        is_scanned: bool,
        ttl: Optional[int] = None
    ):
        """
        Cache scanned PDF status.
        
        Args:
            file_path: Path to PDF
            is_scanned: Whether PDF is scanned
            ttl: Time to live in seconds
        """
        cache_key = self._get_file_hash(file_path)
        # Scanned status rarely changes, use longer TTL
        self.scanned_status_cache.set(
            cache_key,
            is_scanned,
            ttl or (self.default_ttl * 7)  # 7 days default
        )
        logger.debug(f"Cached scanned status for: {Path(file_path).name}")
    
    # Extraction Results Cache
    
    async def get_extraction_result(
        self,
        file_path: str,
        section: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get extraction result from cache.
        
        Args:
            file_path: Path to document
            section: Section type (e.g., 'section_b')
            
        Returns:
            Cached extraction result or None
        """
        file_hash = self._get_file_hash(file_path)
        cache_key = f"{file_hash}:{section}"
        return self.extraction_cache.get(cache_key)
    
    async def set_extraction_result(
        self,
        file_path: str,
        section: str,
        result: Dict[str, Any],
        ttl: Optional[int] = None
    ):
        """
        Cache extraction result.
        
        Args:
            file_path: Path to document
            section: Section type
            result: Extraction result dictionary
            ttl: Time to live in seconds
        """
        file_hash = self._get_file_hash(file_path)
        cache_key = f"{file_hash}:{section}"
        self.extraction_cache.set(cache_key, result, ttl or self.default_ttl)
        logger.debug(f"Cached extraction for {section}: {Path(file_path).name}")
    
    # Table Cache
    
    async def get_tables(self, file_path: str) -> Optional[list]:
        """Get cached table extraction results"""
        cache_key = self._get_file_hash(file_path)
        return self.table_cache.get(cache_key)
    
    async def set_tables(
        self,
        file_path: str,
        tables: list,
        ttl: Optional[int] = None
    ):
        """Cache table extraction results"""
        cache_key = self._get_file_hash(file_path)
        self.table_cache.set(cache_key, tables, ttl or self.default_ttl)
        logger.debug(f"Cached {len(tables)} tables for: {Path(file_path).name}")
    
    # Cache Management
    
    def clear_cache(self, cache_type: Optional[str] = None):
        """
        Clear cache(s).
        
        Args:
            cache_type: Type of cache to clear ('parsed', 'scanned', 'extraction', 'tables')
                       If None, clears all caches
        """
        if cache_type is None:
            self.parsed_docs_cache.clear()
            self.scanned_status_cache.clear()
            self.extraction_cache.clear()
            self.table_cache.clear()
            logger.info("Cleared all caches")
        elif cache_type == "parsed":
            self.parsed_docs_cache.clear()
        elif cache_type == "scanned":
            self.scanned_status_cache.clear()
        elif cache_type == "extraction":
            self.extraction_cache.clear()
        elif cache_type == "tables":
            self.table_cache.clear()
        else:
            logger.warning(f"Unknown cache type: {cache_type}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get statistics for all caches.
        
        Returns:
            Dictionary with cache statistics
        """
        return {
            "parsed_documents": self.parsed_docs_cache.get_stats(),
            "scanned_status": self.scanned_status_cache.get_stats(),
            "extractions": self.extraction_cache.get_stats(),
            "tables": self.table_cache.get_stats(),
            "total_memory_items": (
                len(self.parsed_docs_cache.cache) +
                len(self.scanned_status_cache.cache) +
                len(self.extraction_cache.cache) +
                len(self.table_cache.cache)
            )
        }
