"""
SQLAlchemy models for cocktail recipes.
"""
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    String,
    Text,
    DateTime,
    ForeignKey,
    Float,
    LargeBinary,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column

from .enums import (
    CocktailTemplate,
    Glassware,
    ServingStyle,
    Method,
    SpiritCategory,
    IngredientType,
    Unit,
)


class Base(DeclarativeBase):
    pass


def generate_uuid():
    return str(uuid.uuid4())


class Recipe(Base):
    """Main recipe table."""
    __tablename__ = "recipes"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Classifications - store as strings for SQLite compatibility
    template: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    main_spirit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    glassware: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    serving_style: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)

    # Source tracking
    source_image_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    source_image_data: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    source_image_mime: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    source_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Metadata
    garnish: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # User ownership (nullable for existing/anonymous recipes)
    user_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    ingredients: Mapped[List["RecipeIngredient"]] = relationship(
        "RecipeIngredient", back_populates="recipe", cascade="all, delete-orphan"
    )
    user: Mapped[Optional["User"]] = relationship(
        "User", back_populates="recipes"
    )

    @property
    def has_image(self) -> bool:
        """Check if recipe has image data stored."""
        return self.source_image_data is not None


class Ingredient(Base):
    """Ingredient master table."""
    __tablename__ = "ingredients"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    spirit_category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    common_brands: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    recipe_ingredients: Mapped[List["RecipeIngredient"]] = relationship(
        "RecipeIngredient", back_populates="ingredient"
    )


class RecipeIngredient(Base):
    """Junction table for recipe ingredients with amounts."""
    __tablename__ = "recipe_ingredients"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    recipe_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False
    )
    ingredient_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("ingredients.id"), nullable=False
    )

    # Amount specification
    amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    unit: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Additional info
    notes: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    optional: Mapped[bool] = mapped_column(default=False)
    order: Mapped[int] = mapped_column(default=0)

    # Relationships
    recipe: Mapped["Recipe"] = relationship("Recipe", back_populates="ingredients")
    ingredient: Mapped["Ingredient"] = relationship("Ingredient", back_populates="recipe_ingredients")


class ExtractionJob(Base):
    """Track image extraction jobs."""
    __tablename__ = "extraction_jobs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    image_path: Mapped[str] = mapped_column(String(512), nullable=False)

    # Result
    recipe_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("recipes.id", ondelete="SET NULL"), nullable=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_extraction: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


# Import User at the end to avoid circular import issues
# The relationship is defined via string reference above
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .user import User
