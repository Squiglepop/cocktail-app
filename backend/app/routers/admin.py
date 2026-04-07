"""
Admin router for administrative operations.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..dependencies import require_admin
from ..models import User
from ..schemas import (
    CleanupStatsResponse,
    CategoryCreate,
    CategoryUpdate,
    CategoryAdminResponse,
    CategoryReorderRequest,
    CategoryDeleteResponse,
)
from ..services.auth import get_current_user
from ..services.cleanup import get_cleanup_service
from ..services.database import get_db
from ..services.category_service import (
    TYPE_MAP,
    get_all_by_type,
    get_by_id,
    create,
    update,
    soft_delete,
    reorder,
)

router = APIRouter(prefix="/admin", tags=["admin"])

VALID_CATEGORY_TYPES = {"templates", "glassware", "serving-styles", "methods", "spirits"}


def validate_category_type(type: str) -> None:
    if type not in VALID_CATEGORY_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category type: {type}. Must be one of: {', '.join(sorted(VALID_CATEGORY_TYPES))}",
        )


@router.post("/cleanup-orphans", response_model=CleanupStatsResponse)
async def cleanup_orphaned_images(
    dry_run: bool = Query(
        default=False,
        description="If true, only report what would be deleted without actually deleting"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CleanupStatsResponse:
    """
    Clean up orphaned image files.

    Scans the image storage directory and removes files that are not
    referenced by any recipe in the database.

    Requires authentication. Files newer than 1 hour are skipped to
    avoid deleting files from in-progress uploads.
    """
    cleanup_service = get_cleanup_service()
    stats = cleanup_service.cleanup_orphans(db, dry_run=dry_run)

    return CleanupStatsResponse(
        files_scanned=stats.files_scanned,
        orphans_found=stats.orphans_found,
        orphans_deleted=stats.orphans_deleted,
        bytes_reclaimed=stats.bytes_reclaimed,
        skipped_recent=stats.skipped_recent,
        errors=stats.errors,
        dry_run=dry_run,
    )


# --- Admin Category Endpoints ---


@router.get("/categories/{type}", response_model=List[CategoryAdminResponse])
def get_admin_categories(
    type: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    validate_category_type(type)
    return get_all_by_type(db, type)


@router.post("/categories/{type}", response_model=CategoryAdminResponse, status_code=201)
def create_admin_category(
    type: str,
    data: CategoryCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    validate_category_type(type)
    result = create(db, type, data)
    if result is None:
        raise HTTPException(status_code=409, detail="Category value already exists")
    return result


@router.put("/categories/{type}/{id}", response_model=CategoryAdminResponse)
def update_admin_category(
    type: str,
    id: str,
    data: CategoryUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    validate_category_type(type)
    result = update(db, type, id, data)
    if result is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return result


@router.delete("/categories/{type}/{id}", response_model=CategoryDeleteResponse)
def delete_admin_category(
    type: str,
    id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    validate_category_type(type)
    result = soft_delete(db, type, id)
    if result is None:
        raise HTTPException(status_code=404, detail="Category not found")
    category, recipe_count = result
    return CategoryDeleteResponse(
        message=f"Category '{category.value}' deactivated",
        recipe_count=recipe_count,
    )


@router.post("/categories/{type}/reorder")
def reorder_admin_categories(
    type: str,
    data: CategoryReorderRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    validate_category_type(type)
    invalid_ids = reorder(db, type, data.ids)
    if invalid_ids:
        raise HTTPException(
            status_code=400,
            detail=f"IDs not found: {', '.join(invalid_ids)}",
        )
    return {"message": "Categories reordered successfully"}
