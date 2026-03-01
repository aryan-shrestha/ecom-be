"""Checkout use case: create an order from the active cart.

Production features:
- Idempotency-Key deduplication: same key + actor returns cached order response.
- Inventory reservation with SELECT FOR UPDATE, ordered by variant_id to avoid deadlocks.
- Order snapshot (product name, SKU, price at checkout time).
- Cart converted to CONVERTED status.
"""

import json
import uuid
from datetime import timedelta

from app.application.dto.order_dto import CheckoutRequest, OrderDTO, OrderItemDTO
from app.application.errors.app_errors import IdempotencyConflictError, ResourceNotFoundError, ValidationError
from app.application.interfaces.uow import UnitOfWork
from app.application.ports.audit_log_port import AuditLogPort
from app.application.ports.clock_port import ClockPort
from app.domain.entities.idempotency_key import IdempotencyKey
from app.domain.entities.order import Order, OrderItem, OrderStatus
from app.domain.errors.domain_errors import (
    CartNotFoundError,
    EmptyCartError,
    InsufficientStockError,
    InvalidStockAdjustmentError,
    InventoryNotFoundError,
    VariantNotAvailableError,
)
from app.domain.policies.cart_policy import CartPolicy
from app.domain.policies.inventory_policy import InventoryPolicy
from app.domain.value_objects.money import Money

IDEMPOTENCY_TTL_HOURS = 24
ORDER_NUMBER_PREFIX = "ORD"


