"""Update cart item quantity use case."""

from app.application.dto.cart_dto import CartDTO, UpdateCartItemRequest
from app.application.errors.app_errors import ResourceNotFoundError, ValidationError
from app.application.interfaces.uow import UnitOfWork
from app.application.ports.clock_port import ClockPort
from app.application.use_cases.cart._helpers import build_cart_dto
from app.domain.errors.domain_errors import (
    CartAlreadyConvertedError,
    CartItemNotFoundError,
    CartItemQuantityError,
    CartNotFoundError,
)
from app.domain.policies.cart_policy import CartPolicy


class UpdateCartItemUseCase:
    """Update the quantity of an existing cart item."""

    def __init__(self, uow: UnitOfWork, clock: ClockPort) -> None:
        self.uow = uow
        self.clock = clock

    async def execute(self, request: UpdateCartItemRequest) -> CartDTO:
        try:
            CartPolicy.validate_quantity(request.quantity)
        except CartItemQuantityError as e:
            raise ValidationError(str(e))

        async with self.uow:
            # Resolve cart
            cart = await self._resolve_cart(request)
            if cart is None:
                raise ResourceNotFoundError("Active cart not found")

            try:
                CartPolicy.validate_cart_is_active(cart)
            except CartAlreadyConvertedError as e:
                raise ValidationError(str(e))

            item = cart.find_item_by_id(request.item_id)
            if item is None:
                raise ResourceNotFoundError(f"Cart item {request.item_id} not found")

            now = self.clock.now()
            updated_item = item.with_quantity(request.quantity)
            cart = cart.update_item_quantity(request.item_id, request.quantity, now)

            await self.uow.carts.update_item(updated_item)
            await self.uow.carts.update(cart)
            await self.uow.commit()

            return await build_cart_dto(self.uow, cart)

    async def _resolve_cart(self, request: UpdateCartItemRequest):
        if request.user_id is not None:
            return await self.uow.carts.get_active_by_user_id(request.user_id)
        if request.guest_token is not None:
            return await self.uow.carts.get_active_by_guest_token(request.guest_token)
        return None
