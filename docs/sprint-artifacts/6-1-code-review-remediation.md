# Story 6.1: Code Review Remediation (Medium-Effort Fixes)

Status: done

## Story

As a **developer maintaining the Cocktail Shots codebase**,
I want **to fix the medium-severity findings from the full-project code review**,
So that **the codebase adheres to documented standards for error handling, audit safety, and production logging**.

## Background

A full adversarial code review (2026-04-12) across Epics 1-5 identified 13 findings. The 4 quick wins (C-1: require_admin on cleanup-orphans, C-2: provider hierarchy swap, H-1: Python 3.9 type annotations, L-2: AdminBadge act() warnings) are already fixed. This story covers the 5 medium-effort fixes. Significant-effort items (collections service extraction, collections test suite, recipes service extraction) are deferred to separate stories.

## Acceptance Criteria

### AC-1: IntegrityError Handling on All INSERT Operations

**Given** any endpoint that creates a new database record
**When** a constraint violation occurs (duplicate key, FK violation, race condition)
**Then** the endpoint returns an appropriate HTTP error (400 or 409) instead of an unhandled 500

**Specifically — these 7 locations must catch `IntegrityError`:**
- `POST /api/auth/register` — duplicate email → 400
- `store_refresh_token()` service — JTI collision → raise ValueError
- `POST /api/collections` — constraint violation → 409
- `POST /api/collections/{id}/recipes` — duplicate recipe in collection → 409
- `POST /api/recipes` — constraint violation → 409
- `POST /api/upload/extract` — constraint violation → 500 with job failure
- `POST /api/upload` — constraint violation → 500 with job failure

**Out of scope (documented):** `PUT /api/recipes/{id}` (update) also has an unprotected `db.commit()` at ~line 606, but recipe updates modify existing rows rather than inserting new ones, making constraint violations less likely. Deferred to a future hardening story if needed.

### AC-2: Audit Log Wrapper Simplified (No Dangerous Rollback)

**Given** the `_audit_log()` wrappers in `recipes.py` and `admin.py`
**When** audit logging fails
**Then** the error is logged but `db.rollback()` is NOT called
**And** the already-committed main operation is unaffected

The `AuditService.log()` already uses `db.begin_nested()` (SAVEPOINT) internally. The router wrapper's `db.commit()` + `db.rollback()` is redundant and dangerous. Simplify to just call `AuditService.log()` + `db.commit()`, with only `logger.error()` on failure.

### AC-3: Rating Endpoints Have 401 Test Coverage

**Given** the `PUT /api/recipes/{id}/my-rating` endpoint
**And** the `DELETE /api/recipes/{id}/my-rating` endpoint
**When** called without authentication
**Then** they return 401

### AC-4: Console Statements Replaced with Debug Module

**Given** production frontend code (not test files)
**When** logging is needed for diagnostics
**Then** the existing `lib/debug.ts` module is used (not direct `console.log`/`console.error`)

**Specifically — ~32 console statements across 11 source files must be replaced or removed.**

### AC-5: HTTPException in Auth Service Documented as Accepted Exception

**Given** `get_current_user()` and `get_current_user_optional()` in `services/auth.py`
**When** reviewing for architecture violations
**Then** a code comment documents that these are FastAPI dependencies (not pure services) and the HTTPException usage is intentional

---

## Tasks / Subtasks

### Task 1: Add IntegrityError Handling to Backend INSERT Operations (AC: #1)

- [x] **1.1** `backend/app/routers/auth.py` lines 64-66: Wrap user creation `db.commit()` in try/except `IntegrityError`. On catch: `db.rollback()`, raise `HTTPException(400, detail="Email already registered")`.
  - Import `from sqlalchemy.exc import IntegrityError`
  - The email uniqueness check at line 45 catches most cases, but a race condition can slip through

- [x] **1.2** `backend/app/services/auth.py` lines 196-197: Wrap `store_refresh_token` commit in try/except `IntegrityError`. On catch: `db.rollback()`, raise `ValueError("Token storage failed")`.
  - This is a service function, so follow the ValueError convention (not HTTPException)
  - Import `from sqlalchemy.exc import IntegrityError`

- [x] **1.3** `backend/app/routers/collections.py` line ~232: Wrap `create_collection` commit in try/except `IntegrityError`. On catch: `db.rollback()`, raise `HTTPException(409, detail="Collection could not be created")`.

- [x] **1.4** `backend/app/routers/collections.py` line ~367: Wrap `add_recipe_to_collection` commit in try/except `IntegrityError`. On catch: `db.rollback()`, raise `HTTPException(409, detail="Recipe already in collection")`.

