"""Inventory mapper."""

from app.domain.entities.inventory import Inventory
from app.infrastructure.db.sqlalchemy.models.inventory_model import InventoryModel


class InventoryMapper:
    """Mapper for Inventory entity and InventoryModel."""

    @staticmethod
    def to_entity(model: InventoryModel) -> Inventory:
        """Convert ORM model to domain entity."""
        return Inventory(
            variant_id=model.variant_id,
            on_hand=model.on_hand,
            reserved=model.reserved,
            allow_backorder=model.allow_backorder,
        )

    @staticmethod
    def to_model(entity: Inventory) -> InventoryModel:
        """Convert domain entity to ORM model."""
        return InventoryModel(
            variant_id=entity.variant_id,
            on_hand=entity.on_hand,
            reserved=entity.reserved,
            allow_backorder=entity.allow_backorder,
        )

    @staticmethod
    def update_model(model: InventoryModel, entity: Inventory) -> None:
        """Update existing ORM model from domain entity."""
        model.on_hand = entity.on_hand
        model.reserved = entity.reserved
        model.allow_backorder = entity.allow_backorder
