"""
SQLAlchemy model for user ratings.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column

from .recipe import Base, generate_uuid


class UserRating(Base):
    """User rating table - stores personal ratings for any recipe."""
    __tablename__ = "user_ratings"
    __table_args__ = (
        UniqueConstraint('user_id', 'recipe_id', name='uq_user_rating'),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recipe_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="ratings")
    recipe: Mapped["Recipe"] = relationship("Recipe", back_populates="user_ratings")


# Import at the end to avoid circular imports
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .user import User
    from .recipe import Recipe
