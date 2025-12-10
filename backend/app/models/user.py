"""
SQLAlchemy model for users.
"""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import String, Text, DateTime, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column

from .recipe import Base, generate_uuid


class User(Base):
    """User account table."""
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    email: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    recipes: Mapped[List["Recipe"]] = relationship(
        "Recipe", back_populates="user", lazy="dynamic"
    )


# Import Recipe here to avoid circular import - the relationship is defined via string reference
from .recipe import Recipe
