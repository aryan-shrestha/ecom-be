"""Product mapper."""

from app.domain.entities.product import Product, ProductStatus
from app.domain.value_objects.slug import Slug
from app.infrastructure.db.sqlalchemy.models.product_model import ProductModel


class ProductMapper:
    """Mapper for Product entity and ProductModel."""

    @staticmethod
    def to_entity(model: ProductModel) -> Product:
        """Convert ORM model to domain entity."""
        return Product(
            id=model.id,
            status=ProductStatus(model.status),
            name=model.name,
            slug=Slug(value=model.slug),
            description_short=model.description_short,
            description_long=model.description_long,
            tags=model.tags if model.tags else [],
            featured=model.featured,
            sort_order=model.sort_order,
            created_at=model.created_at,
            updated_at=model.updated_at,
            created_by=model.created_by,
            updated_by=model.updated_by,
        )

    @staticmethod
    def to_model(entity: Product) -> ProductModel:
        """Convert domain entity to ORM model."""
        return ProductModel(
            id=entity.id,
            status=entity.status.value,
            name=entity.name,
            slug=str(entity.slug),
            description_short=entity.description_short,
            description_long=entity.description_long,
            tags=entity.tags,
            featured=entity.featured,
            sort_order=entity.sort_order,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            created_by=entity.created_by,
            updated_by=entity.updated_by,
        )

    @staticmethod
    def update_model(model: ProductModel, entity: Product) -> None:
        """Update existing ORM model from domain entity."""
        model.status = entity.status.value
        model.name = entity.name
        model.slug = str(entity.slug)
        model.description_short = entity.description_short
        model.description_long = entity.description_long
        model.tags = entity.tags
        model.featured = entity.featured
        model.sort_order = entity.sort_order
        model.updated_at = entity.updated_at
        model.updated_by = entity.updated_by
