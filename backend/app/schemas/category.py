"""
Admin category management schemas.
"""
import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


SNAKE_CASE_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


class CategoryCreate(BaseModel):
    value: str = Field(max_length=50)
    label: str = Field(max_length=100)
    description: Optional[str] = None
    category: Optional[str] = Field(default=None, max_length=50)

    @field_validator("value")
    @classmethod
    def validate_snake_case(cls, v: str) -> str:
        if not SNAKE_CASE_PATTERN.match(v):
            raise ValueError(
                "Value must be snake_case (lowercase letters, digits, underscores, starting with a letter)"
            )
        return v


class CategoryUpdate(BaseModel):
    label: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class CategoryAdminResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    value: str
    label: str
    description: Optional[str] = None
    category: Optional[str] = None
    sort_order: int
    is_active: bool
    created_at: datetime


class CategoryReorderRequest(BaseModel):
    ids: list[str]


class CategoryDeleteResponse(BaseModel):
    message: str
    recipe_count: int
