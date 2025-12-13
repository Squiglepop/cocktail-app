"""
Pydantic schemas for collections (playlists).
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class CollectionBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    is_public: bool = False


class CollectionCreate(CollectionBase):
    pass


class CollectionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_public: Optional[bool] = None


class CollectionRecipeAdd(BaseModel):
    recipe_id: str
    position: Optional[int] = None


class CollectionRecipeReorder(BaseModel):
    recipe_id: str
    position: int


class CollectionRecipeResponse(BaseModel):
    id: str
    recipe_id: str
    recipe_name: str
    recipe_template: Optional[str] = None
    recipe_main_spirit: Optional[str] = None
    recipe_has_image: bool = False
    position: int
    added_at: datetime

    class Config:
        from_attributes = True


class CollectionResponse(CollectionBase):
    id: str
    user_id: str
    recipe_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CollectionDetailResponse(CollectionResponse):
    recipes: List[CollectionRecipeResponse] = Field(default_factory=list)


class CollectionListResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    is_public: bool
    recipe_count: int
    created_at: datetime

    class Config:
        from_attributes = True
