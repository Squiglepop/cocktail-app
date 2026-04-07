"""
Category service for database-driven category queries.

Thin DB query wrapper for public category endpoints.
Filters by is_active=True and orders by sort_order.
Admin methods handle full CRUD, reorder, and soft-delete.
"""
from uuid import uuid4

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import (
    Recipe,
    CategoryTemplate,
    CategoryGlassware,
    CategoryServingStyle,
    CategoryMethod,
    CategorySpirit,
)
from app.schemas.category import CategoryCreate, CategoryUpdate


TYPE_MAP = {
    "templates": CategoryTemplate,
    "glassware": CategoryGlassware,
    "serving-styles": CategoryServingStyle,
    "methods": CategoryMethod,
    "spirits": CategorySpirit,
}

RECIPE_FIELD_MAP = {
    "templates": Recipe.template,
    "glassware": Recipe.glassware,
    "serving-styles": Recipe.serving_style,
    "methods": Recipe.method,
    "spirits": Recipe.main_spirit,
}


def get_active_templates(db: Session) -> list[CategoryTemplate]:
    """Get all active templates ordered by sort_order."""
    return (
        db.query(CategoryTemplate)
        .filter(CategoryTemplate.is_active)
        .order_by(CategoryTemplate.sort_order)
        .all()
    )


def get_active_glassware(db: Session) -> list[CategoryGlassware]:
    """Get all active glassware ordered by sort_order."""
    return (
        db.query(CategoryGlassware)
        .filter(CategoryGlassware.is_active)
        .order_by(CategoryGlassware.sort_order)
        .all()
    )


def get_active_serving_styles(db: Session) -> list[CategoryServingStyle]:
    """Get all active serving styles ordered by sort_order."""
    return (
        db.query(CategoryServingStyle)
        .filter(CategoryServingStyle.is_active)
        .order_by(CategoryServingStyle.sort_order)
        .all()
    )


def get_active_methods(db: Session) -> list[CategoryMethod]:
    """Get all active methods ordered by sort_order."""
    return (
        db.query(CategoryMethod)
        .filter(CategoryMethod.is_active)
        .order_by(CategoryMethod.sort_order)
        .all()
    )


def get_active_spirits(db: Session) -> list[CategorySpirit]:
    """Get all active spirits ordered by sort_order."""
    return (
        db.query(CategorySpirit)
        .filter(CategorySpirit.is_active)
        .order_by(CategorySpirit.sort_order)
        .all()
    )


def get_all_active_categories(db: Session) -> dict[str, list]:
    """Get all active categories across all 5 tables in one call."""
    return {
        "templates": get_active_templates(db),
        "spirits": get_active_spirits(db),
        "glassware": get_active_glassware(db),
        "serving_styles": get_active_serving_styles(db),
        "methods": get_active_methods(db),
    }


# --- Admin CRUD methods ---


def get_all_by_type(db: Session, type_name: str) -> list:
    """Get ALL categories (active + inactive) ordered by sort_order."""
    model_class = TYPE_MAP[type_name]
    return db.query(model_class).order_by(model_class.sort_order).all()


def get_by_id(db: Session, type_name: str, category_id: str):
    """Get a single category by ID."""
    model_class = TYPE_MAP[type_name]
    return db.query(model_class).filter(model_class.id == category_id).first()


def create(db: Session, type_name: str, data: CategoryCreate):
    """Create a new category with auto-assigned sort_order."""
    model_class = TYPE_MAP[type_name]

    existing = db.query(model_class).filter(model_class.value == data.value).first()
    if existing:
        return None  # Duplicate — caller raises 409

    max_order = db.query(func.max(model_class.sort_order)).scalar()
    next_order = (max_order + 1) if max_order is not None else 0

    fields = {
        "id": str(uuid4()),
        "value": data.value,
        "label": data.label,
        "sort_order": next_order,
    }
    if hasattr(model_class, "description") and data.description is not None:
        fields["description"] = data.description
    if hasattr(model_class, "category"):
        fields["category"] = data.category if data.category else "specialty"

    record = model_class(**fields)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def update(db: Session, type_name: str, category_id: str, data: CategoryUpdate):
    """Update a category. Value field is immutable."""
    record = get_by_id(db, type_name, category_id)
    if not record:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(record, field):
            setattr(record, field, value)

    db.commit()
    db.refresh(record)
    return record


def soft_delete(db: Session, type_name: str, category_id: str):
    """Soft-delete a category. Returns (category, recipe_count) or None."""
    record = get_by_id(db, type_name, category_id)
    if not record:
        return None

    recipe_count = get_recipe_usage_count(db, type_name, record.value)
    record.is_active = False
    db.commit()
    db.refresh(record)
    return record, recipe_count


def reorder(db: Session, type_name: str, ids: list[str]) -> list[str]:
    """Reorder categories. Returns list of invalid IDs (empty if all valid)."""
    model_class = TYPE_MAP[type_name]

    records = db.query(model_class).filter(model_class.id.in_(ids)).all()
    record_map = {r.id: r for r in records}

    invalid_ids = [cid for cid in ids if cid not in record_map]
    if invalid_ids:
        return invalid_ids

    for index, category_id in enumerate(ids):
        record_map[category_id].sort_order = index

    db.commit()
    return []


def get_recipe_usage_count(db: Session, type_name: str, value: str) -> int:
    """Count how many recipes reference this category value."""
    recipe_field = RECIPE_FIELD_MAP[type_name]
    return db.query(func.count(Recipe.id)).filter(recipe_field == value).scalar() or 0
