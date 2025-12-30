"""
Services.
"""
from .database import get_db, create_tables, run_migrations, SessionLocal
from .extractor import RecipeExtractor, map_to_enum, map_extracted_to_create
from .duplicate_detector import (
    check_for_duplicates,
    compute_hashes_for_recipe,
    DuplicateCheckResult,
    DuplicateMatch,
    ImageHashes,
    clear_hash_cache,
)
from .image_storage import ImageStorageService, get_image_storage
from .cleanup import OrphanedFileCleanupService, CleanupStats, get_cleanup_service
from .security import sanitize_text, sanitize_recipe_name, sanitize_ingredient_name
from .recipe_service import (
    get_or_create_ingredient,
    add_ingredients_to_recipe,
    replace_recipe_ingredients,
)

__all__ = [
    "get_db",
    "create_tables",
    "run_migrations",
    "SessionLocal",
    "RecipeExtractor",
    "map_to_enum",
    "map_extracted_to_create",
    "check_for_duplicates",
    "compute_hashes_for_recipe",
    "DuplicateCheckResult",
    "DuplicateMatch",
    "ImageHashes",
    "clear_hash_cache",
    "ImageStorageService",
    "get_image_storage",
    "OrphanedFileCleanupService",
    "CleanupStats",
    "get_cleanup_service",
    "sanitize_text",
    "sanitize_recipe_name",
    "sanitize_ingredient_name",
    "get_or_create_ingredient",
    "add_ingredients_to_recipe",
    "replace_recipe_ingredients",
]
