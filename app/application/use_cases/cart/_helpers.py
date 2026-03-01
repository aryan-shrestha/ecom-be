"""Shared builder for CartDTO objects (internal, not a public use case)."""

from app.application.dto.cart_dto import CartDTO, CartItemDTO
from app.application.interfaces.uow import UnitOfWork
from app.domain.entities.cart import Cart


async def build_cart_dto(uow: UnitOfWork, cart: Cart) -> CartDTO:
    """
    Build a CartDTO, resolving current variant prices for line subtotals.
    Does NOT commit – caller is responsible for transaction context.
    """
    item_dtos: list[CartItemDTO] = []
    subtotal_amount = 0
    subtotal_currency = "USD"  # default; overwritten by first item

    for item in cart.items:
        variant = await uow.products.get_variant_by_id(item.variant_id)
        if variant is None:
            # Skip orphaned items (variant deleted after adding to cart)
            continue
        price = variant.price
        line_amount = price.amount * item.quantity
        subtotal_amount += line_amount
        subtotal_currency = price.currency
        item_dtos.append(
            CartItemDTO(
                id=item.id,
                cart_id=item.cart_id,
                variant_id=item.variant_id,
                quantity=item.quantity,
                unit_price_amount=price.amount,
                unit_price_currency=price.currency,
                line_subtotal_amount=line_amount,
            )
        )

    return CartDTO(
        id=cart.id,
        status=cart.status.value,
        user_id=cart.user_id,
        guest_token=cart.guest_token,
        items=item_dtos,
        subtotal_amount=subtotal_amount,
        subtotal_currency=subtotal_currency,
        created_at=cart.created_at,
        updated_at=cart.updated_at,
    )
