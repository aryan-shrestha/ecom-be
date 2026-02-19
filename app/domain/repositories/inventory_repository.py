"""Inventory repository interface."""

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from app.domain.entities.inventory import Inventory
from app.domain.entities.stock_movement import StockMovement


class InventoryRepository(ABC):
    """Repository interface for Inventory management."""

    @abstractmethod
    async def get_by_variant_id(self, variant_id: UUID) -> Optional[Inventory]:
        """Retrieve inventory for variant."""
        ...

    @abstractmethod
    async def get_by_variant_id_for_update(self, variant_id: UUID) -> Optional[Inventory]:
        """
        Retrieve inventory for variant with row lock (SELECT FOR UPDATE).
        
        Used for concurrent stock adjustments.
        """
        ...

    @abstractmethod
    async def save(self, inventory: Inventory) -> Inventory:
        """Save new inventory record."""
        ...

    @abstractmethod
    async def update(self, inventory: Inventory) -> Inventory:
        """Update existing inventory."""
        ...

    @abstractmethod
    async def delete(self, variant_id: UUID) -> None:
        """Delete inventory record."""
        ...

    # Stock movements

    @abstractmethod
    async def save_stock_movement(self, movement: StockMovement) -> StockMovement:
        """Save stock movement record."""
        ...

    @abstractmethod
    async def get_stock_movements_for_variant(
        self, variant_id: UUID, limit: int = 100
    ) -> list[StockMovement]:
        """Get stock movement history for variant."""
        ...
