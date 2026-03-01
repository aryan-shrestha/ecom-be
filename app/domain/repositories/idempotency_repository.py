"""Idempotency key repository interface."""

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from app.domain.entities.idempotency_key import IdempotencyKey


class IdempotencyRepository(ABC):
    """Repository for checkout idempotency deduplication."""

    @abstractmethod
    async def get_by_scope_actor_key(
        self, scope: str, actor_identifier: str, key: str
    ) -> Optional[IdempotencyKey]:
        """Retrieve an existing record (if any) by (scope, actor, key)."""
        ...

    @abstractmethod
    async def save(self, idempotency_key: IdempotencyKey) -> IdempotencyKey:
        """Insert new idempotency record."""
        ...

    @abstractmethod
    async def update_response(self, id: UUID, response_body: str) -> None:
        """Store the serialized response body after successful processing."""
        ...