- [x] **1.5** `backend/app/routers/recipes.py` line ~481: Wrap recipe creation `db.commit()` in try/except `IntegrityError`. On catch: `db.rollback()`, raise `HTTPException(409, detail="Recipe could not be created")`.

- [x] **1.6** `backend/app/routers/upload.py` lines ~294 and ~422: Wrap both recipe creation commits in try/except `IntegrityError`. On catch: `db.rollback()`, update job status to "failed", raise `HTTPException(500, detail="Failed to save extracted recipe")`.

- [x] **1.7** Write tests for each IntegrityError path:
  - `test_register_duplicate_email_returns_400` (mock IntegrityError on commit)
  - `test_create_collection_integrity_error_returns_409`
  - `test_add_recipe_to_collection_duplicate_returns_409`
  - `test_create_recipe_integrity_error_returns_409`
  - `test_upload_extract_integrity_error_returns_500` (upload.py extract endpoint)
  - `test_upload_and_extract_integrity_error_returns_500` (upload.py combined endpoint)
  - Tests can mock `db.commit` to raise `IntegrityError` to trigger the handler
  - Reference pattern: see `test_admin_ingredients.py:379-449` for the exact `commit_that_fails` mock pattern used in this codebase

### Task 2: Simplify Audit Log Wrappers (AC: #2)

- [x] **2.1** `backend/app/routers/recipes.py` lines 39-46: Simplify `_audit_log()` — remove `db.rollback()`. The wrapper should be:
  ```python
  def _audit_log(db, admin_id, action, entity_type, entity_id, details):
      """Fire-and-forget audit wrapper. Main operation is already committed."""
      try:
          AuditService.log(db, admin_id, action, entity_type, entity_id, details)
          db.commit()
      except Exception as e:
          logger.error("Audit log failed: %s", e)
  ```

- [x] **2.2** `backend/app/routers/admin.py` lines 68-75: Apply identical simplification.

- [x] **2.3** Verify existing audit tests still pass. The `test_audit_failure_does_not_block_operation` tests in the admin test suite confirm fire-and-forget behavior.

### Task 3: Add Rating Endpoint Auth Tests (AC: #3)

- [x] **3.1** In `backend/tests/test_recipes.py`, add:
  ```python
  def test_rate_recipe_returns_401_without_auth(client, sample_recipe):
      """No token → 401."""
      response = client.put(f"/api/recipes/{sample_recipe.id}/my-rating", json={"score": 4})
      assert response.status_code == 401

  def test_delete_rating_returns_401_without_auth(client, sample_recipe):
      """No token → 401."""
      response = client.delete(f"/api/recipes/{sample_recipe.id}/my-rating")
      assert response.status_code == 401
  ```

### Task 4: Replace Console Statements with Debug Module (AC: #4)

- [x] **4.1** Create namespace loggers for missing domains. The existing `lib/debug.ts` has `swDebug`, `offlineDebug`, `favouritesDebug`, `cacheDebug`. Add:
  ```typescript
  export const homeDebug = debug.ns('home');
  export const recipeDebug = debug.ns('recipe');
  export const playlistDebug = debug.ns('playlist');
  export const shareDebug = debug.ns('share');
  export const apiDebug = debug.ns('api');
  ```

- [x] **4.2** `frontend/app/page.tsx` (5 statements): Replace all `console.log()` with `homeDebug.log()`. Import from `@/lib/debug`.

- [x] **4.3** `frontend/app/recipes/[id]/page.tsx` (4 statements): Replace `console.log()` with `recipeDebug.log()` and `console.error()` with `recipeDebug.error()`.

- [x] **4.4** `frontend/app/playlists/[id]/page.tsx` (7 statements): Replace with `playlistDebug.log()`/`playlistDebug.error()`.

- [x] **4.5** `frontend/components/playlists/AddToPlaylistButton.tsx` (5 statements): Replace with `playlistDebug`.

- [x] **4.6** `frontend/components/playlists/SharePlaylistModal.tsx` (1 statement): Replace `.catch(console.error)` with `.catch(playlistDebug.error)`.

- [x] **4.7** `frontend/components/recipes/RecipeGrid.tsx` (2 statements): Replace with `recipeDebug.log()`.

- [x] **4.8** `frontend/components/ServiceWorkerRegistration.tsx` (2 statements): Replace with `swDebug` (already exists).

