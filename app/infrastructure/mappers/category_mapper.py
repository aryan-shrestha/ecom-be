"""Category mapper."""

from app.domain.entities.category import Category
from app.domain.value_objects.slug import Slug
from app.infrastructure.db.sqlalchemy.models.category_model import CategoryModel


class CategoryMapper:
    """Mapper for Category entity and CategoryModel."""

    @staticmethod
    def to_entity(model: CategoryModel) -> Category:
        """Convert ORM model to domain entity."""
        return Category(
            id=model.id,
            name=model.name,
            slug=Slug(value=model.slug),
            parent_id=model.parent_id,
        )

    @staticmethod
    def to_model(entity: Category) -> CategoryModel:
        """Convert domain entity to ORM model."""
        return CategoryModel(
            id=entity.id,
            name=entity.name,
            slug=str(entity.slug),
            parent_id=entity.parent_id,
        )

    @staticmethod
    def update_model(model: CategoryModel, entity: Category) -> None:
        """Update existing ORM model from domain entity."""
        model.name = entity.name
        model.slug = str(entity.slug)
        model.parent_id = entity.parent_id