def _build_order_dto(order: Order) -> OrderDTO:
    return OrderDTO(
        id=order.id,
        order_number=order.order_number,
        status=order.status.value,
        user_id=order.user_id,
        guest_token=order.guest_token,
        subtotal_amount=order.subtotal.amount,
        grand_total_amount=order.grand_total.amount,
        currency=order.currency,
        notes=order.notes,
        shipping_address=order.shipping_address,
        items=[
            OrderItemDTO(
                id=i.id,
                order_id=i.order_id,
                variant_id=i.variant_id,
                product_name=i.product_name,
                variant_sku=i.variant_sku,
                variant_label=i.variant_label,
                unit_price_amount=i.unit_price.amount,
                unit_price_currency=i.unit_price.currency,
                quantity=i.quantity,
                line_total_amount=i.line_total.amount,
            )
            for i in order.items
        ],
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


def _order_dto_to_json(dto: OrderDTO) -> str:
    """Serialize OrderDTO to JSON for idempotency storage."""
    import dataclasses
    return json.dumps(dataclasses.asdict(dto), default=str)


def _order_dto_from_json(raw: str) -> OrderDTO:
    """Deserialize OrderDTO from JSON."""
    data = json.loads(raw)
    items = [
        OrderItemDTO(
            id=uuid.UUID(i["id"]),
            order_id=uuid.UUID(i["order_id"]),
            variant_id=uuid.UUID(i["variant_id"]),
            product_name=i["product_name"],
            variant_sku=i["variant_sku"],
            variant_label=i["variant_label"],
            unit_price_amount=i["unit_price_amount"],
            unit_price_currency=i["unit_price_currency"],
            quantity=i["quantity"],
            line_total_amount=i["line_total_amount"],
        )
        for i in data["items"]
    ]
    from datetime import datetime
    return OrderDTO(
        id=uuid.UUID(data["id"]),
        order_number=data["order_number"],
        status=data["status"],
        user_id=uuid.UUID(data["user_id"]) if data.get("user_id") else None,
        guest_token=data.get("guest_token"),
        subtotal_amount=data["subtotal_amount"],
        grand_total_amount=data["grand_total_amount"],
        currency=data["currency"],
        notes=data.get("notes"),
        shipping_address=data.get("shipping_address"),
        items=items,
        created_at=datetime.fromisoformat(data["created_at"]),
        updated_at=datetime.fromisoformat(data["updated_at"]),
    )


class CheckoutUseCase:
    """Create an order from the actor's active cart."""

    def __init__(
        self,
        uow: UnitOfWork,
        clock: ClockPort,
        audit_log: AuditLogPort,
    ) -> None:
        self.uow = uow
        self.clock = clock
        self.audit_log = audit_log

    async def execute(self, request: CheckoutRequest) -> OrderDTO:
        actor_identifier = (
            str(request.user_id) if request.user_id else request.guest_token
        )
        if not actor_identifier:
            raise ValidationError("Checkout requires an authenticated user or guest token")

        async with self.uow:
            # ----------------------------------------------------------------
            # 1. Idempotency check
            # ----------------------------------------------------------------
            existing_key = await self.uow.idempotency.get_by_scope_actor_key(
                scope="checkout",
                actor_identifier=actor_identifier,
                key=request.idempotency_key,
            )
            if existing_key is not None:
                if existing_key.response_body is None:
                    # In-flight duplicate (unlikely but safe-guard)
                    raise IdempotencyConflictError(
                        "Request is already being processed. Please retry shortly."
                    )
                # Return cached response
                return _order_dto_from_json(existing_key.response_body)

            # ----------------------------------------------------------------
            # 2. Reserve idempotency slot (response_body=None → in-flight)
            # ----------------------------------------------------------------
            now = self.clock.now()
            idem = IdempotencyKey(
                id=uuid.uuid4(),
                scope="checkout",
                actor_identifier=actor_identifier,
                key=request.idempotency_key,
                response_body=None,
                created_at=now,
                expires_at=now + timedelta(hours=IDEMPOTENCY_TTL_HOURS),
            )
            await self.uow.idempotency.save(idem)
            # Flush so the row is visible within the transaction (prevents race)
            await self.uow._session.flush()  # type: ignore[attr-defined]

            # ----------------------------------------------------------------
            # 3. Load cart
            # ----------------------------------------------------------------
            cart = None
            if request.user_id is not None:
                cart = await self.uow.carts.get_active_by_user_id(request.user_id)
            elif request.guest_token is not None:
                cart = await self.uow.carts.get_active_by_guest_token(request.guest_token)

            if cart is None:
                raise ResourceNotFoundError("No active cart found for checkout")

            CartPolicy.validate_cart_is_active(cart)

            if not cart.items:
                raise ValidationError("Cannot checkout an empty cart")

            # ----------------------------------------------------------------
            # 4. Reserve inventory – lock rows in deterministic order
            # ----------------------------------------------------------------
            sorted_variant_ids = sorted(cart.items, key=lambda i: str(i.variant_id))
            order_items: list[OrderItem] = []
            subtotal_amount = 0
            currency = "USD"

            for cart_item in sorted_variant_ids:
                variant = await self.uow.products.get_variant_by_id(cart_item.variant_id)
                if variant is None:
                    raise ResourceNotFoundError(f"Variant {cart_item.variant_id} not found")
                product = await self.uow.products.get_by_id(variant.product_id)
                if product is None:
                    raise ResourceNotFoundError(f"Product {variant.product_id} not found")

                try:
                    CartPolicy.validate_variant_available(product, variant)
                except VariantNotAvailableError as e:
                    raise ValidationError(str(e))

                inventory = await self.uow.inventory.get_by_variant_id_for_update(cart_item.variant_id)
                if inventory is None:
                    raise ResourceNotFoundError(f"Inventory for variant {cart_item.variant_id} not found")

                try:
                    InventoryPolicy.validate_reservation(inventory, cart_item.quantity)
                except (InsufficientStockError, InvalidStockAdjustmentError) as e:
                    raise ValidationError(str(e))

                updated_inventory = inventory.reserve(cart_item.quantity)
                await self.uow.inventory.update(updated_inventory)

                price_snapshot = variant.price
                currency = price_snapshot.currency
                line_amount = price_snapshot.amount * cart_item.quantity
                subtotal_amount += line_amount

                order_items.append(
                    OrderItem(
                        id=uuid.uuid4(),
                        order_id=uuid.uuid4(),  # placeholder; replaced below
                        variant_id=cart_item.variant_id,
                        product_name=product.name,
                        variant_sku=str(variant.sku),
                        variant_label=None,  # extend if option labels exist
                        unit_price=price_snapshot,
                        quantity=cart_item.quantity,
                    )
                )

            # ----------------------------------------------------------------
            # 5. Create order
            # ----------------------------------------------------------------
            order_id = uuid.uuid4()
            order_number = _generate_order_number(now)

            # Fix order_id references in items
            order_items_final = tuple(
                OrderItem(
                    id=i.id,
                    order_id=order_id,
                    variant_id=i.variant_id,
                    product_name=i.product_name,
                    variant_sku=i.variant_sku,
                    variant_label=i.variant_label,
                    unit_price=i.unit_price,
                    quantity=i.quantity,
                )
                for i in order_items
            )

            subtotal = Money(amount=subtotal_amount, currency=currency)
            order = Order(
                id=order_id,
                order_number=order_number,
                status=OrderStatus.PENDING_PAYMENT,
                user_id=request.user_id,
                guest_token=request.guest_token,
                subtotal=subtotal,
                grand_total=subtotal,  # No tax/shipping calculation yet
                currency=currency,
                notes=request.notes,
                shipping_address=request.shipping_address,
                created_at=now,
                updated_at=now,
                items=order_items_final,
            )
            order = await self.uow.orders.save(order)

            # ----------------------------------------------------------------
            # 6. Convert cart
            # ----------------------------------------------------------------
            converted_cart = cart.convert(now)
            await self.uow.carts.update(converted_cart)

            # ----------------------------------------------------------------
            # 7. Store idempotency response
            # ----------------------------------------------------------------
            order_dto = _build_order_dto(order)
            response_json = _order_dto_to_json(order_dto)
            await self.uow.idempotency.update_response(idem.id, response_json)

            await self.uow.commit()

            await self.audit_log.log_event(
                event_type="order.created",
                user_id=request.user_id,
                details={
                    "order_id": str(order.id),
                    "order_number": order.order_number,
                    "item_count": len(order.items),
                    "grand_total": order.grand_total.amount,
                    "currency": order.currency,
                },
            )

            return order_dto


def _generate_order_number(now) -> str:
    """Generate a human-readable unique order number."""
    ts = now.strftime("%Y%m%d%H%M%S")
    suffix = uuid.uuid4().hex[:6].upper()
    return f"{ORDER_NUMBER_PREFIX}-{ts}-{suffix}"
