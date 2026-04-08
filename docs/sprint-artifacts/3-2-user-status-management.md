# Story 3.2: User Status Management

Status: ready-for-dev

---

## Story

As an **admin**,
I want **to activate/deactivate user accounts and manage admin privileges**,
So that **I can control access to the application**.

---

## Acceptance Criteria

### AC-1: Deactivate User

**Given** I am authenticated as an admin
**When** I call `PATCH /api/admin/users/{id}` with `{ "is_active": false }`
**Then** the user is deactivated
**And** the user's existing refresh tokens are revoked
**And** the user cannot log in until reactivated

### AC-2: Reactivate User

**Given** I am authenticated as an admin
**When** I call `PATCH /api/admin/users/{id}` with `{ "is_active": true }`
**Then** the user is reactivated
**And** the user can log in again

### AC-3: Self-Deactivation Blocked

**Given** I am authenticated as an admin
**When** I try to deactivate MY OWN account
**Then** I receive a 400 Bad Request with `"Cannot deactivate your own account"`
**And** my account remains active

### AC-4: Grant Admin

**Given** I am authenticated as an admin
**When** I call `PATCH /api/admin/users/{id}` with `{ "is_admin": true }`
**Then** the target user is granted admin privileges

### AC-5: Revoke Admin

**Given** I am authenticated as an admin
**When** I call `PATCH /api/admin/users/{id}` with `{ "is_admin": false }`
**Then** the target user's admin privileges are revoked

### AC-6: Self Admin-Revoke Blocked

**Given** I am authenticated as an admin
**When** I try to remove MY OWN admin status
**Then** I receive a 400 Bad Request with `"Cannot remove your own admin status"`
**And** I remain an admin

### AC-7: Deactivated User Login Blocked

**Given** a deactivated user tries to authenticate
**When** they submit valid credentials to `POST /api/auth/login` or `POST /api/auth/token`
**Then** they receive a 401 Unauthorized with `"Account is deactivated"`

### AC-8: Authorization

**Given** I am NOT an admin (regular user or unauthenticated)
**When** I call `PATCH /api/admin/users/{id}`
**Then** I receive 401 (no token) or 403 (regular user)

---

## Tasks / Subtasks

### Task 1: Create User Status Schemas (AC: #1-6)

- [ ] **1.1** Add schemas to `backend/app/schemas/user.py` (file exists from Story 3-1):
  - `UserStatusUpdate`: `is_active` (Optional[bool]), `is_admin` (Optional[bool]) — at least one field must be provided
  - `UserStatusResponse`: `id` (str), `email` (str), `display_name` (Optional[str]), `is_active` (bool), `is_admin` (bool), `message` (str)
- [ ] **1.2** Export new schemas from `backend/app/schemas/__init__.py`

### Task 2: Implement User Status Service (AC: #1-6)

- [ ] **2.1** Add to `backend/app/services/user_service.py` (file exists from Story 3-1):
  - **DO NOT create `get_user_by_id`** — it already exists in `app/services/auth.py:102`. Import it: `from app.services.auth import get_user_by_id`. Alternatively, import it in the router directly where it's needed.
  - `update_user_status(db, user, data, admin_id) -> Tuple[User, str]` — returns (updated_user, message_string). Validates self-protection rules BEFORE modifying. On deactivation, calls `revoke_all_user_tokens(db, user.id)` to invalidate sessions.
- [ ] **2.2** Export new functions from `backend/app/services/__init__.py`

### Task 3: Add Login Block for Deactivated Users (AC: #7)

- [ ] **3.1** In `backend/app/routers/auth.py`, add `is_active` check in BOTH login endpoints:
  - `POST /auth/login` — insert AFTER the `if not user:` HTTPException block (line 84), BEFORE `user.last_login_at` update (line 86)
  - `POST /auth/token` — insert AFTER the `if not user:` HTTPException block (line 134), BEFORE `user.last_login_at` update (line 137)
  - Check: `if not user.is_active: raise HTTPException(status_code=401, detail="Account is deactivated")`
  - CRITICAL: This check must happen AFTER password verification but BEFORE `last_login_at` update and token creation

### Task 4: Add PATCH Endpoint (AC: #1-8)

- [ ] **4.1** Add endpoint to `backend/app/routers/admin.py`:
  - `PATCH /admin/users/{id}` → `UserStatusResponse`
  - Dependencies: `db: Session = Depends(get_db)`, `admin: User = Depends(require_admin)`
  - Call `get_user_by_id` first → 404 if not found
  - Call `update_user_status` → catches self-protection ValueError and returns 400
