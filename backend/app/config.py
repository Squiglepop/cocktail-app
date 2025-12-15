"""
Application configuration.
"""
import os
import secrets
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Get the directory where this config file lives
BASE_DIR = Path(__file__).resolve().parent.parent

# Explicitly load .env file (override=True ensures it loads even if vars exist)
load_dotenv(BASE_DIR / ".env", override=True)


def _get_secret_key() -> str:
    """Get secret key from environment or generate for development."""
    key = os.environ.get("SECRET_KEY")
    if key:
        return key
    # In production (Railway sets RAILWAY_ENVIRONMENT), require SECRET_KEY
    if os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("PRODUCTION"):
        raise ValueError(
            "SECRET_KEY environment variable is required in production. "
            "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
        )
    # Development: generate a random key (will change on restart)
    return secrets.token_urlsafe(32)


def _get_image_storage_dir() -> Path:
    """Get image storage directory, preferring Railway volume mount if available."""
    # Railway sets this when a volume is attached
    railway_mount = os.environ.get("RAILWAY_VOLUME_MOUNT_PATH")
    if railway_mount:
        return Path(railway_mount)
    # Fall back to local path for development
    return Path("./data/images")


class Settings(BaseSettings):
    # Database - defaults to SQLite for easy local testing
    database_url: str = "sqlite:///./cocktails.db"

    # Anthropic API
    anthropic_api_key: str = ""

    # File storage
    upload_dir: Path = Path("./uploads")
    image_storage_dir: Path = _get_image_storage_dir()

    # API settings
    api_prefix: str = "/api"
    debug: bool = False

    # CORS settings - comma-separated list of allowed origins
    # Example: "http://localhost:3000,https://myapp.railway.app"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Authentication settings
    secret_key: str = _get_secret_key()
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    # Image preprocessing for Claude Vision API
    # Downsampling reduces token costs by ~60-70% for mobile screenshots
    vision_max_dimension: int = 1568  # Max width/height, preserves aspect ratio
    vision_jpeg_quality: int = 85  # JPEG compression quality (1-100)
    vision_preprocessing_enabled: bool = True  # Set False to disable

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        if not self.cors_origins:
            return []
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()

# Ensure directories exist
settings.upload_dir.mkdir(parents=True, exist_ok=True)
settings.image_storage_dir.mkdir(parents=True, exist_ok=True)
