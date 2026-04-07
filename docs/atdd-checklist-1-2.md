# ATDD Checklist - Epic 1, Story 2: Admin Recipe Edit

**Date:** 2026-01-10
**Author:** Deemo
**Primary Test Level:** API (pytest)

---

## Story Summary

Enable admin users to edit any recipe in the system regardless of ownership, to fix incorrect data from AI extraction without contacting recipe owners.

**As a** admin user
**I want** to edit any recipe regardless of who created it
**So that** I can fix incorrect data from AI extraction without needing to contact the recipe owner

---

## Acceptance Criteria

1. **AC-1:** Admin can edit non-owned recipe (returns 200)
2. **AC-2:** Non-admin cannot edit non-owned recipe (returns 403)
3. **AC-3:** Admin can edit all fields including ownership transfer
4. **AC-4:** Admin editing own recipe works (regression test)
5. **AC-5:** Regular user editing own recipe works (regression test)

---

## Failing Tests Created (RED Phase)

### API Tests (9 tests)

**File:** `backend/tests/test_recipe_admin.py` (185 lines)

#### TestAdminRecipeEditBypass

- **Test:** `test_admin_can_edit_any_recipe`
  - **Status:** RED - AssertionError: 403 != 200
  - **Verifies:** AC-1 - Admin can edit recipe they don't own

- **Test:** `test_non_admin_cannot_edit_others_recipe`
  - **Status:** GREEN (existing behavior)
  - **Verifies:** AC-2 - Non-admin gets 403 Forbidden

#### TestAdminEditAllFields

- **Test:** `test_admin_can_edit_text_fields`
  - **Status:** RED - AssertionError: 403 != 200
  - **Verifies:** AC-3 - Admin can modify name, description, instructions, notes, garnish

- **Test:** `test_admin_can_edit_category_fields`
  - **Status:** RED - AssertionError: 403 != 200
  - **Verifies:** AC-3 - Admin can modify template, glassware, method, serving_style, main_spirit

- **Test:** `test_admin_can_edit_visibility`
  - **Status:** RED - AssertionError: 403 != 200
  - **Verifies:** AC-3 - Admin can modify visibility setting

#### TestAdminOwnershipTransfer

- **Test:** `test_admin_can_transfer_recipe_ownership`
  - **Status:** RED - AssertionError: 403 != 200
  - **Verifies:** AC-3 - Admin can transfer ownership via user_id field

#### TestAdminOwnRecipeEdit

- **Test:** `test_admin_editing_own_recipe_works`
  - **Status:** GREEN (regression test)
  - **Verifies:** AC-4 - Admin editing their own recipe works

#### TestRegularUserOwnRecipeEdit

- **Test:** `test_owner_can_still_edit_own_recipe`
  - **Status:** GREEN (regression test)
  - **Verifies:** AC-5 - Regular user editing own recipe works

- **Test:** `test_unauthenticated_user_cannot_edit_recipe`
  - **Status:** GREEN (regression test)
  - **Verifies:** Security - unauthenticated requests get 401

---

## Data Factories Created

**No new factories needed.** Story uses existing fixtures from `conftest.py`:

- `admin_user` - Admin user fixture (is_admin=True)
- `admin_auth_token` - JWT token for admin user
- `sample_user` / `auth_token` - Regular user fixture
- `another_user` / `another_auth_token` - Second non-admin user
- `sample_recipe` - Recipe owned by sample_user
- `sample_ingredient` - Ingredient for recipe creation

---

## Fixtures Created

**No new fixtures needed.** All required fixtures exist from Story 1.1:

### Auth Fixtures (`backend/tests/conftest.py`)

- `admin_user` - Creates admin user with `is_admin=True`
  - **Setup:** Creates User with admin privileges
  - **Provides:** User object to test
  - **Cleanup:** Automatic (test_session rollback)

- `admin_auth_token` - JWT for admin user
  - **Setup:** Creates access token using `create_access_token()`
  - **Provides:** JWT string for Authorization header
  - **Cleanup:** None needed (stateless)

**Example Usage:**

```python
def test_admin_action(client, admin_user, admin_auth_token):
    response = client.put(
        "/api/recipes/{id}",
        json={"name": "Updated"},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
```

---

## Mock Requirements

**No external services to mock.** This is pure backend logic testing against in-memory SQLite database.

---

## Required data-testid Attributes

**No UI changes required.** This story is backend-only API modification.

---

## Implementation Checklist

