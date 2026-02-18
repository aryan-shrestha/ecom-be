"""Audit logging port interface."""

from abc import ABC, abstractmethod
from typing import Any, Optional
from uuid import UUID


class AuditLogPort(ABC):
    """Port interface for audit logging."""

    @abstractmethod
    async def log_event(
        self,
        event_type: str,
        user_id: Optional[UUID],
        details: dict[str, Any],
        ip: Optional[str] = None,
    ) -> None:
        """
        Log an audit event.
        
        Args:
            event_type: Type of event (e.g., "user.login", "user.password_changed")
            user_id: User ID associated with event (None for anonymous)
            details: Additional event details
            ip: IP address of request
        """
        ...
