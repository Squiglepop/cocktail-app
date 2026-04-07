# Story 1.2: Admin Recipe Edit

Status: done

---

## Story

As an **admin**,
I want **to edit any recipe regardless of who created it**,
So that **I can fix incorrect data from AI extraction without needing to contact the recipe owner**.

---

## Acceptance Criteria

### AC-1: Admin Can Edit Non-Owned Recipe

**Given** I am authenticated as an admin
**When** I send a PUT request to `/api/recipes/{id}` for a recipe I do NOT own
**Then** the recipe is updated successfully
**And** I receive a 200 response with the updated recipe

### AC-2: Non-Admin Cannot Edit Non-Owned Recipe

**Given** I am authenticated as a regular user (not admin)
**When** I send a PUT request to `/api/recipes/{id}` for a recipe I do NOT own
**Then** I receive a 403 Forbidden response
**And** the recipe is NOT modified

### AC-3: Admin Can Edit All Fields

**Given** I am authenticated as an admin
**When** I edit a recipe
**Then** I can modify all text fields (name, description, instructions, notes, garnish)
**And** I can modify all category assignments (template, glassware, method, serving_style, main_spirit)
**And** I can modify ingredients (add/remove/modify)
**And** I can modify visibility setting
**And** I can transfer ownership to another user (user_id field)

### AC-4: Owner Edit Functionality Preserved

**Given** I am authenticated as an admin
**When** I edit my OWN recipe
**Then** the edit works the same as before (existing functionality preserved)

### AC-5: Regular User Own-Recipe Edit Preserved

**Given** I am authenticated as a regular user (not admin)
**When** I edit a recipe I DO own
**Then** the edit works the same as before (existing functionality preserved)

---

## Tasks / Subtasks

### Task 1: Modify Ownership Check in update_recipe (AC: #1, #2, #4, #5)

