# Story 1.3: Admin Recipe Delete

Status: done

---

## Story

As an **admin**,
I want **to delete any recipe regardless of who created it**,
So that **I can remove inappropriate or duplicate content from the library**.

---

## Acceptance Criteria

### AC-1: Admin Can Delete Non-Owned Recipe

**Given** I am authenticated as an admin
**When** I send a DELETE request to `/api/recipes/{id}` for a recipe I do NOT own
**Then** the recipe is deleted successfully
**And** I receive a 200 response with success message

### AC-2: Non-Admin Cannot Delete Non-Owned Recipe

**Given** I am authenticated as a regular user (not admin)
**When** I send a DELETE request to `/api/recipes/{id}` for a recipe I do NOT own
**Then** I receive a 403 Forbidden response
**And** the recipe is NOT deleted

### AC-3: Image File Cleanup on Delete

**Given** a recipe has an associated image file
**When** an admin deletes the recipe
**Then** the image file is also deleted from storage
**And** the filesystem is cleaned up properly

### AC-4: Recipe Ingredients Cascade Delete

**Given** a recipe has associated ingredients in `recipe_ingredients` junction table
**When** an admin deletes the recipe
**Then** the `recipe_ingredients` records are cascade deleted
**And** no orphaned ingredient associations remain

### AC-5: Admin Can Delete Own Recipe (Existing Functionality Preserved)

**Given** I am authenticated as an admin
**When** I delete my OWN recipe
**Then** the delete works the same as before (existing functionality preserved)

### AC-6: Regular User Can Delete Own Recipe (Regression Check)

**Given** I am authenticated as a regular user (not admin)
**When** I delete a recipe I DO own
**Then** the delete works the same as before (existing functionality preserved)

---

## Tasks / Subtasks

### Task 1: Modify Ownership Check in delete_recipe (AC: #1, #2, #5, #6)

