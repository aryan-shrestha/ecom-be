"""Audit logger implementation."""

import json
import logging
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from app.application.ports.audit_log_port import AuditLogPort

# Configure audit logger
audit_logger = logging.getLogger("audit")
audit_logger.setLevel(logging.INFO)


class StructuredAuditLogger(AuditLogPort):
    """Audit logger that writes structured JSON logs."""

    def __init__(self) -> None:
        self.logger = audit_logger

    async def log_event(
        self,
        event_type: str,
        user_id: Optional[UUID],
        details: dict[str, Any],
        ip: Optional[str] = None,
    ) -> None:
        """Log an audit event as structured JSON."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "user_id": str(user_id) if user_id else None,
            "ip": ip,
            "details": details,
        }
        self.logger.info(json.dumps(log_entry))