- [x] **1.1** Edit [backend/app/routers/recipes.py](backend/app/routers/recipes.py#L526-L551)
- [x] **1.2** Locate the ownership check at lines 546-550:
  ```python
  # CURRENT CODE (lines 546-550):
  if recipe.user_id != current_user.id:
      raise HTTPException(
          status_code=status.HTTP_403_FORBIDDEN,
          detail="You don't have permission to edit this recipe"
      )
  ```
- [x] **1.3** Add admin bypass by checking `is_admin`:
  ```python
  # NEW CODE:
  if recipe.user_id != current_user.id and not current_user.is_admin:
      raise HTTPException(
          status_code=status.HTTP_403_FORBIDDEN,
          detail="You don't have permission to edit this recipe"
      )
  ```
- [x] **1.4** Verify the change preserves:
  - Owner can still edit their own recipe (current_user.id == recipe.user_id bypasses check)
  - Admin can edit any recipe (is_admin bypasses check)
  - Non-owner non-admin still gets 403

### Task 2: Ensure user_id Transfer Works (AC: #3)

- [x] **2.1** Verify RecipeUpdate schema in [backend/app/schemas/recipe.py](backend/app/schemas/recipe.py) includes `user_id: Optional[str]`
- [x] **2.2** If `user_id` is NOT in RecipeUpdate, ADD it:
  ```python
  user_id: Optional[str] = None  # Admin-only: transfer recipe ownership
  ```
- [x] **2.3** The existing update_recipe code already applies all fields from `RecipeUpdate.model_dump(exclude_unset=True)` (line 553-555), so user_id transfer will work automatically once in schema

### Task 3: Write Tests (AC: #1-5)

- [x] **3.1** Create or update `backend/tests/test_recipe_admin.py`
- [x] **3.2** Use existing fixtures from conftest.py:
  - `admin_user` - admin user fixture (already exists from Story 1.1)
  - `admin_auth_token` - admin JWT token (already exists from Story 1.1)
  - `test_user` / `auth_headers` - regular user fixtures
  - `another_user` - second non-admin user
- [x] **3.3** Test: `test_admin_can_edit_any_recipe` (AC: #1)
  - Create recipe owned by `another_user`
  - PUT with admin_auth_token, expect 200
  - Verify recipe fields updated
- [x] **3.4** Test: `test_non_admin_cannot_edit_others_recipe` (AC: #2)
  - Create recipe owned by `another_user`
  - PUT with regular user's auth_headers, expect 403
  - Verify recipe NOT modified
- [x] **3.5** Test: `test_admin_can_edit_all_fields` (AC: #3)
  - Create recipe, edit every field type (text, category, visibility)
  - Verify all changes persisted
- [x] **3.5b** Test: `test_admin_can_modify_recipe_ingredients` (AC: #3)
  - Modify existing ingredient amount, add new ingredient
  - Verify ingredient changes persisted
- [x] **3.6** Test: `test_admin_can_transfer_recipe_ownership` (AC: #3)
  - Create recipe owned by user A
  - Admin transfers to user B via user_id field
  - Verify recipe.user_id == user B
- [x] **3.7** Test: `test_admin_editing_own_recipe_works` (AC: #4)
  - Create recipe owned by admin
  - Admin edits their own recipe, expect 200
- [x] **3.8** Test: `test_owner_can_still_edit_own_recipe` (AC: #5)
  - Regular user edits their own recipe, expect 200
  - Regression test - ensure admin bypass didn't break owner edit
- [x] **3.9** Run full test suite: `pytest` - all tests must pass

### Task 4: Verification

- [x] **4.1** Run `pytest tests/test_recipe_admin.py -v` - all new tests pass
- [x] **4.2** Run `pytest` - full suite passes (no regressions)
- [x] **4.3** Manual verification:
  - Login as admin via API
  - Try editing recipe not owned by admin, verify success
  - Login as regular user, verify cannot edit others' recipes

---

## Dev Notes

### Critical Code Location

**FILE:** [backend/app/routers/recipes.py](backend/app/routers/recipes.py)

**FUNCTION:** `update_recipe` (lines 526-616)

**OWNERSHIP CHECK LOCATION:** Lines 546-550

```python
# Current code to modify (EXACT LINES 546-550):
if recipe.user_id != current_user.id:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You don't have permission to edit this recipe"
    )
```

**CHANGE REQUIRED:** Add `and not current_user.is_admin` to the condition:

```python
if recipe.user_id != current_user.id and not current_user.is_admin:
```

### Architecture Compliance

**This is Story 1.2 in Epic 1.** The `require_admin` dependency was created in Story 1.1 but is NOT needed here because:
- This is NOT an admin-only endpoint - regular users can edit their OWN recipes
- We need an ownership bypass for admins, not full admin-only restriction
- Simply check `current_user.is_admin` in the existing ownership logic

**From [docs/admin-panel-architecture.md](docs/admin-panel-architecture.md#L76-L80):**
> **Modifications Required:**
> - `recipes.py` lines 539-550, 631-642: Add admin bypass to ownership checks
> - Pattern: `if recipe.user_id != current_user.id and not is_admin:`

### Previous Story Intelligence (Story 1.1)

**Test Fixtures Available:**
- `admin_user` - Admin user fixture (conftest.py line ~123)
- `admin_auth_token` - Admin JWT token fixture (conftest.py line ~133)
- Use `admin_auth_token` in Authorization header: `{"Authorization": f"Bearer {admin_auth_token}"}`

**User Model Fields (already added):**
- `is_admin: Mapped[bool]` - Boolean flag for admin status
- Access via `current_user.is_admin`

**Learnings from Story 1.1 Review:**
- Verify actual test coverage with `coverage report`, don't claim coverage without proof
- Test naming must describe WHAT, not just function name
- Always run `git status` to check for untracked new files

### Technical Requirements

| Requirement | Value | Source |
|-------------|-------|--------|
| SQLAlchemy Syntax | `Mapped[]` for any new fields | project_context.md |
| HTTP Error | Use `detail` key | project_context.md |
| Test fixtures | Use existing from conftest.py | project_context.md |
| Test naming | Describe behavior, not function | Story 1.1 learnings |

### File Locations

| File | Action | Purpose |
|------|--------|---------|
| `backend/app/routers/recipes.py` | MODIFY (lines 546-550) | Add admin bypass |
| `backend/app/schemas/recipes.py` | VERIFY/MODIFY | Ensure user_id in RecipeUpdate |
| `backend/tests/test_recipe_admin.py` | CREATE | Admin recipe edit tests |

### Anti-Patterns to Avoid

**DO NOT:**
- Create a new admin-only endpoint - use existing PUT `/api/recipes/{id}`
- Import `require_admin` dependency - not needed for bypass pattern
- Modify the `get_current_user` dependency - keep auth layer separate
- Add audit logging yet - that's Epic 4 (Story 4.2)

**DO:**
- Check `current_user.is_admin` directly in the ownership condition
- Preserve backward compatibility for regular user edit
- Use existing test fixtures

### Edge Cases to Handle

1. **Admin editing their own recipe:** Should work (is_admin OR is_owner both allow edit)
2. **Recipe with no owner (user_id = None):** Current code allows anyone to edit orphan recipes - preserve this behavior
3. **Ownership transfer to non-existent user:** RecipeUpdate should validate user_id exists if provided
4. **Deactivated admin:** get_current_user already rejects inactive users before reaching this check

### RecipeUpdate Schema Check

Before implementing, verify [backend/app/schemas/recipe.py](backend/app/schemas/recipe.py) has `user_id` in RecipeUpdate:

```python
class RecipeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    # ... other fields ...
    user_id: Optional[str] = None  # <-- MUST EXIST for ownership transfer
```

If missing, add it. The existing code at line 553-555 uses `model_dump(exclude_unset=True)` which will automatically include user_id in updates.

### PRD/Architecture Cross-Reference

| Requirement | Implementation |
|-------------|----------------|
| FR-3.3.1: Admin can edit ANY recipe | Add `and not current_user.is_admin` to ownership check |
| FR-3.3.1: All text fields editable | Already supported by RecipeUpdate schema |
| FR-3.3.1: Category assignments editable | Already supported |
| FR-3.3.1: Ingredients editable | Already supported |
| FR-3.3.1: Visibility editable | Already supported |
| FR-3.3.1: Ownership transfer | Add user_id to RecipeUpdate if missing |

---

## Dev Agent Record

### Context Reference

Story context created by BMAD create-story workflow on 2026-01-10.

### Agent Model Used

Claude (implementation), Claude Opus 4.5 (validation)

### Debug Log References

(To be filled during implementation)

### Completion Notes List

- Implementation complete: admin bypass added at recipes.py:546
- 10 tests written and passing in test_recipe_admin.py
- RecipeUpdate schema already had user_id field (line 102)
- Validated 2026-01-10: all ACs covered, tests green
- Added missing ingredient modification test (AC-3 gap)
- **Code Review 2026-01-13**: Added validation for ownership transfer target user exists (recipes.py:552-559)
- **Code Review 2026-01-13**: Updated schema comment to reflect owner OR admin can transfer (recipe.py:102)
- **Code Review 2026-01-13**: Added 4 new tests for ownership transfer edge cases (13 total tests)

### File List

**To Modify:**
- `backend/app/routers/recipes.py` - Add admin bypass to ownership check (line 546-550), add target user validation (line 552-559)
- `backend/app/schemas/recipe.py` - Updated user_id comment (line 102)

**To Create:**
- `backend/tests/test_recipe_admin.py` - Admin recipe edit tests (13 tests)

---

## Change Log

| Date | Change |
|------|--------|
| 2026-01-10 | Story created via create-story workflow, status: ready-for-dev |
| 2026-01-10 | Story implemented and validated, status: done |
| 2026-01-13 | Code review: Added target user validation, owner transfer tests, updated schema comment |
