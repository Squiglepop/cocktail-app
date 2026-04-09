# Story 4.1: Audit Log Infrastructure

Status: done

---

## Story

As a **system**,
I want **an audit logging service that records admin actions**,
So that **all administrative changes are tracked for compliance and troubleshooting**.

---

## Acceptance Criteria

### AC-1: Audit Log Table Migration

**Given** the migration runs
**When** it completes
**Then** the `admin_audit_log` table is created with:
- `id`: VARCHAR(36), primary key (UUID)
- `admin_user_id`: VARCHAR(36), NOT NULL (FK to users.id)
- `action`: VARCHAR(50), NOT NULL
- `entity_type`: VARCHAR(50), NOT NULL
- `entity_id`: VARCHAR(36), nullable
- `details`: JSON, nullable
- `created_at`: TIMESTAMP, NOT NULL, default=now

### AC-2: AuditService.log() Method

**Given** an AuditService exists
**When** `AuditService.log(db, admin_user_id, action, entity_type, entity_id, details)` is called
**Then** a new audit record is created with the provided data and auto-generated timestamp

### AC-3: Fire-and-Forget Error Handling

**Given** the AuditService.log() method fails (database error, etc.)
**When** the error occurs
**Then** the error is logged to application logs
**And** the calling admin operation is NOT blocked
**And** the admin operation completes successfully

### AC-4: Paginated Audit Log Endpoint

**Given** I am authenticated as an admin
**When** I call `GET /api/admin/audit-log`
**Then** I receive a paginated list of audit entries
**And** most recent entries appear first (ordered by `created_at` DESC)

### AC-5: Filter by Action

**Given** I call `GET /api/admin/audit-log?action=category_create`
**When** the response is returned
**Then** results are filtered to only that action type

### AC-6: Filter by Entity Type

**Given** I call `GET /api/admin/audit-log?entity_type=recipe`
**When** the response is returned
**Then** results are filtered to only that entity type

### AC-7: Filter by Date Range

**Given** I call `GET /api/admin/audit-log?from=2026-01-01&to=2026-01-31`
**When** the response is returned
**Then** results are filtered to that date range (inclusive)

### AC-8: Authorization

**Given** I am NOT an admin (regular user or unauthenticated)
**When** I call `GET /api/admin/audit-log`
**Then** I receive 401 (no token) or 403 (regular user)

---

## Tasks / Subtasks

### Task 1: Create AuditLog Model (AC: #1)

- [x] **1.1** Create `backend/app/models/audit_log.py`:
  - Class `AuditLog(Base)` with `__tablename__ = "admin_audit_log"`
  - Fields: `id` (String(36) PK, default=uuid4), `admin_user_id` (String(36), ForeignKey("users.id"), nullable=False), `action` (String(50), nullable=False, index=True), `entity_type` (String(50), nullable=False, index=True), `entity_id` (String(36), nullable=True), `details` (JSON, nullable=True), `created_at` (DateTime, nullable=False, default=func.now(), index=True)
  - Use SQLAlchemy 2.0 `Mapped[]` + `mapped_column()` syntax
  - Import `func` from `sqlalchemy` for `func.now()`
- [x] **1.2** Export `AuditLog` from `backend/app/models/__init__.py`

### Task 2: Create Alembic Migration (AC: #1)

- [x] **2.1** Generate migration: `alembic revision --autogenerate -m "create_audit_log_table"`
- [x] **2.2** REVIEW generated migration — verify:
  - Table name: `admin_audit_log`
  - FK constraint on `admin_user_id` references `users.id`
  - Indexes on `action`, `entity_type`, `created_at`
  - JSON column type (use `sa.JSON` — works for both SQLite and PostgreSQL)
- [x] **2.3** Test migration: `alembic upgrade head` then `alembic downgrade -1` then `alembic upgrade head`

### Task 3: Create AuditService (AC: #2, #3)

- [x] **3.1** Create `backend/app/services/audit_service.py`:
  - Class `AuditService` with static methods
  - `log(db, admin_user_id, action, entity_type, entity_id=None, details=None)` — creates audit record
  - Entire method body wrapped in `try/except Exception` — on failure, log error via `logger.error()` and return None (fire-and-forget)
  - Uses Python `logging` module: `logger = logging.getLogger(__name__)`
