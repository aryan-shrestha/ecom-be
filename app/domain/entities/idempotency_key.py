"""Idempotency key entity for checkout deduplication."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class IdempotencyKey:
    """
    Stores a record of a previously processed request so that replays
    return the cached response rather than creating duplicates.

    Unique constraint: (scope, actor_identifier, key)
    """

    id: UUID
    scope: str               # e.g. "checkout"
    actor_identifier: str    # user_id or guest_token (string form)
    key: str                 # client-supplied Idempotency-Key header value
    response_body: Optional[str]  # JSON-encoded result (None while processing)
    created_at: datetime
    expires_at: datetime

    def __post_init__(self) -> None:
        if not self.scope:
            raise ValueError("scope cannot be empty")
        if not self.actor_identifier:
            raise ValueError("actor_identifier cannot be empty")
        if not self.key:
            raise ValueError("key cannot be empty")

    def is_expired(self, now: datetime) -> bool:
        return now >= self.expires_at

    def with_response(self, response_body: str) -> "IdempotencyKey":
        return IdempotencyKey(
            id=self.id,
            scope=self.scope,
            actor_identifier=self.actor_identifier,
            key=self.key,
            response_body=response_body,
            created_at=self.created_at,
            expires_at=self.expires_at,
        )