- [ ] **4.2** Import `UserStatusUpdate`, `UserStatusResponse` in admin.py
- [ ] **4.3** Import `get_user_by_id` from `app.services.auth` (NOT user_service — it already exists there), import `update_user_status` from user_service

### Task 5: Write Tests (AC: #1-8)

- [ ] **5.1** Create `backend/tests/test_admin_user_status.py`
- [ ] **5.2** Auth tests (MANDATORY — AC-8):
  - `test_patch_user_returns_401_without_auth`
  - `test_patch_user_returns_403_for_regular_user`
- [ ] **5.3** Deactivation tests (AC-1):
  - `test_deactivate_user_sets_is_active_false`
  - `test_deactivate_user_revokes_refresh_tokens`
- [ ] **5.4** Reactivation tests (AC-2):
  - `test_reactivate_user_sets_is_active_true`
- [ ] **5.5** Self-protection tests (AC-3, AC-6):
  - `test_cannot_deactivate_own_account`
  - `test_cannot_remove_own_admin_status`
- [ ] **5.6** Admin privilege tests (AC-4, AC-5):
  - `test_grant_admin_to_regular_user`
  - `test_revoke_admin_from_admin_user`
- [ ] **5.7** Login block tests (AC-7):
  - `test_deactivated_user_cannot_login` (POST /auth/login)
  - `test_deactivated_user_cannot_get_token` (POST /auth/token)
  - `test_reactivated_user_can_login_again`
- [ ] **5.8** Edge case tests:
  - `test_patch_nonexistent_user_returns_404`
  - `test_patch_with_empty_body_returns_422`
  - `test_deactivate_already_inactive_user_succeeds` (idempotent)
  - `test_grant_admin_to_already_admin_succeeds` (idempotent)
  - `test_partial_update_only_is_active` (is_admin unchanged)
  - `test_partial_update_only_is_admin` (is_active unchanged)
  - `test_combined_update_with_self_protection_blocks_entirely` (e.g., `{ "is_active": true, "is_admin": false }` on self — must reject the whole request, not apply `is_active` and reject `is_admin`)
- [ ] **5.9** Run full test suite: `pytest` — no regressions

### Task 6: Final Verification

- [ ] **6.1** Run full backend test suite: `pytest` — expect 472+ existing tests (from 3-1) plus ~19 new tests = ~491+ total
- [ ] **6.2** Verify all existing tests still pass (including 3-1 user list tests — 472 passed at 3-1 completion)
- [ ] **6.3** Run coverage: `coverage run -m pytest tests/test_admin_user_status.py && coverage report --include="app/services/user_service.py,app/routers/admin.py,app/routers/auth.py,app/schemas/user.py"`
- [ ] **6.4** Update `docs/sprint-artifacts/sprint-status.yaml` — mark 3-2 as done

---

## Dev Notes

### CRITICAL: Two Separate Changes in Two Different Routers

This story touches TWO routers:
1. `backend/app/routers/admin.py` — Add PATCH `/admin/users/{id}` endpoint
2. `backend/app/routers/auth.py` — Add `is_active` check in login endpoints

Do NOT forget the auth.py change. The admin endpoint handles status updates, but the login block is what actually prevents deactivated users from authenticating.

### CRITICAL: Reuse `get_user_by_id` from auth service

`get_user_by_id(db, user_id) -> Optional[User]` already exists at `app/services/auth.py:102`. Do NOT create a duplicate in `user_service.py`. Import it in the router:

```python
from app.services.auth import get_user_by_id
```

### Login Block Pattern (auth.py)

Both login endpoints (`/auth/login` ~line 82, `/auth/token` ~line 132) follow the same flow:
1. `authenticate_user()` — verifies email + password
2. **INSERT HERE:** `is_active` check
3. Update `last_login_at`
4. Create tokens

```python
# Add AFTER authenticate_user() succeeds, BEFORE last_login_at update:
if not user.is_active:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Account is deactivated",
    )
```

Note: `get_current_user()` in `services/auth.py:144-149` already rejects inactive users at the token validation level. The login block adds rejection at the authentication level — preventing token issuance entirely.

### Token Invalidation on Deactivation

`revoke_all_user_tokens()` already exists in `services/auth.py:229-239`. Call it when deactivating a user to immediately invalidate all refresh tokens:

```python
from app.services.auth import revoke_all_user_tokens

def update_user_status(db, user, data, admin_id):
    if data.is_active is False and user.is_active:
        # Revoking refresh tokens on deactivation
        revoke_all_user_tokens(db, user.id)
    # ... apply changes
```

Access tokens (JWT) cannot be revoked server-side — they expire naturally. But with refresh tokens revoked, the user can't get new access tokens. Existing access tokens have short expiry (~15 min), so effective lockout is near-immediate.