- [x] **3.2** Export `AuditService` from `backend/app/services/__init__.py`

### Task 4: Create Audit Schemas (AC: #4-7)

- [x] **4.1** Create `backend/app/schemas/audit.py`:
  - `AuditLogResponse`: id (str), admin_user_id (str), admin_email (Optional[str]), action (str), entity_type (str), entity_id (Optional[str]), details (Optional[dict]), created_at (datetime)
  - `AuditLogListResponse`: items (List[AuditLogResponse]), total (int), page (int), per_page (int)
  - `AuditLogFilter`: action (Optional[str]), entity_type (Optional[str]), from_date (Optional[datetime] aliased as "from"), to_date (Optional[datetime] aliased as "to"), page (int = 1), per_page (int = 20)
- [x] **4.2** Export new schemas from `backend/app/schemas/__init__.py`

### Task 5: Add Query Method to AuditService (AC: #4-7)

- [x] **5.1** Add to `audit_service.py`:
  - `list_audit_logs(db, action=None, entity_type=None, from_date=None, to_date=None, page=1, per_page=20)` — returns (items, total_count)
  - Filter chain: `.filter(AuditLog.action == action)` if action provided, etc.
  - Date range: `created_at >= from_date` and `created_at <= to_date` (inclusive)
  - Order: `created_at DESC`
  - Pagination: `.offset((page - 1) * per_page).limit(per_page)`
  - Join with User table to get admin_email for display

### Task 6: Add Audit Log Endpoint to Admin Router (AC: #4-8)

- [x] **6.1** Add to `backend/app/routers/admin.py`:
  - `GET /admin/audit-log` — protected by `require_admin`
  - Query params: `action` (Optional[str]), `entity_type` (Optional[str]), `from` (Optional[datetime] — use `Query(alias="from")` since `from` is a Python keyword), `to` (Optional[datetime] — use `Query(alias="to")`), `page` (int = 1), `per_page` (int = 20)
  - Returns `AuditLogListResponse`
  - Rate limit: `@limiter.limit("30/minute")` (read-heavy, allow more)
- [x] **6.2** Import AuditService, AuditLogListResponse, AuditLogResponse in admin.py

### Task 7: Write Tests (AC: #1-8)

- [x] **7.1** Create `backend/tests/test_audit_log.py`
- [x] **7.2** Auth tests (MANDATORY — AC-8):
  - `test_get_audit_log_returns_401_without_auth`
  - `test_get_audit_log_returns_403_for_regular_user`
- [x] **7.3** AuditService.log() tests (AC-2):
  - `test_audit_log_creates_record`
  - `test_audit_log_with_details_json`
  - `test_audit_log_without_entity_id`
  - `test_audit_log_without_details`
- [x] **7.4** Fire-and-forget tests (AC-3):
  - `test_audit_log_failure_does_not_raise` — mock `db.add` or `db.commit` to raise, verify no exception propagates
  - `test_audit_log_failure_logs_error` — verify `logger.error` called on failure
- [x] **7.5** Paginated list tests (AC-4):
  - `test_list_audit_logs_returns_paginated_results`
  - `test_list_audit_logs_ordered_by_created_at_desc`
  - `test_list_audit_logs_empty_returns_empty_list`
- [x] **7.6** Filter tests (AC-5, 6, 7):
  - `test_filter_by_action`
  - `test_filter_by_entity_type`
  - `test_filter_by_date_range`
  - `test_filter_combined_action_and_entity_type`
- [x] **7.7** Pagination tests:
  - `test_pagination_page_2`
  - `test_pagination_per_page_limit`
- [x] **7.8** Run full test suite: `pytest` — no regressions (496 existing + 21 new = 517 total)

### Task 8: Final Verification

- [x] **8.1** Run full backend test suite: `pytest` — all pass (517 passed)
- [x] **8.2** Run coverage: 100% on audit_service.py, audit_log.py, audit.py schemas
- [x] **8.3** Verify migration applies cleanly on fresh DB
- [x] **8.4** Update `docs/sprint-artifacts/sprint-status.yaml` — mark 4-1 as review

---

## Dev Notes

### CRITICAL: Fire-and-Forget Pattern

The single most important design constraint for AuditService: **audit failures MUST NEVER block admin operations**. The entire `log()` method body must be wrapped in try/except:

```python
import logging
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog
import uuid

logger = logging.getLogger(__name__)

class AuditService:
    @staticmethod
    def log(db: Session, admin_user_id: str, action: str, entity_type: str,
            entity_id: str = None, details: dict = None) -> None:
        try:
            entry = AuditLog(
                id=str(uuid.uuid4()),
                admin_user_id=admin_user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                details=details,
            )
            db.add(entry)
            db.flush()  # Flush within current transaction, don't commit separately
        except Exception as e:
            logger.error(f"Audit log failed: {e}")
            # DO NOT re-raise! Fire-and-forget.
```

**CRITICAL: Use `db.flush()` NOT `db.commit()`** — the audit log should participate in the calling operation's transaction. If the caller commits, the audit record is saved. If the caller rolls back, the audit record is also rolled back. This is correct behavior — we don't want orphaned audit records for operations that failed.

However, the fire-and-forget aspect means: if the `flush()` fails (e.g., constraint violation on audit table), we catch the exception and let the caller's operation proceed. The caller is responsible for its own `commit()`.

### CRITICAL: `from` is a Python Reserved Keyword

FastAPI query parameter `from` requires special handling:

```python
from fastapi import Query
from datetime import datetime
from typing import Optional

@router.get("/admin/audit-log")
@limiter.limit("30/minute")
async def get_audit_log(
    request: Request,
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    from_date: Optional[datetime] = Query(None, alias="from"),
    to_date: Optional[datetime] = Query(None, alias="to"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
```

### CRITICAL: JSON Column Compatibility

SQLAlchemy's `JSON` type works on both SQLite and PostgreSQL:
- PostgreSQL: Native JSONB
- SQLite: Stored as TEXT, deserialized by SQLAlchemy

Use `from sqlalchemy import JSON` — do NOT import from `sqlalchemy.dialects.postgresql`.

### Model Pattern — Follow Existing Convention

Use SQLAlchemy 2.0 `Mapped[]` syntax consistent with the project:

```python
from sqlalchemy import String, DateTime, JSON, ForeignKey, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column
from app.models import Base
from typing import Optional
import uuid

class AuditLog(Base):
    __tablename__ = "admin_audit_log"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    admin_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now(), index=True)
```

**Note:** Use `Optional` from `typing` (Python 3.9 compatible), NOT `str | None` (requires 3.10+).

### Audit Action Naming Convention

