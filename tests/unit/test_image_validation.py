"""Test image format detection using Pillow (replaces imghdr)."""

import io

import pytest
from PIL import Image

from app.application.errors.app_errors import ImageProcessingError


def validate_image_format(file_data: bytes, allowed_formats: set[str]) -> str:
    """
    Validate image format from bytes using Pillow.
    
    Args:
        file_data: Image file bytes
        allowed_formats: Set of allowed format names (lowercase)
        
    Returns:
        Detected format (lowercase)
        
    Raises:
        ImageProcessingError: If invalid/corrupted or unsupported format
    """
    from PIL import UnidentifiedImageError
    
    try:
        img = Image.open(io.BytesIO(file_data))
        detected_format = img.format.lower() if img.format else None
        if detected_format not in allowed_formats:
            raise ImageProcessingError(
                f"Unsupported image format: {detected_format}. Allowed: {', '.join(allowed_formats).upper()}"
            )
        return detected_format
    except UnidentifiedImageError:
        raise ImageProcessingError("Invalid or corrupted image file")
    except ImageProcessingError:
        raise
    except Exception as e:
        raise ImageProcessingError(f"Failed to process image: {str(e)}")


# Test data: minimal valid image headers
PNG_HEADER = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde'
JPEG_HEADER = b'\xff\xd8\xff\xe0\x00\x10JFIF'
WEBP_HEADER = b'RIFF\x00\x00\x00\x00WEBPVP8 '
GIF_HEADER = b'GIF89a'


def create_test_image(format: str, width: int = 10, height: int = 10) -> bytes:
    """Create a valid test image."""
    img = Image.new('RGB', (width, height), color='red')
    buf = io.BytesIO()
    img.save(buf, format=format.upper())
    return buf.getvalue()


@pytest.mark.parametrize("format_name,expected", [
    ("png", "png"),
    ("jpeg", "jpeg"),
    ("webp", "webp"),
])
def test_validate_supported_formats(format_name, expected):
    """Test detection of supported formats."""
    image_bytes = create_test_image(format_name)
    result = validate_image_format(image_bytes, {"jpeg", "png", "webp"})
    assert result == expected


def test_validate_unsupported_format():
    """Test rejection of unsupported format (GIF)."""
    gif_bytes = create_test_image("gif")
    
    with pytest.raises(ImageProcessingError) as exc_info:
        validate_image_format(gif_bytes, {"jpeg", "png", "webp"})
    
    assert "Unsupported image format" in str(exc_info.value)


def test_validate_corrupted_image():
    """Test rejection of corrupted image data."""
    corrupted = b"not an image at all"
    
    with pytest.raises(ImageProcessingError) as exc_info:
        validate_image_format(corrupted, {"jpeg", "png", "webp"})
    
    assert "Invalid or corrupted" in str(exc_info.value)


def test_validate_truncated_image():
    """Test rejection of truncated image (incomplete header)."""
    truncated = PNG_HEADER[:10]  # Only first 10 bytes
    
    with pytest.raises(ImageProcessingError):
        validate_image_format(truncated, {"jpeg", "png", "webp"})


def test_validate_empty_data():
    """Test rejection of empty data."""
    with pytest.raises(ImageProcessingError):
        validate_image_format(b"", {"jpeg", "png", "webp"})
