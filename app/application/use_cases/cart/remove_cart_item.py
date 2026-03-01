"""Remove a single item from cart use case."""

from app.application.dto.cart_dto import CartDTO, RemoveCartItemRequest
from app.application.errors.app_errors import ResourceNotFoundError, ValidationError
from app.application.interfaces.uow import UnitOfWork
from app.application.ports.clock_port import ClockPort
from app.application.use_cases.cart._helpers import build_cart_dto
from app.domain.errors.domain_errors import CartAlreadyConvertedError
from app.domain.policies.cart_policy import CartPolicy


class RemoveCartItemUseCase:
    """Remove a single item from the actor's cart."""

    def __init__(self, uow: UnitOfWork, clock: ClockPort) -> None:
        self.uow = uow
        self.clock = clock

    async def execute(self, request: RemoveCartItemRequest) -> CartDTO:
        async with self.uow:
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
            cart = cart.remove_item(request.item_id, now)

            await self.uow.carts.delete_item(request.item_id)
            await self.uow.carts.update(cart)
            await self.uow.commit()

            return await build_cart_dto(self.uow, cart)

    async def _resolve_cart(self, request: RemoveCartItemRequest):
        if request.user_id is not None:
            return await self.uow.carts.get_active_by_user_id(request.user_id)
        if request.guest_token is not None:
            return await self.uow.carts.get_active_by_guest_token(request.guest_token)
        return None
