"""Unit tests for MemoryCache implementation."""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from app.infrastructure.caching.memory_cache import MemoryCache


@pytest.mark.asyncio
async def test_get_non_existent_key():
    """Test getting a non-existent key returns None."""
    cache = MemoryCache()
    result = await cache.get("non_existent")
    assert result is None


@pytest.mark.asyncio
async def test_set_and_get():
    """Test setting and getting a value."""
    cache = MemoryCache()
    await cache.set("test_key", "test_value", 60)
    result = await cache.get("test_key")
    assert result == "test_value"


@pytest.mark.asyncio
async def test_get_expired_key():
    """Test getting an expired key returns None and removes it."""
    cache = MemoryCache()
    
    # Set with very short TTL
    await cache.set("expired_key", "value", 1)
    
    # Mock time to be past expiration
    with patch("app.infrastructure.caching.memory_cache.datetime") as mock_datetime:
        # First call returns current time (for set operation if cached)
        # Second call returns future time (for get operation)
        future_time = datetime.utcnow() + timedelta(seconds=10)
        mock_datetime.utcnow.return_value = future_time
        
        result = await cache.get("expired_key")
        assert result is None
        
        # Verify key was removed
        assert "expired_key" not in cache._cache


@pytest.mark.asyncio
async def test_delete():
    """Test deleting a key."""
    cache = MemoryCache()
    await cache.set("key_to_delete", "value", 60)
    
    # Verify key exists
    assert await cache.get("key_to_delete") == "value"
    
    # Delete key
    await cache.delete("key_to_delete")
    
    # Verify key no longer exists
    assert await cache.get("key_to_delete") is None


@pytest.mark.asyncio
async def test_delete_non_existent_key():
    """Test deleting a non-existent key doesn't raise error."""
    cache = MemoryCache()
    await cache.delete("non_existent")  # Should not raise


@pytest.mark.asyncio
async def test_clear():
    """Test clearing all cache entries."""
    cache = MemoryCache()
    await cache.set("key1", "value1", 60)
    await cache.set("key2", "value2", 60)
    await cache.set("key3", "value3", 60)
    
    # Verify keys exist
    assert await cache.get("key1") == "value1"
    assert await cache.get("key2") == "value2"
    
    # Clear cache
    await cache.clear()
    
    # Verify all keys gone
    assert await cache.get("key1") is None
    assert await cache.get("key2") is None
    assert await cache.get("key3") is None


@pytest.mark.asyncio
async def test_delete_pattern_wildcard_suffix():
    """Test delete_pattern with wildcard suffix (e.g., 'products:*')."""
    cache = MemoryCache()
    
    # Set up test data
    await cache.set("products:1", "product1", 60)
    await cache.set("products:2", "product2", 60)
    await cache.set("products:storefront:list", "list", 60)
    await cache.set("users:1", "user1", 60)
    await cache.set("category:1", "cat1", 60)
    
    # Delete pattern
    await cache.delete_pattern("products:*")
    
    # Verify products keys deleted
    assert await cache.get("products:1") is None
    assert await cache.get("products:2") is None
    assert await cache.get("products:storefront:list") is None
    
    # Verify other keys remain
    assert await cache.get("users:1") == "user1"
    assert await cache.get("category:1") == "cat1"


@pytest.mark.asyncio
async def test_delete_pattern_wildcard_prefix():
    """Test delete_pattern with wildcard prefix."""
    cache = MemoryCache()
    
    await cache.set("products:storefront:1", "p1", 60)
    await cache.set("products:storefront:2", "p2", 60)
    await cache.set("products:admin:1", "a1", 60)
    
    # Delete only storefront
    await cache.delete_pattern("products:storefront:*")
    
    assert await cache.get("products:storefront:1") is None
    assert await cache.get("products:storefront:2") is None
    assert await cache.get("products:admin:1") == "a1"


@pytest.mark.asyncio
async def test_delete_pattern_exact_match():
    """Test delete_pattern with exact key (no wildcards)."""
    cache = MemoryCache()
    
    await cache.set("exact:key", "value", 60)
    await cache.set("exact:key:other", "other", 60)
    
    # Delete exact pattern
    await cache.delete_pattern("exact:key")
    
    assert await cache.get("exact:key") is None
    assert await cache.get("exact:key:other") == "other"


