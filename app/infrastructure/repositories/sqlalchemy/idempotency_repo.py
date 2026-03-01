"""SQLAlchemy implementation of IdempotencyRepository."""

from typing import Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.idempotency_key import IdempotencyKey
from app.domain.repositories.idempotency_repository import IdempotencyRepository
from app.infrastructure.db.sqlalchemy.models.idempotency_key_model import IdempotencyKeyModel


class SqlAlchemyIdempotencyRepository(IdempotencyRepository):
    """SQLAlchemy implementation of IdempotencyRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_scope_actor_key(
        self, scope: str, actor_identifier: str, key: str
    ) -> Optional[IdempotencyKey]:
        stmt = select(IdempotencyKeyModel).where(
            IdempotencyKeyModel.scope == scope,
            IdempotencyKeyModel.actor_identifier == actor_identifier,
            IdempotencyKeyModel.key == key,
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return _to_entity(model)

    async def save(self, idempotency_key: IdempotencyKey) -> IdempotencyKey:
        model = IdempotencyKeyModel(
            id=idempotency_key.id,
            scope=idempotency_key.scope,
            actor_identifier=idempotency_key.actor_identifier,
            key=idempotency_key.key,
            response_body=idempotency_key.response_body,
            created_at=idempotency_key.created_at,
            expires_at=idempotency_key.expires_at,
        )
        self.session.add(model)
        await self.session.flush()
        return _to_entity(model)

    async def update_response(self, id: UUID, response_body: str) -> None:
        stmt = (
            update(IdempotencyKeyModel)
            .where(IdempotencyKeyModel.id == id)
            .values(response_body=response_body)
        )
        await self.session.execute(stmt)
        await self.session.flush()


def _to_entity(model: IdempotencyKeyModel) -> IdempotencyKey:
    return IdempotencyKey(
        id=model.id,
        scope=model.scope,
        actor_identifier=model.actor_identifier,
        key=model.key,
        response_body=model.response_body,
        created_at=model.created_at,
        expires_at=model.expires_at,
    )
