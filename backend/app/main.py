"""
FastAPI application entry point.
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.services import create_tables, run_migrations
from app.routers import recipes_router, upload_router, categories_router, auth_router, collections_router, admin_router

# Rate limiter - limits by remote IP address
limiter = Limiter(key_func=get_remote_address)


def validate_production_config():
    """Validate required environment variables in production."""
    is_production = os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("PRODUCTION")
    if not is_production:
        return

    missing = []
    if not settings.anthropic_api_key:
        missing.append("ANTHROPIC_API_KEY")
    if not os.environ.get("DATABASE_URL"):
        missing.append("DATABASE_URL")
    # SECRET_KEY is already validated in config.py

    if missing:
        raise RuntimeError(
            f"Missing required environment variables for production: {', '.join(missing)}"
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Validate production config
    validate_production_config()

    # Startup: run migrations in production, create tables in development
    if os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("PRODUCTION"):
        run_migrations()
    else:
        create_tables()
    yield
    # Shutdown: cleanup if needed


app = FastAPI(
    title="Cocktail Recipe Extractor",
    description="Extract and manage cocktail recipes from screenshots",
    version="0.1.0",
    lifespan=lifespan,
)

# Rate limiting setup
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for uploaded images
app.mount("/uploads", StaticFiles(directory=str(settings.upload_dir)), name="uploads")

# Include routers
app.include_router(auth_router, prefix=settings.api_prefix)
app.include_router(recipes_router, prefix=settings.api_prefix)
app.include_router(upload_router, prefix=settings.api_prefix)
app.include_router(categories_router, prefix=settings.api_prefix)
app.include_router(collections_router, prefix=settings.api_prefix)
app.include_router(admin_router, prefix=settings.api_prefix)


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "name": "Cocktail Recipe Extractor API",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
