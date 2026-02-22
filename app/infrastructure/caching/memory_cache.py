"""In-memory cache implementation."""

import fnmatch
from datetime import datetime, timedelta
from typing import Any, Optional


class MemoryCache:
    """
    Simple in-memory cache with TTL support.
    
    WARNING: This is a per-instance cache. In multi-instance deployments,
    consider using Redis or similar distributed cache.
    """

    def __init__(self) -> None:
        self._cache: dict[str, tuple[Any, datetime]] = {}

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key not in self._cache:
            return None

        value, expires_at = self._cache[key]
        if datetime.utcnow() >= expires_at:
            # Expired
            del self._cache[key]
            return None

        return value

    async def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        """Set value in cache with TTL."""
        expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
        self._cache[key] = (value, expires_at)

    async def delete(self, key: str) -> None:
        """Delete key from cache."""
        self._cache.pop(key, None)

    async def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()

    async def delete_pattern(self, pattern: str) -> None:
        """
        Delete all keys matching the given glob pattern.
        
        Also purges any expired keys encountered during the scan.
        
        Args:
            pattern: Glob pattern to match keys (e.g., "products:*", "user:123:*")
                    Supports * (any chars), ? (single char), [seq], [!seq]
        """
        now = datetime.utcnow()
        keys_to_delete = []
        
        # Scan all keys and collect matches and expired keys
        for key, (value, expires_at) in list(self._cache.items()):
            # Remove expired keys
            if now >= expires_at:
                keys_to_delete.append(key)
            # Match pattern on non-expired keys
            elif fnmatch.fnmatch(key, pattern):
                keys_to_delete.append(key)
        
        # Delete collected keys
        for key in keys_to_delete:
            self._cache.pop(key, None)
