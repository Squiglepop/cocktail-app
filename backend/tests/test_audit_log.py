"""
Tests for audit log infrastructure (Story 4-1).
"""
import logging
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from app.services.audit_service import AuditService


# --- Helper ---


def _create_audit_entry(db, admin_user_id, action="category_create",
                        entity_type="category", entity_id=None, details=None):
    AuditService.log(db, admin_user_id, action, entity_type, entity_id, details)
    db.commit()


# --- AC-8: Auth Tests ---


def test_get_audit_log_returns_401_without_auth(client):
    response = client.get("/api/admin/audit-log")
    assert response.status_code == 401


def test_get_audit_log_returns_403_for_regular_user(client, auth_token):
    response = client.get(
        "/api/admin/audit-log",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 403


# --- AC-2: AuditService.log() Tests ---


def test_audit_log_creates_record(test_session, admin_user):
    AuditService.log(
        test_session, admin_user.id, "category_create", "category",
        entity_id="cat-123", details={"name": "Sour"},
    )
    test_session.commit()

    from app.models.audit_log import AuditLog
    records = test_session.query(AuditLog).all()
    assert len(records) == 1
    record = records[0]
    assert record.admin_user_id == admin_user.id
    assert record.action == "category_create"
    assert record.entity_type == "category"
    assert record.entity_id == "cat-123"
    assert record.details == {"name": "Sour"}
    assert record.created_at is not None


def test_audit_log_with_details_json(test_session, admin_user):
    details = {"old": {"name": "A"}, "new": {"name": "B"}, "changed": ["name"]}
    AuditService.log(
        test_session, admin_user.id, "category_update", "category",
        entity_id="cat-1", details=details,
    )
    test_session.commit()

    from app.models.audit_log import AuditLog
    record = test_session.query(AuditLog).first()
    assert record.details == details


def test_audit_log_without_entity_id(test_session, admin_user):
    AuditService.log(test_session, admin_user.id, "user_activate", "user")
    test_session.commit()

    from app.models.audit_log import AuditLog
    record = test_session.query(AuditLog).first()
    assert record.entity_id is None


def test_audit_log_without_details(test_session, admin_user):
    AuditService.log(
        test_session, admin_user.id, "recipe_admin_delete", "recipe",
        entity_id="r-1",
    )
    test_session.commit()

    from app.models.audit_log import AuditLog
    record = test_session.query(AuditLog).first()
    assert record.details is None


# --- AC-3: Fire-and-Forget Tests ---


def test_audit_log_failure_does_not_raise(test_session, admin_user):
    with patch.object(test_session, "add", side_effect=Exception("DB exploded")):
        # Should NOT raise — fire-and-forget
        AuditService.log(
            test_session, admin_user.id, "category_create", "category",
        )


def test_audit_log_failure_logs_error(test_session, admin_user, caplog):
    with patch.object(test_session, "add", side_effect=Exception("DB exploded")):
        with caplog.at_level(logging.ERROR, logger="app.services.audit_service"):
            AuditService.log(
                test_session, admin_user.id, "category_create", "category",
            )
    assert "Audit log failed" in caplog.text
    assert "DB exploded" in caplog.text


def test_audit_log_flush_failure_does_not_poison_session(test_session, admin_user):
    """Verify that a DB-level flush failure in AuditService.log() does NOT
    leave the session in PendingRollbackError state — the caller's transaction
    must remain usable (savepoint isolation)."""
    from app.models.audit_log import AuditLog
    import uuid as _uuid

    original_flush = test_session.flush

    call_count = [0]

    def fail_once(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] == 1:
            raise Exception("Simulated flush failure")
        return original_flush(*args, **kwargs)

    with patch.object(test_session, "flush", side_effect=fail_once):
        AuditService.log(
            test_session, admin_user.id, "category_create", "category",
        )

    # Session must still be usable — this is the critical assertion
    entry = AuditLog(
        id=str(_uuid.uuid4()),
        admin_user_id=admin_user.id,
        action="after_failure",
        entity_type="category",
        created_at=datetime.now(timezone.utc),
    )
    test_session.add(entry)
    test_session.flush()
    test_session.commit()

    records = test_session.query(AuditLog).filter(
        AuditLog.action == "after_failure"
    ).all()
    assert len(records) == 1


# --- AC-4: Paginated List Tests ---


def test_list_audit_logs_returns_paginated_results(client, admin_auth_token, admin_user, test_session):
    for i in range(3):
        _create_audit_entry(test_session, admin_user.id, action=f"action_{i}", entity_type="category")

    response = client.get(
        "/api/admin/audit-log",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3
    assert data["page"] == 1
    assert data["per_page"] == 20


def test_list_audit_logs_ordered_by_created_at_desc(test_session, admin_user):
    from app.models.audit_log import AuditLog
    import uuid

    now = datetime.now(timezone.utc)
    for i in range(3):
        entry = AuditLog(
            id=str(uuid.uuid4()),
            admin_user_id=admin_user.id,
            action=f"action_{i}",
            entity_type="category",
            created_at=now - timedelta(hours=2 - i),  # 0 oldest, 2 newest
        )
        test_session.add(entry)
    test_session.commit()

    items, total = AuditService.list_audit_logs(test_session)
    assert total == 3
    assert items[0][0].action == "action_2"  # newest first
    assert items[2][0].action == "action_0"  # oldest last


def test_list_audit_logs_ordered_by_created_at_desc_via_http(client, admin_auth_token, admin_user, test_session):
    """AC-4: Verify newest-first ordering at HTTP level."""
    from app.models.audit_log import AuditLog
    import uuid

    now = datetime.now(timezone.utc)
    for i in range(3):
        entry = AuditLog(
            id=str(uuid.uuid4()),
            admin_user_id=admin_user.id,
            action=f"action_{i}",
            entity_type="category",
            created_at=now - timedelta(hours=2 - i),  # 0 oldest, 2 newest
        )
        test_session.add(entry)
    test_session.commit()

    response = client.get(
        "/api/admin/audit-log",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    actions = [item["action"] for item in data["items"]]
    assert actions == ["action_2", "action_1", "action_0"]


def test_list_audit_logs_empty_returns_empty_list(client, admin_auth_token):
    response = client.get(
        "/api/admin/audit-log",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


# --- AC-5, 6, 7: Filter Tests ---


def test_filter_by_action(client, admin_auth_token, admin_user, test_session):
    _create_audit_entry(test_session, admin_user.id, action="category_create", entity_type="category")
    _create_audit_entry(test_session, admin_user.id, action="user_activate", entity_type="user")

    response = client.get(
        "/api/admin/audit-log?action=category_create",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["action"] == "category_create"


def test_filter_by_entity_type(client, admin_auth_token, admin_user, test_session):
    _create_audit_entry(test_session, admin_user.id, action="category_create", entity_type="category")
    _create_audit_entry(test_session, admin_user.id, action="user_activate", entity_type="user")

    response = client.get(
        "/api/admin/audit-log?entity_type=user",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["entity_type"] == "user"


def test_filter_by_date_range(test_session, admin_user):
    from app.models.audit_log import AuditLog
    import uuid

    now = datetime.now(timezone.utc)
    dates = [
        now - timedelta(days=10),  # outside range
        now - timedelta(days=3),   # inside range
        now - timedelta(days=1),   # inside range
    ]
    for i, dt in enumerate(dates):
        entry = AuditLog(
            id=str(uuid.uuid4()),
            admin_user_id=admin_user.id,
            action=f"action_{i}",
            entity_type="category",
            created_at=dt,
        )
        test_session.add(entry)
    test_session.commit()

    from_date = now - timedelta(days=5)
    to_date = now
    items, total = AuditService.list_audit_logs(
        test_session, from_date=from_date, to_date=to_date,
    )
    assert total == 2


def test_filter_combined_action_and_entity_type(client, admin_auth_token, admin_user, test_session):
    _create_audit_entry(test_session, admin_user.id, action="category_create", entity_type="category")
    _create_audit_entry(test_session, admin_user.id, action="category_create", entity_type="ingredient")
    _create_audit_entry(test_session, admin_user.id, action="user_activate", entity_type="user")

    response = client.get(
        "/api/admin/audit-log?action=category_create&entity_type=category",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["action"] == "category_create"
    assert data["items"][0]["entity_type"] == "category"


# --- Pagination Tests ---


def test_pagination_page_2(client, admin_auth_token, admin_user, test_session):
    for i in range(5):
        _create_audit_entry(test_session, admin_user.id, action=f"action_{i}", entity_type="category")

    response = client.get(
        "/api/admin/audit-log?page=2&per_page=2",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["page"] == 2


def test_pagination_per_page_limit(client, admin_auth_token, admin_user, test_session):
    for i in range(10):
        _create_audit_entry(test_session, admin_user.id, action=f"action_{i}", entity_type="category")

    response = client.get(
        "/api/admin/audit-log?per_page=3",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 10
    assert len(data["items"]) == 3


# --- Review Fix: HTTP-level date range filter test (AC-7) ---


def test_filter_by_date_range_via_http(client, admin_auth_token, admin_user, test_session):
    """AC-7: Verify ?from=&to= query aliases work at HTTP level."""
    from app.models.audit_log import AuditLog
    import uuid

    now = datetime.now(timezone.utc)
    # Old entry — outside range
    old = AuditLog(
        id=str(uuid.uuid4()), admin_user_id=admin_user.id,
        action="old_action", entity_type="category",
        created_at=now - timedelta(days=30),
    )
    # Recent entry — inside range
    recent = AuditLog(
        id=str(uuid.uuid4()), admin_user_id=admin_user.id,
        action="recent_action", entity_type="category",
        created_at=now - timedelta(days=1),
    )
    test_session.add_all([old, recent])
    test_session.commit()

    from_str = (now - timedelta(days=5)).strftime("%Y-%m-%dT%H:%M:%S")
    to_str = now.strftime("%Y-%m-%dT%H:%M:%S")

    response = client.get(
        f"/api/admin/audit-log?from={from_str}&to={to_str}",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["action"] == "recent_action"


# --- Review Fix: Verify admin_email populated in response ---


def test_audit_log_response_includes_admin_email(client, admin_auth_token, admin_user, test_session):
    _create_audit_entry(test_session, admin_user.id, action="category_create", entity_type="category")

    response = client.get(
        "/api/admin/audit-log",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["admin_email"] == admin_user.email


# --- Review Fix: per_page upper bound enforcement ---


def test_per_page_exceeding_max_returns_422(client, admin_auth_token):
    response = client.get(
        "/api/admin/audit-log?per_page=200",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 422
