"""Image mapper."""

from app.domain.entities.product_image import ProductImage
from app.domain.entities.stock_movement import StockMovement
from app.infrastructure.db.sqlalchemy.models.product_image_model import ProductImageModel
from app.infrastructure.db.sqlalchemy.models.stock_movement_model import StockMovementModel


class ImageMapper:
    """Mapper for ProductImage entity and ProductImageModel."""

    @staticmethod
    def to_entity(model: ProductImageModel) -> ProductImage:
        """Convert ORM model to domain entity."""
        return ProductImage(
            id=model.id,
            product_id=model.product_id,
            url=model.url,
            alt_text=model.alt_text,
            position=model.position,
            created_at=model.created_at,
        )

    @staticmethod
    def to_model(entity: ProductImage) -> ProductImageModel:
        """Convert domain entity to ORM model."""
        return ProductImageModel(
            id=entity.id,
            product_id=entity.product_id,
            url=entity.url,
            alt_text=entity.alt_text,
            position=entity.position,
            created_at=entity.created_at,
        )

    @staticmethod
    def update_model(model: ProductImageModel, entity: ProductImage) -> None:
        """Update existing ORM model from domain entity."""
        model.url = entity.url
        model.alt_text = entity.alt_text
        model.position = entity.position


class StockMovementMapper:
    """Mapper for StockMovement entity and StockMovementModel."""

    @staticmethod
    def to_entity(model: StockMovementModel) -> StockMovement:
        """Convert ORM model to domain entity."""
        return StockMovement(
            id=model.id,
            variant_id=model.variant_id,
            delta=model.delta,
            reason=model.reason,
            note=model.note,
            created_at=model.created_at,
            created_by=model.created_by,
        )

    @staticmethod
    def to_model(entity: StockMovement) -> StockMovementModel:
        """Convert domain entity to ORM model."""
        return StockMovementModel(
            id=entity.id,
            variant_id=entity.variant_id,
            delta=entity.delta,
            reason=entity.reason,
            note=entity.note,
            created_at=entity.created_at,
            created_by=entity.created_by,
        )