### Test: test_admin_can_edit_any_recipe (AC-1)

**File:** `backend/tests/test_recipe_admin.py`

**Tasks to make this test pass:**

- [ ] Open `backend/app/routers/recipes.py`
- [ ] Locate ownership check at lines 546-550:
  ```python
  if recipe.user_id != current_user.id:
  ```
- [ ] Add admin bypass:
  ```python
  if recipe.user_id != current_user.id and not current_user.is_admin:
  ```
- [ ] Run test: `pytest tests/test_recipe_admin.py::TestAdminRecipeEditBypass::test_admin_can_edit_any_recipe -v`
- [ ] Test passes (green phase)

**Estimated Effort:** 0.25 hours

---

### Test: test_admin_can_edit_text_fields (AC-3)

**File:** `backend/tests/test_recipe_admin.py`

**Tasks to make this test pass:**

- [ ] Same code change as above (single line modification)
- [ ] Run test: `pytest tests/test_recipe_admin.py::TestAdminEditAllFields::test_admin_can_edit_text_fields -v`
- [ ] Test passes (green phase)

**Estimated Effort:** 0 hours (same fix)

---

### Test: test_admin_can_edit_category_fields (AC-3)

**File:** `backend/tests/test_recipe_admin.py`

**Tasks to make this test pass:**

- [ ] Same code change as above
- [ ] Run test: `pytest tests/test_recipe_admin.py::TestAdminEditAllFields::test_admin_can_edit_category_fields -v`
- [ ] Test passes (green phase)

**Estimated Effort:** 0 hours (same fix)

---

### Test: test_admin_can_edit_visibility (AC-3)

**File:** `backend/tests/test_recipe_admin.py`

**Tasks to make this test pass:**

- [ ] Same code change as above
- [ ] Run test: `pytest tests/test_recipe_admin.py::TestAdminEditAllFields::test_admin_can_edit_visibility -v`
- [ ] Test passes (green phase)

**Estimated Effort:** 0 hours (same fix)

---

### Test: test_admin_can_transfer_recipe_ownership (AC-3)

**File:** `backend/tests/test_recipe_admin.py`

**Tasks to make this test pass:**

- [ ] Verify `RecipeUpdate` schema includes `user_id: Optional[str]`
- [ ] If missing, add to `backend/app/schemas/recipes.py`:
  ```python
  user_id: Optional[str] = None  # Admin-only: transfer ownership
  ```
- [ ] Run test: `pytest tests/test_recipe_admin.py::TestAdminOwnershipTransfer -v`
- [ ] Test passes (green phase)

**Estimated Effort:** 0.25 hours

---

## Running Tests

```bash
# Run all failing tests for this story
cd backend && source venv/bin/activate && pytest tests/test_recipe_admin.py -v

# Run specific test file
pytest tests/test_recipe_admin.py -v

# Run single test
pytest tests/test_recipe_admin.py::TestAdminRecipeEditBypass::test_admin_can_edit_any_recipe -v

# Run tests with coverage
pytest tests/test_recipe_admin.py --cov=app.routers.recipes -v

# Run full test suite to check for regressions
pytest
```

---

## Red-Green-Refactor Workflow

### RED Phase (Complete)

**TEA Agent Responsibilities:**

- All tests written and failing (5 new tests in RED)
- Regression tests passing (4 tests in GREEN)
- Using existing fixtures from conftest.py
- Implementation checklist created

**Verification:**

```
tests/test_recipe_admin.py::TestAdminRecipeEditBypass::test_admin_can_edit_any_recipe FAILED
tests/test_recipe_admin.py::TestAdminRecipeEditBypass::test_non_admin_cannot_edit_others_recipe PASSED
tests/test_recipe_admin.py::TestAdminEditAllFields::test_admin_can_edit_text_fields FAILED
tests/test_recipe_admin.py::TestAdminEditAllFields::test_admin_can_edit_category_fields FAILED
tests/test_recipe_admin.py::TestAdminEditAllFields::test_admin_can_edit_visibility FAILED
tests/test_recipe_admin.py::TestAdminOwnershipTransfer::test_admin_can_transfer_recipe_ownership FAILED
tests/test_recipe_admin.py::TestAdminOwnRecipeEdit::test_admin_editing_own_recipe_works PASSED
tests/test_recipe_admin.py::TestRegularUserOwnRecipeEdit::test_owner_can_still_edit_own_recipe PASSED
tests/test_recipe_admin.py::TestRegularUserOwnRecipeEdit::test_unauthenticated_user_cannot_edit_recipe PASSED

5 failed, 4 passed
```

