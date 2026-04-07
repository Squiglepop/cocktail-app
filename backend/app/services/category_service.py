"""
Category service for database-driven category queries.

Thin DB query wrapper for public category endpoints.
Filters by is_active=True and orders by sort_order.
"""
from sqlalchemy.orm import Session

from app.models import (
    CategoryTemplate,
    CategoryGlassware,
    CategoryServingStyle,
    CategoryMethod,
    CategorySpirit,
)


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
