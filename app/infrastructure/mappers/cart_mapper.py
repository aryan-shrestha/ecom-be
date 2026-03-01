"""Cart and CartItem mapper."""

from app.domain.entities.cart import Cart, CartItem, CartStatus
from app.infrastructure.db.sqlalchemy.models.cart_item_model import CartItemModel
from app.infrastructure.db.sqlalchemy.models.cart_model import CartModel


class CartMapper:
    """Mapper for Cart entity and CartModel."""

    @staticmethod
    def to_entity(model: CartModel, items: tuple[CartItem, ...] = ()) -> Cart:
        return Cart(
            id=model.id,
            status=CartStatus(model.status),
            user_id=model.user_id,
            guest_token=model.guest_token,
            created_at=model.created_at,
            updated_at=model.updated_at,
            items=items,
        )

    @staticmethod
    def to_model(entity: Cart) -> CartModel:
        return CartModel(
            id=entity.id,
            status=entity.status.value,
            user_id=entity.user_id,
            guest_token=entity.guest_token,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    @staticmethod
    def update_model(model: CartModel, entity: Cart) -> None:
        model.status = entity.status.value
        model.updated_at = entity.updated_at


class CartItemMapper:
    """Mapper for CartItem entity and CartItemModel."""

    @staticmethod
    def to_entity(model: CartItemModel) -> CartItem:
        return CartItem(
            id=model.id,
            cart_id=model.cart_id,
            variant_id=model.variant_id,
            quantity=model.quantity,
        )

    @staticmethod
    def to_model(entity: CartItem) -> CartItemModel:
        return CartItemModel(
            id=entity.id,
            cart_id=entity.cart_id,
            variant_id=entity.variant_id,
            quantity=entity.quantity,
        )

    @staticmethod
    def update_model(model: CartItemModel, entity: CartItem) -> None:
        model.quantity = entity.quantity