---

### GREEN Phase (DEV Team - Next Steps)

**DEV Agent Responsibilities:**

1. **Pick one failing test** - Start with `test_admin_can_edit_any_recipe`
2. **Read the test** - Understand expected behavior (admin bypass)
3. **Implement minimal code** - Add `and not current_user.is_admin` to ownership check
4. **Run the test** - Verify it now passes
5. **Move to next test** - All 5 failing tests should now pass
6. **Verify regression tests** - 4 existing tests should still pass

**Key Implementation:**

```python
# backend/app/routers/recipes.py line 546-550
# BEFORE:
if recipe.user_id != current_user.id:

# AFTER:
if recipe.user_id != current_user.id and not current_user.is_admin:
```

**Progress Tracking:**

- Check off tasks as you complete them
- Run `pytest tests/test_recipe_admin.py -v` after each change
- Run full `pytest` to verify no regressions

---

### REFACTOR Phase (DEV Team - After All Tests Pass)

**DEV Agent Responsibilities:**

1. **Verify all tests pass** (9 tests in green)
2. **Review code quality** - Is the admin check clean?
3. **Run full test suite** - `pytest` should pass all tests
4. **Update story status** - Mark as done in sprint-status.yaml

---

## Next Steps

1. **Review this checklist** with team
2. **Run failing tests** to confirm RED phase: `pytest tests/test_recipe_admin.py -v`
3. **Begin implementation** - Single line change to recipes.py:546
4. **Verify with tests** - All 9 tests should pass
5. **Run full suite** - `pytest` for regression check
6. **Update story status** - Change to 'done' in sprint-status.yaml

---

## Knowledge Base References Applied

This ATDD workflow used:

- **test-quality.md** - Given-When-Then structure, one assertion per test
- **fixture-architecture.md** - Reused existing fixtures from conftest.py
- **test-levels-framework.md** - Selected API (pytest) level for backend logic

---

## Test Execution Evidence

### Initial Test Run (RED Phase Verification)

**Command:** `pytest tests/test_recipe_admin.py -v`

**Results:**

```
tests/test_recipe_admin.py::TestAdminRecipeEditBypass::test_admin_can_edit_any_recipe FAILED [ 11%]
tests/test_recipe_admin.py::TestAdminRecipeEditBypass::test_non_admin_cannot_edit_others_recipe PASSED [ 22%]
tests/test_recipe_admin.py::TestAdminEditAllFields::test_admin_can_edit_text_fields FAILED [ 33%]
tests/test_recipe_admin.py::TestAdminEditAllFields::test_admin_can_edit_category_fields FAILED [ 44%]
tests/test_recipe_admin.py::TestAdminEditAllFields::test_admin_can_edit_visibility FAILED [ 55%]
tests/test_recipe_admin.py::TestAdminOwnershipTransfer::test_admin_can_transfer_recipe_ownership FAILED [ 66%]
tests/test_recipe_admin.py::TestAdminOwnRecipeEdit::test_admin_editing_own_recipe_works PASSED [ 77%]
tests/test_recipe_admin.py::TestRegularUserOwnRecipeEdit::test_owner_can_still_edit_own_recipe PASSED [ 88%]
tests/test_recipe_admin.py::TestRegularUserOwnRecipeEdit::test_unauthenticated_user_cannot_edit_recipe PASSED [100%]

5 failed, 4 passed
```

**Summary:**

- Total tests: 9
- Passing: 4 (regression tests)
- Failing: 5 (expected - admin bypass not implemented)
- Status: RED phase verified

**Expected Failure Messages:**

All failures show `AssertionError: 403 != 200` - the admin gets 403 Forbidden when trying to edit recipes they don't own. This is the exact behavior we want to change.

---

## Notes

- This story is **backend-only** - no frontend changes required
- The implementation is a **single line change** to recipes.py:546
- All test fixtures already exist from Story 1.1
- May need to add `user_id` to `RecipeUpdate` schema for ownership transfer
- DO NOT modify delete_recipe (that's Story 1.3)

---

## Contact

**Questions or Issues?**

- Refer to story file: `docs/sprint-artifacts/1-2-admin-recipe-edit.md`
- Check `docs/admin-panel-architecture.md` for patterns

---

**Generated by BMad TEA Agent** - 2026-01-10
