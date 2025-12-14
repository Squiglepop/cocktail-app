"""
Memory-efficient image preprocessing for Claude Vision API.

Design priorities (in order):
1. Memory efficiency - minimize peak memory usage, explicit cleanup
2. Robustness - handle edge cases, corrupted images, various formats
3. Speed - use efficient algorithms where possible

Claude Vision tokens scale with image resolution. Downsampling to 1568px
max dimension typically reduces tokens by 60-70% for mobile screenshots
while preserving text readability.
"""
import io
import logging
from pathlib import Path
from typing import Tuple, Optional

from PIL import Image, UnidentifiedImageError

logger = logging.getLogger(__name__)

# Claude Vision optimal max dimension (balances quality vs tokens)
DEFAULT_MAX_DIMENSION = 1568
DEFAULT_JPEG_QUALITY = 85

# Minimum dimension to avoid over-downsampling small images
MIN_DIMENSION = 256


class ImagePreprocessingError(Exception):
    """Raised when image preprocessing fails."""
    pass


class ImagePreprocessor:
    """
    Downsample images for Claude Vision while minimizing memory usage.

    Memory strategy:
    - Uses PIL's lazy loading (image data not decoded until accessed)
    - Processes images in a single pass
    - Uses context managers for explicit resource cleanup
    - Avoids holding multiple copies of image data
    """

    def __init__(
        self,
        max_dimension: int = DEFAULT_MAX_DIMENSION,
        jpeg_quality: int = DEFAULT_JPEG_QUALITY,
        enabled: bool = True,
    ):
        """
        Initialize preprocessor with configuration.

        Args:
            max_dimension: Maximum width or height for output image
            jpeg_quality: JPEG compression quality (1-100)
            enabled: If False, returns original image data unchanged
        """
        self.max_dimension = max_dimension
        self.jpeg_quality = jpeg_quality
        self.enabled = enabled

    def process_file(self, image_path: Path) -> Tuple[bytes, str]:
        """
        Load, downsample, and return image bytes optimized for Claude Vision.

        Args:
            image_path: Path to the image file

        Returns:
            Tuple of (image_bytes, media_type)

        Raises:
            ImagePreprocessingError: If image cannot be processed
            FileNotFoundError: If image file doesn't exist
        """
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        if not self.enabled:
            return self._read_original(image_path)

        try:
            with Image.open(image_path) as img:
                return self._process_image(img, image_path.suffix.lower())
        except UnidentifiedImageError as e:
            # Image format not recognized by PIL - return original bytes
            # This handles edge cases like corrupted files or unusual formats
            logger.warning(
                f"Cannot identify image format for {image_path}, returning original: {e}"
            )
            return self._read_original(image_path)
        except Exception as e:
            logger.warning(
                f"Preprocessing failed for {image_path}, falling back to original: {e}"
            )
            # Fallback: return original on any processing error
            return self._read_original(image_path)

    def process_bytes(
        self,
        image_data: bytes,
        original_media_type: Optional[str] = None,
    ) -> Tuple[bytes, str]:
        """
        Process raw image bytes (for DB-stored or in-memory images).

        Args:
            image_data: Raw image bytes
            original_media_type: Optional hint for original format

        Returns:
            Tuple of (processed_bytes, media_type)
        """
        if not self.enabled:
            # Return as-is with best-guess media type
            media_type = original_media_type or "image/jpeg"
            return image_data, media_type

        try:
            with Image.open(io.BytesIO(image_data)) as img:
                # Infer suffix from format for consistency
                format_to_suffix = {
                    "JPEG": ".jpg",
                    "PNG": ".png",
                    "GIF": ".gif",
                    "WEBP": ".webp",
                }
                suffix = format_to_suffix.get(img.format, ".jpg")
                return self._process_image(img, suffix)
        except UnidentifiedImageError as e:
            # Image format not recognized by PIL - return original bytes
            logger.warning(
                f"Cannot identify image format from bytes, returning original: {e}"
            )
            media_type = original_media_type or "image/jpeg"
            return image_data, media_type
        except Exception as e:
            logger.warning(
                f"Preprocessing failed for image bytes, returning original: {e}"
            )
            media_type = original_media_type or "image/jpeg"
            return image_data, media_type

    def _process_image(self, img: Image.Image, original_suffix: str) -> Tuple[bytes, str]:
        """
        Core processing logic for a PIL Image object.

        Args:
            img: PIL Image object (caller must manage lifecycle)
            original_suffix: Original file extension for format hints

        Returns:
            Tuple of (processed_bytes, media_type)
        """
        width, height = img.size
        needs_resize = width > self.max_dimension or height > self.max_dimension

        # Don't upscale tiny images
        is_tiny = width < MIN_DIMENSION and height < MIN_DIMENSION

        if needs_resize and not is_tiny:
            img = self._resize_image(img, width, height)

        # Determine output format and convert if beneficial
        output_bytes, media_type = self._encode_image(img, original_suffix)

        return output_bytes, media_type

    def _resize_image(
        self,
        img: Image.Image,
        width: int,
        height: int,
    ) -> Image.Image:
        """
        Resize image to fit within max_dimension, preserving aspect ratio.

        Uses LANCZOS resampling for quality. For speed-critical applications,
        consider BILINEAR which is ~2x faster with slightly lower quality.
        """
        ratio = min(self.max_dimension / width, self.max_dimension / height)
        new_width = int(width * ratio)
        new_height = int(height * ratio)

        logger.debug(
            f"Resizing image from {width}x{height} to {new_width}x{new_height} "
            f"({ratio:.2%} of original)"
        )

        # LANCZOS provides best quality for downsampling
        # It's slower than BILINEAR but quality matters for text extraction
        return img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    def _encode_image(
        self,
        img: Image.Image,
        original_suffix: str,
    ) -> Tuple[bytes, str]:
        """
        Encode image to bytes, optimizing format where possible.

        Strategy:
        - Convert PNG/WebP without transparency to JPEG (smaller)
        - Keep transparency-containing images as PNG
        - GIFs stay as GIF (may be animated)
        """
        has_transparency = self._has_transparency(img)
        is_gif = original_suffix == ".gif"

        # Determine output format
        if is_gif:
            # Keep GIFs as-is (may be animated, special handling needed)
            output_format = "GIF"
            media_type = "image/gif"
        elif has_transparency:
            output_format = "PNG"
            media_type = "image/png"
        else:
            # Convert to JPEG for smaller size
            output_format = "JPEG"
            media_type = "image/jpeg"

            # Ensure RGB mode for JPEG (no alpha, no palette)
            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")

        # Encode to bytes
        buffer = io.BytesIO()
        save_kwargs = {}

        if output_format == "JPEG":
            save_kwargs["quality"] = self.jpeg_quality
            save_kwargs["optimize"] = True
        elif output_format == "PNG":
            save_kwargs["optimize"] = True

        img.save(buffer, format=output_format, **save_kwargs)

        return buffer.getvalue(), media_type

    def _has_transparency(self, img: Image.Image) -> bool:
        """Check if image has meaningful transparency that should be preserved."""
        if img.mode == "RGBA":
            # Check if alpha channel has any non-opaque pixels
            alpha = img.getchannel("A")
            # Quick check: if min alpha is 255, no transparency
            if alpha.getextrema()[0] == 255:
                return False
            return True
        elif img.mode == "LA":
            alpha = img.getchannel("A")
            if alpha.getextrema()[0] == 255:
                return False
            return True
        elif img.mode == "P" and "transparency" in img.info:
            return True
        return False

    def _read_original(self, image_path: Path) -> Tuple[bytes, str]:
        """Read original image without processing."""
        suffix = image_path.suffix.lower()
        media_type_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        media_type = media_type_map.get(suffix, "image/jpeg")

        with open(image_path, "rb") as f:
            return f.read(), media_type


# Module-level convenience instance with defaults
_default_preprocessor: Optional[ImagePreprocessor] = None


def get_preprocessor() -> ImagePreprocessor:
    """Get or create the default preprocessor instance."""
    global _default_preprocessor
    if _default_preprocessor is None:
        # Import here to avoid circular imports
        from app.config import settings
        _default_preprocessor = ImagePreprocessor(
            max_dimension=getattr(settings, "vision_max_dimension", DEFAULT_MAX_DIMENSION),
            jpeg_quality=getattr(settings, "vision_jpeg_quality", DEFAULT_JPEG_QUALITY),
            enabled=getattr(settings, "vision_preprocessing_enabled", True),
        )
    return _default_preprocessor


def reset_preprocessor() -> None:
    """Reset the default preprocessor (useful for testing or config changes)."""
    global _default_preprocessor
    _default_preprocessor = None
