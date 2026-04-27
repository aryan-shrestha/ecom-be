from typing import Optional
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.size import Size
from app.domain.repositories.size_repository import SizeRepository
from app.infrastructure.db.sqlalchemy.models.size_model import SizeModel
from app.infrastructure.mappers.size_mapper import SizeMapper


class SqlAlchemySizeRepository(SizeRepository):
    """SQLAlchemy implementation of the SizeRepository interface."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, size_id: UUID) -> Optional[Size]:
        """Retrieve size by ID."""
        result = await self.session.get(SizeModel, size_id)
        return SizeMapper.to_entity(result) if result else None

    async def list_all(self) -> list[Size]:
        """List all sizes."""
        result = await self.session.execute(select(SizeModel))
        return [SizeMapper.to_entity(row) for row in result.scalars().all()]

    async def list_by_product_id(self, product_id: UUID) -> list[Size]:
        """List all sizes for a given product ID."""
        result = await self.session.execute(
            select(SizeModel).where(SizeModel.product_id == product_id)
        )
        return [SizeMapper.to_entity(row) for row in result.scalars().all()]

    async def save(self, size: Size) -> Size:
        """Save new size."""
        model = SizeMapper.to_model(size)
        self.session.add(model)
        await self.session.flush()
        return SizeMapper.to_entity(model)

    async def update(self, size: Size) -> Size:
        """Update existing size."""
        model = await self.session.get(SizeModel, size.id)
        if not model:
            raise ValueError("Size not found")
        SizeMapper.update_model(model, size)
        await self.session.flush()
        return SizeMapper.to_entity(model)

    async def delete(self, size_id: UUID) -> None:
        """Delete size (soft delete recommended)."""
        await self.session.execute(delete(SizeModel).where(SizeModel.id == size_id))
        await self.session.flush()