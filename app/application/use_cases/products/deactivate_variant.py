"""Deactivate variant use case."""

from typing import Optional
from uuid import UUID

from app.application.dto.product_dto import VariantDTO, MoneyDTO
from app.application.errors.app_errors import ResourceNotFoundError
from app.application.interfaces.uow import UnitOfWork
from app.application.ports.audit_log_port import AuditLogPort
from app.application.ports.cache_port import CachePort
from app.application.ports.clock_port import ClockPort


class DeactivateVariantUseCase:
    """Use case for deactivating a product variant."""

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

    async def execute(self, variant_id: UUID, deactivated_by: Optional[UUID] = None) -> VariantDTO:
        """
        Deactivate variant.
        
        Raises:
            ResourceNotFoundError: If variant not found
        """
        async with self.uow:
            # Get variant
            variant = await self.uow.products.get_variant_by_id(variant_id)
            if not variant:
                raise ResourceNotFoundError(f"Variant {variant_id} not found")

            # Deactivate
            now = self.clock.now()
            deactivated_variant = variant.deactivate(now)

            # Save
            deactivated_variant = await self.uow.products.update_variant(deactivated_variant)
            await self.uow.commit()

            # Invalidate cache
            await self.cache.delete(f"product:{variant.product_id}")
            await self.cache.delete_pattern("products:storefront:*")

            # Audit log
            await self.audit_log.log_event(
                event_type="variant.deactivated",
                user_id=deactivated_by,
                details={
                    "variant_id": str(deactivated_variant.id),
                    "sku": str(deactivated_variant.sku),
                },
            )

            return VariantDTO(
                id=deactivated_variant.id,
                product_id=deactivated_variant.product_id,
                sku=str(deactivated_variant.sku),
                barcode=deactivated_variant.barcode,
                status=deactivated_variant.status.value,
                price=MoneyDTO(amount=deactivated_variant.price.amount, currency=deactivated_variant.price.currency),
                compare_at_price=(
                    MoneyDTO(amount=deactivated_variant.compare_at_price.amount, currency=deactivated_variant.compare_at_price.currency)
                    if deactivated_variant.compare_at_price
                    else None
                ),
                cost=(
                    MoneyDTO(amount=deactivated_variant.cost.amount, currency=deactivated_variant.cost.currency)
                    if deactivated_variant.cost
                    else None
                ),
                weight=deactivated_variant.weight,
                length=deactivated_variant.length,
                width=deactivated_variant.width,
                height=deactivated_variant.height,
                is_default=deactivated_variant.is_default,
                created_at=deactivated_variant.created_at,
                updated_at=deactivated_variant.updated_at,
            )
