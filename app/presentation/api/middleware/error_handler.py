"""Error handling middleware."""

import logging
from typing import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


async def error_handler_middleware(request: Request, call_next: Callable) -> Response:
    """Global error handler middleware."""
    try:
        return await call_next(request)
    except Exception as e:
        logger.exception(f"Unhandled exception: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )
