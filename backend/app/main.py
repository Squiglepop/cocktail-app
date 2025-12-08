"""
FastAPI application entry point.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.services import create_tables
from app.routers import recipes_router, upload_router, categories_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup: create tables
    create_tables()
    yield
    # Shutdown: cleanup if needed


app = FastAPI(
    title="Cocktail Recipe Extractor",
    description="Extract and manage cocktail recipes from screenshots",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for uploaded images
app.mount("/uploads", StaticFiles(directory=str(settings.upload_dir)), name="uploads")

# Include routers
app.include_router(recipes_router, prefix=settings.api_prefix)
app.include_router(upload_router, prefix=settings.api_prefix)
app.include_router(categories_router, prefix=settings.api_prefix)


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
