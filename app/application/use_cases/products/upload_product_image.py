"""Upload product image use case."""

import io
import uuid

from PIL import Image, UnidentifiedImageError

from app.application.dto.product_dto import ProductImageDTO, UploadProductImageRequest
from app.application.errors.app_errors import (
    ImageProcessingError,
    ImageUploadError,
    ResourceNotFoundError,
    ValidationError,
)
from app.application.interfaces.uow import UnitOfWork
from app.application.ports.audit_log_port import AuditLogPort
from app.application.ports.cache_port import CachePort
from app.application.ports.clock_port import ClockPort
from app.application.ports.file_storage_port import FileStoragePort
from app.domain.entities.product_image import ProductImage
from app.domain.errors.domain_errors import InvalidImageFormatError, ImageTooLargeError


class UploadProductImageUseCase:
    """Use case for uploading an image to a product via cloud storage."""

    # Allowed MIME types
    ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

    def __init__(
        self,
        uow: UnitOfWork,
        file_storage: FileStoragePort,
        clock: ClockPort,
        audit_log: AuditLogPort,
        cache: CachePort,
        max_image_bytes: int,
    ) -> None:
        self.uow = uow
        self.file_storage = file_storage
        self.clock = clock
        self.audit_log = audit_log
        self.cache = cache
        self.max_image_bytes = max_image_bytes

    async def execute(self, request: UploadProductImageRequest) -> ProductImageDTO:
        """
        Upload image for product.
        
        Validates:
        - Product exists
        - Content-Type is allowed
        - File size is within limit
        - Image bytes are valid (checks magic bytes)
        
        Then:
        - Uploads to cloud storage
        - Persists DB record with metadata
        - Invalidates caches
        - Emits audit event
        
        Raises:
            ResourceNotFoundError: If product not found
            ValidationError: If validation fails
            ImageUploadError: If upload fails
        """
        # Validate content type
        if request.content_type not in self.ALLOWED_MIME_TYPES:
            raise ValidationError(
                f"Invalid image format. Allowed: {', '.join(self.ALLOWED_MIME_TYPES)}"
            )

        # Validate file size
        if len(request.file_data) > self.max_image_bytes:
            max_mb = self.max_image_bytes / (1024 * 1024)
            raise ValidationError(f"Image size exceeds maximum of {max_mb:.1f}MB")

        # Validate image bytes using Pillow (checks magic bytes and format)
        try:
            img = Image.open(io.BytesIO(request.file_data))
            detected_format = img.format.lower() if img.format else None
            if detected_format not in {"jpeg", "png", "webp"}:
                raise ImageProcessingError(
                    f"Unsupported image format: {detected_format}. Allowed: JPEG, PNG, WEBP"
                )
        except UnidentifiedImageError:
            raise ImageProcessingError("Invalid or corrupted image file")
        except Exception as e:
            raise ImageProcessingError(f"Failed to process image: {str(e)}")

        async with self.uow:
            # Check product exists
            product = await self.uow.products.get_by_id(request.product_id)
            if not product:
                raise ResourceNotFoundError(f"Product {request.product_id} not found")

            # Get existing images to determine position
            existing_images = await self.uow.products.get_images_for_product(request.product_id)
            
            # Determine position
            if request.position is not None:
                position = request.position
            else:
                position = len(existing_images)

            # Upload to cloud storage
            try:
                upload_result = await self.file_storage.upload_image(
                    file_data=request.file_data,
                    filename=request.filename,
                    folder=f"products/{request.product_id}",
                    content_type=request.content_type,
                )
            except Exception as e:
                raise ImageUploadError(f"Failed to upload image: {str(e)}")

            # Create image entity
            now = self.clock.now()
            image = ProductImage(
                id=uuid.uuid4(),
                product_id=request.product_id,
                url=upload_result.url,
                alt_text=request.alt_text,
                position=position,
                created_at=now,
                provider="cloudinary",
                provider_public_id=upload_result.public_id,
                bytes_size=upload_result.bytes_size,
                width=upload_result.width,
                height=upload_result.height,
                format=upload_result.format,
            )

            # Save image
            image = await self.uow.products.save_image(image)
            await self.uow.commit()

            # Invalidate caches
            await self.cache.delete(f"product:{request.product_id}")
            await self.cache.delete(f"product:slug:{product.slug}")
            await self.cache.delete_pattern("products:storefront:*")

            # Audit log
            await self.audit_log.log_event(
                event_type="product.image.uploaded",
                user_id=request.uploaded_by,
                details={
                    "product_id": str(request.product_id),
                    "image_id": str(image.id),
                    "url": image.url,
                    "provider": image.provider,
                    "bytes": image.bytes_size,
                },
            )

            return ProductImageDTO(
                id=image.id,
                product_id=image.product_id,
                url=image.url,
                alt_text=image.alt_text,
                position=image.position,
                created_at=image.created_at,
                provider=image.provider,
                provider_public_id=image.provider_public_id,
                bytes_size=image.bytes_size,
                width=image.width,
                height=image.height,
                format=image.format,
            )
