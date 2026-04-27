"""Add product variant use case."""

import uuid

from app.application.dto.product_dto import CreateVariantRequest, VariantDTO, MoneyDTO
from app.application.dto.color_dto import ColorDTO
from app.application.dto.size_dto import SizeDTO
from app.application.errors.app_errors import ConflictError, ResourceNotFoundError
from app.application.interfaces.uow import UnitOfWork
from app.application.ports.audit_log_port import AuditLogPort
from app.application.ports.clock_port import ClockPort
from app.domain.entities.inventory import Inventory
from app.domain.entities.product_variant import ProductVariant, VariantStatus
from app.domain.value_objects.money import Money
from app.domain.value_objects.sku import SKU


class AddVariantUseCase:
    """Use case for adding a variant to a product."""

    def __init__(
        self,
        uow: UnitOfWork,
        clock: ClockPort,
        audit_log: AuditLogPort,
    ) -> None:
        self.uow = uow
        self.clock = clock
        self.audit_log = audit_log

    async def execute(self, request: CreateVariantRequest) -> VariantDTO:
        """
        Add variant to product.
        
        Raises:
            ResourceNotFoundError: If product not found
            ConflictError: If SKU already exists
        """
        async with self.uow:
            # Check product exists
            product = await self.uow.products.get_by_id(request.product_id)
            if not product:
                raise ResourceNotFoundError(f"Product {request.product_id} not found")

            # Check SKU uniqueness
            sku = SKU.from_string(request.sku)
            existing_variant = await self.uow.products.get_variant_by_sku(str(sku))
            if existing_variant:
                raise ConflictError(f"Variant with SKU '{sku}' already exists")

            color = None
            if request.color_id:
                color = await self.uow.colors.get_by_id(request.color_id)
                if not color or color.product_id != request.product_id:
                    raise ResourceNotFoundError("Color not found for product")

            size = None
            if request.size_id:
                size = await self.uow.sizes.get_by_id(request.size_id)
                if not size or size.product_id != request.product_id:
                    raise ResourceNotFoundError("Size not found for product")

            # Create variant
            now = self.clock.now()
            variant_id = uuid.uuid4()
            
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

            variant = ProductVariant(
                id=variant_id,
                product_id=request.product_id,
                sku=sku,
                barcode=request.barcode,
                status=VariantStatus.ACTIVE,
                price=price,
                compare_at_price=compare_at_price,
                cost=cost,
                color_id=request.color_id,
                size_id=request.size_id,
                is_default=request.is_default,
                created_at=now,
                updated_at=now,
            )

            # Save variant
            variant = await self.uow.products.save_variant(variant)

            # Initialize inventory
            inventory = Inventory(
                variant_id=variant_id,
                on_hand=request.initial_stock,
                reserved=0,
                allow_backorder=request.allow_backorder,
            )
            await self.uow.inventory.save(inventory)

            await self.uow.commit()

            # Audit log
            await self.audit_log.log_event(
                event_type="variant.created",
                user_id=None,
                details={
                    "variant_id": str(variant.id),
                    "product_id": str(request.product_id),
                    "sku": str(variant.sku),
                },
            )

            return VariantDTO(
                id=variant.id,
                product_id=variant.product_id,
                sku=str(variant.sku),
                barcode=variant.barcode,
                status=variant.status.value,
                price=MoneyDTO(amount=variant.price.amount, currency=variant.price.currency),
                compare_at_price=(
                    MoneyDTO(amount=variant.compare_at_price.amount, currency=variant.compare_at_price.currency)
                    if variant.compare_at_price
                    else None
                ),
                cost=(
                    MoneyDTO(amount=variant.cost.amount, currency=variant.cost.currency)
                    if variant.cost
                    else None
                ),
                color_id=variant.color_id,
                size_id=variant.size_id,
                color=(
                    ColorDTO(
                        id=color.id,
                        product_id=color.product_id,
                        name=color.name,
                        hex_value=color.hex_value,
                        created_at=color.created_at,
                        updated_at=color.updated_at,
                    )
                    if color
                    else None
                ),
                size=(
                    SizeDTO(
                        id=size.id,
                        product_id=size.product_id,
                        name=size.name,
                        created_at=size.created_at,
                        updated_at=size.updated_at,
                    )
                    if size
                    else None
                ),
                is_default=variant.is_default,
                created_at=variant.created_at,
                updated_at=variant.updated_at,
            )
