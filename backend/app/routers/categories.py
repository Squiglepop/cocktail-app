"""
Category endpoints for dropdowns and filters.
"""
from fastapi import APIRouter

from app.models.enums import (
    CocktailTemplate,
    Glassware,
    GlasswareCategory,
    ServingStyle,
    Method,
    SpiritCategory,
    GLASSWARE_CATEGORIES,
    TEMPLATE_DISPLAY_NAMES,
    TEMPLATE_DESCRIPTIONS,
    GLASSWARE_DISPLAY_NAMES,
    SERVING_STYLE_DESCRIPTIONS,
    METHOD_DESCRIPTIONS,
)
from app.schemas import CategoryItem, CategoryGroup, CategoriesResponse


router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=CategoriesResponse)
def get_all_categories():
    """Get all category options for filters/dropdowns."""

    # Templates
    templates = [
        CategoryItem(
            value=t.value,
            display_name=TEMPLATE_DISPLAY_NAMES.get(t, t.value),
            description=TEMPLATE_DESCRIPTIONS.get(t),
        )
        for t in CocktailTemplate
    ]

    # Spirits
    spirits = [
        CategoryItem(value=s.value, display_name=s.value.replace("_", " ").title())
        for s in SpiritCategory
    ]

    # Glassware - grouped by category
    glassware_groups = {}
    for glass in Glassware:
        category = GLASSWARE_CATEGORIES.get(glass, GlasswareCategory.SPECIALTY)
        if category not in glassware_groups:
            glassware_groups[category] = []
        glassware_groups[category].append(
            CategoryItem(
                value=glass.value,
                display_name=GLASSWARE_DISPLAY_NAMES.get(glass, glass.value),
            )
        )

    glassware = [
        CategoryGroup(name=cat.value.title(), items=items)
        for cat, items in glassware_groups.items()
    ]

    # Serving styles
    serving_styles = [
        CategoryItem(
            value=s.value,
            display_name=s.value.replace("_", " ").title(),
            description=SERVING_STYLE_DESCRIPTIONS.get(s),
        )
        for s in ServingStyle
    ]

    # Methods
    methods = [
        CategoryItem(
            value=m.value,
            display_name=m.value.replace("_", " ").title(),
            description=METHOD_DESCRIPTIONS.get(m),
        )
        for m in Method
    ]

    return CategoriesResponse(
        templates=templates,
        spirits=spirits,
        glassware=glassware,
        serving_styles=serving_styles,
        methods=methods,
    )


@router.get("/templates")
def get_templates():
    """Get all cocktail templates/families."""
    return [
        {
            "value": t.value,
            "display_name": TEMPLATE_DISPLAY_NAMES.get(t, t.value),
            "description": TEMPLATE_DESCRIPTIONS.get(t),
        }
        for t in CocktailTemplate
    ]


@router.get("/spirits")
def get_spirits():
    """Get all spirit categories."""
    return [
        {"value": s.value, "display_name": s.value.replace("_", " ").title()}
        for s in SpiritCategory
    ]


@router.get("/glassware")
def get_glassware():
    """Get all glassware options grouped by category."""
    glassware_groups = {}
    for glass in Glassware:
        category = GLASSWARE_CATEGORIES.get(glass, GlasswareCategory.SPECIALTY)
        if category not in glassware_groups:
            glassware_groups[category] = []
        glassware_groups[category].append(
            {
                "value": glass.value,
                "display_name": GLASSWARE_DISPLAY_NAMES.get(glass, glass.value),
            }
        )

    return [
        {"category": cat.value, "name": cat.value.title(), "items": items}
        for cat, items in glassware_groups.items()
    ]


@router.get("/serving-styles")
def get_serving_styles():
    """Get all serving styles."""
    return [
        {
            "value": s.value,
            "display_name": s.value.replace("_", " ").title(),
            "description": SERVING_STYLE_DESCRIPTIONS.get(s),
        }
        for s in ServingStyle
    ]


@router.get("/methods")
def get_methods():
    """Get all preparation methods."""
    return [
        {
            "value": m.value,
            "display_name": m.value.replace("_", " ").title(),
            "description": METHOD_DESCRIPTIONS.get(m),
        }
        for m in Method
    ]
