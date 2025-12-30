"""
SQLAlchemy model for refresh tokens.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column

from .recipe import Base, generate_uuid


class RefreshToken(Base):
    """Refresh token storage for JWT authentication."""
    __tablename__ = "refresh_tokens"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    jti: Mapped[str] = mapped_column(
        String(36), unique=True, index=True, nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Optional: token family for rotation tracking
    family_id: Mapped[Optional[str]] = mapped_column(
        String(36), nullable=True, index=True
    )

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")