Actions follow `{entity}_{verb}` pattern in snake_case. For Story 4-1, no actions are wired yet (that's Story 4-2). But the service should accept any string — validation of action names is the caller's responsibility.

Known actions (for reference, wired in Story 4-2):
- `category_create`, `category_update`, `category_delete`
- `ingredient_create`, `ingredient_update`, `ingredient_delete`, `ingredient_merge`
- `recipe_admin_update`, `recipe_admin_delete`
- `user_activate`, `user_deactivate`, `user_grant_admin`, `user_revoke_admin`

### Admin Email in Response

The audit log endpoint should join with `User` to include the admin's email for display. Use a left join (admin user might theoretically be deleted):

```python
from sqlalchemy import select
from app.models.user import User
from app.models.audit_log import AuditLog

@staticmethod
def list_audit_logs(db: Session, action=None, entity_type=None,
                    from_date=None, to_date=None, page=1, per_page=20):
    query = db.query(AuditLog, User.email.label("admin_email")).outerjoin(
        User, AuditLog.admin_user_id == User.id
    )

    if action:
        query = query.filter(AuditLog.action == action)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if from_date:
        query = query.filter(AuditLog.created_at >= from_date)
    if to_date:
        query = query.filter(AuditLog.created_at <= to_date)

    total = query.count()
    items = query.order_by(AuditLog.created_at.desc()) \
                 .offset((page - 1) * per_page) \
                 .limit(per_page) \
                 .all()

    return items, total
```

### Rate Limiting Pattern

slowapi is already installed and configured in `main.py`. The admin router already imports `limiter` and `Request`. Follow the same pattern used in auth.py:

```python
from app.main import limiter
from starlette.requests import Request

@router.get("/admin/audit-log")
@limiter.limit("30/minute")
async def get_audit_log(request: Request, ...):
```

**Note:** `request: Request` parameter is REQUIRED for slowapi — it extracts the client IP for rate limiting.

### Extend Existing Files — File Actions

| File | Action | What to Add |
|------|--------|-------------|
| `backend/app/models/audit_log.py` | CREATE | AuditLog model |
| `backend/app/models/__init__.py` | MODIFY | Export AuditLog |
| `backend/app/services/audit_service.py` | CREATE | AuditService class with log() and list_audit_logs() |
| `backend/app/services/__init__.py` | MODIFY | Export AuditService |
| `backend/app/schemas/audit.py` | CREATE | AuditLogResponse, AuditLogListResponse |
| `backend/app/schemas/__init__.py` | MODIFY | Export new schemas |
| `backend/app/routers/admin.py` | MODIFY | Add GET /admin/audit-log endpoint |
| `backend/alembic/versions/xxx_create_audit_log_table.py` | CREATE (autogenerated) | Migration for admin_audit_log table |
| `backend/tests/test_audit_log.py` | CREATE | ~16 tests |

### Test Fixture Strategy

Reuse existing fixtures from `conftest.py`:
- `client` — TestClient with DB overrides and disabled rate limiting
- `admin_auth_token` — JWT for admin user
- `admin_user` — Admin user object (for creating audit records)
- `auth_token` — JWT for regular user (403 tests)
- `test_session` — SQLAlchemy session for direct DB manipulation

Create local test helper to seed audit records:

```python
def _create_audit_entry(db, admin_user_id, action="category_create",
                        entity_type="category", entity_id=None, details=None):
    from app.services.audit_service import AuditService
    AuditService.log(db, admin_user_id, action, entity_type, entity_id, details)
    db.commit()
```

### Auth Test Pattern (MANDATORY)

```python
def test_get_audit_log_returns_401_without_auth(client):
    response = client.get("/api/admin/audit-log")
    assert response.status_code == 401

def test_get_audit_log_returns_403_for_regular_user(client, auth_token):
    response = client.get(
        "/api/admin/audit-log",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 403
```

### Migration Sequence Context

This migration is the 5th in the admin panel migration sequence (per architecture doc):
1. `add_user_admin_fields` — DONE (Epic 1)
2. `create_category_tables` — DONE (Epic 1)
3. `seed_categories_from_enums` — DONE (Epic 1)
4. `add_ingredient_id_index` — DONE (Epic 1)
5. **`create_audit_log_table` — THIS STORY**

The migration depends on `users` table existing (FK constraint). Since all previous migrations are applied, this is safe.

### No Frontend Changes in This Story

Frontend audit log viewer is Story 5-6. This story is backend-only.

### No Audit Integration in This Story

Wiring `AuditService.log()` calls into existing admin endpoints (categories, ingredients, users, recipes) is Story 4-2. This story creates the infrastructure only. The endpoint and service must work, but no existing code calls them yet.

### Anti-Patterns to Avoid

**DO NOT:**
- Use `db.commit()` inside `AuditService.log()` — use `db.flush()` to participate in caller's transaction
- Re-raise exceptions in the `AuditService.log()` catch block — fire-and-forget means fire-and-forget
- Import `JSON` from `sqlalchemy.dialects.postgresql` — use `sqlalchemy.JSON` for cross-DB compatibility
- Use `from` as a Python variable name — alias it as `from_date` with `Query(alias="from")`
- Add `@pytest.mark.asyncio` to tests — asyncio_mode=auto in pytest config
- Import `describe`/`it`/`expect` in test files — this is pytest, not vitest
- Create separate audit router file — add endpoint to existing `admin.py`
- Add enum validation for `action` or `entity_type` params — accept any string, validation is caller's job in 4-2
- Use `str | None` type hints — use `Optional[str]` for Python 3.9 compatibility
- Use `Base.metadata.create_all()` — Alembic only

**DO:**
- Wrap entire `AuditService.log()` body in try/except
- Use `db.flush()` not `db.commit()` in the audit service
- Include `request: Request` param for slowapi rate limiting
- Use `Query(alias="from")` for the `from` date filter
- Test that audit failure does NOT propagate exceptions
- Test that audit failure IS logged via `logger.error`
- Use `func.now()` for `created_at` default (database-side timestamp)
- Follow existing pagination pattern from user list endpoint (Story 3-1)

### Previous Story Intelligence (3-2)

**From Story 3-2 (User Status Management) — COMPLETED (496 tests passing):**
- `admin.py` currently has: category CRUD, ingredient CRUD, user list, user status PATCH — add audit-log GET after these
- `require_admin` dependency works reliably — same pattern for audit endpoint
- Self-protection patterns established — not relevant to audit (read-only endpoint)
- `revoke_all_user_tokens` pattern — not relevant to audit
- Code review found: standardize error messages, add WWW-Authenticate headers — audit endpoint returns data, not auth errors, so less relevant
- Rate limiting already on auth endpoints — extend pattern to audit endpoint

### Git Intelligence

Recent commits:
```
14dc8d4 feat: Add Epic 2 ingredient management, Epic 3 user admin, and code review fixes
acd1f9d fix: Use TRUE instead of 1 for boolean is_active in seed migration for PostgreSQL compatibility
428b5ea fix: Use TRUE/FALSE instead of 1/0 in admin migration for PostgreSQL compatibility
```

Boolean handling in migrations uses Python `True`/`False` — SQLAlchemy handles SQLite/PostgreSQL differences. JSON column also works cross-DB via SQLAlchemy abstraction. No special handling needed.

### Project Structure Notes

- Alignment with architecture doc's file structure: `models/audit_log.py`, `services/audit_service.py`, `schemas/audit.py` — all specified in architecture
- No conflicts with existing files — all new files except admin.py modification
- admin.py endpoint addition follows same pattern as user list (Story 3-1) and user status (Story 3-2)

### References

- [Source: docs/epics.md#Story 4.1 — Acceptance criteria (lines 590-635)]
- [Source: docs/admin-panel-architecture.md#Audit Log Storage — fire-and-forget pattern, table schema]
- [Source: docs/admin-panel-architecture.md#Audit Action Naming — {entity}_{verb} pattern]
- [Source: docs/admin-panel-architecture.md#Project Structure — audit_log.py, audit_service.py locations]
- [Source: docs/admin-panel-architecture.md#Migration Sequence — audit log is 5th migration]
- [Source: docs/project_context.md#Fire-and-Forget Audit Logging — code pattern with test requirement]
- [Source: docs/project_context.md#Admin Panel Patterns — require_admin, auth test pattern]
- [Source: docs/project_context.md#Defensive Coding — IntegrityError handling, service error conventions]
- [Source: backend/app/models/user.py — User model with is_admin field (FK target for audit_log)]
- [Source: backend/app/routers/admin.py — existing admin endpoints to extend]
- [Source: backend/app/dependencies.py — require_admin dependency]
- [Source: backend/app/main.py — slowapi limiter setup, router mounting]
- [Source: backend/tests/conftest.py — test fixtures (admin_user, client, test_session)]
- [Source: docs/sprint-artifacts/3-2-user-status-management.md — previous story patterns and learnings]

---

## Dev Agent Record

### Context Reference

Story context created by BMAD create-story workflow on 2026-04-09.

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

None — clean implementation, no debugging needed.

### Completion Notes List

- Created `AuditLog` model with SQLAlchemy 2.0 Mapped[] syntax, 7 columns, 3 indexes, FK to users.id
- Alembic migration `f2c3f52ad94e` — cleaned autogenerate output to only audit log table (removed unrelated schema drift)
- `AuditService.log()` — fire-and-forget with try/except, uses `db.flush()` not `db.commit()` per story spec
- `AuditService.list_audit_logs()` — left join with User for admin_email, filter chain for action/entity_type/date range, pagination, DESC ordering
- `AuditLogResponse` and `AuditLogListResponse` Pydantic schemas with `from_attributes=True`
- `GET /admin/audit-log` endpoint with `require_admin`, slowapi rate limit (30/min), Query alias for `from`/`to` params
- 17 tests covering all 8 ACs: auth (401/403), service log (4 tests), fire-and-forget (2 tests), paginated list (3 tests), filters (4 tests), pagination (2 tests)
- Full regression: 513 tests passing (496 existing + 17 new), 0 failures

### Code Review Fixes (2026-04-09)

- **[C-1] Missing AuditLogFilter schema** — Created `AuditLogFilter` in `schemas/audit.py`, exported from `schemas/__init__.py`
- **[H-1] Fire-and-forget session poisoning** — `AuditService.log()` now uses `db.begin_nested()` (SAVEPOINT) to isolate audit flush failures from the caller's transaction. Without this, a `db.flush()` failure left the session in `PendingRollbackError` state, breaking the caller's commit. Added `test_audit_log_flush_failure_does_not_poison_session` test.
- **[M-1] Date range filter untested at HTTP level** — Added `test_filter_by_date_range_via_http` to verify `?from=&to=` Query aliases work end-to-end
- **[M-3] Inefficient count query** — Separated count query from JOIN query in `list_audit_logs()`. Count now uses `func.count(AuditLog.id)` without the User outerjoin.
- **[L-1] JSON null storage** — Added `none_as_null=True` to `details` column so Python `None` stores as SQL NULL, not JSON `'null'`
- **[L-2] admin_email response test** — Added `test_audit_log_response_includes_admin_email`
- **[L-3] per_page validation test** — Added `test_per_page_exceeding_max_returns_422`
- Post-fix regression: 517 tests passing (496 existing + 21 audit), 0 failures

### Code Review 2 Fixes (2026-04-09)

- **[M-1] begin_nested() not used as context manager** — Changed `nested = db.begin_nested()` to `with db.begin_nested():` for explicit savepoint lifecycle management
- **[M-2] AuditLogFilter dead code** — Removed unused `AuditLogFilter` schema from `schemas/audit.py` and `schemas/__init__.py` (never referenced by any endpoint)
- **[M-3] FK ondelete unspecified** — Added explicit `ondelete="RESTRICT"` to `admin_user_id` FK. Changed `outerjoin` to `join` in `list_audit_logs()` since RESTRICT guarantees the user exists. Updated migration accordingly.
- **[L-1] Ordering untested at HTTP level** — Added `test_list_audit_logs_ordered_by_created_at_desc_via_http` to verify newest-first ordering through the endpoint
- **[L-2] datetime.utcnow() deprecated** — Replaced all `datetime.utcnow()` with `datetime.now(timezone.utc)` in test file for Python 3.12+ compatibility
- Post-fix regression: 518 tests passing (496 existing + 22 audit), 0 failures

### Change Log

- 2026-04-09: Story 4-1 implementation complete — audit log infrastructure (model, migration, service, schemas, endpoint, tests)
- 2026-04-09: Code review 1 fixes — savepoint isolation, missing schema, optimized count, 4 new tests
- 2026-04-09: Code review 2 fixes — context manager, dead code removal, FK ondelete, HTTP ordering test, utcnow deprecation

### File List

| File | Action |
| ---- | ------ |
| `backend/app/models/audit_log.py` | Created — AuditLog model |
| `backend/app/models/__init__.py` | Modified — export AuditLog |
| `backend/alembic/versions/f2c3f52ad94e_create_audit_log_table.py` | Created — migration for admin_audit_log table |
| `backend/app/services/audit_service.py` | Created — AuditService with log() and list_audit_logs() |
| `backend/app/services/__init__.py` | Modified — export AuditService |
| `backend/app/schemas/audit.py` | Created — AuditLogResponse, AuditLogListResponse |
| `backend/app/schemas/__init__.py` | Modified — export audit schemas |
| `backend/app/routers/admin.py` | Modified — added GET /admin/audit-log endpoint, limiter, imports |
| `backend/tests/test_audit_log.py` | Created — 22 tests |
| `docs/sprint-artifacts/sprint-status.yaml` | Modified — 4-1 status: done |
