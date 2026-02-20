"""Local file storage implementation."""

import io
import os
import shutil
import uuid
from pathlib import Path
from typing import BinaryIO, Optional

from PIL import Image

from app.application.ports.file_storage_port import FileStoragePort, ImageUploadResult


class LocalFileStorage(FileStoragePort):
    """Local filesystem storage implementation."""

    def __init__(self, base_path: str, base_url: str) -> None:
        """
        Initialize local file storage.
        
        Args:
            base_path: Absolute path to storage directory
            base_url: Base URL for serving files (e.g., "/static/uploads")
        """
        self.base_path = Path(base_path)
        self.base_url = base_url.rstrip("/")
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def save_file(self, file: BinaryIO, filename: str, folder: str = "") -> str:
        """
        Save file to local storage.
        
        Generates unique filename to avoid collisions.
        """
        # Sanitize folder
        folder = folder.strip("/")
        
        # Generate unique filename
        ext = Path(filename).suffix
        unique_name = f"{uuid.uuid4()}{ext}"
        
        # Build path
        if folder:
            target_dir = self.base_path / folder
        else:
            target_dir = self.base_path
            
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / unique_name
        
        # Save file
        with open(target_path, "wb") as f:
            shutil.copyfileobj(file, f)
        
        # Return URL
        if folder:
            return f"{self.base_url}/{folder}/{unique_name}"
        else:
            return f"{self.base_url}/{unique_name}"

    async def upload_image(
        self,
        file_data: bytes,
        filename: str,
        folder: str = "",
        content_type: Optional[str] = None,
    ) -> ImageUploadResult:
        """
        Upload image to local storage with metadata extraction.
        
        Args:
            file_data: Image file bytes
            filename: Original filename
            folder: Folder to store in
            content_type: MIME type (unused for local)
            
        Returns:
            ImageUploadResult with URL and metadata
        """
        # Extract metadata using PIL
        img = Image.open(io.BytesIO(file_data))
        width, height = img.size
        img_format = img.format.lower() if img.format else "unknown"
        bytes_size = len(file_data)

        # Sanitize folder
        folder = folder.strip("/")
        
        # Generate unique filename
        ext = Path(filename).suffix
        unique_name = f"{uuid.uuid4()}{ext}"
        
        # Build path
        if folder:
            target_dir = self.base_path / folder
        else:
            target_dir = self.base_path
            
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / unique_name
        
        # Save file
        with open(target_path, "wb") as f:
            f.write(file_data)
        
        # Build URL
        if folder:
            url = f"{self.base_url}/{folder}/{unique_name}"
        else:
            url = f"{self.base_url}/{unique_name}"

        # For local storage, public_id is same as unique_name
        return ImageUploadResult(
            url=url,
            public_id=unique_name,
            bytes_size=bytes_size,
            width=width,
            height=height,
            format=img_format,
        )

    async def delete_file(self, file_path: str) -> None:
        """Delete file from local storage."""
        # Extract relative path from URL
        if file_path.startswith(self.base_url):
            relative = file_path[len(self.base_url):].lstrip("/")
            full_path = self.base_path / relative
            if full_path.exists():
                full_path.unlink()

    async def delete_by_public_id(self, public_id: str) -> None:
        """Delete file by public ID (for local, public_id is filename)."""
        # For local storage, scan directories to find the file
        for root, dirs, files in os.walk(self.base_path):
            if public_id in files:
                file_path = Path(root) / public_id
                file_path.unlink()
                break

    async def file_exists(self, file_path: str) -> bool:
        """Check if file exists in local storage."""
        if file_path.startswith(self.base_url):
            relative = file_path[len(self.base_url):].lstrip("/")
            full_path = self.base_path / relative
            return full_path.exists()
        return False

    def get_file_url(self, file_path: str) -> str:
        """Get public URL for file."""
        return file_path
