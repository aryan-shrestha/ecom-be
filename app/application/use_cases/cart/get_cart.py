"""Get or create active cart for an actor (user or guest)."""

import uuid
from datetime import datetime

from app.application.dto.cart_dto import CartDTO, GetCartRequest
from app.application.interfaces.uow import UnitOfWork
from app.application.ports.clock_port import ClockPort
from app.application.use_cases.cart._helpers import build_cart_dto
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
            cart = await self._resolve_or_create(request)
            return await build_cart_dto(self.uow, cart)

    async def _resolve_or_create(self, request: GetCartRequest) -> Cart:
        """Find existing active cart or create a new one."""
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
        cart = await self.uow.carts.save(new_cart)
        await self.uow.commit()
        return cart