- [x] **4.9** `frontend/lib/auth-context.tsx` (2 statements): Replace `console.error()` calls with a new `authDebug` namespace logger. Note: `debug.error()` always logs regardless of env — correct for auth failures.

- [x] **4.10** `frontend/lib/share.ts` (2 statements): Replace with `shareDebug.error()`.

- [x] **4.11** `frontend/app/health/route.ts` (1 statement): Replace with `apiDebug.error()`.

- [x] **4.12** `frontend/app/api/[...path]/route.ts` (1 statement): Replace with `apiDebug.error()`.

- [x] **4.13** Verify no regressions: `npm test -- --run` passes. Verify no remaining `console.log` or `console.error` in non-test source files (grep to confirm).

### Task 5: Document Auth Service HTTPException as Accepted Pattern (AC: #5)

- [x] **5.1** In `backend/app/services/auth.py`, add a clarifying comment above `get_current_user()` (~line 120):
  ```python
  # NOTE: get_current_user is a FastAPI Depends() dependency, not a pure service.
  # HTTPException is intentional here — this function is always called via Depends()
  # and never directly by service code. See project_context.md architecture boundaries.
  ```

---

## Dev Notes

### Line Numbers Are Approximate

All line references in this story were captured at story-creation time. After the first edit to a file (e.g., adding a try/except block), subsequent line numbers in that same file will shift. **Match by function name and surrounding code pattern, not by line number alone.**

### Error Handling Convention
Services: `ValueError` (→ 400), `LookupError` (→ 404), `return None` (→ 404/409). Routers catch and convert.
Exception: FastAPI dependencies (`get_current_user`, `require_admin`) may raise HTTPException directly.

### IntegrityError Pattern (from project_context.md)
```python
from sqlalchemy.exc import IntegrityError

try:
    db.commit()
    db.refresh(record)
    return record
except IntegrityError:
    db.rollback()
    raise HTTPException(status_code=409, detail="Already exists")
```

### Debug Module Pattern (from lib/debug.ts)
```typescript
import { homeDebug } from '@/lib/debug';
// In dev: logs with [home] prefix. In prod: silenced (except .error()).
homeDebug.log('message', data);
homeDebug.error('always logs, even in prod');
```

### Files Modified

**Backend (7 files):**
- `backend/app/routers/auth.py` — IntegrityError on register
- `backend/app/routers/collections.py` — IntegrityError on create + add recipe
- `backend/app/routers/recipes.py` — IntegrityError on create + audit wrapper fix
- `backend/app/routers/upload.py` — IntegrityError on extract (2 locations)
- `backend/app/routers/admin.py` — audit wrapper fix
- `backend/app/services/auth.py` — IntegrityError on refresh token + comment
- `backend/tests/test_recipes.py` — rating auth tests

**Frontend (12 files):**
- `frontend/lib/debug.ts` — add namespace loggers
- `frontend/app/page.tsx` — replace console.log
- `frontend/app/recipes/[id]/page.tsx` — replace console.log/error
- `frontend/app/playlists/[id]/page.tsx` — replace console.log/error
- `frontend/app/health/route.ts` — replace console.error
- `frontend/app/api/[...path]/route.ts` — replace console.error
- `frontend/components/playlists/AddToPlaylistButton.tsx` — replace console.log/error
- `frontend/components/playlists/SharePlaylistModal.tsx` — replace console.error
- `frontend/components/recipes/RecipeGrid.tsx` — replace console.log
- `frontend/components/ServiceWorkerRegistration.tsx` — replace console.log/error
- `frontend/lib/auth-context.tsx` — replace console.error
- `frontend/lib/share.ts` — replace console.error

### Project Structure Notes

- All changes are modifications to existing files — no new files created except namespace loggers added to existing `debug.ts`
- Follows existing `project_context.md` patterns exactly
- No new dependencies introduced

### References

