"""Dependency injection container for FastAPI."""

from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces.uow import UnitOfWork
from app.application.ports.audit_log_port import AuditLogPort
from app.application.ports.cache_port import CachePort
from app.application.ports.clock_port import ClockPort
from app.application.ports.crypto_port import PasswordHasherPort, TokenHasherPort
from app.application.ports.file_storage_port import FileStoragePort
from app.application.ports.jwt_port import JwtPort
from app.application.use_cases.auth.change_password import ChangePasswordUseCase
from app.application.use_cases.auth.login import LoginUseCase
from app.application.use_cases.auth.logout import LogoutUseCase
from app.application.use_cases.auth.logout_all import LogoutAllUseCase
from app.application.use_cases.auth.refresh import RefreshUseCase
from app.application.use_cases.auth.register import RegisterUseCase
from app.application.use_cases.rbac.assign_role import AssignRoleUseCase
from app.application.use_cases.rbac.check_permission import CheckPermissionUseCase
from app.application.use_cases.products.create_product import CreateProductUseCase
from app.application.use_cases.products.update_product import UpdateProductUseCase
from app.application.use_cases.products.publish_product import PublishProductUseCase
from app.application.use_cases.products.archive_product import ArchiveProductUseCase
from app.application.use_cases.products.add_variant import AddVariantUseCase
from app.application.use_cases.products.update_variant import UpdateVariantUseCase
from app.application.use_cases.products.deactivate_variant import DeactivateVariantUseCase
from app.application.use_cases.products.adjust_stock import AdjustStockUseCase
from app.application.use_cases.products.add_product_image import AddProductImageUseCase
from app.application.use_cases.products.upload_product_image import UploadProductImageUseCase
from app.application.use_cases.products.upload_variant_image import UploadVariantImageUseCase
from app.application.use_cases.products.remove_product_image import RemoveProductImageUseCase
from app.application.use_cases.products.reorder_product_images import ReorderProductImagesUseCase
from app.application.use_cases.products.assign_categories import AssignCategoriesUseCase
from app.application.use_cases.products.get_product_admin import GetProductAdminUseCase
from app.application.use_cases.products.list_products_admin import ListProductsAdminUseCase
from app.application.use_cases.products.get_product_storefront import GetProductStorefrontUseCase
from app.application.use_cases.products.list_products_storefront import ListProductsStorefrontUseCase
from app.application.use_cases.categories.create_category import CreateCategoryUseCase
from app.application.use_cases.categories.list_categories import ListCategoriesUseCase
from app.infrastructure.caching.memory_cache import MemoryCache
from app.infrastructure.caching.system_clock import SystemClock
from app.infrastructure.observability.audit_logger import StructuredAuditLogger
from app.infrastructure.security.jwt_service import JwtService
from app.infrastructure.storage.cloudinary_storage import CloudinaryStorage
from app.infrastructure.storage.local_file_storage import LocalFileStorage
from app.infrastructure.security.password_hasher import Argon2PasswordHasher
from app.infrastructure.security.token_hasher import HmacTokenHasher
from app.infrastructure.uow.sqlalchemy_uow import SqlAlchemyUnitOfWork
from config.settings import settings


