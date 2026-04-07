"""
Category endpoints for dropdowns and filters.

Database-driven: queries category tables, filters by is_active,
orders by sort_order. No Python enum iteration.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from typing import List

from app.schemas import CategoryItem, CategoryGroup, CategoriesResponse
from app.services import (
    get_db,
    get_active_templates,
    get_active_glassware,
    get_active_serving_styles,
    get_active_methods,
    get_active_spirits,
    get_all_active_categories,
)


router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=CategoriesResponse)
def get_all_categories(db: Session = Depends(get_db)):
    """Get all category options for filters/dropdowns."""
    cats = get_all_active_categories(db)

    templates = [
        CategoryItem(
            value=t.value,
            display_name=t.label,
            description=t.description,
        )
        for t in cats["templates"]
    ]

    spirits = [
        CategoryItem(value=s.value, display_name=s.label)
        for s in cats["spirits"]
    ]

    # Glassware grouped by category — uses CategoryGroup schema (no "category" key)
    glass_groups = {}
    for g in cats["glassware"]:
        glass_groups.setdefault(g.category, []).append(
            CategoryItem(value=g.value, display_name=g.label)
        )
    glassware = [
        CategoryGroup(name=cat.title(), items=items)
        for cat, items in glass_groups.items()
    ]

    serving_styles = [
        CategoryItem(
            value=s.value,
            display_name=s.label,
            description=s.description,
        )
        for s in cats["serving_styles"]
    ]

    methods = [
        CategoryItem(
            value=m.value,
            display_name=m.label,
            description=m.description,
        )
        for m in cats["methods"]
    ]

    return CategoriesResponse(
        templates=templates,
        spirits=spirits,
        glassware=glassware,
        serving_styles=serving_styles,
        methods=methods,
    )


@router.get("/templates", response_model=List[CategoryItem])
def get_templates(db: Session = Depends(get_db)):
    """Get all cocktail templates/families."""
    return [
        {
            "value": t.value,
            "display_name": t.label,
            "description": t.description,
        }
        for t in get_active_templates(db)
    ]


@router.get("/spirits", response_model=List[CategoryItem])
def get_spirits(db: Session = Depends(get_db)):
    """Get all spirit categories."""
    return [
        {"value": s.value, "display_name": s.label}
        for s in get_active_spirits(db)
    ]


@router.get("/glassware")
def get_glassware(db: Session = Depends(get_db)):
    """Get all glassware options grouped by category."""
    groups = {}
    for g in get_active_glassware(db):
        groups.setdefault(g.category, []).append(
            {"value": g.value, "display_name": g.label}
        )
    return [
        {"category": cat, "name": cat.title(), "items": items}
        for cat, items in groups.items()
    ]


@router.get("/serving-styles", response_model=List[CategoryItem])
def get_serving_styles(db: Session = Depends(get_db)):
    """Get all serving styles."""
    return [
        {
            "value": s.value,
            "display_name": s.label,
            "description": s.description,
        }
        for s in get_active_serving_styles(db)
    ]


@router.get("/methods", response_model=List[CategoryItem])
def get_methods(db: Session = Depends(get_db)):
    """Get all preparation methods."""
    return [
        {
            "value": m.value,
            "display_name": m.label,
            "description": m.description,
        }
        for m in get_active_methods(db)
    ]
