"""Get or create active cart for an actor (user or guest)."""

import uuid

from app.application.dto.cart_dto import CartDTO, CartItemDTO, GetCartRequest
from app.application.interfaces.uow import UnitOfWork
from app.application.ports.clock_port import ClockPort
from app.domain.entities.cart import Cart, CartStatus


class GetCartUseCase:
    """
    Retrieve the current active cart for the actor.
    If no cart exists yet, one is transparently created.
    """

    def __init__(self, uow: UnitOfWork, clock: ClockPort) -> None:
        self.uow = uow
        self.clock = clock

    async def execute(self, request: GetCartRequest) -> CartDTO:
        async with self.uow:
            cart_dto = await self._resolve_or_create(request)
            return cart_dto

    async def _resolve_or_create(self, request: GetCartRequest) -> CartDTO:
        """Find existing active cart or create a new one."""
        cart: Cart | None = None
        if request.user_id is not None:
            cart = await self.uow.carts.get_active_by_user_id(request.user_id)
        elif request.guest_token is not None:
            cart = await self.uow.carts.get_active_by_guest_token(request.guest_token)

        item_dtos: list[CartItemDTO] = []
        subtotal_amount = 0
        if cart is not None:
            items = cart.items
            for item in items:
                variant = await self.uow.products.get_variant_by_id(item.variant_id)
                variant_images = await self.uow.products.get_images_for_variant(variant.id)
                product = await self.uow.products.get_by_id(variant.product_id)
                item_dto = CartItemDTO(
                    id=item.id,
                    cart_id=item.cart_id,
                    variant_id=variant.id,
                    product_id=product.id,
                    product_name=product.name,
                    product_slug=str(product.slug),
                    variant_images=[i.url for i in variant_images],
                    quantity=item.quantity,
                    unit_price_amount=variant.price.amount,
                    unit_price_currency=variant.price.currency,
                    line_subtotal_amount=item.quantity * variant.price.amount,
                )
                item_dtos.append(item_dto)
                subtotal_amount += item_dto.line_subtotal_amount

            cart_dto = CartDTO(
                id=cart.id,
                status=cart.status,
                user_id=cart.user_id,
                guest_token=cart.guest_token,
                items=item_dtos,
                subtotal_amount=subtotal_amount,
                subtotal_currency=item_dtos[0].unit_price_currency if item_dtos else "NPR",
                created_at=cart.created_at,
                updated_at=cart.updated_at,            
            )
            return cart_dto

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
        cart = await self.uow.carts.save(new_cart)
        await self.uow.commit()
        return CartDTO(
            id=cart.id,
            status=cart.status,
            user_id=cart.user_id,
            guest_token=cart.guest_token,
            items=[],
            subtotal_amount=0,
            subtotal_currency="NPR",
            created_at=cart.created_at,
            updated_at=cart.updated_at,
        )
