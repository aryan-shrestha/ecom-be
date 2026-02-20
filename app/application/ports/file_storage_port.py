"""File storage port."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import BinaryIO, Optional


@dataclass
class ImageUploadResult:
    """Result of image upload operation."""

    url: str
    public_id: Optional[str]
    bytes_size: int
    width: int
    height: int
    format: str


class FileStoragePort(ABC):
    """Port for file storage operations."""

    @abstractmethod
    async def save_file(self, file: BinaryIO, filename: str, folder: str = "") -> str:
        """
        Save file to storage.
        
        Args:
            file: File-like object to save
            filename: Name of file
            folder: Optional folder/prefix
            
        Returns:
            URL or path to saved file
        """
        ...

    @abstractmethod
    async def upload_image(
        self,
        file_data: bytes,
        filename: str,
        folder: str = "",
        content_type: Optional[str] = None,
    ) -> ImageUploadResult:
        """
        Upload image to storage with metadata extraction.
        
        Args:
            file_data: Image file bytes
            filename: Original filename
            folder: Folder/prefix to store in
            content_type: MIME type of image
            
        Returns:
            ImageUploadResult with URL and metadata
        """
        ...

    @abstractmethod
    async def delete_file(self, file_path: str) -> None:
        """Delete file from storage."""
        ...

    @abstractmethod
    async def delete_by_public_id(self, public_id: str) -> None:
        """Delete file by provider public ID (for cloud providers)."""
        ...

    @abstractmethod
    async def file_exists(self, file_path: str) -> bool:
        """Check if file exists in storage."""
        ...

    @abstractmethod
    def get_file_url(self, file_path: str) -> str:
        """Get public URL for file."""
        ...
