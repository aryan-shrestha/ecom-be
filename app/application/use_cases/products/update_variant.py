"""Update product variant use case."""

from app.application.dto.product_dto import UpdateVariantRequest, VariantDTO, MoneyDTO
from app.application.errors.app_errors import ResourceNotFoundError
from app.application.interfaces.uow import UnitOfWork
from app.application.ports.audit_log_port import AuditLogPort
from app.application.ports.cache_port import CachePort
from app.application.ports.clock_port import ClockPort
from app.domain.entities.product_variant import VariantStatus
from app.domain.value_objects.money import Money


class UpdateVariantUseCase:
    """Use case for updating a product variant."""

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

    async def execute(self, request: UpdateVariantRequest) -> VariantDTO:
        """
        Update variant details.
        
        Raises:
            ResourceNotFoundError: If variant not found
        """
        async with self.uow:
            # Get variant
            variant = await self.uow.products.get_variant_by_id(request.variant_id)
            if not variant:
                raise ResourceNotFoundError(f"Variant {request.variant_id} not found")

            # Update variant
            now = self.clock.now()
            price = Money(amount=request.price_amount, currency=request.price_currency)
            compare_at_price = (
                Money(amount=request.compare_at_price_amount, currency=request.compare_at_price_currency)
                if request.compare_at_price_amount is not None
                else None
            )
            cost = (
                Money(amount=request.cost_amount, currency=request.cost_currency)
                if request.cost_amount is not None
                else None
            )

            updated_variant = variant.update(
                barcode=request.barcode,
                status=VariantStatus(request.status),
                price=price,
                compare_at_price=compare_at_price,
                cost=cost,
                weight=request.weight,
                length=request.length,
                width=request.width,
                height=request.height,
                updated_at=now,
            )

            # Save
            updated_variant = await self.uow.products.update_variant(updated_variant)
            await self.uow.commit()

            # Invalidate cache
            await self.cache.delete(f"product:{variant.product_id}")
            await self.cache.delete_pattern("products:storefront:*")

            # Audit log
            await self.audit_log.log_event(
                event_type="variant.updated",
                user_id=None,
                details={
                    "variant_id": str(updated_variant.id),
                    "sku": str(updated_variant.sku),
                },
            )

            return VariantDTO(
                id=updated_variant.id,
                product_id=updated_variant.product_id,
                sku=str(updated_variant.sku),
                barcode=updated_variant.barcode,
                status=updated_variant.status.value,
                price=MoneyDTO(amount=updated_variant.price.amount, currency=updated_variant.price.currency),
                compare_at_price=(
                    MoneyDTO(amount=updated_variant.compare_at_price.amount, currency=updated_variant.compare_at_price.currency)
                    if updated_variant.compare_at_price
                    else None
                ),
                cost=(
                    MoneyDTO(amount=updated_variant.cost.amount, currency=updated_variant.cost.currency)
                    if updated_variant.cost
                    else None
                ),
                weight=updated_variant.weight,
                length=updated_variant.length,
                width=updated_variant.width,
                height=updated_variant.height,
                is_default=updated_variant.is_default,
                created_at=updated_variant.created_at,
                updated_at=updated_variant.updated_at,
            )
