"""
Audit logging service for tracking admin actions.
"""
import logging
import uuid
from typing import List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.user import User

logger = logging.getLogger(__name__)


class AuditService:
    @staticmethod
    def log(
        db: Session,
        admin_user_id: str,
        action: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        details: Optional[dict] = None,
    ) -> None:
        """Create an audit log entry. Fire-and-forget — never raises.

        Uses a SAVEPOINT so that a flush failure does not poison the
        caller's transaction (PendingRollbackError).
        """
        try:
            with db.begin_nested():
                entry = AuditLog(
                    id=str(uuid.uuid4()),
                    admin_user_id=admin_user_id,
                    action=action,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    details=details,
                )
                db.add(entry)
                db.flush()
        except Exception as e:
            logger.error(f"Audit log failed: {e}")

    @staticmethod
    def list_audit_logs(
        db: Session,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
        from_date=None,
        to_date=None,
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[List, int]:
        """Query audit logs with optional filters. Returns (items, total_count)."""
        # Build filter conditions once — shared by count and data queries
        filters = []
        if action:
            filters.append(AuditLog.action == action)
        if entity_type:
            filters.append(AuditLog.entity_type == entity_type)
        if from_date:
            filters.append(AuditLog.created_at >= from_date)
        if to_date:
            filters.append(AuditLog.created_at <= to_date)

        # Count on AuditLog only — no JOIN needed
        count_query = db.query(func.count(AuditLog.id))
        for f in filters:
            count_query = count_query.filter(f)
        total = count_query.scalar()

        # Data query with JOIN for admin_email (RESTRICT FK guarantees user exists)
        data_query = db.query(AuditLog, User.email.label("admin_email")).join(
            User, AuditLog.admin_user_id == User.id
        )
        for f in filters:
            data_query = data_query.filter(f)

        items = (
            data_query.order_by(AuditLog.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        return items, total
