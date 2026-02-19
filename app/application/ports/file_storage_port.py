"""File storage port."""

from abc import ABC, abstractmethod
from typing import BinaryIO


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
    async def delete_file(self, file_path: str) -> None:
        """Delete file from storage."""
        ...

    @abstractmethod
    async def file_exists(self, file_path: str) -> bool:
        """Check if file exists in storage."""
        ...

    @abstractmethod
    def get_file_url(self, file_path: str) -> str:
        """Get public URL for file."""
        ...
