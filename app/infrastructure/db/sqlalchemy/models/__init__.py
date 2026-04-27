"""SQLAlchemy models package.

Import all models here so Alembic can reliably register metadata.
"""

from app.infrastructure.db.sqlalchemy.models.cart_item_model import CartItemModel
from app.infrastructure.db.sqlalchemy.models.cart_model import CartModel
from app.infrastructure.db.sqlalchemy.models.category_model import CategoryModel
from app.infrastructure.db.sqlalchemy.models.color_model import ColorModel
from app.infrastructure.db.sqlalchemy.models.idempotency_key_model import IdempotencyKeyModel
from app.infrastructure.db.sqlalchemy.models.inventory_model import InventoryModel
from app.infrastructure.db.sqlalchemy.models.order_item_model import OrderItemModel
from app.infrastructure.db.sqlalchemy.models.order_model import OrderModel
from app.infrastructure.db.sqlalchemy.models.permission_model import PermissionModel
from app.infrastructure.db.sqlalchemy.models.product_category_model import ProductCategoryModel
from app.infrastructure.db.sqlalchemy.models.product_image_model import ProductImageModel
from app.infrastructure.db.sqlalchemy.models.product_model import ProductModel
from app.infrastructure.db.sqlalchemy.models.product_variant_model import ProductVariantModel
from app.infrastructure.db.sqlalchemy.models.refresh_token_model import RefreshTokenModel
from app.infrastructure.db.sqlalchemy.models.role_model import RoleModel
from app.infrastructure.db.sqlalchemy.models.role_permission_model import RolePermissionModel
from app.infrastructure.db.sqlalchemy.models.size_model import SizeModel
from app.infrastructure.db.sqlalchemy.models.stock_movement_model import StockMovementModel
from app.infrastructure.db.sqlalchemy.models.user_model import UserModel
from app.infrastructure.db.sqlalchemy.models.user_role_model import UserRoleModel
from app.infrastructure.db.sqlalchemy.models.variant_image_model import VariantImageModel

__all__ = [
    "CartItemModel",
    "CartModel",
    "CategoryModel",
    "ColorModel",
    "IdempotencyKeyModel",
    "InventoryModel",
    "OrderItemModel",
    "OrderModel",
    "PermissionModel",
    "ProductCategoryModel",
    "ProductImageModel",
    "ProductModel",
    "ProductVariantModel",
    "RefreshTokenModel",
    "RoleModel",
    "RolePermissionModel",
    "SizeModel",
    "StockMovementModel",
    "UserModel",
    "UserRoleModel",
    "VariantImageModel",
]
