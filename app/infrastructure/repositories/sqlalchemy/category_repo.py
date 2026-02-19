"""SQLAlchemy implementation of CategoryRepository."""

from typing import Optional
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.category import Category
from app.domain.repositories.category_repository import CategoryRepository
from app.domain.value_objects.slug import Slug
from app.infrastructure.db.sqlalchemy.models.category_model import CategoryModel
from app.infrastructure.mappers.category_mapper import CategoryMapper


class SqlAlchemyCategoryRepository(CategoryRepository):
    """SQLAlchemy implementation of CategoryRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, category_id: UUID) -> Optional[Category]:
        """Retrieve category by ID."""
        stmt = select(CategoryModel).where(CategoryModel.id == category_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return CategoryMapper.to_entity(model) if model else None

    async def get_by_slug(self, slug: Slug) -> Optional[Category]:
        """Retrieve category by slug."""
        stmt = select(CategoryModel).where(CategoryModel.slug == str(slug))
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return CategoryMapper.to_entity(model) if model else None

    async def exists_by_slug(self, slug: Slug) -> bool:
        """Check if category exists with given slug."""
        stmt = select(CategoryModel.id).where(CategoryModel.slug == str(slug))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get_children(self, parent_id: UUID) -> list[Category]:
        """Get child categories."""
        stmt = select(CategoryModel).where(CategoryModel.parent_id == parent_id)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [CategoryMapper.to_entity(m) for m in models]

    async def get_root_categories(self) -> list[Category]:
        """Get root categories (no parent)."""
        stmt = select(CategoryModel).where(CategoryModel.parent_id.is_(None))
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [CategoryMapper.to_entity(m) for m in models]

    async def save(self, category: Category) -> Category:
        """Save new category."""
        model = CategoryMapper.to_model(category)
        self.session.add(model)
        await self.session.flush()
        return CategoryMapper.to_entity(model)

    async def update(self, category: Category) -> Category:
        """Update existing category."""
        stmt = select(CategoryModel).where(CategoryModel.id == category.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one()
        CategoryMapper.update_model(model, category)
        await self.session.flush()
        return CategoryMapper.to_entity(model)

    async def delete(self, category_id: UUID) -> None:
        """Delete category."""
        stmt = delete(CategoryModel).where(CategoryModel.id == category_id)
        await self.session.execute(stmt)
        await self.session.flush()

    async def list_all(self) -> list[Category]:
        """List all categories."""
        stmt = select(CategoryModel).order_by(CategoryModel.name)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [CategoryMapper.to_entity(m) for m in models]
