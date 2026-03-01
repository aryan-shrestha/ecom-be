"""Merge guest cart into authenticated user cart on login."""

import uuid

from app.application.dto.cart_dto import CartDTO, MergeGuestCartRequest
from app.application.interfaces.uow import UnitOfWork
from app.application.ports.clock_port import ClockPort
from app.application.use_cases.cart._helpers import build_cart_dto
from app.domain.entities.cart import Cart, CartItem, CartStatus
from app.domain.policies.cart_policy import CartPolicy
from app.domain.errors.domain_errors import CartItemQuantityError


class MergeGuestCartUseCase:
    """
    Merge a guest cart into the authenticated user's cart.

    Rules:
    - If user has no active cart, the guest cart is re-owned (user_id set,
      guest_token cleared).
    - If user already has an active cart, items from the guest cart are merged
      in (quantities summed, capped at MAX_QUANTITY_PER_ITEM).
    - The guest cart is abandoned after a successful merge.
    """

    def __init__(self, uow: UnitOfWork, clock: ClockPort) -> None:
        self.uow = uow
        self.clock = clock

    async def execute(self, request: MergeGuestCartRequest) -> CartDTO:
        async with self.uow:
            guest_cart = await self.uow.carts.get_active_by_guest_token(request.guest_token)
            if guest_cart is None:
                # Nothing to merge – return (or create) user cart as-is
                user_cart = await self.uow.carts.get_active_by_user_id(request.user_id)
                if user_cart is None:
                    now = self.clock.now()
                    user_cart = Cart(
                        id=uuid.uuid4(),
                        status=CartStatus.ACTIVE,
                        user_id=request.user_id,
                        guest_token=None,
                        created_at=now,
                        updated_at=now,
                        items=(),
                    )
                    user_cart = await self.uow.carts.save(user_cart)
                    await self.uow.commit()
                return await build_cart_dto(self.uow, user_cart)

            now = self.clock.now()
            user_cart = await self.uow.carts.get_active_by_user_id(request.user_id)

            if user_cart is None:
                # Re-own guest cart: claim it as the user cart
                # We persist new user-owned cart and abandon guest cart
                user_cart = Cart(
                    id=uuid.uuid4(),
                    status=CartStatus.ACTIVE,
                    user_id=request.user_id,
                    guest_token=None,
                    created_at=now,
                    updated_at=now,
                    items=(),
                )
                saved_user_cart = await self.uow.carts.save(user_cart)

                for guest_item in guest_cart.items:
                    # Validate variant still available - skip if not
                    variant = await self.uow.products.get_variant_by_id(guest_item.variant_id)
                    if variant is None:
                        continue
                    product = await self.uow.products.get_by_id(variant.product_id)
                    if product is None:
                        continue
                    try:
                        CartPolicy.validate_variant_available(product, variant)
                    except Exception:
                        continue

                    qty = min(guest_item.quantity, CartPolicy.validate_quantity.__func__.__defaults__[0] if hasattr(CartPolicy.validate_quantity, '__func__') else 100)
                    from app.domain.policies.cart_policy import MAX_QUANTITY_PER_ITEM
                    qty = min(guest_item.quantity, MAX_QUANTITY_PER_ITEM)
                    new_item = CartItem(
                        id=uuid.uuid4(),
                        cart_id=saved_user_cart.id,
                        variant_id=guest_item.variant_id,
                        quantity=qty,
                    )
                    saved_user_cart = saved_user_cart.add_item(new_item, now)
                    await self.uow.carts.save_item(new_item)

                await self.uow.carts.update(saved_user_cart)
            else:
                # Merge guest items into user cart
                saved_user_cart = user_cart
                for guest_item in guest_cart.items:
                    variant = await self.uow.products.get_variant_by_id(guest_item.variant_id)
                    if variant is None:
                        continue
                    product = await self.uow.products.get_by_id(variant.product_id)
                    if product is None:
                        continue
                    try:
                        CartPolicy.validate_variant_available(product, variant)
                    except Exception:
                        continue

                    from app.domain.policies.cart_policy import MAX_QUANTITY_PER_ITEM
                    existing = saved_user_cart.find_item_by_variant(guest_item.variant_id)
                    if existing:
                        new_qty = min(existing.quantity + guest_item.quantity, MAX_QUANTITY_PER_ITEM)
                        updated_item = existing.with_quantity(new_qty)
                        saved_user_cart = saved_user_cart.update_item_quantity(existing.id, new_qty, now)
                        await self.uow.carts.update_item(updated_item)
                    else:
                        qty = min(guest_item.quantity, MAX_QUANTITY_PER_ITEM)
                        new_item = CartItem(
                            id=uuid.uuid4(),
                            cart_id=saved_user_cart.id,
                            variant_id=guest_item.variant_id,
                            quantity=qty,
                        )
                        saved_user_cart = saved_user_cart.add_item(new_item, now)
                        await self.uow.carts.save_item(new_item)

                await self.uow.carts.update(saved_user_cart)

            # Abandon guest cart
            abandoned_guest = guest_cart.abandon(now)
            await self.uow.carts.update(abandoned_guest)
            await self.uow.commit()

            return await build_cart_dto(self.uow, saved_user_cart)
