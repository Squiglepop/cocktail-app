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
    Visibility,
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
    visibility: str = Field(default=Visibility.PUBLIC.value)


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
    visibility: Optional[str] = None


class RecipeRatingUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)


class RecipeResponse(RecipeBase):
    id: str
    source_url: Optional[str] = None
    source_type: Optional[str] = None
    user_id: Optional[str] = None
    visibility: str = Visibility.PUBLIC.value
    my_rating: Optional[int] = None  # Current user's rating for this recipe
    has_image: bool = False
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
    has_image: bool = False
    user_id: Optional[str] = None
    visibility: str = Visibility.PUBLIC.value
    my_rating: Optional[int] = None  # Current user's rating for this recipe
    created_at: datetime

    class Config:
        from_attributes = True


# --- Extraction Schemas ---


class ExtractedIngredient(BaseModel):
    """Ingredient as extracted from image.

    Field lengths are constrained to prevent abuse via oversized AI outputs.
    """
    name: str = Field(..., min_length=1, max_length=200)
    amount: Optional[float] = Field(None, ge=0, le=10000)
    unit: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = Field(None, max_length=500)
    type: Optional[str] = Field(None, max_length=50)  # Will be mapped to IngredientType


class ExtractedRecipe(BaseModel):
    """Recipe as extracted from image by AI.

    Field lengths are constrained to prevent abuse via oversized AI outputs
    or prompt injection attacks that generate excessive content.
    """
    name: str = Field(..., min_length=1, max_length=300)
    description: Optional[str] = Field(None, max_length=2000)
    ingredients: List[ExtractedIngredient] = Field(default_factory=list, max_length=50)
    instructions: Optional[str] = Field(None, max_length=10000)
    template: Optional[str] = Field(None, max_length=100)  # Will be mapped to CocktailTemplate
    main_spirit: Optional[str] = Field(None, max_length=100)  # Will be mapped to SpiritCategory
    glassware: Optional[str] = Field(None, max_length=100)  # Will be mapped to Glassware
    serving_style: Optional[str] = Field(None, max_length=100)  # Will be mapped to ServingStyle
    method: Optional[str] = Field(None, max_length=100)  # Will be mapped to Method
    garnish: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = Field(None, max_length=5000)


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


# --- Duplicate Detection Schemas ---


class DuplicateMatchResponse(BaseModel):
    """A potential duplicate match."""
    recipe_id: str
    recipe_name: str
    match_type: str  # "exact_image", "similar_image", "same_recipe"
    confidence: float  # 0.0 to 1.0
    details: str


class DuplicateCheckResponse(BaseModel):
    """Response from duplicate detection check."""
    is_duplicate: bool
    matches: List[DuplicateMatchResponse] = Field(default_factory=list)


class UploadWithDuplicateCheckResponse(BaseModel):
    """Response from upload endpoint with duplicate detection."""
    job: ExtractionJobResponse
    duplicates: Optional[DuplicateCheckResponse] = None


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
