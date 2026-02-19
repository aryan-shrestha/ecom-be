"""SQLAlchemy implementation of ProductRepository."""

from typing import Optional
from uuid import UUID

from sqlalchemy import delete, func, or_, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.product import Product, ProductStatus
from app.domain.entities.product_image import ProductImage
from app.domain.entities.product_variant import ProductVariant
from app.domain.repositories.product_repository import ProductRepository
from app.domain.value_objects.slug import Slug
from app.infrastructure.db.sqlalchemy.models.product_category_model import ProductCategoryModel
from app.infrastructure.db.sqlalchemy.models.product_image_model import ProductImageModel
from app.infrastructure.db.sqlalchemy.models.product_model import ProductModel
from app.infrastructure.db.sqlalchemy.models.product_variant_model import ProductVariantModel
from app.infrastructure.mappers.product_mapper import ProductMapper
from app.infrastructure.mappers.variant_mapper import VariantMapper
from app.infrastructure.mappers.image_mapper import ImageMapper


class SqlAlchemyProductRepository(ProductRepository):
    """SQLAlchemy implementation of ProductRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, product_id: UUID) -> Optional[Product]:
        """Retrieve product by ID."""
        stmt = select(ProductModel).where(ProductModel.id == product_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return ProductMapper.to_entity(model) if model else None

    async def get_by_slug(self, slug: Slug) -> Optional[Product]:
        """Retrieve product by slug."""
        stmt = select(ProductModel).where(ProductModel.slug == str(slug))
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return ProductMapper.to_entity(model) if model else None

    async def exists_by_slug(self, slug: Slug) -> bool:
        """Check if product exists with given slug."""
        stmt = select(ProductModel.id).where(ProductModel.slug == str(slug))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def save(self, product: Product) -> Product:
        """Save new product."""
        model = ProductMapper.to_model(product)
        self.session.add(model)
        await self.session.flush()
        return ProductMapper.to_entity(model)

    async def update(self, product: Product) -> Product:
        """Update existing product."""
        stmt = select(ProductModel).where(ProductModel.id == product.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one()
        ProductMapper.update_model(model, product)
        await self.session.flush()
        return ProductMapper.to_entity(model)

    async def delete(self, product_id: UUID) -> None:
        """Delete product."""
        stmt = delete(ProductModel).where(ProductModel.id == product_id)
        await self.session.execute(stmt)
        await self.session.flush()

    async def list_paginated(
        self,
        offset: int,
        limit: int,
        status: Optional[ProductStatus] = None,
        category_id: Optional[UUID] = None,
        tag: Optional[str] = None,
        featured: Optional[bool] = None,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> tuple[list[Product], int]:
        """List products with pagination and filters."""
        # Build query
        query = select(ProductModel)

        # Apply filters
        filters = []
        if status is not None:
            filters.append(ProductModel.status == status.value)
        if featured is not None:
            filters.append(ProductModel.featured == featured)
        if tag is not None:
            filters.append(ProductModel.tags.contains([tag]))
        if category_id is not None:
            # Join with product_categories
            query = query.join(
                ProductCategoryModel,
                ProductCategoryModel.product_id == ProductModel.id,
            )
            filters.append(ProductCategoryModel.category_id == category_id)

        if filters:
            query = query.where(and_(*filters))

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.session.execute(count_query)
        total = count_result.scalar_one()

        # Apply sorting
        if sort_by == "created_at":
            sort_col = ProductModel.created_at
        elif sort_by == "sort_order":
            sort_col = ProductModel.sort_order
        else:
            sort_col = ProductModel.created_at

        if sort_desc:
            query = query.order_by(sort_col.desc())
        else:
            query = query.order_by(sort_col.asc())

        # Apply pagination
        query = query.offset(offset).limit(limit)

        # Execute
        result = await self.session.execute(query)
        models = result.scalars().all()

        products = [ProductMapper.to_entity(m) for m in models]
        return products, total

    # Variant operations

    async def get_variant_by_id(self, variant_id: UUID) -> Optional[ProductVariant]:
        """Retrieve variant by ID."""
        stmt = select(ProductVariantModel).where(ProductVariantModel.id == variant_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return VariantMapper.to_entity(model) if model else None

    async def get_variant_by_sku(self, sku: str) -> Optional[ProductVariant]:
        """Retrieve variant by SKU."""
        stmt = select(ProductVariantModel).where(ProductVariantModel.sku == sku)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return VariantMapper.to_entity(model) if model else None

    async def get_variants_for_product(self, product_id: UUID) -> list[ProductVariant]:
        """Get all variants for a product."""
        stmt = select(ProductVariantModel).where(ProductVariantModel.product_id == product_id)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [VariantMapper.to_entity(m) for m in models]

    async def save_variant(self, variant: ProductVariant) -> ProductVariant:
        """Save new variant."""
        model = VariantMapper.to_model(variant)
        self.session.add(model)
        await self.session.flush()
        return VariantMapper.to_entity(model)

    async def update_variant(self, variant: ProductVariant) -> ProductVariant:
        """Update existing variant."""
        stmt = select(ProductVariantModel).where(ProductVariantModel.id == variant.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one()
        VariantMapper.update_model(model, variant)
        await self.session.flush()
        return VariantMapper.to_entity(model)

    async def delete_variant(self, variant_id: UUID) -> None:
        """Delete variant."""
        stmt = delete(ProductVariantModel).where(ProductVariantModel.id == variant_id)
        await self.session.execute(stmt)
        await self.session.flush()

    # Image operations

    async def get_image_by_id(self, image_id: UUID) -> Optional[ProductImage]:
        """Retrieve image by ID."""
        stmt = select(ProductImageModel).where(ProductImageModel.id == image_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return ImageMapper.to_entity(model) if model else None

    async def get_images_for_product(self, product_id: UUID) -> list[ProductImage]:
        """Get all images for a product, ordered by position."""
        stmt = (
            select(ProductImageModel)
            .where(ProductImageModel.product_id == product_id)
            .order_by(ProductImageModel.position)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [ImageMapper.to_entity(m) for m in models]

    async def save_image(self, image: ProductImage) -> ProductImage:
        """Save new image."""
        model = ImageMapper.to_model(image)
        self.session.add(model)
        await self.session.flush()
        return ImageMapper.to_entity(model)

    async def update_image(self, image: ProductImage) -> ProductImage:
        """Update existing image."""
        stmt = select(ProductImageModel).where(ProductImageModel.id == image.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one()
        ImageMapper.update_model(model, image)
        await self.session.flush()
        return ImageMapper.to_entity(model)

    async def delete_image(self, image_id: UUID) -> None:
        """Delete image."""
        stmt = delete(ProductImageModel).where(ProductImageModel.id == image_id)
        await self.session.execute(stmt)
        await self.session.flush()

    async def reorder_images(self, product_id: UUID, image_positions: dict[UUID, int]) -> None:
        """Reorder product images."""
        for image_id, position in image_positions.items():
            stmt = select(ProductImageModel).where(ProductImageModel.id == image_id)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            if model and model.product_id == product_id:
                model.position = position
        await self.session.flush()

    # Category assignments

    async def get_category_ids_for_product(self, product_id: UUID) -> list[UUID]:
        """Get category IDs assigned to product."""
        stmt = select(ProductCategoryModel.category_id).where(
            ProductCategoryModel.product_id == product_id
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def assign_categories(self, product_id: UUID, category_ids: list[UUID]) -> None:
        """Assign categories to product (replaces existing)."""
        # Delete existing assignments
        stmt = delete(ProductCategoryModel).where(ProductCategoryModel.product_id == product_id)
        await self.session.execute(stmt)

        # Add new assignments
        for category_id in category_ids:
            assoc = ProductCategoryModel(product_id=product_id, category_id=category_id)
            self.session.add(assoc)

        await self.session.flush()
