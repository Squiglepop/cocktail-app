"""
Admin user management service.
"""
from typing import Dict, List, Optional, Tuple

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..models.recipe import Recipe
from ..models.user import User
from ..schemas.user import UserStatusUpdate
from .auth import revoke_all_user_tokens


def list_users(
    db: Session,
    page: int,
    per_page: int,
    search: Optional[str] = None,
    status_filter: Optional[str] = None,
) -> Tuple[List[Dict], int]:
    """List users with computed recipe_count. Returns (list of dicts, total count)."""
    # Base query with filters (no subquery — used for counting)
    base_query = db.query(User)

    if search:
        escaped = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        search_filter = or_(
            User.email.ilike(f"%{escaped}%", escape="\\"),
            User.display_name.ilike(f"%{escaped}%", escape="\\"),
        )
        base_query = base_query.filter(search_filter)

    if status_filter == "active":
        base_query = base_query.filter(User.is_active == True)
    elif status_filter == "inactive":
        base_query = base_query.filter(User.is_active == False)

    total = base_query.count()

    # Data query adds recipe_count subquery only for the fetched page
    recipe_count_subq = (
        db.query(func.count(Recipe.id))
        .filter(Recipe.user_id == User.id)
        .correlate(User)
        .scalar_subquery()
    )

    rows = (
        base_query.with_entities(User, recipe_count_subq.label("recipe_count"))
        .order_by(User.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    items = []
    for user, recipe_count in rows:
        items.append({
            "id": user.id,
            "email": user.email,
            "display_name": user.display_name,
            "is_active": user.is_active,
            "is_admin": user.is_admin,
            "recipe_count": recipe_count,
            "created_at": user.created_at,
            "last_login_at": user.last_login_at,
        })

    return items, total


def update_user_status(
    db: Session,
    user: User,
    data: UserStatusUpdate,
    admin_id: str,
) -> Tuple[User, str]:
    """Update user active/admin status. Returns (updated_user, message)."""
    if user.id == admin_id:
        if data.is_active is False:
            raise ValueError("Cannot deactivate your own account")
        if data.is_admin is False:
            raise ValueError("Cannot remove your own admin status")

    changes = []
    if data.is_active is not None and data.is_active != user.is_active:
        if data.is_active is False:
            revoke_all_user_tokens(db, user.id)
        user.is_active = data.is_active
        changes.append("activated" if data.is_active else "deactivated")

    if data.is_admin is not None and data.is_admin != user.is_admin:
        user.is_admin = data.is_admin
        changes.append("granted admin" if data.is_admin else "revoked admin")

    if data.display_name is not None and data.display_name != user.display_name:
        user.display_name = data.display_name
        changes.append(f"display_name updated to '{data.display_name}'")

    db.commit()
    db.refresh(user)
    message = f"User {', '.join(changes)}" if changes else "No changes applied"
    return user, message