class Container:
    """Dependency injection container."""

    def __init__(self) -> None:
        # Ports (singletons)
        self._clock: ClockPort = SystemClock()
        self._password_hasher: PasswordHasherPort = Argon2PasswordHasher()
        self._token_hasher: TokenHasherPort = HmacTokenHasher(
            settings.refresh_token_hmac_secret
        )
        self._jwt_service: JwtPort = JwtService(
            private_key=settings.get_jwt_private_key(),
            public_key=settings.get_jwt_public_key(),
            algorithm=settings.jwt_algorithm,
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            kid=settings.jwt_active_kid,
            access_token_ttl_minutes=settings.jwt_access_token_ttl_minutes)

        # File storage - Use Cloudinary if configured, otherwise local
        if settings.cloudinary_url:
            self._file_storage: FileStoragePort = CloudinaryStorage(
                cloudinary_url=settings.cloudinary_url,
                folder_prefix=settings.cloudinary_folder_prefix,
            )
        else:
            # Fallback to local storage (for development/testing)
            self._file_storage: FileStoragePort = LocalFileStorage(
                base_path="./storage/uploads",
                base_url="/storage/uploads",
            )
            clock=self._clock,
        
        self._audit_log: AuditLogPort = StructuredAuditLogger()
        self._cache: CachePort = MemoryCache()

    def get_password_hasher(self) -> PasswordHasherPort:
        """Get password hasher."""
        return self._password_hasher

    def get_token_hasher(self) -> TokenHasherPort:
        """Get token hasher."""
        return self._token_hasher

    def get_jwt_service(self) -> JwtPort:
        """Get JWT service."""
        return self._jwt_service

    def get_clock(self) -> ClockPort:
        """Get clock."""
        return self._clock

    def get_audit_log(self) -> AuditLogPort:
        """Get audit logger."""
        return self._audit_log

    def get_cache(self) -> CachePort:
        """Get cache."""
        return self._cache

    def get_file_storage(self) -> FileStoragePort:
        """Get file storage."""
        return self._file_storage

    def get_uow(self, session: AsyncSession) -> UnitOfWork:
        """Get Unit of Work."""
        return SqlAlchemyUnitOfWork(session)

    # Use cases
    def get_register_use_case(self, session: AsyncSession) -> RegisterUseCase:
        """Get RegisterUseCase."""
        return RegisterUseCase(
            uow=self.get_uow(session),
            password_hasher=self._password_hasher,
            clock=self._clock,
            audit_log=self._audit_log,
        )

    def get_login_use_case(self, session: AsyncSession) -> LoginUseCase:
        """Get LoginUseCase."""
        return LoginUseCase(
            uow=self.get_uow(session),
            password_hasher=self._password_hasher,
            token_hasher=self._token_hasher,
            jwt_service=self._jwt_service,
            clock=self._clock,
            audit_log=self._audit_log,
            refresh_token_ttl_days=settings.refresh_token_ttl_days,
        )

    def get_refresh_use_case(self, session: AsyncSession) -> RefreshUseCase:
        """Get RefreshUseCase."""
        return RefreshUseCase(
            uow=self.get_uow(session),
            token_hasher=self._token_hasher,
            jwt_service=self._jwt_service,
            clock=self._clock,
            audit_log=self._audit_log,
            refresh_token_ttl_days=settings.refresh_token_ttl_days,
        )

    def get_logout_use_case(self, session: AsyncSession) -> LogoutUseCase:
        """Get LogoutUseCase."""
        return LogoutUseCase(
            uow=self.get_uow(session),
            token_hasher=self._token_hasher,
            clock=self._clock,
            audit_log=self._audit_log,
        )

    def get_logout_all_use_case(self, session: AsyncSession) -> LogoutAllUseCase:
        """Get LogoutAllUseCase."""
        return LogoutAllUseCase(
            uow=self.get_uow(session),
            clock=self._clock,
            audit_log=self._audit_log,
        )

    def get_change_password_use_case(self, session: AsyncSession) -> ChangePasswordUseCase:
        """Get ChangePasswordUseCase."""
        return ChangePasswordUseCase(
            uow=self.get_uow(session),
            password_hasher=self._password_hasher,
            clock=self._clock,
            audit_log=self._audit_log,
        )

    def get_check_permission_use_case(self, session: AsyncSession) -> CheckPermissionUseCase:
        """Get CheckPermissionUseCase."""
        return CheckPermissionUseCase(
            uow=self.get_uow(session),
            cache=self._cache,
        )

    def get_assign_role_use_case(self, session: AsyncSession) -> AssignRoleUseCase:
        """Get AssignRoleUseCase."""
        return AssignRoleUseCase(
            uow=self.get_uow(session),
            audit_log=self._audit_log,
        )

    # Product use cases

    def get_create_product_use_case(self, session: AsyncSession) -> CreateProductUseCase:
        """Get CreateProductUseCase."""
        return CreateProductUseCase(
            uow=self.get_uow(session),
            clock=self._clock,
            audit_log=self._audit_log,
        )

    def get_update_product_use_case(self, session: AsyncSession) -> UpdateProductUseCase:
        """Get UpdateProductUseCase."""
        return UpdateProductUseCase(
            uow=self.get_uow(session),
            clock=self._clock,
            audit_log=self._audit_log,
        )

    def get_publish_product_use_case(self, session: AsyncSession) -> PublishProductUseCase:
        """Get PublishProductUseCase."""
        return PublishProductUseCase(
            uow=self.get_uow(session),
            clock=self._clock,
            audit_log=self._audit_log,
            cache=self._cache,
        )

    def get_archive_product_use_case(self, session: AsyncSession) -> ArchiveProductUseCase:
        """Get ArchiveProductUseCase."""
        return ArchiveProductUseCase(
            uow=self.get_uow(session),
            clock=self._clock,
            audit_log=self._audit_log,
            cache=self._cache,
        )

    def get_add_variant_use_case(self, session: AsyncSession) -> AddVariantUseCase:
        """Get AddVariantUseCase."""
        return AddVariantUseCase(
            uow=self.get_uow(session),
            clock=self._clock,
            audit_log=self._audit_log,
        )

    def get_update_variant_use_case(self, session: AsyncSession) -> UpdateVariantUseCase:
        """Get UpdateVariantUseCase."""
        return UpdateVariantUseCase(
            uow=self.get_uow(session),
            clock=self._clock,
            audit_log=self._audit_log,
            cache=self._cache,
        )

    def get_deactivate_variant_use_case(self, session: AsyncSession) -> DeactivateVariantUseCase:
        """Get DeactivateVariantUseCase."""
        return DeactivateVariantUseCase(
            uow=self.get_uow(session),
            clock=self._clock,
            audit_log=self._audit_log,
            cache=self._cache,
        )

    def get_adjust_stock_use_case(self, session: AsyncSession) -> AdjustStockUseCase:
        """Get AdjustStockUseCase."""
        return AdjustStockUseCase(
            uow=self.get_uow(session),
            clock=self._clock,
            audit_log=self._audit_log,
            cache=self._cache,
        )

    def get_add_product_image_use_case(self, session: AsyncSession) -> AddProductImageUseCase:
        """Get AddProductImageUseCase."""
        return AddProductImageUseCase(
            uow=self.get_uow(session),
            clock=self._clock,
            audit_log=self._audit_log,
            cache=self._cache,
        )

    def get_upload_product_image_use_case(self, session: AsyncSession) -> UploadProductImageUseCase:
        """Get UploadProductImageUseCase."""
        return UploadProductImageUseCase(
            uow=self.get_uow(session),
            file_storage=self._file_storage,
            clock=self._clock,
            audit_log=self._audit_log,
            cache=self._cache,
            max_image_bytes=settings.max_image_bytes,
        )

    def get_upload_variant_image_use_case(self, session: AsyncSession) -> UploadVariantImageUseCase:
        """Get UploadVariantImageUseCase."""
        return UploadVariantImageUseCase(
            uow=self.get_uow(session),
            file_storage=self._file_storage,
            clock=self._clock,
            audit_log=self._audit_log,
            cache=self._cache,
            max_image_bytes=settings.max_image_bytes,
        )

    def get_remove_product_image_use_case(self, session: AsyncSession) -> RemoveProductImageUseCase:
        """Get RemoveProductImageUseCase."""
        return RemoveProductImageUseCase(
            uow=self.get_uow(session),
            audit_log=self._audit_log,
            cache=self._cache,
        )

    def get_reorder_product_images_use_case(self, session: AsyncSession) -> ReorderProductImagesUseCase:
        """Get ReorderProductImagesUseCase."""
        return ReorderProductImagesUseCase(
            uow=self.get_uow(session),
            audit_log=self._audit_log,
            cache=self._cache,
        )

    def get_assign_categories_use_case(self, session: AsyncSession) -> AssignCategoriesUseCase:
        """Get AssignCategoriesUseCase."""
        return AssignCategoriesUseCase(
            uow=self.get_uow(session),
            audit_log=self._audit_log,
            cache=self._cache,
        )

    def get_get_product_admin_use_case(self, session: AsyncSession) -> GetProductAdminUseCase:
        """Get GetProductAdminUseCase."""
        return GetProductAdminUseCase(
            uow=self.get_uow(session),
        )

    def get_list_products_admin_use_case(self, session: AsyncSession) -> ListProductsAdminUseCase:
        """Get ListProductsAdminUseCase."""
        return ListProductsAdminUseCase(
            uow=self.get_uow(session),
        )

    def get_get_product_storefront_use_case(self, session: AsyncSession) -> GetProductStorefrontUseCase:
        """Get GetProductStorefrontUseCase."""
        return GetProductStorefrontUseCase(
            uow=self.get_uow(session),
            cache=self._cache,
        )

    def get_list_products_storefront_use_case(self, session: AsyncSession) -> ListProductsStorefrontUseCase:
        """Get ListProductsStorefrontUseCase."""
        return ListProductsStorefrontUseCase(
            uow=self.get_uow(session),
            cache=self._cache,
        )

    # Category use cases

    def get_create_category_use_case(self, session: AsyncSession) -> CreateCategoryUseCase:
        """Get CreateCategoryUseCase."""
        return CreateCategoryUseCase(
            uow=self.get_uow(session),
            audit_log=self._audit_log,
        )

    def get_list_categories_use_case(self, session: AsyncSession) -> ListCategoriesUseCase:
        """Get ListCategoriesUseCase."""
        return ListCategoriesUseCase(
            uow=self.get_uow(session),
        )


@lru_cache
def get_container() -> Container:
    """Get singleton container instance."""
    return Container()
