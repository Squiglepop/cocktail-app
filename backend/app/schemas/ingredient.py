"""
Admin ingredient management schemas.
"""
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class IngredientAdminCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    type: Literal[
        "spirit", "liqueur", "wine_fortified", "bitter", "syrup",
        "juice", "mixer", "dairy", "egg", "garnish", "other",
    ]
    spirit_category: Optional[str] = Field(default=None, max_length=50)
    description: Optional[str] = None
    common_brands: Optional[str] = None


class IngredientAdminUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    type: Optional[Literal[
        "spirit", "liqueur", "wine_fortified", "bitter", "syrup",
        "juice", "mixer", "dairy", "egg", "garnish", "other",
    ]] = None
    spirit_category: Optional[str] = Field(default=None, max_length=50)
    description: Optional[str] = None
    common_brands: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def reject_null_required_fields(cls, data):
        if isinstance(data, dict):
            for field in ("name", "type"):
                if field in data and data[field] is None:
                    raise ValueError(f"'{field}' cannot be null")
        return data


class IngredientAdminResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    type: str
    spirit_category: Optional[str] = None
    description: Optional[str] = None
    common_brands: Optional[str] = None


class IngredientListResponse(BaseModel):
    items: List[IngredientAdminResponse]
    total: int
    page: int
    per_page: int


class IngredientDeleteResponse(BaseModel):
    message: str
    recipe_count: int


DETECTION_REASONS = Literal[
    "exact_match_case_insensitive", "fuzzy_match", "variation_pattern"
]


class DuplicateMatch(BaseModel):
    ingredient_id: str
    name: str
    type: str
    similarity_score: float = Field(description="1.0 for target (reference point); actual ratio for duplicates")
    detection_reason: DETECTION_REASONS
    usage_count: int


class DuplicateGroup(BaseModel):
    target: DuplicateMatch
    duplicates: List[DuplicateMatch]
    group_reason: DETECTION_REASONS


class DuplicateDetectionResponse(BaseModel):
    groups: List[DuplicateGroup]
    total_groups: int
    total_duplicates: int


class IngredientMergeRequest(BaseModel):
    source_ids: List[str] = Field(min_length=1)
    target_id: str

    @model_validator(mode="before")
    @classmethod
    def deduplicate_source_ids(cls, data):
        if isinstance(data, dict) and "source_ids" in data:
            data["source_ids"] = list(dict.fromkeys(data["source_ids"]))
        return data


class IngredientMergeResponse(BaseModel):
    message: str
    recipes_affected: int
    sources_removed: int