**Double-commit note:** `revoke_all_user_tokens()` calls `db.commit()` internally (auth.py:238). `update_user_status` also commits after applying changes. This means deactivation performs two commits. If the second fails, tokens are revoked but user stays active. Acceptable at cocktail app scale — do NOT refactor `revoke_all_user_tokens` to remove its commit (it's used elsewhere independently).

### Self-Protection Logic

Two self-protection rules — both return 400:
1. Admin cannot set `is_active=False` on their own user ID
2. Admin cannot set `is_admin=False` on their own user ID

```python
def update_user_status(db, user, data, admin_id):
    if user.id == admin_id:
        if data.is_active is False:
            raise ValueError("Cannot deactivate your own account")
        if data.is_admin is False:
            raise ValueError("Cannot remove your own admin status")
    # ... apply changes
```

In the router, catch `ValueError` and return 400:
```python
try:
    updated_user, message = update_user_status(db, user, data, admin.id)
except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
```

### Schema Design — Partial Update

`UserStatusUpdate` allows updating `is_active`, `is_admin`, or both. At least one must be provided:

```python
from pydantic import BaseModel, model_validator  # NOTE: model_validator is NOT in existing user.py — must add this import

class UserStatusUpdate(BaseModel):
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None

    @model_validator(mode="after")
    def at_least_one_field(self):
        if self.is_active is None and self.is_admin is None:
            raise ValueError("At least one of is_active or is_admin must be provided")
        return self
```

### Service Return Pattern

Return `(User, str)` tuple — the updated user and a human-readable message:

```python
def update_user_status(db, user, data, admin_id):
    # ... self-protection checks ...
    changes = []
    if data.is_active is not None and data.is_active != user.is_active:
        if data.is_active is False:
            revoke_all_user_tokens(db, user.id)
        user.is_active = data.is_active
        changes.append("activated" if data.is_active else "deactivated")

    if data.is_admin is not None and data.is_admin != user.is_admin:
        user.is_admin = data.is_admin
        changes.append("granted admin" if data.is_admin else "revoked admin")

    db.commit()
    db.refresh(user)
    message = f"User {', '.join(changes)}" if changes else "No changes applied"
    return user, message
```

### Extend Existing Files — File Actions

| File | Action | What to Add |
|------|--------|-------------|
| `backend/app/schemas/user.py` | MODIFY (exists from 3-1) | Add UserStatusUpdate, UserStatusResponse |
| `backend/app/schemas/__init__.py` | MODIFY | Export new schemas |
| `backend/app/services/user_service.py` | MODIFY (exists from 3-1) | Add update_user_status (NOT get_user_by_id — use from auth service) |
| `backend/app/services/__init__.py` | MODIFY | Export new functions |
| `backend/app/routers/admin.py` | MODIFY | Add PATCH /admin/users/{id} endpoint |
| `backend/app/routers/auth.py` | MODIFY | Add is_active check in both login endpoints |
| `backend/tests/test_admin_user_status.py` | CREATE | User status management tests |

### Test Fixture Strategy

Reuse existing `conftest.py` fixtures:
- `client` — TestClient with DB overrides
- `admin_auth_token` — JWT for admin user
- `admin_user` — Admin user (for self-protection tests)
- `auth_token` — JWT for regular user (for 403 tests)
- `sample_user` — Regular user target for status changes
- `inactive_user` — Already exists (line 106-118) — deactivated user for login block tests
- `another_user` — Second regular user

For testing deactivated user login:
```python
def test_deactivated_user_cannot_login(client, inactive_user):
    response = client.post(
        "/api/auth/login",
        json={"email": "inactive@example.com", "password": "testpassword123"},
    )
    assert response.status_code == 401
    assert "deactivated" in response.json()["detail"].lower()
```

For testing token revocation on deactivation, create a refresh token for the target user first:
```python
def test_deactivate_user_revokes_refresh_tokens(client, admin_auth_token, sample_user, test_session):
    from app.services.auth import create_refresh_token, store_refresh_token
    # Create a refresh token for sample_user
    token, jti, expires = create_refresh_token(data={"sub": sample_user.id})
    store_refresh_token(test_session, sample_user.id, jti, expires)

    # Deactivate user
    response = client.patch(
        f"/api/admin/users/{sample_user.id}",
        json={"is_active": False},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200

    # Verify token is revoked
    from app.models.refresh_token import RefreshToken
    token_record = test_session.query(RefreshToken).filter_by(jti=jti).first()
    assert token_record.revoked is True
```

### Auth Test Pattern (MANDATORY)

```python
def test_patch_user_returns_401_without_auth(client, sample_user):
    response = client.patch(
        f"/api/admin/users/{sample_user.id}",
        json={"is_active": False},
    )
    assert response.status_code == 401

def test_patch_user_returns_403_for_regular_user(client, auth_token, sample_user):
    response = client.patch(
        f"/api/admin/users/{sample_user.id}",
        json={"is_active": False},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 403
```

### Route Placement in admin.py

Add `PATCH /admin/users/{id}` AFTER the `GET /admin/users` endpoint from Story 3-1 (or after ingredient endpoints if 3-1 not yet implemented). No path conflict — PATCH method is distinct from GET.

### No Audit Logging in This Story

Audit logging is Story 4-1/4-2. Do NOT add audit logging. The architecture defines audit actions `user_activate`, `user_deactivate`, `user_grant_admin`, `user_revoke_admin` — these will be wired in Story 4-2.

### No Frontend Changes in This Story

Frontend admin user management UI is Story 5-5. This story is backend-only.

### No New Dependencies

Everything uses existing packages. `revoke_all_user_tokens` is already implemented.

### No Database Migrations

All User model fields (`is_active`, `is_admin`) already exist from Epic 1. No schema changes needed.

### Anti-Patterns to Avoid (Story-Specific)

**DO NOT:**
- Forget to add `is_active` check in BOTH login endpoints (auth.py has two: `/login` and `/token`)
- Try to revoke JWT access tokens server-side (they expire naturally — revoke refresh tokens only)
- Allow admin to deactivate themselves or remove their own admin status
- Use PUT for partial update (use PATCH — only provided fields change)
- Add audit logging (Story 4-1/4-2)
- Create a new router file (extend admin.py for the PATCH endpoint)
- Modify `get_current_user` in services/auth.py (it already handles inactive users at token level)

**DO:**
- Call `revoke_all_user_tokens(db, user.id)` when deactivating (not when reactivating)
- Validate at least one field provided in `UserStatusUpdate`
- Return 400 (not 403) for self-protection violations — the admin IS authorized, the action is just prohibited
- Make status changes idempotent (deactivating an already-inactive user succeeds silently)
- Use `detail` key in all HTTPExceptions

### References

- [Source: docs/epics.md#Story 3.2 — Acceptance criteria (lines 539-583)]
- [Source: docs/admin-panel-architecture.md#Phase 5 — User management endpoints]
- [Source: docs/admin-panel-architecture.md#Audit Action Naming — user_activate/deactivate/grant_admin/revoke_admin (Story 4-2)]
- [Source: docs/project_context.md#Admin Panel Patterns — auth patterns, defensive coding, pre-review checklist]
- [Source: backend/app/models/user.py — User model (is_active, is_admin fields)]
- [Source: backend/app/routers/auth.py:71-112 — POST /auth/login (needs is_active check)]
- [Source: backend/app/routers/auth.py:115-161 — POST /auth/token (needs is_active check)]
- [Source: backend/app/services/auth.py:122-151 — get_current_user (already checks is_active at token level)]
- [Source: backend/app/services/auth.py:229-239 — revoke_all_user_tokens (call on deactivation)]
- [Source: backend/app/dependencies.py:10-33 — require_admin dependency]
- [Source: backend/app/routers/admin.py — existing admin endpoints to extend]
- [Source: backend/tests/conftest.py — test fixtures (inactive_user at line 106, admin_user, sample_user)]
- [Source: docs/sprint-artifacts/3-1-user-list-search.md — previous story patterns]

### Previous Story Intelligence (3-1)

**From Story 3-1 (User List & Search) — COMPLETED (472 tests passing):**
- `user_service.py` EXISTS with `list_users()` — extend it with `update_user_status()`
- `schemas/user.py` EXISTS with `UserAdminResponse`, `UserListResponse` — extend with `UserStatusUpdate`, `UserStatusResponse`
- Pagination pattern established in list endpoint — not relevant here (single resource PATCH)
- LIKE wildcard escaping pattern — not relevant here (no search)
- `hash_password` (NOT `get_password_hash`) — confirmed in conftest.py and services/auth.py

### Git Intelligence

```
acd1f9d fix: Use TRUE instead of 1 for boolean is_active in seed migration for PostgreSQL compatibility
428b5ea fix: Use TRUE/FALSE instead of 1/0 in admin migration for PostgreSQL compatibility
7af9393 feat: Add admin category CRUD, reorder, and soft-delete endpoints (Story 1-6)
```

Boolean handling uses Python `True`/`False` in code — SQLite and PostgreSQL both handle this correctly via SQLAlchemy's `Boolean` type.

---

## Dev Agent Record

### Context Reference

Story context created by BMAD create-story workflow on 2026-04-09.

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

### Completion Notes List

### File List
