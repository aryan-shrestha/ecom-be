"""Unit tests for upload product image use case."""

import io
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest
from PIL import Image

from app.application.dto.product_dto import ProductImageDTO, UploadProductImageRequest
from app.application.errors.app_errors import (
    ImageProcessingError,
    ImageUploadError,
    ResourceNotFoundError,
    ValidationError,
)
from app.application.ports.file_storage_port import ImageUploadResult
from app.application.use_cases.products.upload_product_image import (
    UploadProductImageUseCase,
)
from app.domain.entities.product import Product, ProductStatus
from app.domain.value_objects.slug import Slug


def create_test_image_bytes(width: int = 100, height: int = 100) -> bytes:
    """Create a test image as bytes."""
    img = Image.new('RGB', (width, height), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes.read()


@pytest.fixture
def mock_uow():
    """Create mock UnitOfWork."""
    uow = Mock()
    uow.products = Mock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock()
    uow.commit = AsyncMock()
    return uow


@pytest.fixture
def mock_file_storage():
    """Create mock FileStorage."""
    storage = Mock()
    storage.upload_image = AsyncMock()
    return storage


@pytest.fixture
def mock_clock():
    """Create mock Clock."""
    clock = Mock()
    clock.now = Mock(return_value=datetime(2024, 1, 1, 12, 0, 0))
    return clock


@pytest.fixture
def mock_audit_log():
    """Create mock AuditLog."""
    audit = Mock()
    audit.log_event = AsyncMock()
    return audit


@pytest.fixture
def mock_cache():
    """Create mock Cache."""
    cache = Mock()
    cache.delete = AsyncMock()
    cache.delete_pattern = AsyncMock()
    return cache


@pytest.fixture
def use_case(mock_uow, mock_file_storage, mock_clock, mock_audit_log, mock_cache):
    """Create UploadProductImageUseCase with mocks."""
    return UploadProductImageUseCase(
        uow=mock_uow,
        file_storage=mock_file_storage,
        clock=mock_clock,
        audit_log=mock_audit_log,
        cache=mock_cache,
        max_image_bytes=5 * 1024 * 1024,  # 5MB
    )


@pytest.mark.asyncio
async def test_upload_image_success(use_case, mock_uow, mock_file_storage, mock_audit_log):
    """Test successful image upload."""
    product_id = uuid.uuid4()
    user_id = uuid.uuid4()
    
    # Mock product exists
    product = Product(
        id=product_id,
        name="Test Product",
        slug=Slug("test-product"),
        status=ProductStatus.DRAFT,
        description_short=None,
        description_long=None,
        tags=[],
        featured=False,
        sort_order=0,
        created_at=datetime(2024, 1, 1),
        updated_at=datetime(2024, 1, 1),
        created_by=user_id,
        updated_by=None,
    )
    mock_uow.products.get_by_id = AsyncMock(return_value=product)
    mock_uow.products.get_images_for_product = AsyncMock(return_value=[])
    
    # Mock file storage upload
    upload_result = ImageUploadResult(
        url="https://res.cloudinary.com/test.jpg",
        public_id="products/test-id/image123",
        bytes_size=12345,
        width=800,
        height=600,
        format="jpg",
    )
    mock_file_storage.upload_image = AsyncMock(return_value=upload_result)
    
    # Mock save image
    mock_uow.products.save_image = AsyncMock(
        side_effect=lambda img: img  # Return the same image
    )
    
    # Create request
    image_bytes = create_test_image_bytes()
    request = UploadProductImageRequest(
        product_id=product_id,
        file_data=image_bytes,
        filename="test.png",
        content_type="image/png",
        alt_text="Test image",
        position=None,
        uploaded_by=user_id,
    )
    
    # Execute
    result = await use_case.execute(request)
    
    # Assert
    assert isinstance(result, ProductImageDTO)
    assert result.url == upload_result.url
    assert result.provider == "cloudinary"
    assert result.provider_public_id == upload_result.public_id
    assert result.bytes_size == upload_result.bytes_size
    assert result.width == upload_result.width
    assert result.height == upload_result.height
    
    # Verify storage upload was called
    mock_file_storage.upload_image.assert_called_once()
    
    # Verify audit log
    mock_audit_log.log_event.assert_called_once()


@pytest.mark.asyncio
async def test_upload_image_product_not_found(use_case, mock_uow):
    """Test upload fails when product doesn't exist."""
    product_id = uuid.uuid4()
    
    # Mock product not found
    mock_uow.products.get_by_id = AsyncMock(return_value=None)
    
    # Create request
    image_bytes = create_test_image_bytes()
    request = UploadProductImageRequest(
        product_id=product_id,
        file_data=image_bytes,
        filename="test.png",
        content_type="image/png",
        alt_text="Test image",
        position=None,
        uploaded_by=uuid.uuid4(),
    )
    
    # Execute and assert
    with pytest.raises(ResourceNotFoundError):
        await use_case.execute(request)


@pytest.mark.asyncio
async def test_upload_image_invalid_content_type(use_case, mock_uow):
    """Test upload fails with invalid content type."""
    product_id = uuid.uuid4()
    
    # Create request with invalid content type
    request = UploadProductImageRequest(
        product_id=product_id,
        file_data=b"some data",
        filename="test.txt",
        content_type="text/plain",
        alt_text=None,
        position=None,
        uploaded_by=uuid.uuid4(),
    )
    
    # Execute and assert
    with pytest.raises(ValidationError) as exc_info:
        await use_case.execute(request)
    
    assert "Invalid image format" in str(exc_info.value)


@pytest.mark.asyncio
async def test_upload_image_file_too_large(use_case, mock_uow):
    """Test upload fails when file is too large."""
    product_id = uuid.uuid4()
    
    # Create request with file larger than max
    large_data = b"x" * (6 * 1024 * 1024)  # 6MB (exceeds 5MB limit)
    request = UploadProductImageRequest(
        product_id=product_id,
        file_data=large_data,
        filename="test.png",
        content_type="image/png",
        alt_text=None,
        position=None,
        uploaded_by=uuid.uuid4(),
    )
    
    # Execute and assert
    with pytest.raises(ValidationError) as exc_info:
        await use_case.execute(request)
    
    assert "exceeds maximum" in str(exc_info.value)


@pytest.mark.asyncio
async def test_upload_image_corrupted_file(use_case, mock_uow):
    """Test upload fails with corrupted image data."""
    product_id = uuid.uuid4()
    user_id = uuid.uuid4()
    
    # Mock product exists
    product = Product(
        id=product_id,
        name="Test Product",
        slug=Slug("test-product"),
        status=ProductStatus.DRAFT,
        description_short=None,
        description_long=None,
        tags=[],
        featured=False,
        sort_order=0,
        created_at=datetime(2024, 1, 1),
        updated_at=datetime(2024, 1, 1),
        created_by=user_id,
        updated_by=None,
    )
    mock_uow.products.get_by_id = AsyncMock(return_value=product)
    
    # Create request with corrupted PNG data
    corrupted_data = b"fake png data"
    request = UploadProductImageRequest(
        product_id=product_id,
        file_data=corrupted_data,
        filename="test.png",
        content_type="image/png",
        alt_text=None,
        position=None,
        uploaded_by=user_id,
    )
    
    # Execute and assert
    with pytest.raises(ImageProcessingError):
        await use_case.execute(request)
