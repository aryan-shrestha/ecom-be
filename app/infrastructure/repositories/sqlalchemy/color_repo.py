"""
SQLAlchemy implementation of the Color repository.
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.color import Color
from app.domain.repositories.color_repository import ColorRepository
from app.infrastructure.db.sqlalchemy.models.color_model import ColorModel
from app.infrastructure.mappers.color_mapper import ColorMapper


class SqlAlchemyColorRepository(ColorRepository):
    """SQLAlchemy implementation of the ColorRepository interface."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, color_id: UUID) -> Optional[Color]:
        """Retrieve color by ID."""
        result = await self.session.get(ColorModel, color_id)
        return ColorMapper.to_entity(result) if result else None

    async def list_all(self) -> list[Color]:
        """List all colors."""
        result = await self.session.execute(select(ColorModel))
        return [ColorMapper.to_entity(row) for row in result.scalars().all()]

    async def list_by_product_id(self, product_id: UUID) -> list[Color]:
        """List all colors for a given product ID."""
        result = await self.session.execute(
            select(ColorModel).where(ColorModel.product_id == product_id)
        )
        return [ColorMapper.to_entity(row) for row in result.scalars().all()]

    async def save(self, color: Color) -> Color:
        """Save new color."""
        model = ColorMapper.to_model(color)
        self.session.add(model)
        await self.session.flush()
        return ColorMapper.to_entity(model)

    async def update(self, color: Color) -> Color:
        """Update existing color."""
        model = await self.session.get(ColorModel, color.id)
        if not model:
            raise ValueError("Color not found")
        ColorMapper.update_model(model, color)
        await self.session.flush()
        return ColorMapper.to_entity(model)

    async def delete(self, color_id: UUID) -> None:
        """Delete color (soft delete recommended)."""
        await self.session.execute(delete(ColorModel).where(ColorModel.id == color_id))
        await self.session.flush()