"""Product DTOs."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass
class MoneyDTO:
    """Money data transfer object."""

    amount: int  # Minor units (cents)
    currency: str


@dataclass
class ProductDTO:
    """Product data transfer object."""

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


@dataclass
class VariantDTO:
    """Product variant data transfer object."""

    id: UUID
    product_id: UUID
    sku: str
    barcode: Optional[str]
    status: str
    price: MoneyDTO
    compare_at_price: Optional[MoneyDTO]
    cost: Optional[MoneyDTO]
    weight: Optional[int]
    length: Optional[int]
    width: Optional[int]
    height: Optional[int]
    is_default: bool
    created_at: datetime
    updated_at: datetime


@dataclass
class CategoryDTO:
    """Category data transfer object."""

    id: UUID
    name: str
    slug: str
    parent_id: Optional[UUID]


@dataclass
class InventoryDTO:
    """Inventory data transfer object."""

    variant_id: UUID
    on_hand: int
    reserved: int
    allow_backorder: bool


@dataclass
class StockMovementDTO:
    """Stock movement data transfer object."""

    id: UUID
    variant_id: UUID
    delta: int
    reason: str
    note: Optional[str]
    created_at: datetime
    created_by: Optional[UUID]


@dataclass
class ProductImageDTO:
    """Product image data transfer object."""

    id: UUID
    product_id: UUID
    url: str
    alt_text: Optional[str]
    position: int
    created_at: datetime


# Request DTOs


@dataclass
class CreateProductRequest:
    """Request to create product."""

    name: str
    slug: str
    description_short: Optional[str] = None
    description_long: Optional[str] = None
    tags: list[str] = None
    featured: bool = False
    sort_order: int = 0
    created_by: Optional[UUID] = None

    def __post_init__(self) -> None:
        """Set defaults."""
        if self.tags is None:
            self.tags = []


@dataclass
class UpdateProductRequest:
    """Request to update product."""

    product_id: UUID
    name: str
    description_short: Optional[str]
    description_long: Optional[str]
    tags: list[str]
    featured: bool
    sort_order: int
    updated_by: Optional[UUID] = None


@dataclass
class CreateVariantRequest:
    """Request to create variant."""

    product_id: UUID
    sku: str
    barcode: Optional[str]
    price_amount: int
    price_currency: str
    compare_at_price_amount: Optional[int] = None
    compare_at_price_currency: Optional[str] = None
    cost_amount: Optional[int] = None
    cost_currency: Optional[str] = None
    weight: Optional[int] = None
    length: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    is_default: bool = False
    initial_stock: int = 0
    allow_backorder: bool = False


@dataclass
class UpdateVariantRequest:
    """Request to update variant."""

    variant_id: UUID
    barcode: Optional[str]
    status: str
    price_amount: int
    price_currency: str
    compare_at_price_amount: Optional[int]
    compare_at_price_currency: Optional[str]
    cost_amount: Optional[int]
    cost_currency: Optional[str]
    weight: Optional[int]
    length: Optional[int]
    width: Optional[int]
    height: Optional[int]


@dataclass
class AdjustStockRequest:
    """Request to adjust stock."""

    variant_id: UUID
    delta: int
    reason: str
    note: Optional[str] = None
    created_by: Optional[UUID] = None


@dataclass
class AddProductImageRequest:
    """Request to add product image."""

    product_id: UUID
    url: str
    alt_text: Optional[str] = None


@dataclass
class ReorderImagesRequest:
    """Request to reorder images."""

    product_id: UUID
    image_positions: dict[UUID, int]  # image_id -> position


@dataclass
class AssignCategoriesRequest:
    """Request to assign categories to product."""

    product_id: UUID
    category_ids: list[UUID]


@dataclass
class CreateCategoryRequest:
    """Request to create category."""

    name: str
    slug: str
    parent_id: Optional[UUID] = None


@dataclass
class UpdateCategoryRequest:
    """Request to update category."""

    category_id: UUID
    name: str
    parent_id: Optional[UUID]


# Response DTOs


@dataclass
class ProductDetailResponse:
    """Detailed product response with variants, images, categories."""

    product: ProductDTO
    variants: list[VariantDTO]
    images: list[ProductImageDTO]
    categories: list[CategoryDTO]
    inventory_map: dict[UUID, InventoryDTO]  # variant_id -> inventory


@dataclass
class ProductListResponse:
    """Paginated product list response."""

    products: list[ProductDTO]
    total: int
    offset: int
    limit: int


@dataclass
class StorefrontProductDTO:
    """Storefront product DTO (limited fields)."""

    id: UUID
    slug: str
    name: str
    description_short: Optional[str]
    description_long: Optional[str]
    tags: list[str]
    featured: bool
