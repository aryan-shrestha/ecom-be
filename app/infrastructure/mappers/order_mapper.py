"""Order and OrderItem mapper."""

from app.domain.entities.order import Order, OrderItem, OrderStatus
from app.domain.value_objects.money import Money
from app.infrastructure.db.sqlalchemy.models.order_item_model import OrderItemModel
from app.infrastructure.db.sqlalchemy.models.order_model import OrderModel


class OrderItemMapper:
    """Mapper for OrderItem entity and OrderItemModel."""

    @staticmethod
    def to_entity(model: OrderItemModel, order_id) -> OrderItem:
        return OrderItem(
            id=model.id,
            order_id=order_id,
            variant_id=model.variant_id,
            product_name=model.product_name,
            variant_sku=model.variant_sku,
            variant_label=model.variant_label,
            unit_price=Money(amount=model.unit_price_amount, currency=model.unit_price_currency),
            quantity=model.quantity,
        )

    @staticmethod
    def to_model(entity: OrderItem) -> OrderItemModel:
        return OrderItemModel(
            id=entity.id,
            order_id=entity.order_id,
            variant_id=entity.variant_id,
            product_name=entity.product_name,
            variant_sku=entity.variant_sku,
            variant_label=entity.variant_label,
            unit_price_amount=entity.unit_price.amount,
            unit_price_currency=entity.unit_price.currency,
            quantity=entity.quantity,
        )


class OrderMapper:
    """Mapper for Order entity and OrderModel."""

    @staticmethod
    def to_entity(model: OrderModel, items: tuple[OrderItem, ...] = ()) -> Order:
        return Order(
            id=model.id,
            order_number=model.order_number,
            status=OrderStatus(model.status),
            user_id=model.user_id,
            guest_token=model.guest_token,
            subtotal=Money(amount=model.subtotal_amount, currency=model.currency),
            grand_total=Money(amount=model.grand_total_amount, currency=model.currency),
            currency=model.currency,
            notes=model.notes,
            shipping_address=model.shipping_address,
            created_at=model.created_at,
            updated_at=model.updated_at,
            items=items,
        )

    @staticmethod
    def to_model(entity: Order) -> OrderModel:
        return OrderModel(
            id=entity.id,
            order_number=entity.order_number,
            status=entity.status.value,
            user_id=entity.user_id,
            guest_token=entity.guest_token,
            subtotal_amount=entity.subtotal.amount,
            grand_total_amount=entity.grand_total.amount,
            currency=entity.currency,
            notes=entity.notes,
            shipping_address=entity.shipping_address,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    @staticmethod
    def update_model(model: OrderModel, entity: Order) -> None:
        model.status = entity.status.value
        model.notes = entity.notes
        model.shipping_address = entity.shipping_address
        model.updated_at = entity.updated_at
