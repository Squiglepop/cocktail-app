"""
Category table models for database-driven category management.

These tables replace Python enums for categories, allowing admin modification
without code deployments.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Boolean, Integer, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from .recipe import Base, generate_uuid


class CategoryTemplate(Base):
    """Cocktail template/family category table."""
    __tablename__ = "category_templates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    value: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )


class CategoryGlassware(Base):
    """Glassware category table."""
    __tablename__ = "category_glassware"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    value: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # stemmed/short/tall/specialty
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )


class CategoryServingStyle(Base):
    """Serving style category table."""
    __tablename__ = "category_serving_styles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    value: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )


class CategoryMethod(Base):
    """Preparation method category table."""
    __tablename__ = "category_methods"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    value: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )


class CategorySpirit(Base):
    """Spirit category table."""
    __tablename__ = "category_spirits"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    value: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
