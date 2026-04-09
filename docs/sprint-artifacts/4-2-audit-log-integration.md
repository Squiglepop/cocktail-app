# Story 4.2: Audit Log Integration

Status: done

## Story

As an **admin**,
I want **all my administrative actions automatically logged**,
So that **I can review what changes were made and by whom**.

## Acceptance Criteria

### AC-1: Category Actions Logged

**Given** an admin creates a category
**When** the `POST /api/admin/categories/{type}` endpoint succeeds
**Then** an audit entry is created with:
- `action`: `category_create`
- `entity_type`: `category`
- `entity_id`: new category's id
- `details`: `{"type": "<type>", "value": "<value>", "label": "<label>"}`

**Given** an admin updates a category
**When** the `PUT /api/admin/categories/{type}/{id}` endpoint succeeds
**Then** an audit entry is created with:
- `action`: `category_update`
- `entity_type`: `category`
- `entity_id`: category id
- `details`: `{"type": "<type>", "changes": {"<field>": [<old_value>, <new_value>]}}`
- Only changed fields appear in `changes` (no noise for unchanged fields)

**Given** an admin deletes (soft-deletes) a category
**When** the `DELETE /api/admin/categories/{type}/{id}` endpoint succeeds
**Then** an audit entry is created with:
- `action`: `category_delete`
- `entity_type`: `category`
- `entity_id`: category id
- `details`: `{"type": "<type>", "value": "<value>"}`

### AC-2: Ingredient Actions Logged

**Given** an admin creates an ingredient
**When** `POST /api/admin/ingredients` succeeds
**Then** an audit entry is created with:
- `action`: `ingredient_create`
- `entity_type`: `ingredient`
- `entity_id`: new ingredient id
- `details`: `{"name": "<name>", "type": "<type>"}`

**Given** an admin updates an ingredient
**When** `PUT /api/admin/ingredients/{id}` succeeds
**Then** an audit entry is created with:
- `action`: `ingredient_update`
- `entity_type`: `ingredient`
- `entity_id`: ingredient id
- `details`: `{"changes": {"<field>": [<old_value>, <new_value>]}}` (changed fields only)

**Given** an admin deletes an ingredient
**When** `DELETE /api/admin/ingredients/{id}` succeeds (200, not 409)
**Then** an audit entry is created with:
- `action`: `ingredient_delete`
- `entity_type`: `ingredient`
- `entity_id`: ingredient id
- `details`: `{"name": "<name>", "type": "<type>"}`

**Given** an admin merges ingredients
**When** `POST /api/admin/ingredients/merge` succeeds
**Then** an audit entry is created with:
- `action`: `ingredient_merge`
- `entity_type`: `ingredient`
- `entity_id`: target ingredient id
- `details`: `{"source_ids": [...], "source_names": [...], "target_id": "<id>", "target_name": "<name>", "recipes_updated": <count>}`

### AC-3: Recipe Admin Actions Logged (Admin Editing Another User's Recipe Only)

**Given** an admin updates a recipe owned by ANOTHER user
**When** `PUT /api/recipes/{id}` succeeds
**Then** an audit entry is created with:
- `action`: `recipe_admin_update`
- `entity_type`: `recipe`
- `entity_id`: recipe id
- `details`: `{"recipe_name": "<name>", "owner_id": "<user_id>", "changes": {"<field>": [<old_value>, <new_value>]}}`
- Only changed scalar fields appear in `changes`; ingredients changes noted as `"ingredients": "updated"` if changed

**Given** an admin deletes a recipe owned by ANOTHER user
**When** `DELETE /api/recipes/{id}` succeeds
**Then** an audit entry is created with:
- `action`: `recipe_admin_delete`
- `entity_type`: `recipe`
- `entity_id`: recipe id
- `details`: `{"recipe_name": "<name>", "owner_id": "<user_id>"}`

