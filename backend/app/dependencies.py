"""
FastAPI dependencies for authorization and common patterns.
"""
from fastapi import Depends, HTTPException

from app.models import User
from app.services.auth import get_current_user


async def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Require admin privileges for endpoint access.

    Validates that the current user has admin privileges. Returns 403 Forbidden
    if the user is not an admin.

    Note: get_current_user already validates is_active (auth.py:204),
    so deactivated users are rejected before reaching this check.

    Args:
        current_user: The authenticated user from get_current_user dependency.

    Returns:
        The authenticated admin user.

    Raises:
        HTTPException: 403 Forbidden if user is not an admin.
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