@pytest.mark.asyncio
async def test_delete_pattern_question_mark():
    """Test delete_pattern with ? wildcard (single character)."""
    cache = MemoryCache()
    
    await cache.set("user:1", "u1", 60)
    await cache.set("user:2", "u2", 60)
    await cache.set("user:10", "u10", 60)
    
    # Match single digit
    await cache.delete_pattern("user:?")
    
    assert await cache.get("user:1") is None
    assert await cache.get("user:2") is None
    assert await cache.get("user:10") == "u10"  # Two chars, not matched


@pytest.mark.asyncio
async def test_delete_pattern_no_matches():
    """Test delete_pattern when no keys match."""
    cache = MemoryCache()
    
    await cache.set("products:1", "p1", 60)
    await cache.set("users:1", "u1", 60)
    
    # Delete pattern with no matches
    await cache.delete_pattern("categories:*")
    
    # All keys should remain
    assert await cache.get("products:1") == "p1"
    assert await cache.get("users:1") == "u1"


@pytest.mark.asyncio
async def test_delete_pattern_purges_expired_keys():
    """Test that delete_pattern also removes expired keys."""
    cache = MemoryCache()
    
    # Set up mix of valid and expired keys
    await cache.set("products:1", "p1", 60)
    await cache.set("products:2", "p2", 1)  # Short TTL
    await cache.set("users:1", "u1", 1)  # Short TTL, different prefix
    
    # Mock time to expire some keys
    with patch("app.infrastructure.caching.memory_cache.datetime") as mock_datetime:
        future_time = datetime.utcnow() + timedelta(seconds=10)
        mock_datetime.utcnow.return_value = future_time
        
        # Delete products pattern - should also clean up expired keys
        await cache.delete_pattern("products:*")
        
        # Both products keys deleted (one by pattern, one expired)
        assert await cache.get("products:1") is None
        assert await cache.get("products:2") is None
        
        # Expired users key also removed during scan
        assert "users:1" not in cache._cache


@pytest.mark.asyncio
async def test_delete_pattern_empty_cache():
    """Test delete_pattern on empty cache."""
    cache = MemoryCache()
    await cache.delete_pattern("any:*")  # Should not raise


@pytest.mark.asyncio
async def test_delete_pattern_all_expired():
    """Test delete_pattern when all matching keys are expired."""
    cache = MemoryCache()
    
    await cache.set("products:1", "p1", 1)
    await cache.set("products:2", "p2", 1)
    
    # Mock time to expire all keys
    with patch("app.infrastructure.caching.memory_cache.datetime") as mock_datetime:
        future_time = datetime.utcnow() + timedelta(seconds=10)
        mock_datetime.utcnow.return_value = future_time
        
        await cache.delete_pattern("products:*")
        
        # All keys removed
        assert len(cache._cache) == 0


@pytest.mark.asyncio
async def test_ttl_behavior():
    """Test that TTL is correctly calculated and enforced."""
    cache = MemoryCache()
    
    with patch("app.infrastructure.caching.memory_cache.datetime") as mock_datetime:
        start_time = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = start_time
        
        # Set with 60 second TTL
        await cache.set("key", "value", 60)
        
        # Verify value is retrievable before expiration
        mock_datetime.utcnow.return_value = start_time + timedelta(seconds=30)
        assert await cache.get("key") == "value"
        
        # Verify value expires after TTL
        mock_datetime.utcnow.return_value = start_time + timedelta(seconds=61)
        assert await cache.get("key") is None


@pytest.mark.asyncio
async def test_pattern_with_brackets():
    """Test delete_pattern with bracket character classes."""
    cache = MemoryCache()
    
    await cache.set("item:a", "a", 60)
    await cache.set("item:b", "b", 60)
    await cache.set("item:c", "c", 60)
    await cache.set("item:d", "d", 60)
    
    # Match only a and b
    await cache.delete_pattern("item:[ab]")
    
    assert await cache.get("item:a") is None
    assert await cache.get("item:b") is None
    assert await cache.get("item:c") == "c"
    assert await cache.get("item:d") == "d"
