"""Cache port interface for caching permission checks."""

from abc import ABC, abstractmethod
from typing import Any, Optional


class CachePort(ABC):
    """Port interface for caching operations."""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        ...

    @abstractmethod
    async def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        """
        Set value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time-to-live in seconds
        """
        ...

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete key from cache."""
        ...

    @abstractmethod
    async def clear(self) -> None:
        """Clear all cache entries."""
        ...

    @abstractmethod
    async def delete_pattern(self, pattern: str) -> None:
        """
        Delete all keys matching the given pattern.
        
        Args:
            pattern: Glob pattern to match keys (e.g., "products:*", "user:123:*")
        """
        ...
