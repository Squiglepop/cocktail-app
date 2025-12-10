"""
Pydantic schemas for API validation and serialization.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.enums import (
    CocktailTemplate,
    Glassware,
    ServingStyle,
    Method,
    SpiritCategory,
    IngredientType,
    Unit,
)


# --- Ingredient Schemas ---


class IngredientBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    type: str
    spirit_category: Optional[str] = None
    description: Optional[str] = None
    common_brands: Optional[str] = None


class IngredientCreate(IngredientBase):
    pass


class IngredientResponse(IngredientBase):
    id: str

    class Config:
        from_attributes = True


# --- Recipe Ingredient Schemas ---


class RecipeIngredientBase(BaseModel):
    amount: Optional[float] = Field(None, ge=0)
    unit: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=255)
    optional: bool = False
    order: int = 0


class RecipeIngredientCreate(RecipeIngredientBase):
    ingredient_id: Optional[str] = None
    ingredient_name: Optional[str] = None  # For creating new ingredients on-the-fly
    ingredient_type: Optional[str] = None


class RecipeIngredientResponse(RecipeIngredientBase):
    id: str
    ingredient: IngredientResponse

    class Config:
        from_attributes = True


# --- Recipe Schemas ---


class RecipeBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    instructions: Optional[str] = None
    template: Optional[str] = None
    main_spirit: Optional[str] = None
    glassware: Optional[str] = None
    serving_style: Optional[str] = None
    method: Optional[str] = None
    garnish: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None


class RecipeCreate(RecipeBase):
    ingredients: List[RecipeIngredientCreate] = Field(default_factory=list)


class RecipeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    instructions: Optional[str] = None
    template: Optional[str] = None
    main_spirit: Optional[str] = None
    glassware: Optional[str] = None
    serving_style: Optional[str] = None
    method: Optional[str] = None
    garnish: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None
    ingredients: Optional[List[RecipeIngredientCreate]] = None


class RecipeResponse(RecipeBase):
    id: str
    source_image_path: Optional[str] = None
    source_url: Optional[str] = None
    source_type: Optional[str] = None
    user_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    ingredients: List[RecipeIngredientResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


class RecipeListResponse(BaseModel):
    id: str
    name: str
    template: Optional[str] = None
    main_spirit: Optional[str] = None
    glassware: Optional[str] = None
    serving_style: Optional[str] = None
    source_image_path: Optional[str] = None
    user_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# --- Extraction Schemas ---


class ExtractedIngredient(BaseModel):
    """Ingredient as extracted from image."""
    name: str
    amount: Optional[float] = None
    unit: Optional[str] = None
    notes: Optional[str] = None
    type: Optional[str] = None  # Will be mapped to IngredientType


class ExtractedRecipe(BaseModel):
    """Recipe as extracted from image by AI."""
    name: str
    description: Optional[str] = None
    ingredients: List[ExtractedIngredient] = Field(default_factory=list)
    instructions: Optional[str] = None
    template: Optional[str] = None  # Will be mapped to CocktailTemplate
    main_spirit: Optional[str] = None  # Will be mapped to SpiritCategory
    glassware: Optional[str] = None  # Will be mapped to Glassware
    serving_style: Optional[str] = None  # Will be mapped to ServingStyle
    method: Optional[str] = None  # Will be mapped to Method
    garnish: Optional[str] = None
    notes: Optional[str] = None


class ExtractionJobResponse(BaseModel):
    id: str
    status: str
    image_path: str
    recipe_id: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# --- Filter/Query Schemas ---


class RecipeFilters(BaseModel):
    template: Optional[str] = None
    main_spirit: Optional[str] = None
    glassware: Optional[str] = None
    serving_style: Optional[str] = None
    method: Optional[str] = None
    search: Optional[str] = None  # Search in name/description


# --- Category Schemas ---


class CategoryItem(BaseModel):
    value: str
    display_name: str
    description: Optional[str] = None


class CategoryGroup(BaseModel):
    name: str
    items: List[CategoryItem]


class CategoriesResponse(BaseModel):
    templates: List[CategoryItem]
    spirits: List[CategoryItem]
    glassware: List[CategoryGroup]  # Grouped by category
    serving_styles: List[CategoryItem]
    methods: List[CategoryItem]
