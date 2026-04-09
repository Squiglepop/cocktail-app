"""
Admin router for administrative operations.
"""
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from ..dependencies import require_admin
from ..models import User, Ingredient
from ..schemas import (
    CleanupStatsResponse,
    CategoryCreate,
    CategoryUpdate,
    CategoryAdminResponse,
    CategoryReorderRequest,
    CategoryDeleteResponse,
    IngredientAdminCreate,
    IngredientAdminUpdate,
    IngredientAdminResponse,
    IngredientListResponse,
    IngredientDeleteResponse,
    DuplicateDetectionResponse,
    IngredientMergeRequest,
    IngredientMergeResponse,
    UserAdminResponse,
    UserListResponse,
    UserStatusUpdate,
    UserStatusResponse,
    AuditLogResponse,
    AuditLogListResponse,
)
from ..services.audit_service import AuditService
from ..services.auth import get_current_user, get_user_by_id
from ..services.cleanup import get_cleanup_service
from ..services.database import get_db
from ..services.ingredient_service import (
    list_ingredients,
    get_by_id as get_ingredient_by_id,
    create_ingredient,
    update_ingredient,
    delete_ingredient,
    detect_duplicates,
    merge_ingredients,
)
from ..services.user_service import list_users, update_user_status
from ..services.category_service import (
    TYPE_MAP,
    get_all_by_type,
    get_by_id,
    create,
    update,
    soft_delete,
    reorder,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])
limiter = Limiter(key_func=get_remote_address)


def _audit_log(db, admin_id, action, entity_type, entity_id, details):
    """Fire-and-forget audit wrapper. Main operation is already committed by service."""
    try:
        AuditService.log(db, admin_id, action, entity_type, entity_id, details)
        db.commit()
    except Exception as e:
        logger.error("Audit log failed: %s", e)
        db.rollback()

