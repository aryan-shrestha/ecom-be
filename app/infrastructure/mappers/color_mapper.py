"""
Color mapper
"""
from app.domain.entities.color import Color
from app.infrastructure.db.sqlalchemy.models.color_model import ColorModel


class ColorMapper:
    """Mapper for Color entity and ColorModel."""

    @staticmethod
    def to_entity(model: ColorModel) -> Color:
        """Convert ORM model to domain entity."""
        return Color(
            id=model.id,
            name=model.name,
            hex_value=model.hex_value,
            product_id=model.product_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(entity: Color) -> ColorModel:
        """Convert domain entity to ORM model."""
        return ColorModel(
            id=entity.id,
            name=entity.name,
            hex_value=entity.hex_value,
            product_id=entity.product_id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    @staticmethod
    def update_model(model: ColorModel, entity: Color) -> None:
        """Update existing ORM model from domain entity."""
        model.name = entity.name
        model.hex_value = entity.hex_value
        model.product_id = entity.product_id
        model.updated_at = entity.updated_at