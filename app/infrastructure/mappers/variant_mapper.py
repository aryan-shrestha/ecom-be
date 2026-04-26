"""Product variant mapper."""

from app.domain.entities.product_variant import ProductVariant, VariantStatus, Color
from app.domain.value_objects.money import Money
from app.domain.value_objects.sku import SKU
from app.infrastructure.db.sqlalchemy.models.product_variant_model import ProductVariantModel


class VariantMapper:
    """Mapper for ProductVariant entity and ProductVariantModel."""

    @staticmethod
    def to_entity(model: ProductVariantModel) -> ProductVariant:
        """Convert ORM model to domain entity."""
        price = Money(amount=model.price_amount, currency=model.price_currency)
        compare_at_price = (
            Money(amount=model.compare_at_price_amount, currency=model.compare_at_price_currency)
            if model.compare_at_price_amount is not None
            else None
        )
        cost = (
            Money(amount=model.cost_amount, currency=model.cost_currency)
            if model.cost_amount is not None
            else None
        )

        return ProductVariant(
            id=model.id,
            product_id=model.product_id,
            sku=SKU(value=model.sku),
            barcode=model.barcode,
            status=VariantStatus(model.status),
            price=price,
            compare_at_price=compare_at_price,
            cost=cost,
            color=Color(name=model.color["name"], hex_code=model.color.get("hex_code")) if model.color else None,
            size=model.size,
            is_default=model.is_default,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(entity: ProductVariant) -> ProductVariantModel:
        """Convert domain entity to ORM model."""
        return ProductVariantModel(
            id=entity.id,
            product_id=entity.product_id,
            sku=str(entity.sku),
            barcode=entity.barcode,
            status=entity.status.value,
            price_amount=entity.price.amount,
            price_currency=entity.price.currency,
            compare_at_price_amount=(
                entity.compare_at_price.amount if entity.compare_at_price else None
            ),
            compare_at_price_currency=(
                entity.compare_at_price.currency if entity.compare_at_price else None
            ),
            cost_amount=entity.cost.amount if entity.cost else None,
            cost_currency=entity.cost.currency if entity.cost else None,
            color={"name": entity.color.name, "hex_code": entity.color.hex_code} if entity.color else None,
            size=entity.size,
            is_default=entity.is_default,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    @staticmethod
    def update_model(model: ProductVariantModel, entity: ProductVariant) -> None:
        """Update existing ORM model from domain entity."""
        model.sku = str(entity.sku)
        model.barcode = entity.barcode
        model.status = entity.status.value
        model.price_amount = entity.price.amount
        model.price_currency = entity.price.currency
        model.compare_at_price_amount = (
            entity.compare_at_price.amount if entity.compare_at_price else None
        )
        model.compare_at_price_currency = (
            entity.compare_at_price.currency if entity.compare_at_price else None
        )
        model.cost_amount = entity.cost.amount if entity.cost else None
        model.cost_currency = entity.cost.currency if entity.cost else None
        model.color = {"name": entity.color.name, "hex_code": entity.color.hex_code} if entity.color else None
        model.size = entity.size
        model.is_default = entity.is_default
        model.updated_at = entity.updated_at
