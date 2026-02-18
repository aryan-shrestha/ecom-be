"""In-memory cache implementation."""

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