VALID_CATEGORY_TYPES = {"templates", "glassware", "serving-styles", "methods", "spirits"}
VALID_INGREDIENT_TYPES = {
    "spirit", "liqueur", "wine_fortified", "bitter", "syrup",
    "juice", "mixer", "dairy", "egg", "garnish", "other",
}


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
    _audit_log(db, admin.id, "category_create", "category", result.id, {"type": type, "value": result.value, "label": result.label})
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
    # Capture old values before update
    existing = get_by_id(db, type, id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Category not found")
    old_values = {"label": existing.label, "description": existing.description, "is_active": existing.is_active}
    result = update(db, type, id, data)
    if result is None:
        raise HTTPException(status_code=404, detail="Category not found")
    # Compute changes from only the fields the caller sent
    update_fields = data.model_dump(exclude_unset=True)
    changes = {
        field: [old_values[field], getattr(result, field)]
        for field in update_fields
        if old_values.get(field) != getattr(result, field)
    }
    if changes:
        _audit_log(db, admin.id, "category_update", "category", id, {"type": type, "changes": changes})
    return result


@router.delete("/categories/{type}/{id}", response_model=CategoryDeleteResponse)
def delete_admin_category(
    type: str,
    id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    validate_category_type(type)
    # Capture value before delete
    existing = get_by_id(db, type, id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Category not found")
    pre_delete_value = existing.value
    result = soft_delete(db, type, id)
    if result is None:
        raise HTTPException(status_code=404, detail="Category not found")
    category, recipe_count = result
    _audit_log(db, admin.id, "category_delete", "category", id, {"type": type, "value": pre_delete_value})
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


# --- Admin Ingredient Endpoints ---


@router.get("/ingredients", response_model=IngredientListResponse)
def list_admin_ingredients(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=100),
    search: Optional[str] = None,
    ingredient_type: Optional[str] = Query(default=None, alias="type"),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    if ingredient_type and ingredient_type not in VALID_INGREDIENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid ingredient type: {ingredient_type}. Must be one of: {', '.join(sorted(VALID_INGREDIENT_TYPES))}",
        )
    items, total = list_ingredients(db, page, per_page, search, ingredient_type)
    return IngredientListResponse(
        items=items, total=total, page=page, per_page=per_page,
    )


@router.get("/ingredients/duplicates", response_model=DuplicateDetectionResponse)
def get_ingredient_duplicates(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    groups = detect_duplicates(db)
    return DuplicateDetectionResponse(
        groups=groups,
        total_groups=len(groups),
        total_duplicates=sum(len(g.duplicates) for g in groups),
    )


@router.post("/ingredients/merge", response_model=IngredientMergeResponse)
def merge_admin_ingredients(
    data: IngredientMergeRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    # Capture names BEFORE merge — sources are deleted during merge
    target = db.query(Ingredient).filter(Ingredient.id == data.target_id).first()
    sources = db.query(Ingredient).filter(Ingredient.id.in_(data.source_ids)).all()
    pre_merge_target_name = target.name if target else None
    pre_merge_source_names = [s.name for s in sources]
    try:
        recipes_affected, sources_removed = merge_ingredients(db, data.target_id, data.source_ids)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    _audit_log(db, admin.id, "ingredient_merge", "ingredient", data.target_id, {
        "source_ids": data.source_ids, "source_names": pre_merge_source_names,
        "target_id": data.target_id, "target_name": pre_merge_target_name,
        "recipes_updated": recipes_affected,
    })
    return IngredientMergeResponse(
        message=f"Merged {sources_removed} ingredient(s). {recipes_affected} recipe(s) affected.",
        recipes_affected=recipes_affected,
        sources_removed=sources_removed,
    )


@router.get("/ingredients/{id}", response_model=IngredientAdminResponse)
def get_admin_ingredient(
    id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    ingredient = get_ingredient_by_id(db, id)
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    return ingredient


@router.post("/ingredients", response_model=IngredientAdminResponse, status_code=201)
def create_admin_ingredient(
    data: IngredientAdminCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    result = create_ingredient(db, data)
    if result is None:
        raise HTTPException(status_code=409, detail="Ingredient name already exists")
    _audit_log(db, admin.id, "ingredient_create", "ingredient", result.id, {"name": result.name, "type": result.type})
    return result


@router.put("/ingredients/{id}", response_model=IngredientAdminResponse)
def update_admin_ingredient(
    id: str,
    data: IngredientAdminUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    ingredient = get_ingredient_by_id(db, id)
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    # Capture old values before update
    old_values = {
        "name": ingredient.name, "type": ingredient.type,
        "spirit_category": ingredient.spirit_category,
        "description": ingredient.description, "common_brands": ingredient.common_brands,
    }
    result = update_ingredient(db, ingredient, data)
    if result is None:
        raise HTTPException(status_code=409, detail="Ingredient name already exists")
    # Compute changes
    update_fields = data.model_dump(exclude_unset=True)
    changes = {
        field: [old_values[field], getattr(result, field)]
        for field in update_fields
        if old_values.get(field) != getattr(result, field)
    }
    if changes:
        _audit_log(db, admin.id, "ingredient_update", "ingredient", id, {"changes": changes})
    return result


@router.delete(
    "/ingredients/{id}",
    response_model=IngredientDeleteResponse,
    responses={409: {"model": IngredientDeleteResponse, "description": "Ingredient in use"}},
)
def delete_admin_ingredient(
    id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    ingredient = get_ingredient_by_id(db, id)
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    # Capture before delete
    pre_delete_name = ingredient.name
    pre_delete_type = ingredient.type
    deleted, recipe_count = delete_ingredient(db, ingredient)
    if not deleted:
        return JSONResponse(
            status_code=409,
            content={
                "message": f"Ingredient '{ingredient.name}' is used in {recipe_count} recipe(s) and cannot be deleted",
                "recipe_count": recipe_count,
            },
        )
    _audit_log(db, admin.id, "ingredient_delete", "ingredient", id, {"name": pre_delete_name, "type": pre_delete_type})
    return IngredientDeleteResponse(
        message=f"Ingredient '{pre_delete_name}' deleted successfully",
        recipe_count=0,
    )


# --- Admin User Endpoints ---

VALID_USER_STATUSES = {"active", "inactive"}


@router.get("/users", response_model=UserListResponse)
def list_admin_users(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    if status and status not in VALID_USER_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status: {status}. Must be one of: {', '.join(sorted(VALID_USER_STATUSES))}",
        )
    items, total = list_users(db, page, per_page, search, status)
    return UserListResponse(
        items=items, total=total, page=page, per_page=per_page,
    )


@router.patch("/users/{id}", response_model=UserStatusResponse)
def update_admin_user_status(
    id: str,
    data: UserStatusUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = get_user_by_id(db, id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Capture old state before update
    old_is_active = user.is_active
    old_is_admin = user.is_admin
    try:
        updated_user, message = update_user_status(db, user, data, admin.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    # No audit if no changes
    if message != "No changes applied":
        if old_is_active != updated_user.is_active:
            action = "user_activate" if updated_user.is_active else "user_deactivate"
            _audit_log(db, admin.id, action, "user", user.id, {"email": updated_user.email})
        if old_is_admin != updated_user.is_admin:
            action = "user_grant_admin" if updated_user.is_admin else "user_revoke_admin"
            _audit_log(db, admin.id, action, "user", user.id, {"email": updated_user.email})
    return UserStatusResponse(
        id=updated_user.id,
        email=updated_user.email,
        display_name=updated_user.display_name,
        is_active=updated_user.is_active,
        is_admin=updated_user.is_admin,
        message=message,
    )


# --- Admin Audit Log Endpoints ---


@router.get("/audit-log", response_model=AuditLogListResponse)
@limiter.limit("30/minute")
async def get_audit_log(
    request: Request,
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    from_date: Optional[datetime] = Query(None, alias="from"),
    to_date: Optional[datetime] = Query(None, alias="to"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    items, total = AuditService.list_audit_logs(
        db,
        action=action,
        entity_type=entity_type,
        from_date=from_date,
        to_date=to_date,
        page=page,
        per_page=per_page,
    )
    return AuditLogListResponse(
        items=[
            AuditLogResponse(
                id=audit_log.id,
                admin_user_id=audit_log.admin_user_id,
                admin_email=admin_email,
                action=audit_log.action,
                entity_type=audit_log.entity_type,
                entity_id=audit_log.entity_id,
                details=audit_log.details,
                created_at=audit_log.created_at,
            )
            for audit_log, admin_email in items
        ],
        total=total,
        page=page,
        per_page=per_page,
    )
