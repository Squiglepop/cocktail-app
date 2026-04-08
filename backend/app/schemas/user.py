"""
Admin user management schemas.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, model_validator


class UserAdminResponse(BaseModel):
    """Built from dicts, NOT model instances (recipe_count is computed)."""
    id: str
    email: str
    display_name: Optional[str] = None
    is_active: bool
    is_admin: bool
    recipe_count: int
    created_at: datetime
    last_login_at: Optional[datetime] = None


class UserListResponse(BaseModel):
    items: List[UserAdminResponse]
    total: int
    page: int
    per_page: int


class UserStatusUpdate(BaseModel):
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None

    @model_validator(mode="after")
    def at_least_one_field(self):
        if self.is_active is None and self.is_admin is None:
            raise ValueError("At least one of is_active or is_admin must be provided")
        return self


class UserStatusResponse(BaseModel):
    id: str
    email: str
    display_name: Optional[str] = None
    is_active: bool
    is_admin: bool
    message: str