- [Source: Full Project Code Review 2026-04-12] — review findings document
- [Source: docs/project_context.md#Defensive Coding Patterns] — IntegrityError handling pattern
- [Source: docs/project_context.md#Admin Panel Patterns] — SAVEPOINT and audit patterns
- [Source: docs/project_context.md#Code Quality & Style] — architecture boundaries
- [Source: docs/admin-panel-architecture.md#Audit Atomicity] — fire-and-forget pattern

## Dev Agent Record

### Implementation Plan

- Task 1: Added `IntegrityError` try/except around all INSERT `db.commit()` calls in 6 locations across auth, collections, recipes, and upload routers. Services use `ValueError` convention. Upload endpoints re-raise as `HTTPException` to bypass outer catch-all.
- Task 2: Removed dangerous `db.rollback()` from `_audit_log()` wrappers in `recipes.py` and `admin.py`. `AuditService.log()` already uses `db.begin_nested()` (SAVEPOINT) internally.
- Task 3: Added 2 missing 401 auth tests for rating PUT/DELETE endpoints.
- Task 4: Added 6 namespace loggers to `debug.ts` (`home`, `recipe`, `playlist`, `share`, `api`, `auth`). Replaced ~32 console statements across 11 source files. Updated 1 test file (`ServiceWorkerRegistration.test.tsx`) to match new debug module behavior.
- Task 5: Added clarifying comment above `get_current_user()` documenting intentional HTTPException usage in FastAPI dependency.

### Completion Notes List

- ✅ Task 1: IntegrityError handling on 7 INSERT operations (6 code locations + tests)
- ✅ Task 2: Audit wrapper simplified — removed dangerous `db.rollback()` in 2 files
- ✅ Task 3: Rating endpoint auth tests — 2 new 401 tests
- ✅ Task 4: Console statements replaced — 32 statements across 11 files migrated to debug module
- ✅ Task 5: Auth service HTTPException documented as accepted pattern
- All 552 backend tests pass (82% coverage)
- 360/361 frontend tests pass (1 pre-existing flaky test in recipe-edit ingredient management — passes in isolation)

### Change Log

- 2026-04-12: Implemented all 5 tasks for story 6-1 code review remediation
- 2026-04-12: Code review fixes — added missing store_refresh_token IntegrityError test, added IntegrityError handling to extract-multi endpoint, documented 3 quick-win file changes in File List, corrected frontend test count

### File List

**Backend (modified):**
- `backend/app/routers/auth.py` — IntegrityError import + try/except on register commit
- `backend/app/routers/collections.py` — IntegrityError import + try/except on create_collection and add_recipe commits
- `backend/app/routers/recipes.py` — IntegrityError import + try/except on create_recipe commit + audit wrapper db.rollback() removed
- `backend/app/routers/upload.py` — IntegrityError import + try/except on all three extract endpoint commits (extract, extract-immediate, extract-multi) + HTTPException re-raise
- `backend/app/routers/admin.py` — audit wrapper db.rollback() removed
- `backend/app/services/auth.py` — IntegrityError import + try/except on store_refresh_token + documentation comment
- `backend/app/services/category_service.py` — Python 3.9 type annotations (list[X] → List[X]) (quick-win H-1)
- `backend/tests/test_auth.py` — 1 new IntegrityError test (register race condition)
- `backend/tests/test_cleanup.py` — Auth test fixes: added 401/403 tests, switched to admin_auth_token (quick-win C-1)
- `backend/tests/test_recipes.py` — 3 new tests (recipe IntegrityError, collection IntegrityError, collection recipe duplicate + 2 rating auth tests)
- `backend/tests/test_upload.py` — 2 new IntegrityError tests (extract + extract-immediate)
- `backend/tests/test_services/test_token_service.py` — 1 new IntegrityError test (store_refresh_token JTI collision)

**Frontend (modified):**
- `frontend/lib/debug.ts` — 6 new namespace loggers (home, recipe, playlist, share, api, auth)
- `frontend/app/page.tsx` — console.log → homeDebug.log (5 replacements)
- `frontend/app/recipes/[id]/page.tsx` — console.log/error → recipeDebug (4 replacements)
- `frontend/app/playlists/[id]/page.tsx` — console.error → playlistDebug.error (7 replacements)
- `frontend/app/health/route.ts` — console.error → apiDebug.error
- `frontend/app/api/[...path]/route.ts` — console.error → apiDebug.error
- `frontend/app/layout.tsx` — Provider hierarchy fix: OfflineProvider now wraps FavouritesProvider (matches project_context.md order) (quick-win C-2)
- `frontend/components/playlists/AddToPlaylistButton.tsx` — console.log/error → playlistDebug (5 replacements)
- `frontend/components/playlists/SharePlaylistModal.tsx` — console.error → playlistDebug.error
- `frontend/components/recipes/RecipeGrid.tsx` — console.log → recipeDebug.log (2 replacements)
- `frontend/components/ServiceWorkerRegistration.tsx` — console.log/error → swDebug
- `frontend/lib/auth-context.tsx` — console.error → authDebug.error (2 replacements)
- `frontend/lib/share.ts` — console.error → shareDebug.error (2 replacements)
- `frontend/tests/components/ServiceWorkerRegistration.test.tsx` — updated to match debug module output format
