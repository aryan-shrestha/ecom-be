"""SQLAlchemy implementation of InventoryRepository."""

from typing import Optional
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.inventory import Inventory
from app.domain.entities.stock_movement import StockMovement
from app.domain.repositories.inventory_repository import InventoryRepository
from app.infrastructure.db.sqlalchemy.models.inventory_model import InventoryModel
from app.infrastructure.db.sqlalchemy.models.stock_movement_model import StockMovementModel
from app.infrastructure.mappers.inventory_mapper import InventoryMapper
from app.infrastructure.mappers.image_mapper import StockMovementMapper


class SqlAlchemyInventoryRepository(InventoryRepository):
    """SQLAlchemy implementation of InventoryRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_variant_id(self, variant_id: UUID) -> Optional[Inventory]:
        """Retrieve inventory for variant."""
        stmt = select(InventoryModel).where(InventoryModel.variant_id == variant_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return InventoryMapper.to_entity(model) if model else None

    async def get_by_variant_id_for_update(self, variant_id: UUID) -> Optional[Inventory]:
        """
        Retrieve inventory for variant with row lock (SELECT FOR UPDATE).
        
        Used for concurrent stock adjustments.
        """
        stmt = (
            select(InventoryModel)
            .where(InventoryModel.variant_id == variant_id)
            .with_for_update()
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return InventoryMapper.to_entity(model) if model else None

    async def save(self, inventory: Inventory) -> Inventory:
        """Save new inventory record."""
        model = InventoryMapper.to_model(inventory)
        self.session.add(model)
        await self.session.flush()
        return InventoryMapper.to_entity(model)

    async def update(self, inventory: Inventory) -> Inventory:
        """Update existing inventory."""
        stmt = select(InventoryModel).where(InventoryModel.variant_id == inventory.variant_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one()
        InventoryMapper.update_model(model, inventory)
        await self.session.flush()
        return InventoryMapper.to_entity(model)

    async def delete(self, variant_id: UUID) -> None:
        """Delete inventory record."""
        stmt = delete(InventoryModel).where(InventoryModel.variant_id == variant_id)
        await self.session.execute(stmt)
        await self.session.flush()

    # Stock movements

    async def save_stock_movement(self, movement: StockMovement) -> StockMovement:
        """Save stock movement record."""
        model = StockMovementMapper.to_model(movement)
        self.session.add(model)
        await self.session.flush()
        return StockMovementMapper.to_entity(model)

    async def get_stock_movements_for_variant(
        self, variant_id: UUID, limit: int = 100
    ) -> list[StockMovement]:
        """Get stock movement history for variant."""
        stmt = (
            select(StockMovementModel)
            .where(StockMovementModel.variant_id == variant_id)
            .order_by(StockMovementModel.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [StockMovementMapper.to_entity(m) for m in models]
