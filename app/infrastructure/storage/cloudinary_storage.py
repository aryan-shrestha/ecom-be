"""Cloudinary storage implementation."""

import io
from typing import Optional

import cloudinary
import cloudinary.uploader

from app.application.errors.app_errors import ImageUploadError
from app.application.ports.file_storage_port import FileStoragePort, ImageUploadResult


class CloudinaryStorage(FileStoragePort):
    """Cloudinary cloud storage implementation."""

    def __init__(self, cloudinary_url: str, folder_prefix: str = "") -> None:
        """
        Initialize Cloudinary storage.
        
        Args:
            cloudinary_url: Cloudinary URL (cloudinary://API_KEY:API_SECRET@CLOUD_NAME)
            folder_prefix: Optional folder prefix for all uploads
        """
        self.folder_prefix = folder_prefix.strip("/")
        # Configure cloudinary from URL
        cloudinary.config(cloudinary_url=cloudinary_url)

    async def save_file(self, file: io.BytesIO, filename: str, folder: str = "") -> str:
        """
        Save file to Cloudinary (simple upload).
        
        Note: This is a basic implementation. For images, use upload_image instead.
        """
        try:
            folder_path = self._build_folder_path(folder)
            result = cloudinary.uploader.upload(
                file,
                folder=folder_path,
                resource_type="auto",
            )
            return result.get("secure_url", result["url"])
        except Exception as e:
            raise ImageUploadError(f"Failed to upload file: {str(e)}")

    async def upload_image(
        self,
        file_data: bytes,
        filename: str,
        folder: str = "",
        content_type: Optional[str] = None,
    ) -> ImageUploadResult:
        """
        Upload image to Cloudinary with metadata extraction.
        
        Args:
            file_data: Image file bytes
            filename: Original filename
            folder: Folder to store in (will be prefixed with folder_prefix)
            content_type: MIME type (unused, Cloudinary auto-detects)
            
        Returns:
            ImageUploadResult with URL and metadata
        """
        try:
            # Build folder path
            folder_path = self._build_folder_path(folder)

            # Upload to Cloudinary
            result = cloudinary.uploader.upload(
                file_data,
                folder=folder_path,
                resource_type="image",
                format=None,  # Auto-detect
                quality="auto",
            )

            # Extract metadata (Cloudinary provides most of this)
            return ImageUploadResult(
                url=result["secure_url"],
                public_id=result["public_id"],
                bytes_size=result["bytes"],
                width=result["width"],
                height=result["height"],
                format=result["format"],
            )

        except cloudinary.exceptions.Error as e:
            raise ImageUploadError(f"Cloudinary upload failed: {str(e)}")
        except Exception as e:
            raise ImageUploadError(f"Image upload failed: {str(e)}")

    async def delete_file(self, file_path: str) -> None:
        """
        Delete file from Cloudinary by URL.
        
        Note: This requires extracting public_id from URL or better to use delete_by_public_id.
        """
        # This is tricky with Cloudinary; prefer delete_by_public_id
        raise NotImplementedError("Use delete_by_public_id for Cloudinary")

    async def delete_by_public_id(self, public_id: str) -> None:
        """Delete file from Cloudinary by public ID."""
        try:
            cloudinary.uploader.destroy(public_id, resource_type="image")
        except Exception as e:
            # Log but don't fail if deletion fails
            pass

    async def file_exists(self, file_path: str) -> bool:
        """Check if file exists (not efficiently supported by Cloudinary API)."""
        # Cloudinary doesn't provide efficient existence check via URL
        return False

    def get_file_url(self, file_path: str) -> str:
        """Get public URL for file (for Cloudinary, just return the path as-is)."""
        return file_path

    def _build_folder_path(self, folder: str) -> str:
        """Build full folder path with prefix."""
        folder = folder.strip("/")
        if self.folder_prefix and folder:
            return f"{self.folder_prefix}/{folder}"
        elif self.folder_prefix:
            return self.folder_prefix
        else:
            return folder
