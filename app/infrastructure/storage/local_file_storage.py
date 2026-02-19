"""Local file storage implementation."""

import os
import shutil
import uuid
from pathlib import Path
from typing import BinaryIO

from app.application.ports.file_storage_port import FileStoragePort


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

    async def delete_file(self, file_path: str) -> None:
        """Delete file from local storage."""
        # Extract relative path from URL
        if file_path.startswith(self.base_url):
            relative = file_path[len(self.base_url):].lstrip("/")
            full_path = self.base_path / relative
            if full_path.exists():
                full_path.unlink()

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
