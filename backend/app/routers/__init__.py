"""
API Routers.
"""
from .recipes import router as recipes_router
from .upload import router as upload_router
from .categories import router as categories_router
from .auth import router as auth_router

__all__ = ["recipes_router", "upload_router", "categories_router", "auth_router"]
