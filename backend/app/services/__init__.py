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
from .ingredient_service import (
    list_ingredients,
    get_by_id as get_ingredient_by_id,
    create_ingredient,
    update_ingredient,
    delete_ingredient,
    get_recipe_usage_count as get_ingredient_recipe_usage_count,
    detect_duplicates,
    merge_ingredients,
)
from .user_service import list_users, update_user_status
from .audit_service import AuditService
from .category_service import (
    get_active_templates,
    get_active_glassware,
    get_active_serving_styles,
    get_active_methods,
    get_active_spirits,
    get_all_active_categories,
    TYPE_MAP,
    RECIPE_FIELD_MAP,
    get_all_by_type,
    get_by_id,
    create as create_category,
    update as update_category,
    soft_delete as soft_delete_category,
    reorder as reorder_categories,
    get_recipe_usage_count,
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
    "get_active_templates",
    "get_active_glassware",
    "get_active_serving_styles",
    "get_active_methods",
    "get_active_spirits",
    "get_all_active_categories",
    "TYPE_MAP",
    "RECIPE_FIELD_MAP",
    "get_all_by_type",
    "get_by_id",
    "create_category",
    "update_category",
    "soft_delete_category",
    "reorder_categories",
    "get_recipe_usage_count",
    # Admin ingredient service
    "list_ingredients",
    "get_ingredient_by_id",
    "create_ingredient",
    "update_ingredient",
    "delete_ingredient",
    "get_ingredient_recipe_usage_count",
    "detect_duplicates",
    "merge_ingredients",
    # Admin user service
    "list_users",
    "update_user_status",
    # Audit service
    "AuditService",
]
