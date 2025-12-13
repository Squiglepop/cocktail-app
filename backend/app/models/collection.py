"""
SQLAlchemy models for recipe collections (playlists).
"""
import uuid
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import String, Text, DateTime, ForeignKey, Boolean, Integer, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column

from .recipe import Base, generate_uuid

if TYPE_CHECKING:
    from .user import User
    from .recipe import Recipe


class Collection(Base):
    """Collection (playlist) of recipes."""
    __tablename__ = "collections"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Owner (required - collections must have an owner)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Privacy setting (private by default)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="collections")
    collection_recipes: Mapped[List["CollectionRecipe"]] = relationship(
        "CollectionRecipe", back_populates="collection", cascade="all, delete-orphan"
    )
    shares: Mapped[List["CollectionShare"]] = relationship(
        "CollectionShare", back_populates="collection", cascade="all, delete-orphan"
    )

    @property
    def recipe_count(self) -> int:
        """Number of recipes in this collection."""
        return len(self.collection_recipes)


class CollectionRecipe(Base):
    """Junction table for collections and recipes."""
    __tablename__ = "collection_recipes"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    collection_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("collections.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recipe_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Position for ordering within the collection
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # When the recipe was added
    added_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    collection: Mapped["Collection"] = relationship("Collection", back_populates="collection_recipes")
    recipe: Mapped["Recipe"] = relationship("Recipe")


class CollectionShare(Base):
    """Sharing a collection with another user."""
    __tablename__ = "collection_shares"
    __table_args__ = (
        UniqueConstraint("collection_id", "shared_with_user_id", name="uq_collection_share"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    collection_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("collections.id", ondelete="CASCADE"), nullable=False, index=True
    )
    shared_with_user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Permission level - can the shared user edit (add/remove/reorder recipes)?
    can_edit: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # When the share was created
    shared_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    collection: Mapped["Collection"] = relationship("Collection", back_populates="shares")
    shared_with_user: Mapped["User"] = relationship("User", back_populates="shared_collections")
