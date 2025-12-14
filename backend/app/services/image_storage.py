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

        Handles both new storage format (just filename) and legacy format
        (uploads/filename path) for backwards compatibility.

        Args:
            filename: The image filename (relative path).

        Returns:
            Full Path object to the image file.
        """
        # Try the standard storage location first
        standard_path = self.storage_dir / filename
        if standard_path.exists():
            return standard_path

        # Legacy support: if filename has 'uploads/' prefix, check the old location
        # Old recipes stored full paths like 'uploads/xxx.jpg' and files were in ./uploads/
        if filename.startswith("uploads/"):
            legacy_path = Path(filename)
            if legacy_path.exists():
                return legacy_path

        # Also check for the filename without uploads/ prefix at the root
        if filename.startswith("uploads/"):
            bare_filename = filename.replace("uploads/", "", 1)
            bare_path = self.storage_dir / bare_filename
            if bare_path.exists():
                return bare_path

        # Return the standard path (may not exist, caller handles 404)
        return standard_path

    def delete_image(self, filename: str) -> bool:
        """
        Delete an image file from the filesystem.

        Handles both new storage format and legacy format for backwards compatibility.

        Args:
            filename: The image filename to delete.

        Returns:
            True if the file was deleted, False if it didn't exist.
        """
        # Use get_image_path to find the actual file location (handles legacy paths)
        filepath = self.get_image_path(filename)
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
