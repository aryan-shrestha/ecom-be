"""Adjust stock use case."""

import uuid

from app.application.dto.product_dto import AdjustStockRequest, StockMovementDTO
from app.application.errors.app_errors import ResourceNotFoundError, ValidationError
from app.application.interfaces.uow import UnitOfWork
from app.application.ports.audit_log_port import AuditLogPort
from app.application.ports.cache_port import CachePort
from app.application.ports.clock_port import ClockPort
from app.domain.entities.stock_movement import StockMovement
from app.domain.errors.domain_errors import (
    InsufficientStockError,
    InvalidStockAdjustmentError,
)
from app.domain.policies.inventory_policy import InventoryPolicy


class AdjustStockUseCase:
    """Use case for adjusting variant stock."""

    def __init__(
        self,
        uow: UnitOfWork,
        clock: ClockPort,
        audit_log: AuditLogPort,
        cache: CachePort,
    ) -> None:
        self.uow = uow
        self.clock = clock
        self.audit_log = audit_log
        self.cache = cache

    async def execute(self, request: AdjustStockRequest) -> StockMovementDTO:
        """
        Adjust stock for variant.
        
        Uses SELECT FOR UPDATE for concurrency safety.
        
        Raises:
            ResourceNotFoundError: If variant or inventory not found
            ValidationError: If adjustment is invalid
        """
        async with self.uow:
            # Get variant
            variant = await self.uow.products.get_variant_by_id(request.variant_id)
            if not variant:
                raise ResourceNotFoundError(f"Variant {request.variant_id} not found")

            # Get inventory with lock
            inventory = await self.uow.inventory.get_by_variant_id_for_update(request.variant_id)
            if not inventory:
                raise ResourceNotFoundError(f"Inventory for variant {request.variant_id} not found")

            # Validate adjustment
            try:
                InventoryPolicy.validate_adjustment(inventory, request.delta)
            except (InsufficientStockError, InvalidStockAdjustmentError) as e:
                raise ValidationError(str(e))

            # Apply adjustment
            updated_inventory = inventory.adjust_on_hand(request.delta)

            # Save inventory
            await self.uow.inventory.update(updated_inventory)

            # Create stock movement record
            now = self.clock.now()
            movement = StockMovement(
                id=uuid.uuid4(),
                variant_id=request.variant_id,
                delta=request.delta,
                reason=request.reason,
                note=request.note,
                created_at=now,
                created_by=request.created_by,
            )

            movement = await self.uow.inventory.save_stock_movement(movement)
            await self.uow.commit()

            # Invalidate cache
            await self.cache.delete(f"product:{variant.product_id}")
            await self.cache.delete_pattern("products:storefront:*")

            # Audit log
            await self.audit_log.log_event(
                event_type="stock.adjusted",
                user_id=request.created_by,
                details={
                    "variant_id": str(request.variant_id),
                    "sku": str(variant.sku),
                    "delta": request.delta,
                    "reason": request.reason,
                    "new_on_hand": updated_inventory.on_hand,
                },
            )

            return StockMovementDTO(
                id=movement.id,
                variant_id=movement.variant_id,
                delta=movement.delta,
                reason=movement.reason,
                note=movement.note,
                created_at=movement.created_at,
                created_by=movement.created_by,
            )
