"""
Application configuration.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Get the directory where this config file lives
BASE_DIR = Path(__file__).resolve().parent.parent

# Explicitly load .env file (override=True ensures it loads even if vars exist)
load_dotenv(BASE_DIR / ".env", override=True)


class Settings(BaseSettings):
    # Database - defaults to SQLite for easy local testing
    database_url: str = "sqlite:///./cocktails.db"

    # Anthropic API
    anthropic_api_key: str = ""

    # File storage
    upload_dir: Path = Path("./uploads")

    # API settings
    api_prefix: str = "/api"
    debug: bool = False


settings = Settings()

# Ensure upload directory exists
settings.upload_dir.mkdir(parents=True, exist_ok=True)