**Note:** Admin editing/deleting their OWN recipe is NOT audited (that's normal user behavior).
**Note:** Admin editing/deleting a recipe with no owner (`user_id = None`) is NOT audited.

### AC-4: User Status Actions Logged

**Given** an admin activates a user
**When** `PATCH /api/admin/users/{id}` is called with `{"is_active": true}` and the user was inactive
**Then** an audit entry is created with `action: user_activate`, `entity_type: user`, `entity_id: user.id`, `details: {"email": "<email>"}`

**Given** an admin deactivates a user
**When** `PATCH /api/admin/users/{id}` is called with `{"is_active": false}` and the user was active
**Then** an audit entry is created with `action: user_deactivate`, `entity_type: user`, `entity_id: user.id`, `details: {"email": "<email>"}`

**Given** an admin grants admin status
**When** `PATCH /api/admin/users/{id}` is called with `{"is_admin": true}` and user was not admin
**Then** an audit entry is created with `action: user_grant_admin`, `entity_type: user`, `entity_id: user.id`, `details: {"email": "<email>"}`

**Given** an admin revokes admin status
**When** `PATCH /api/admin/users/{id}` is called with `{"is_admin": false}` and user was admin
**Then** an audit entry is created with `action: user_revoke_admin`, `entity_type: user`, `entity_id: user.id`, `details: {"email": "<email>"}`

**Given** an admin updates BOTH `is_active` and `is_admin` in one call
**When** both values actually change
**Then** TWO separate audit entries are created (one per action type)

**Given** no actual changes occur (PATCH with same values as current state)
**When** the endpoint returns "No changes applied"
**Then** NO audit entry is created

### AC-5: Fire-and-Forget — Audit Never Blocks Operations

**Given** `AuditService.log()` fails (any exception)
**When** an admin performs any operation (category/ingredient/recipe/user)
**Then** the admin operation still succeeds
**And** the error is logged via `logger.error()`
**And** the HTTP response is unaffected

---

## Tasks / Subtasks

### Task 1: Wire Audit Calls into Category Endpoints (AC: #1)

- [x] **1.1** In `backend/app/routers/admin.py`, update `create_admin_category`:
  - After `result = create(db, type, data)` succeeds (not None)
  - Call `_audit_log(db, admin.id, "category_create", "category", result.id, {"type": type, "value": result.value, "label": result.label})`

- [x] **1.2** Update `update_admin_category`:
  - BEFORE calling `update()`: call `get_by_id(db, type, id)` and copy scalar values into a dict: `old_values = {"label": cat.label, "description": cat.description, "is_active": cat.is_active}` (these are the three `CategoryUpdate` fields — `value` and `sort_order` are NOT mutable through this endpoint)
  - If `get_by_id` returns `None`, skip audit — the `update()` call will return `None` and trigger the existing 404 response
  - After `result = update(db, type, id, data)` succeeds (not None)
  - Compute `changes` dict using `data.model_dump(exclude_unset=True)`: `{field: [old_values[field], getattr(result, field)] for field in update_fields if old_values[field] != getattr(result, field)}`
  - Skip audit call if `changes` dict is empty (no actual changes — consistent with ingredient update behavior)
  - Call `_audit_log(db, admin.id, "category_update", "category", id, {"type": type, "changes": changes})`

- [x] **1.3** Update `delete_admin_category`:
  - BEFORE calling `soft_delete()`: call `get_by_id(db, type, id)` to capture `value`. Note: `soft_delete()` returns a **tuple** `(category, recipe_count)` — the category object IS available after, but always capture value BEFORE for consistency with update/delete pattern
  - If `get_by_id` returns `None`, skip audit — `soft_delete()` will return `None` and trigger the existing 404
  - After `result = soft_delete(db, type, id)` succeeds (result is not None), unpack as `category, recipe_count = result` (existing code already does this)
  - Call `_audit_log(db, admin.id, "category_delete", "category", id, {"type": type, "value": pre_delete_value})`

### Task 2: Wire Audit Calls into Ingredient Endpoints (AC: #2)

- [x] **2.1** Update `create_admin_ingredient`:
  - After `result = create_ingredient(db, data)` succeeds (not None)
  - Call `_audit_log(db, admin.id, "ingredient_create", "ingredient", result.id, {"name": result.name, "type": result.type})`

- [x] **2.2** Update `update_admin_ingredient`:
  - BEFORE calling `update_ingredient()`: capture old values of all mutable fields from `ingredient` object (name, type, spirit_category, description, common_brands)
  - After `result = update_ingredient(db, ingredient, data)` succeeds
  - Compute `changes`: iterate `data.model_dump(exclude_unset=True)` and compare each field to old value
  - Call `_audit_log(db, admin.id, "ingredient_update", "ingredient", id, {"changes": changes})`
  - Skip audit call entirely if `changes` dict is empty (no actual changes)

- [x] **2.3** Update `delete_admin_ingredient`:
  - BEFORE calling `delete_ingredient()`: capture `ingredient.name` and `ingredient.type`
  - After `deleted, recipe_count = delete_ingredient(db, ingredient)` where `deleted is True`
  - Call `_audit_log(db, admin.id, "ingredient_delete", "ingredient", id, {"name": pre_delete_name, "type": pre_delete_type})`

- [x] **2.4** Update `merge_admin_ingredients`:
  - REQUIRES: Add `Ingredient` to the model imports at top of `admin.py`: `from ..models import User, Ingredient`
  - BEFORE calling `merge_ingredients()`: fetch target and all sources to capture names
  - After `recipes_affected, sources_removed = merge_ingredients(db, data.target_id, data.source_ids)` succeeds
  - Call `_audit_log(db, admin.id, "ingredient_merge", "ingredient", data.target_id, {"source_ids": data.source_ids, "source_names": [s.name for s in sources], "target_id": data.target_id, "target_name": target.name, "recipes_updated": recipes_affected})`
  - **CRITICAL**: Capture source names BEFORE `merge_ingredients()` — sources are deleted during merge

### Task 3: Wire Audit Calls into Recipe Endpoints (AC: #3)

- [x] **3.1** Update `update_recipe` in `backend/app/routers/recipes.py`:
  - ONLY audit when `current_user.is_admin is True AND recipe.user_id is not None AND recipe.user_id != current_user.id`
  - BEFORE updating: capture old values of mutable scalar fields (name, description, instructions, template, main_spirit, glassware, serving_style, method, garnish, notes, source_url, visibility, **user_id**)
  - Also capture whether ingredients were provided (`recipe_data.ingredients is not None`)
  - After `db.commit()`: compute `changes` dict from `update_data` vs old values
  - Add `"ingredients": "updated"` to changes if `recipe_data.ingredients is not None`
  - Import and add helper: `from app.services.audit_service import AuditService` + `_audit_log` helper (same as admin.py)
  - Call `_audit_log(db, current_user.id, "recipe_admin_update", "recipe", recipe_id, {"recipe_name": old_name, "owner_id": pre_update_owner_id, "changes": changes})`
  - **Note:** Include `user_id` in capture list — ownership transfers are arguably the most important admin action to audit

- [x] **3.2** Update `delete_recipe` in `recipes.py`:
  - ONLY audit when `current_user.is_admin is True AND recipe.user_id is not None AND recipe.user_id != current_user.id`
  - Capture `recipe.name`, `recipe.user_id` BEFORE the delete
  - After `db.delete(recipe)` + `db.commit()` (already in existing code)
  - Call `_audit_log(db, current_user.id, "recipe_admin_delete", "recipe", recipe_id, {"recipe_name": pre_delete_name, "owner_id": pre_delete_owner_id})`

### Task 4: Wire Audit Calls into User Status Endpoint (AC: #4)

- [x] **4.1** Update `update_admin_user_status` in `admin.py`:
  - BEFORE calling `update_user_status()`: capture `user.is_active` and `user.is_admin` (old state)
  - After `updated_user, message = update_user_status(db, user, data, admin.id)` succeeds
  - Do NOT audit if no changes (message == "No changes applied") — return early
  - Determine what changed by comparing old vs new values:
    - If `old_is_active != updated_user.is_active`:
      - `_audit_log(db, admin.id, "user_activate" if updated_user.is_active else "user_deactivate", "user", user.id, {"email": updated_user.email})`
    - If `old_is_admin != updated_user.is_admin`:
      - `_audit_log(db, admin.id, "user_grant_admin" if updated_user.is_admin else "user_revoke_admin", "user", user.id, {"email": updated_user.email})`
  - Two separate `_audit_log()` calls — so one failing doesn't prevent the other

### Task 5: Write Tests (AC: #1-5)

- [x] **5.1** Create `backend/tests/test_audit_log_integration.py`

- [x] **5.2** Category audit tests (AC-1):
  - `test_category_create_generates_audit_entry` — verify entry action, entity_type, entity_id, details type/value/label
  - `test_category_update_generates_audit_entry_with_changes` — verify only changed fields in details.changes
  - `test_category_update_no_change_skips_audit` — update called with same values → empty changes dict → no audit entry created (consistent with ingredient update behavior)
  - `test_category_delete_generates_audit_entry` — verify action + pre-delete value captured

- [x] **5.3** Ingredient audit tests (AC-2):
  - `test_ingredient_create_generates_audit_entry` — verify details.name and details.type
  - `test_ingredient_update_generates_audit_entry_with_changes`
  - `test_ingredient_delete_generates_audit_entry` — verify name/type captured before delete
  - `test_ingredient_merge_generates_audit_entry` — verify source_names captured (sources are gone after merge)

- [x] **5.4** Recipe admin audit tests (AC-3):
  - `test_recipe_admin_update_generates_audit_when_admin_edits_other_user_recipe`
  - `test_recipe_admin_delete_generates_audit_when_admin_deletes_other_user_recipe`
  - `test_recipe_no_audit_when_admin_edits_own_recipe` — admin updating their OWN recipe: no audit
  - `test_recipe_no_audit_when_admin_edits_unowned_recipe` — recipe.user_id is None: no audit

- [x] **5.5** User status audit tests (AC-4):
  - `test_user_activate_generates_audit_entry`
  - `test_user_deactivate_generates_audit_entry`
  - `test_user_grant_admin_generates_audit_entry`
  - `test_user_revoke_admin_generates_audit_entry`
  - `test_user_status_no_change_no_audit` — PATCH with values already matching current state
  - `test_user_status_both_changes_generate_two_audit_entries` — PATCH changes both is_active and is_admin

- [x] **5.6** Fire-and-forget tests for each entity type (AC-5):
  - `test_category_create_succeeds_when_audit_fails` — mock `AuditService.log` to raise, verify 201 still returned
  - `test_ingredient_create_succeeds_when_audit_fails`
  - `test_user_status_update_succeeds_when_audit_fails`
  - `test_recipe_admin_delete_succeeds_when_audit_fails`

- [x] **5.7** Run full test suite: `pytest` — no regressions (~517 existing from 4-1 + ~22 new = ~539 total)

### Task 6: Final Verification

- [x] **6.1** Run `pytest` — all pass
- [x] **6.2** Run `coverage report --include="app/routers/admin.py,app/routers/recipes.py"` — new audit paths covered
- [x] **6.3** Update `docs/sprint-artifacts/sprint-status.yaml` — mark 4-2 as `review`

---

## Dev Notes

### CRITICAL: Commit Pattern After AuditService.log()

The existing services (`create_ingredient`, `update_ingredient`, `category_service.create`, etc.) all call `db.commit()` internally. After they return, the session's transaction is already committed. `AuditService.log()` calls `db.flush()` — this writes the audit entry to the session's pending state but does NOT commit it. Since FastAPI's `get_db` dependency calls `db.close()` which rolls back uncommitted state, the audit entry MUST be committed after the flush.

Note: `AuditService.log()` internally uses `db.begin_nested()` (SAVEPOINT) to isolate audit flush failures from the session state. If the flush fails, only the savepoint is rolled back — the outer session remains clean.

**Use this helper in both `admin.py` and `recipes.py`** to avoid repeating the same try/except/rollback 10+ times:

```python
import logging

logger = logging.getLogger(__name__)

def _audit_log(db, admin_id, action, entity_type, entity_id, details):
    """Fire-and-forget audit wrapper. Main operation is already committed by service."""
    try:
        AuditService.log(db, admin_id, action, entity_type, entity_id, details)
        db.commit()   # REQUIRED to persist the flushed audit entry
    except Exception as e:
        logger.error(f"Audit log failed: {e}")
        # Safe: main operation already committed by service; rollback only affects audit entry
        db.rollback()
```

Add `import logging`, `logger = logging.getLogger(__name__)`, and the `_audit_log` helper at module level in both `admin.py` and `recipes.py`.

**EXCEPTION:** The user status endpoint (Task 4.1) needs TWO separate `_audit_log()` calls (one per change type), so one failing doesn't prevent the other. The helper works for this — just call it twice.

### CRITICAL: Capture Old State BEFORE the Operation

Services may mutate ORM objects in-place. Always read old values BEFORE calling the service:

```python
# ✅ CORRECT — capture before modification
old_label = category.label
result = update(db, type, id, data)  # may mutate in-place

# ❌ WRONG — object may already reflect new state
result = update(db, type, id, data)
old_label = category.label  # This is the NEW label!
```

**Merge special case:** Source ingredients are DELETED during `merge_ingredients()`. The merge endpoint must fetch target + sources and capture names BEFORE calling merge. This is safe — `merge_ingredients()` fetches them again internally. Add `Ingredient` model import (see Task 2.4).

### CRITICAL: Computing Changes Dict Pattern

Use `data.model_dump(exclude_unset=True)` to get only caller-sent fields, then compare to captured old values:

```python
update_fields = data.model_dump(exclude_unset=True)
changes = {
    field: [old_values[field], getattr(result, field)]
    for field in update_fields
    if old_values.get(field) != getattr(result, field)
}
```

This pattern applies to category update, ingredient update, and recipe admin update.

### CRITICAL: Recipe Audit — Condition Check

Only audit recipe admin operations when an admin is acting on ANOTHER user's recipe:

```python
is_admin_action = (
    current_user is not None
    and current_user.is_admin
    and recipe.user_id is not None
    and recipe.user_id != current_user.id
)
```

Place `is_admin_action` check + old state capture right after the ownership check, before update logic. For recipe update, include `user_id` in the capture list to track ownership transfers.

### Required Imports and Setup

**`admin.py`** — `AuditService` already imported from 4-1. Add:
```python
import logging
from ..models import User, Ingredient  # Add Ingredient to existing import

logger = logging.getLogger(__name__)
```
Plus the `_audit_log` helper function (see commit pattern above).

**`recipes.py`** — Add:
```python
from app.services.audit_service import AuditService
import logging

logger = logging.getLogger(__name__)
```
Plus the same `_audit_log` helper function.

### Test Note: Admin Rate Limiter

`admin.py` has its own `limiter = Limiter(key_func=get_remote_address)` at line 62. If tests hit admin endpoints rapidly and get rate-limited (429), disable it in conftest like the auth limiter:
```python
from app.routers.admin import limiter as admin_limiter
admin_limiter.enabled = False
```

### Test Pattern: Verifying Audit Entry Created

```python
def test_category_create_generates_audit_entry(
    client, test_session, admin_auth_token
):
    response = client.post(
        "/api/admin/categories/templates",
        json={"value": "daisy", "label": "Daisy"},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 201
    category_id = response.json()["id"]

    # Verify audit entry created
    from app.models.audit_log import AuditLog
    entry = test_session.query(AuditLog).filter(
        AuditLog.action == "category_create"
    ).first()
    assert entry is not None
    assert entry.entity_id == category_id
    assert entry.entity_type == "category"
    assert entry.details["type"] == "templates"
    assert entry.details["value"] == "daisy"
    assert entry.details["label"] == "Daisy"
```

### Test Pattern: Fire-and-Forget

```python
def test_category_create_succeeds_when_audit_fails(
    client, admin_auth_token, mocker
):
    mocker.patch(
        "app.services.audit_service.AuditService.log",
        side_effect=Exception("DB connection lost")
    )
    response = client.post(
        "/api/admin/categories/templates",
        json={"value": "tropical", "label": "Tropical"},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    # Main operation MUST still succeed
    assert response.status_code == 201
```

### Test Pattern: User Status Both Changes

```python
def test_user_status_both_changes_generate_two_audit_entries(
    client, test_session, admin_auth_token, inactive_user
):
    # Patch a user: activate AND grant admin in one call
    response = client.patch(
        f"/api/admin/users/{inactive_user.id}",
        json={"is_active": True, "is_admin": True},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200

    from app.models.audit_log import AuditLog
    entries = test_session.query(AuditLog).filter(
        AuditLog.entity_id == inactive_user.id
    ).all()
    actions = {e.action for e in entries}
    assert "user_activate" in actions
    assert "user_grant_admin" in actions
```

### Files to Modify

| File | Action | What to Add |
|------|--------|-------------|
| `backend/app/routers/admin.py` | MODIFY | `import logging` + `Ingredient` model import + `_audit_log` helper + audit calls in category, ingredient, user endpoints |
| `backend/app/routers/recipes.py` | MODIFY | `AuditService` import + `import logging` + `_audit_log` helper + audit calls in update_recipe, delete_recipe |
| `backend/tests/test_audit_log_integration.py` | CREATE | ~22 tests covering all ACs |
| `docs/sprint-artifacts/sprint-status.yaml` | MODIFY | 4-2 status → review |

**NO** new model/schema/migration/service files needed — all infrastructure from Story 4-1 is in place.

### Previous Story Intelligence (4-1)

**From Story 4-1 (Audit Log Infrastructure) — COMPLETED (513 tests passing, status: review):**
- `AuditService.log(db, admin_user_id, action, entity_type, entity_id=None, details=None)` is the exact signature
- Uses `db.flush()` not `db.commit()` — router must call `db.commit()` after
- `AuditLog` model in `backend/app/models/audit_log.py` — `admin_audit_log` table
- `AuditService` already imported in `admin.py`
- All category, ingredient, and user admin endpoints exist in `admin.py` — no new endpoints needed
- Recipe update/delete live in `recipes.py` — admin check already at line 546 and 647
- Existing tests in `test_audit_log.py` (17 tests) — do NOT modify that file; create a new one

### Audit Action Reference (all 12 actions this story wires)

| Action | entity_type | When |
|--------|-------------|------|
| `category_create` | category | POST /admin/categories/{type} |
| `category_update` | category | PUT /admin/categories/{type}/{id} |
| `category_delete` | category | DELETE /admin/categories/{type}/{id} |
| `ingredient_create` | ingredient | POST /admin/ingredients |
| `ingredient_update` | ingredient | PUT /admin/ingredients/{id} |
| `ingredient_delete` | ingredient | DELETE /admin/ingredients/{id} (success only) |
| `ingredient_merge` | ingredient | POST /admin/ingredients/merge |
| `recipe_admin_update` | recipe | PUT /recipes/{id} — admin editing other user's recipe |
| `recipe_admin_delete` | recipe | DELETE /recipes/{id} — admin deleting other user's recipe |
| `user_activate` | user | PATCH /admin/users/{id} — is_active: false→true |
| `user_deactivate` | user | PATCH /admin/users/{id} — is_active: true→false |
| `user_grant_admin` | user | PATCH /admin/users/{id} — is_admin: false→true |
| `user_revoke_admin` | user | PATCH /admin/users/{id} — is_admin: true→false |

### References

- [Source: backend/app/services/audit_service.py — `AuditService.log(db, admin_user_id, action, entity_type, entity_id=None, details=None)` uses `db.flush()` not `db.commit()`]
- [Source: backend/app/services/ingredient_service.py:339-398 — `merge_ingredients()` deletes source Ingredient objects during merge]
- [Source: backend/app/services/user_service.py:73-100 — `update_user_status()` returns `(user, message)`, message="No changes applied" when nothing changed]
- [Source: backend/tests/conftest.py — available fixtures: `admin_auth_token`, `admin_user`, `test_session`, `sample_user`, `auth_token`, `inactive_user`, `another_user`, `sample_recipe`, `orphan_recipe`]
- [Source: backend/tests/test_audit_log.py — 17 existing infrastructure tests, do NOT modify]

---

## Dev Agent Record

### Context Reference

Story context created by BMAD create-story workflow on 2026-04-09.

### Agent Model Used

Claude Opus 4.6

### Debug Log References

- Initial test run: 2 failures (seeded category value collision for "cobbler"/"fizz"), 4 errors (pytest-mock not installed). Fixed by using unique test values and `unittest.mock.patch` context managers.

### Completion Notes List

- Wired all 13 audit actions across 4 entity types (category, ingredient, recipe, user)
- Added `_audit_log` fire-and-forget helper to both `admin.py` and `recipes.py`
- Category update and ingredient update skip audit when no actual changes detected
- Recipe audit only triggers when admin edits/deletes ANOTHER user's recipe (not own, not unowned)
- User status changes generate separate audit entries per change type (activate/deactivate, grant/revoke admin)
- All 22 integration tests passing, 540 total tests passing (0 regressions)
- admin.py coverage: 99%, audit paths fully covered

### Change Log

- 2026-04-09: Story 4-2 implemented — all 13 audit actions wired, 22 integration tests added
- 2026-04-09: Code review fixes — added `if changes:` guard on recipe admin update, added ingredient no-change test, added recipe no-change test, added logger.error assertions to fire-and-forget tests, added admin_user_id assertions to category/ingredient tests, fixed f-string logging to lazy %s format (542 total tests passing)

### File List

| File | Action |
|------|--------|
| `backend/app/routers/admin.py` | MODIFIED — added `import logging`, `Ingredient` model import, `_audit_log` helper, audit calls in category/ingredient/user endpoints |
| `backend/app/routers/recipes.py` | MODIFIED — added `AuditService` import, `import logging`, `_audit_log` helper, audit calls in update_recipe/delete_recipe |
| `backend/tests/test_audit_log_integration.py` | CREATED — 22 tests covering AC-1 through AC-5 |
| `docs/sprint-artifacts/sprint-status.yaml` | MODIFIED — 4-2 status: ready-for-dev → review |
| `docs/sprint-artifacts/4-2-audit-log-integration.md` | MODIFIED — tasks marked complete, Dev Agent Record filled |
