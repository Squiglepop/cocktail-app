"""
Image storage service for filesystem-based image storage.

Stores images on the filesystem instead of in the database to reduce
memory usage and improve database performance.
"""
from pathlib import Path
from typing import Optional
from uuid import uuid4


class ImageStorageService:
    """Service for storing and retrieving images from the filesystem."""

    EXTENSIONS = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/gif": ".gif",
    }

    def __init__(self, storage_dir: Path):
        """
        Initialize the image storage service.

        Args:
            storage_dir: Directory where images will be stored.
        """
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save_image(self, image_data: bytes, mime_type: str) -> str:
        """
        Save image to filesystem.

        Args:
            image_data: Raw image bytes.
            mime_type: MIME type of the image (e.g., 'image/jpeg').

        Returns:
            The filename of the saved image (relative path).
        """
        ext = self._get_extension(mime_type)
        filename = f"{uuid4()}{ext}"
        filepath = self.storage_dir / filename
        filepath.write_bytes(image_data)
        return filename

    def get_image_path(self, filename: str) -> Path:
        """
        Get the full filesystem path for an image filename.

        Args:
            filename: The image filename (relative path).

        Returns:
            Full Path object to the image file.
        """
        return self.storage_dir / filename

    def delete_image(self, filename: str) -> bool:
        """
        Delete an image file from the filesystem.

        Args:
            filename: The image filename to delete.

        Returns:
            True if the file was deleted, False if it didn't exist.
        """
        filepath = self.storage_dir / filename
        if filepath.exists():
            filepath.unlink()
            return True
        return False

    def _get_extension(self, mime_type: str) -> str:
        """
        Get file extension for a MIME type.

        Args:
            mime_type: MIME type string.

        Returns:
            File extension including the dot (e.g., '.jpg').
        """
        return self.EXTENSIONS.get(mime_type, ".jpg")


# Singleton instance - will be initialized when config is available
_image_storage: Optional[ImageStorageService] = None


def get_image_storage() -> ImageStorageService:
    """
    Get the image storage service singleton.

    Returns:
        ImageStorageService instance configured with settings.
    """
    global _image_storage
    if _image_storage is None:
        from app.config import settings
        _image_storage = ImageStorageService(settings.image_storage_dir)
    return _image_storage
