"""Get product storefront detail use case."""

from app.application.dto.product_dto import (
    ProductDetailResponse,
    ProductDTO,
    VariantDTO,
    ProductImageDTO,
    CategoryDTO,
    InventoryDTO,
    MoneyDTO,
)
from app.application.errors.app_errors import ResourceNotFoundError
from app.application.interfaces.uow import UnitOfWork
from app.application.ports.cache_port import CachePort
from app.domain.entities.product import ProductStatus
from app.domain.entities.product_variant import VariantStatus
import json


class GetProductStorefrontUseCase:
    """Use case for getting product detail (storefront - published only)."""

    def __init__(self, uow: UnitOfWork, cache: CachePort) -> None:
        self.uow = uow
        self.cache = cache

    async def execute(self, slug: str) -> ProductDetailResponse:
        """
        Get published product by slug with full details (storefront view).
        
        Only PUBLISHED products and ACTIVE variants visible.
        
        Raises:
            ResourceNotFoundError: If product not found or not published
        """
        # Try cache first
        cache_key = f"product:slug:{slug}"
        cached = await self.cache.get(cache_key)
        if cached:
            # Deserialize from cache (simplified - in production use proper serialization)
            pass  # For now, skip cache deserialization

        async with self.uow:
            # Get product by slug
            from app.domain.value_objects.slug import Slug
            product_slug = Slug(value=slug)
            product = await self.uow.products.get_by_slug(product_slug)
            
            if not product or product.status != ProductStatus.PUBLISHED:
                raise ResourceNotFoundError(f"Product '{slug}' not found")

            # Get active variants only
            all_variants = await self.uow.products.get_variants_for_product(product.id)
            variants = [v for v in all_variants if v.status == VariantStatus.ACTIVE]

            # Get images
            images = await self.uow.products.get_images_for_product(product.id)

            # Get categories
            category_ids = await self.uow.products.get_category_ids_for_product(product.id)
            categories = []
            for cat_id in category_ids:
                cat = await self.uow.categories.get_by_id(cat_id)
                if cat:
                    categories.append(cat)

            # Get inventory for active variants
            inventory_map = {}
            for variant in variants:
                inv = await self.uow.inventory.get_by_variant_id(variant.id)
                if inv:
                    inventory_map[variant.id] = InventoryDTO(
                        variant_id=inv.variant_id,
                        on_hand=inv.on_hand,
                        reserved=inv.reserved,
                        allow_backorder=inv.allow_backorder,
                    )

            # Build response
            response = ProductDetailResponse(
                product=ProductDTO(
                    id=product.id,
                    status=product.status.value,
                    name=product.name,
                    slug=str(product.slug),
                    description_short=product.description_short,
                    description_long=product.description_long,
                    tags=product.tags,
                    featured=product.featured,
                    sort_order=product.sort_order,
                    created_at=product.created_at,
                    updated_at=product.updated_at,
                ),
                variants=[
                    VariantDTO(
                        id=v.id,
                        product_id=v.product_id,
                        sku=str(v.sku),
                        barcode=v.barcode,
                        status=v.status.value,
                        price=MoneyDTO(amount=v.price.amount, currency=v.price.currency),
                        compare_at_price=(
                            MoneyDTO(amount=v.compare_at_price.amount, currency=v.compare_at_price.currency)
                            if v.compare_at_price
                            else None
                        ),
                        cost=None,  # Hide cost from storefront
                        weight=v.weight,
                        length=v.length,
                        width=v.width,
                        height=v.height,
                        is_default=v.is_default,
                        created_at=v.created_at,
                        updated_at=v.updated_at,
                    )
                    for v in variants
                ],
                images=[
                    ProductImageDTO(
                        id=img.id,
                        product_id=img.product_id,
                        url=img.url,
                        alt_text=img.alt_text,
                        position=img.position,
                        created_at=img.created_at,
                    )
                    for img in images
                ],
                categories=[
                    CategoryDTO(
                        id=cat.id,
                        name=cat.name,
                        slug=str(cat.slug),
                        parent_id=cat.parent_id,
                    )
                    for cat in categories
                ],
                inventory_map=inventory_map,
            )

            # Cache response (TTL 5 minutes)
            # await self.cache.set(cache_key, serialize(response), ttl=300)

            return response
