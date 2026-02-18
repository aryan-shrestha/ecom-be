"""Rate limiting middleware (in-memory)."""

import time
from collections import defaultdict
from typing import Callable

from fastapi import HTTPException, Request, Response, status

from config.settings import settings


class InMemoryRateLimiter:
    """
    Simple in-memory rate limiter.
    
    WARNING: This is per-instance only. For multi-instance deployments,
    use a distributed rate limiter (Redis, etc.).
    """

    def __init__(self) -> None:
        # key -> list of timestamps
        self._requests: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> bool:
        """Check if request is allowed under rate limit."""
        now = time.time()
        window_start = now - window_seconds

        # Clean old requests
        self._requests[key] = [ts for ts in self._requests[key] if ts > window_start]

        # Check limit
        if len(self._requests[key]) >= max_requests:
            return False

        # Record request
        self._requests[key].append(now)
        return True


# Global rate limiter instance
_rate_limiter = InMemoryRateLimiter()


def rate_limit_middleware_factory(
    path_configs: dict[str, tuple[int, int]]
) -> Callable:
    """
    Factory for creating rate limit middleware.
    
    Args:
        path_configs: Dict of path_prefix -> (max_requests, window_seconds)
    """

    async def middleware(request: Request, call_next: Callable) -> Response:
        """Rate limit middleware."""
        # Check if path needs rate limiting
        for path_prefix, (max_requests, window_seconds) in path_configs.items():
            if request.url.path.startswith(path_prefix):
                # Use IP as rate limit key
                client_ip = request.client.host if request.client else "unknown"
                key = f"{path_prefix}:{client_ip}"

                if not _rate_limiter.is_allowed(key, max_requests, window_seconds):
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Rate limit exceeded",
                    )
                break

        return await call_next(request)

    return middleware


# Configure rate limits for specific paths
rate_limit_middleware = rate_limit_middleware_factory(
    {
        "/auth/login": (
            settings.rate_limit_login_max_requests,
            settings.rate_limit_login_window_seconds,
        ),
        "/auth/refresh": (
            settings.rate_limit_refresh_max_requests,
            settings.rate_limit_refresh_window_seconds,
        ),
    }
)