- [x] **1.1** Edit [backend/app/routers/recipes.py](backend/app/routers/recipes.py#L638-L642)
- [x] **1.2** Locate the ownership check at lines 638-642:
  ```python
  # CURRENT CODE (lines 638-642):
  if recipe.user_id != current_user.id:
      raise HTTPException(
          status_code=status.HTTP_403_FORBIDDEN,
          detail="You don't have permission to delete this recipe"
      )
  ```
- [x] **1.3** Add admin bypass by checking `is_admin` (same pattern as line 546):
  ```python
  # NEW CODE:
  if recipe.user_id != current_user.id and not current_user.is_admin:
      raise HTTPException(
          status_code=status.HTTP_403_FORBIDDEN,
          detail="You don't have permission to delete this recipe"
      )
  ```
- [x] **1.4** Verify the change preserves:
  - Owner can still delete their own recipe (current_user.id == recipe.user_id bypasses check)
  - Admin can delete any recipe (is_admin bypasses check)
  - Non-owner non-admin still gets 403

### Task 2: Verify Image Deletion Logic (AC: #3)

- [x] **2.1** Confirm image deletion code exists at lines 644-647:
  ```python
  if recipe.source_image_path:
      image_storage = get_image_storage()
      image_storage.delete_image(recipe.source_image_path)
  ```
- [x] **2.2** No changes needed - existing code handles image cleanup
- [x] **2.3** Write test to verify image deletion works for admin delete

### Task 3: Verify Cascade Delete for Ingredients (AC: #4)

- [x] **3.1** Confirm Recipe model has cascade relationship with RecipeIngredient
- [x] **3.2** Verify `db.delete(recipe)` triggers cascade (line 649)
- [x] **3.3** No changes needed if cascade is configured - write test to verify

### Task 4: Write Tests (AC: #1-6)

- [x] **4.1** Add tests to existing `backend/tests/test_recipe_admin.py` (created in Story 1.2)
- [x] **4.2** Use existing fixtures from conftest.py:
  - `admin_user` / `admin_auth_token` - admin fixtures
  - `test_user` / `auth_headers` - regular user fixtures
  - `another_user` - second non-admin user
- [x] **4.3** Test: `test_admin_can_delete_any_recipe` (AC: #1)
  - Create recipe owned by `another_user`
  - DELETE with admin_auth_token, expect 200
  - Verify recipe no longer exists in database
- [x] **4.4** Test: `test_non_admin_cannot_delete_others_recipe` (AC: #2)
  - Create recipe owned by `another_user`
  - DELETE with regular user's auth_headers, expect 403
  - Verify recipe still exists in database
- [x] **4.5** Test: `test_admin_delete_removes_recipe_image` (AC: #3)
  - Create recipe with image_path
  - Mock image storage delete
  - DELETE with admin_auth_token
  - Verify `delete_image` was called with correct path
- [x] **4.6** Test: `test_admin_delete_cascades_to_recipe_ingredients` (AC: #4)
  - Create recipe with ingredients
  - DELETE with admin_auth_token
  - Verify recipe_ingredients records were deleted
- [x] **4.7** Test: `test_admin_can_delete_own_recipe` (AC: #5)
  - Create recipe owned by admin
  - DELETE with admin_auth_token, expect 200
  - Verify recipe deleted
- [x] **4.8** Test: `test_owner_can_still_delete_own_recipe` (AC: #6)
  - Regular user deletes their own recipe, expect 200
  - Regression test - ensure admin bypass didn't break owner delete
- [x] **4.9** Run full test suite: `pytest` - all tests must pass

### Task 5: Verification

- [x] **5.1** Run `pytest tests/test_recipe_admin.py -v` - all new tests pass (16/16 passed)
- [x] **5.2** Run `pytest` - full suite passes (293/293 passed, no regressions)
- [x] **5.3** Manual verification:
  - Login as admin via API
  - Delete a recipe not owned by admin, verify success
  - Login as regular user, verify cannot delete others' recipes
- [x] **5.4** Verify no orphaned recipe_ingredients remain after delete

---

## Dev Notes

### Critical Code Location

**FILE:** [backend/app/routers/recipes.py](backend/app/routers/recipes.py)

**FUNCTION:** `delete_recipe` (lines 619-652)

**OWNERSHIP CHECK LOCATION:** Lines 638-642

```python
# Current code to modify (EXACT LINES 638-642):
if recipe.user_id != current_user.id:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You don't have permission to delete this recipe"
    )
```

**CHANGE REQUIRED:** Add `and not current_user.is_admin` to the condition:

```python
if recipe.user_id != current_user.id and not current_user.is_admin:
```

**THIS IS THE EXACT SAME PATTERN AS STORY 1.2** - See line 546 which already has the admin bypass for edit.

### Architecture Compliance

**This is Story 1.3 in Epic 1.** Follow the exact same pattern as Story 1.2.

**From [docs/admin-panel-architecture.md](docs/admin-panel-architecture.md#L76-L80):**
> **Modifications Required:**
> - `recipes.py` lines 539-550, 631-642: Add admin bypass to ownership checks
> - Pattern: `if recipe.user_id != current_user.id and not is_admin:`

### Previous Story Intelligence

**From Story 1.2 (Admin Recipe Edit):**
- Admin bypass pattern: `and not current_user.is_admin` added to ownership check
- Test fixtures: `admin_user`, `admin_auth_token` already available
- Tests written in `test_recipe_admin.py` - ADD NEW TESTS TO THIS FILE
- All 8 edit tests passing, 290+ total tests in suite

**From Story 1.1 (Admin User Setup):**
- `is_admin` field available on User model
- Access via `current_user.is_admin`
- Test naming must describe WHAT behavior is tested
- Always run `git status` to check for untracked files
- Verify coverage with `coverage report`

### Git Intelligence (Recent Commits)

```
5163a06 feat: Add admin capabilities for user and recipe management (Epic 1)
0ee7f5e feat: Polish mobile filter dropdown UX
e8bf331 fix: Show empty state when filters return no results
```

**Commit `5163a06` includes:**
- Story 1.1: Admin user setup (is_admin field, require_admin dependency)
- Story 1.2: Admin recipe edit bypass
- Tests in `test_recipe_admin.py` and `test_admin_auth.py`

### Technical Requirements

| Requirement | Value | Source |
|-------------|-------|--------|
| Python Version | 3.9+ | project_context.md |
| SQLAlchemy Syntax | `Mapped[]` (no changes needed) | project_context.md |
| HTTP Error | Use `detail` key | project_context.md |
| Test fixtures | Use existing from conftest.py | project_context.md |
| Test naming | Describe behavior | Story 1.1/1.2 learnings |

### File Locations

| File | Action | Purpose |
|------|--------|---------|
| `backend/app/routers/recipes.py` | MODIFY (line 638) | Add admin bypass |
| `backend/tests/test_recipe_admin.py` | MODIFY (add tests) | Admin recipe delete tests |

### Anti-Patterns to Avoid

**DO NOT:**
- Create a new admin-only endpoint - use existing DELETE `/api/recipes/{id}`
- Import `require_admin` dependency - not needed for bypass pattern
- Modify image deletion logic - it already works
- Add audit logging yet - that's Epic 4 (Story 4.2)
- Create a new test file - add to existing `test_recipe_admin.py`

**DO:**
- Check `current_user.is_admin` directly in the existing ownership condition
- Preserve backward compatibility for regular user delete
- Use existing test fixtures
- Follow the EXACT pattern from Story 1.2

### Image Deletion - Already Implemented

The delete function already handles image cleanup at lines 644-647:
```python
if recipe.source_image_path:
    image_storage = get_image_storage()
    image_storage.delete_image(recipe.source_image_path)
```

No changes needed - just verify with tests.

### Cascade Delete - Already Implemented

SQLAlchemy ORM cascade handles `recipe_ingredients` deletion. The Recipe model has a relationship with cascade configured. When `db.delete(recipe)` runs, orphaned junction records are automatically deleted.

No changes needed - just verify with tests.

### Edge Cases to Handle

1. **Admin deleting their own recipe:** Should work (is_admin OR is_owner both allow delete)
2. **Recipe with no owner (user_id = None):** Current code allows anyone to delete orphan recipes - preserve this behavior
3. **Recipe without image:** `source_image_path` check handles this (line 645)
4. **Recipe with no ingredients:** No junction records to cascade - no issue
5. **Deactivated admin:** get_current_user already rejects inactive users before reaching this check

### PRD/Architecture Cross-Reference

| Requirement | Implementation |
|-------------|----------------|
| FR-3.3.2: Admin bypass for delete | Add `and not current_user.is_admin` to ownership check |
| FR-3.3.2: Hard delete | Already implemented - `db.delete(recipe)` |
| FR-3.3.2: Image cleanup | Already implemented - lines 644-647 |
| FR-3.3.2: Cascade to recipe_ingredients | Already implemented - ORM cascade |

### Test Coverage Requirements

Add 6 new tests to `test_recipe_admin.py`:
1. `test_admin_can_delete_any_recipe`
2. `test_non_admin_cannot_delete_others_recipe`
3. `test_admin_delete_removes_recipe_image`
4. `test_admin_delete_cascades_to_recipe_ingredients`
5. `test_admin_can_delete_own_recipe`
6. `test_owner_can_still_delete_own_recipe`

---

## Dev Agent Record

### Context Reference

Story context created by BMAD create-story workflow on 2026-01-13.

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- No debug issues encountered - implementation followed exact pattern from Story 1.2

### Completion Notes List

- **Task 1**: Added `and not current_user.is_admin` to ownership check at line 638 in `recipes.py`. Single-line change matching the exact pattern from Story 1.2 (line 546).
- **Task 2**: Verified image deletion logic exists at lines 644-647. No changes needed.
- **Task 3**: Verified cascade delete is properly configured:
  - Recipe model has `cascade="all, delete-orphan"` on ingredients relationship (line 93)
  - RecipeIngredient has `ForeignKey(..., ondelete="CASCADE")` (line 135)
- **Task 4**: Added 6 new test classes/methods to `test_recipe_admin.py`:
  - `TestAdminRecipeDeleteBypass` (2 tests)
  - `TestAdminDeleteImageCleanup` (1 test)
  - `TestAdminDeleteCascade` (1 test)
  - `TestAdminDeleteOwnRecipe` (1 test)
  - `TestRegularUserOwnRecipeDelete` (1 test)
- **Task 5**: All 293 backend tests pass. Coverage at 76%.

### Implementation Plan

Single-line modification following established admin bypass pattern:
```python
# Before (line 638):
if recipe.user_id != current_user.id:

# After:
if recipe.user_id != current_user.id and not current_user.is_admin:
```

### File List

**Modified:**
- `backend/app/routers/recipes.py` - Added admin bypass to delete ownership check (line 647), updated docstring (line 634)
- `backend/tests/test_recipe_admin.py` - Added 8 tests for admin delete (lines 423-693), updated module docstring

---

## Change Log

| Date | Change |
|------|--------|
| 2026-01-13 | Story created via create-story workflow, status: ready-for-dev |
| 2026-01-13 | Implementation complete: admin bypass added, 6 tests added, 293/293 tests pass. Status: Ready for Review |
| 2026-01-30 | **Code Review**: Fixed outdated docstring (recipes.py:634), added 2 tests (unauthenticated delete, orphan recipe delete), updated test module docstring. 21 tests pass. Status: done |
