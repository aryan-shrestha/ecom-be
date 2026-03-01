"""Add item to cart use case."""

import uuid

from app.application.dto.cart_dto import AddCartItemRequest, CartDTO
from app.application.errors.app_errors import ResourceNotFoundError, ValidationError
from app.application.interfaces.uow import UnitOfWork
from app.application.ports.clock_port import ClockPort
from app.application.use_cases.cart._helpers import build_cart_dto
from app.domain.entities.cart import Cart, CartItem, CartStatus
from app.domain.errors.domain_errors import (
    CartAlreadyConvertedError,
    CartItemQuantityError,
    VariantNotAvailableError,
)
from app.domain.policies.cart_policy import CartPolicy


class AddCartItemUseCase:
    """Add a variant to the actor's active cart (creates cart if none exists)."""

    def __init__(self, uow: UnitOfWork, clock: ClockPort) -> None:
        self.uow = uow
        self.clock = clock

    async def execute(self, request: AddCartItemRequest) -> CartDTO:
        try:
            CartPolicy.validate_quantity(request.quantity)
        except CartItemQuantityError as e:
            raise ValidationError(str(e))

        async with self.uow:
            # Validate variant & product
            variant = await self.uow.products.get_variant_by_id(request.variant_id)
            if variant is None:
                raise ResourceNotFoundError(f"Variant {request.variant_id} not found")
            product = await self.uow.products.get_by_id(variant.product_id)
            if product is None:
                raise ResourceNotFoundError(f"Product for variant {request.variant_id} not found")

            try:
                CartPolicy.validate_variant_available(product, variant)
            except VariantNotAvailableError as e:
                raise ValidationError(str(e))

            # Resolve or create cart
            cart = await self._get_or_create_cart(request)

            try:
                CartPolicy.validate_cart_is_active(cart)
            except CartAlreadyConvertedError as e:
                raise ValidationError(str(e))

            # Check if variant already in cart
            existing = cart.find_item_by_variant(request.variant_id)
            now = self.clock.now()

            if existing:
                new_qty = existing.quantity + request.quantity
                try:
                    CartPolicy.validate_quantity(new_qty)
                except CartItemQuantityError as e:
                    raise ValidationError(str(e))
                updated_item = existing.with_quantity(new_qty)
                cart = cart.update_item_quantity(existing.id, new_qty, now)
                await self.uow.carts.update_item(updated_item)
            else:
                new_item = CartItem(
                    id=uuid.uuid4(),
                    cart_id=cart.id,
                    variant_id=request.variant_id,
                    quantity=request.quantity,
                )
                cart = cart.add_item(new_item, now)
                await self.uow.carts.save_item(new_item)

            await self.uow.carts.update(cart)
            await self.uow.commit()

            return await build_cart_dto(self.uow, cart)

    async def _get_or_create_cart(self, request: AddCartItemRequest) -> Cart:
        cart: Cart | None = None
        if request.user_id is not None:
            cart = await self.uow.carts.get_active_by_user_id(request.user_id)
        elif request.guest_token is not None:
            cart = await self.uow.carts.get_active_by_guest_token(request.guest_token)

        if cart is not None:
            return cart

        now = self.clock.now()
        new_cart = Cart(
            id=uuid.uuid4(),
            status=CartStatus.ACTIVE,
            user_id=request.user_id,
            guest_token=request.guest_token,
            created_at=now,
            updated_at=now,
            items=(),
        )
        saved = await self.uow.carts.save(new_cart)
        return saved
