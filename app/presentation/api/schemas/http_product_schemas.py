"""HTTP request/response schemas for product endpoints."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# Money schema


class MoneySchema(BaseModel):
    """Money representation."""

    amount: int = Field(..., description="Amount in minor units (cents)")
    currency: str = Field(..., min_length=3, max_length=3, description="ISO 4217 currency code")


# Product schemas


class CreateProductRequestSchema(BaseModel):
    """Request to create product."""

    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=200)
    description_short: Optional[str] = Field(None, max_length=500)
    description_long: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    featured: bool = False
    sort_order: int = Field(default=0, ge=0)


class UpdateProductRequestSchema(BaseModel):
    """Request to update product."""

    name: str = Field(..., min_length=1, max_length=255)
    description_short: Optional[str] = Field(None, max_length=500)
    description_long: Optional[str] = None
    tags: list[str]
    featured: bool
    sort_order: int = Field(..., ge=0)


class ProductResponseSchema(BaseModel):
    """Product response."""

    id: UUID
    status: str
    name: str
    slug: str
    description_short: Optional[str]
    description_long: Optional[str]
    tags: list[str]
    featured: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None


# Variant schemas


class CreateVariantRequestSchema(BaseModel):
    """Request to create variant."""

    sku: str = Field(..., min_length=1, max_length=100)
    barcode: Optional[str] = Field(None, max_length=100)
    price_amount: int = Field(..., gt=0)
    price_currency: str = Field(..., min_length=3, max_length=3)
    compare_at_price_amount: Optional[int] = Field(None, gt=0)
    compare_at_price_currency: Optional[str] = Field(None, min_length=3, max_length=3)
    cost_amount: Optional[int] = Field(None, gt=0)
    cost_currency: Optional[str] = Field(None, min_length=3, max_length=3)
    weight: Optional[int] = Field(None, ge=0)
    length: Optional[int] = Field(None, ge=0)
    width: Optional[int] = Field(None, ge=0)
    height: Optional[int] = Field(None, ge=0)
    is_default: bool = False
    initial_stock: int = Field(default=0, ge=0)
    allow_backorder: bool = False


class UpdateVariantRequestSchema(BaseModel):
    """Request to update variant."""

    barcode: Optional[str] = Field(None, max_length=100)
    status: str = Field(..., pattern="^(ACTIVE|INACTIVE)$")
    price_amount: int = Field(..., gt=0)
    price_currency: str = Field(..., min_length=3, max_length=3)
    compare_at_price_amount: Optional[int] = Field(None, gt=0)
    compare_at_price_currency: Optional[str] = Field(None, min_length=3, max_length=3)
    cost_amount: Optional[int] = Field(None, gt=0)
    cost_currency: Optional[str] = Field(None, min_length=3, max_length=3)
    weight: Optional[int] = Field(None, ge=0)
    length: Optional[int] = Field(None, ge=0)
    width: Optional[int] = Field(None, ge=0)
    height: Optional[int] = Field(None, ge=0)


class VariantResponseSchema(BaseModel):
    """Variant response."""

    id: UUID
    product_id: UUID
    sku: str
    barcode: Optional[str]
    status: str
    price: MoneySchema
    compare_at_price: Optional[MoneySchema]
    cost: Optional[MoneySchema]
    weight: Optional[int]
    length: Optional[int]
    width: Optional[int]
    height: Optional[int]
    is_default: bool
    created_at: datetime
    updated_at: datetime


# Inventory schemas


class InventoryResponseSchema(BaseModel):
    """Inventory response."""

    variant_id: UUID
    on_hand: int
    reserved: int
    allow_backorder: bool
    available: int  # Computed: on_hand - reserved


class AdjustStockRequestSchema(BaseModel):
    """Request to adjust stock."""

    delta: int = Field(..., description="Positive to add, negative to subtract")
    reason: str = Field(..., min_length=1, max_length=100)
    note: Optional[str] = Field(None, max_length=500)


class StockMovementResponseSchema(BaseModel):
    """Stock movement response."""

    id: UUID
    variant_id: UUID
    delta: int
    reason: str
    note: Optional[str]
    created_at: datetime
    created_by: Optional[UUID]


# Category schemas


class CreateCategoryRequestSchema(BaseModel):
    """Request to create category."""

    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=200)
    parent_id: Optional[UUID] = None


class UpdateCategoryRequestSchema(BaseModel):
    """Request to update category."""

    name: str = Field(..., min_length=1, max_length=100)
    parent_id: Optional[UUID] = None


class CategoryResponseSchema(BaseModel):
    """Category response."""

    id: UUID
    name: str
    slug: str
    parent_id: Optional[UUID]


# Image schemas


class AddProductImageRequestSchema(BaseModel):
    """Request to add product image."""

    url: str = Field(..., min_length=1, max_length=1000)
    alt_text: Optional[str] = Field(None, max_length=255)


class ProductImageResponseSchema(BaseModel):
    """Product image response."""

    id: UUID
    product_id: UUID
    url: str
    alt_text: Optional[str]
    position: int
    created_at: datetime
    provider: Optional[str] = None
    provider_public_id: Optional[str] = None
    bytes_size: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    format: Optional[str] = None


class VariantImageResponseSchema(BaseModel):
    """Variant image response."""

    id: UUID
    variant_id: UUID
    url: str
    alt_text: Optional[str]
    position: int
    created_at: datetime
    provider: Optional[str] = None
    provider_public_id: Optional[str] = None
    bytes_size: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    format: Optional[str] = None


class ReorderImagesRequestSchema(BaseModel):
    """Request to reorder images."""

    image_positions: dict[UUID, int] = Field(..., description="Map of image_id to position")


# Assignment schemas


class AssignCategoriesRequestSchema(BaseModel):
    """Request to assign categories."""

    category_ids: list[UUID]


# Detail response schemas


class ProductDetailResponseSchema(BaseModel):
    """Detailed product response with variants, images, and categories."""

    product: ProductResponseSchema
    variants: list[VariantResponseSchema]
    images: list[ProductImageResponseSchema]
    categories: list[CategoryResponseSchema]
    inventory: dict[UUID, InventoryResponseSchema]  # variant_id -> inventory


class ProductListResponseSchema(BaseModel):
    """Paginated product list response."""

    products: list[ProductResponseSchema]
    total: int
    offset: int
    limit: int


# Storefront schemas (simplified)


class StorefrontVariantResponseSchema(BaseModel):
    """Storefront variant response (no cost)."""

    id: UUID
    sku: str
    price: MoneySchema
    compare_at_price: Optional[MoneySchema]
    is_default: bool
    in_stock: bool


class StorefrontProductDetailResponseSchema(BaseModel):
    """Storefront product detail response."""

    id: UUID
    slug: str
    name: str
    description_short: Optional[str]
    description_long: Optional[str]
    tags: list[str]
    featured: bool
    variants: list[StorefrontVariantResponseSchema]
    images: list[ProductImageResponseSchema]
    categories: list[CategoryResponseSchema]


class StorefrontProductListItemSchema(BaseModel):
    """Storefront product list item."""

    id: UUID
    slug: str
    name: str
    description_short: Optional[str]
    tags: list[str]
    featured: bool


class StorefrontProductListResponseSchema(BaseModel):
    """Storefront product list response."""

    products: list[StorefrontProductListItemSchema]
    total: int
    offset: int
    limit: int
