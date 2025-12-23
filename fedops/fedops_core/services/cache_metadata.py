"""
Cache Metadata Repository

Tracks SAM.gov API fetch timestamps and parameters to enable intelligent caching.
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from appwrite.query import Query
from fedops_core.services.appwrite_repository import AppwriteRepository
import hashlib
import json
import logging

logger = logging.getLogger(__name__)

# Default cache TTL: 2 hours
DEFAULT_CACHE_TTL_SECONDS = 2 * 60 * 60


class CacheMetadataRepository(AppwriteRepository):
    """Repository for cache metadata tracking."""
    
    def __init__(self):
        super().__init__("cache_metadata")
    
    def _generate_cache_key(self, fetch_params: Dict[str, Any]) -> str:
        """
        Generate a consistent cache key from fetch parameters.
        
        Args:
            fetch_params: Dictionary of search parameters
            
        Returns:
            SHA256 hash of normalized parameters
        """
        # Normalize params by sorting keys and converting to JSON
        normalized = json.dumps(fetch_params, sort_keys=True)
        return hashlib.sha256(normalized.encode()).hexdigest()
    
    async def get_cache_entry(
        self, 
        fetch_params: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Get cache entry for given fetch parameters.
        
        Args:
            fetch_params: Dictionary of search parameters
            
        Returns:
            Cache entry if exists, None otherwise
        """
        cache_key = self._generate_cache_key(fetch_params)
        return await self.find_by_field("cache_key", cache_key)
    
    async def is_cache_valid(
        self, 
        fetch_params: Dict[str, Any],
        ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS
    ) -> bool:
        """
        Check if cache is valid for given parameters.
        
        Args:
            fetch_params: Dictionary of search parameters
            ttl_seconds: Time-to-live in seconds (default: 2 hours)
            
        Returns:
            True if cache exists and is not expired
        """
        entry = await self.get_cache_entry(fetch_params)
        
        if not entry:
            return False
        
        last_fetch_str = entry.get("last_fetch_time")
        if not last_fetch_str:
            return False
        
        try:
            last_fetch = datetime.fromisoformat(last_fetch_str)
            expires_at = last_fetch + timedelta(seconds=ttl_seconds)
            return datetime.utcnow() < expires_at
        except (ValueError, TypeError):
            logger.warning(f"Invalid timestamp in cache entry: {last_fetch_str}")
            return False
    
    async def update_cache_entry(
        self,
        fetch_params: Dict[str, Any],
        record_count: int,
        source: str = "SAM.gov"
    ) -> Dict[str, Any]:
        """
        Update or create cache entry after a successful fetch.
        
        Args:
            fetch_params: Dictionary of search parameters used
            record_count: Number of records fetched
            source: Data source (default: SAM.gov)
            
        Returns:
            Updated or created cache entry
        """
        cache_key = self._generate_cache_key(fetch_params)
        
        cache_data = {
            "cache_key": cache_key,
            "last_fetch_time": datetime.utcnow().isoformat(),
            "fetch_params": fetch_params,
            "record_count": record_count,
            "source": source
        }
        
        # Check if entry already exists
        existing = await self.find_by_field("cache_key", cache_key)
        
        if existing:
            return await self.update(existing["id"], cache_data)
        else:
            return await self.create(cache_data)
    
    async def get_time_until_expiry(
        self,
        fetch_params: Dict[str, Any],
        ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS
    ) -> Optional[int]:
        """
        Get seconds until cache expires.
        
        Args:
            fetch_params: Dictionary of search parameters
            ttl_seconds: Time-to-live in seconds
            
        Returns:
            Seconds until expiry, or None if cache doesn't exist
        """
        entry = await self.get_cache_entry(fetch_params)
        
        if not entry:
            return None
        
        last_fetch_str = entry.get("last_fetch_time")
        if not last_fetch_str:
            return None
        
        try:
            last_fetch = datetime.fromisoformat(last_fetch_str)
            expires_at = last_fetch + timedelta(seconds=ttl_seconds)
            remaining = (expires_at - datetime.utcnow()).total_seconds()
            return max(0, int(remaining))
        except (ValueError, TypeError):
            return None
    
    async def invalidate_cache(self, fetch_params: Dict[str, Any]) -> bool:
        """
        Invalidate cache for given parameters.
        
        Args:
            fetch_params: Dictionary of search parameters
            
        Returns:
            True if cache was invalidated
        """
        cache_key = self._generate_cache_key(fetch_params)
        entry = await self.find_by_field("cache_key", cache_key)
        
        if entry:
            return await self.delete(entry["id"])
        
        return False
    
    async def invalidate_all_caches(self) -> int:
        """
        Invalidate all cache entries.
        
        Returns:
            Number of cache entries deleted
        """
        return await self.delete_many([])
