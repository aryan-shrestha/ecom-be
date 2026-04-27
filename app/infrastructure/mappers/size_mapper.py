from app.domain.entities.size import Size
from app.infrastructure.db.sqlalchemy.models.size_model import SizeModel

class SizeMapper:
    """Mapper for Size entity and SizeModel."""

    @staticmethod
    def to_entity(model: SizeModel) -> Size:
        """Convert ORM model to domain entity."""
        return Size(
            id=model.id,
            name=model.name,
            product_id=model.product_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(entity: Size) -> SizeModel:
        """Convert domain entity to ORM model."""
        return SizeModel(
            id=entity.id,
            name=entity.name,
            product_id=entity.product_id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    @staticmethod
    def update_model(model: SizeModel, entity: Size) -> None:
        """Update existing ORM model from domain entity."""
        model.name = entity.name
        model.product_id = entity.product_id
        model.updated_at = entity.updated_at