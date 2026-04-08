# Story 2.3: Ingredient Merge

Status: done

---

## Story

As an **admin**,
I want **to merge duplicate ingredients into a single target**,
So that **recipes reference consistent ingredient names**.

---

## Acceptance Criteria

### AC-1: Merge Endpoint

**Given** I am authenticated as an admin
**When** I call `POST /api/admin/ingredients/merge` with `{ "source_ids": [...], "target_id": "..." }`
**Then** all `recipe_ingredients` records referencing source ingredients are updated to reference the target
**And** the source ingredients are deleted
**And** I receive a response with the count of recipes affected

### AC-2: Data Integrity — No Lost Associations

**Given** a merge operation is performed
**When** it completes
**Then** no recipes lose their ingredient associations
**And** the target ingredient's usage count increases by the sum of source usage counts (minus deduplicated rows)

### AC-3: Same-Recipe Duplicate Handling

**Given** a source ingredient and target ingredient both appear in the same recipe
**When** the merge runs
**Then** the source's `RecipeIngredient` row is deleted (not updated) to avoid duplicate `(recipe_id, target_id)` rows
**And** the recipe retains its reference to the target ingredient

### AC-4: Transaction Atomicity

**Given** a merge operation fails mid-transaction
**When** the error occurs
**Then** the entire operation rolls back
**And** no data is modified

### AC-5: Target Not Found

**Given** I try to merge with a `target_id` that doesn't exist
**When** I submit the request
**Then** I receive a 404 Not Found response

### AC-6: Source Contains Target

**Given** I try to merge with `source_ids` that include the `target_id`
**When** I submit the request
**Then** I receive a 400 Bad Request response ("cannot merge ingredient into itself")

### AC-7: Authorization

**Given** I am NOT an admin (regular user or unauthenticated)
**When** I call `POST /api/admin/ingredients/merge`
**Then** I receive 401 (no token) or 403 (regular user)

### AC-8: Empty or Invalid Source IDs

**Given** I submit an empty `source_ids` list
**When** the request is validated
**Then** I receive a 422 Unprocessable Entity (Pydantic min_length=1 validation)

### AC-9: Nonexistent Source IDs

**Given** one or more `source_ids` don't exist in the database
**When** I submit the request
**Then** I receive a 404 Not Found with detail listing which source IDs were not found

---

## Tasks / Subtasks

### Task 1: Create Merge Schemas (AC: #1, #8)

- [x] **1.1** Add schemas to `backend/app/schemas/ingredient.py`:
  - `IngredientMergeRequest`: `source_ids` (List[str], min_length=1), `target_id` (str)
  - `IngredientMergeResponse`: `message` (str), `recipes_affected` (int), `sources_removed` (int)
- [x] **1.2** Export new schemas from `backend/app/schemas/__init__.py`

### Task 2: Implement Merge Service (AC: #1-6, #9)

- [x] **2.1** Add merge function to `backend/app/services/ingredient_service.py`:
  - `merge_ingredients(db, target_id, source_ids) -> Union[Tuple[int, int], str]`
    - Returns `(recipes_affected, sources_removed)` on success
    - Returns error string on validation failure (caller maps to HTTP error)
  - Logic flow:
    1. Validate target exists → error string if not
    2. Validate target_id not in source_ids → error string if so
    3. Validate all source_ids exist → error string listing missing IDs if not
    4. For each source ingredient:
       a. Find all `RecipeIngredient` rows with `ingredient_id = source.id`
       b. For each row, check if a `RecipeIngredient` already exists for `(row.recipe_id, target_id)`
       c. If YES (same recipe already has target): **DELETE** the source's `RecipeIngredient` row
       d. If NO: **UPDATE** `ingredient_id` to `target_id`
    5. Delete all source `Ingredient` records
    6. Commit (single transaction — any failure rolls back everything)
    7. Return `(recipes_affected, sources_removed)`
- [x] **2.2** `recipes_affected` = count of DISTINCT `recipe_id` values that had any `RecipeIngredient` row updated or deleted during the merge
- [x] **2.3** `sources_removed` = `len(source_ids)` (all sources are always deleted)
- [x] **2.4** Export `merge_ingredients` from `backend/app/services/__init__.py`

### Task 3: Add Merge Endpoint (AC: #1, #5-9)

- [x] **3.1** Add endpoint to `backend/app/routers/admin.py`:
  - `POST /admin/ingredients/merge` → accepts `IngredientMergeRequest`, returns `IngredientMergeResponse`
  - Uses `require_admin` + `get_db` via `Depends`
  - CRITICAL: Place this route BEFORE `GET /admin/ingredients/{id}` — although POST vs GET shouldn't conflict, keep all fixed-path routes before parameterized ones for consistency
- [x] **3.2** Router maps service return value to HTTP responses:
  - Success tuple → 200 with `IngredientMergeResponse`
  - Error string containing "not found" → 404
  - Error string containing "cannot merge" → 400
- [x] **3.3** Import `merge_ingredients` from ingredient_service
- [x] **3.4** Import `IngredientMergeRequest`, `IngredientMergeResponse` in admin.py

### Task 4: Write Tests (AC: #1-9)

- [x] **4.1** Create `backend/tests/test_ingredient_merge.py`
- [x] **4.2** Auth tests:
  - `test_merge_returns_401_without_auth`
  - `test_merge_returns_403_for_regular_user`
- [x] **4.3** Validation tests:
  - `test_merge_returns_404_when_target_not_found`
  - `test_merge_returns_400_when_source_contains_target`
  - `test_merge_returns_404_when_source_id_not_found`
  - `test_merge_returns_422_with_empty_source_ids`
- [x] **4.4** Happy path tests:
  - `test_merge_updates_recipe_ingredients_to_target` — source ingredient's RecipeIngredient rows now point to target
  - `test_merge_deletes_source_ingredients` — source ingredients no longer exist after merge
  - `test_merge_returns_correct_recipes_affected_count`
  - `test_merge_returns_correct_sources_removed_count`
- [x] **4.5** Same-recipe edge case tests:
  - `test_merge_handles_same_recipe_with_source_and_target` — when a recipe uses both source and target, source's RecipeIngredient is deleted (not duplicated)
  - `test_merge_recipe_retains_target_after_overlap_merge` — the recipe still has the target ingredient after merge
- [x] **4.6** Multi-source tests:
  - `test_merge_multiple_sources_into_target` — merge 2+ sources at once
  - `test_merge_sources_with_no_recipe_usage` — sources not used in any recipe are still deleted
- [x] **4.7** Data integrity tests:
  - `test_merge_preserves_unrelated_recipe_ingredients` — other ingredients in same recipes are untouched
  - `test_target_ingredient_unchanged_after_merge` — target's name/type/etc. are not modified
- [x] **4.8** Transaction rollback test (AC-4):
  - `test_merge_rolls_back_on_failure` — mock `db.commit()` to raise, verify no ingredients deleted and no RecipeIngredient rows modified. SQLAlchemy handles this automatically but AC-4 explicitly requires rollback verification.
- [x] **4.9** Run full test suite: `pytest` — no regressions

### Task 5: Final Verification

- [x] **5.1** Run full backend test suite: `pytest`
- [x] **5.2** Verify all existing tests still pass (including 2-1 and 2-2 tests)
- [x] **5.3** Update `docs/sprint-artifacts/sprint-status.yaml` — mark 2-3 as done

---

## Dev Notes

### CRITICAL: Same-Recipe Overlap — The Gotcha That Will Bite You

There is **NO unique constraint** on `(recipe_id, ingredient_id)` in `recipe_ingredients`. However, naively updating `ingredient_id` from source to target when the recipe ALREADY has a `RecipeIngredient` row for the target creates **duplicate rows** — same recipe referencing the same ingredient twice. This is logically wrong.

**The fix:** Before updating each source's `RecipeIngredient` row, check if the same `recipe_id` already has a row pointing to `target_id`. If yes, DELETE the source row instead of updating it.

```python
from sqlalchemy import and_

def merge_ingredients(db: Session, target_id: str, source_ids: List[str]) -> Union[Tuple[int, int], str]:
    # 1. Validate target exists
    target = db.query(Ingredient).filter(Ingredient.id == target_id).first()
    if not target:
        return "Target ingredient not found"

    # 2. Validate target not in sources
    if target_id in source_ids:
        return "Cannot merge ingredient into itself"

    # 3. Validate all sources exist
    sources = db.query(Ingredient).filter(Ingredient.id.in_(source_ids)).all()
    found_ids = {s.id for s in sources}
    missing = set(source_ids) - found_ids
    if missing:
        return f"Source ingredient(s) not found: {', '.join(sorted(missing))}"

    # 4. Track affected recipes
    affected_recipe_ids = set()

    for source in sources:
        source_ri_rows = db.query(RecipeIngredient).filter(
            RecipeIngredient.ingredient_id == source.id
        ).all()

        for ri in source_ri_rows:
            affected_recipe_ids.add(ri.recipe_id)
            # Check if target already in this recipe
            existing_target_ri = db.query(RecipeIngredient).filter(
                and_(
                    RecipeIngredient.recipe_id == ri.recipe_id,
                    RecipeIngredient.ingredient_id == target_id,
                )
            ).first()

            if existing_target_ri:
                # Recipe already has target — delete source row
                db.delete(ri)
            else:
                # Recipe doesn't have target — update source → target
                ri.ingredient_id = target_id

    # 5. Flush RI changes before deleting sources
    # (SQLAlchemy ORM may try to nullify FK on delete otherwise)
    db.flush()

    # 6. Delete source ingredients
    for source in sources:
        db.delete(source)

    # 7. Commit (single transaction)
    db.commit()

    return (len(affected_recipe_ids), len(source_ids))
```

### Service Return Convention

The service returns a **tuple** on success or a **string** on validation failure. The router maps strings to HTTP errors.

**⚠️ FRAGILE STRING MATCHING WARNING:** The router uses `"not found" in result.lower()` to determine 404 vs 400. If you change the wording of error strings in the service, the HTTP status code silently breaks. Keep error strings stable, or consider switching to an enum/sentinel pattern if this becomes a maintenance problem.

```python
@router.post("/ingredients/merge", response_model=IngredientMergeResponse)
def merge_admin_ingredients(
    data: IngredientMergeRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    result = merge_ingredients(db, data.target_id, data.source_ids)
    if isinstance(result, str):
        if "not found" in result.lower():
            raise HTTPException(status_code=404, detail=result)
        raise HTTPException(status_code=400, detail=result)
    recipes_affected, sources_removed = result
    return IngredientMergeResponse(
        message=f"Merged {sources_removed} ingredient(s). {recipes_affected} recipe(s) affected.",
        recipes_affected=recipes_affected,
        sources_removed=sources_removed,
    )
```

### Route Placement in admin.py

Place `POST /admin/ingredients/merge` with the other ingredient endpoints. Since it's a POST and the parameterized routes are GET/PUT/DELETE on `/{id}`, there's no actual path conflict. But for readability and consistency, place it near the other ingredient endpoints — ideally between the list endpoint and the `{id}` endpoints:

```python
# Suggested order in admin.py:
GET  /ingredients           # List (existing)
POST /ingredients           # Create (existing)
GET  /ingredients/duplicates  # From Story 2-2
POST /ingredients/merge       # THIS STORY
GET  /ingredients/{id}      # Single (existing)
PUT  /ingredients/{id}      # Update (existing)
DELETE /ingredients/{id}    # Delete (existing)
```

### Extend Existing Files — DO NOT Create New Router/Service Files

| File | Action | What to Add |
|------|--------|-------------|
| `backend/app/schemas/ingredient.py` | MODIFY | Add 2 new schemas (IngredientMergeRequest, IngredientMergeResponse) |
| `backend/app/schemas/__init__.py` | MODIFY | Export new schemas |
| `backend/app/services/ingredient_service.py` | MODIFY | Add merge_ingredients function |
| `backend/app/services/__init__.py` | MODIFY | Export merge_ingredients |
| `backend/app/routers/admin.py` | MODIFY | Add POST /admin/ingredients/merge endpoint + imports |
| `backend/tests/test_ingredient_merge.py` | CREATE | Merge tests |

### Test Fixture Strategy

Reuse existing `conftest.py` fixtures:
- `client` — TestClient with DB overrides
- `admin_auth_token` — JWT for admin user
- `auth_token` — JWT for regular user (for 403 tests)
- `sample_ingredient` — existing Tequila ingredient (can be used as target)
- `sample_recipe` — Margarita linked to `sample_ingredient` via RecipeIngredient

Create test-local ingredients and recipe associations directly in each test. Use the admin API to create ingredients (via POST /api/admin/ingredients), then create RecipeIngredient rows through the test session for recipe associations:

```python
def _create_ingredient(client, admin_auth_token, name, type="spirit"):
    """Helper to create an ingredient via API."""
    resp = client.post(
        "/api/admin/ingredients",
        json={"name": name, "type": type},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert resp.status_code == 201
    return resp.json()

def _link_ingredient_to_recipe(test_session, recipe_id, ingredient_id, amount=1.0, unit="oz"):
    """Helper to create a RecipeIngredient directly in DB."""
    from app.models.recipe import RecipeIngredient
    ri = RecipeIngredient(
        recipe_id=recipe_id,
        ingredient_id=ingredient_id,
        amount=amount,
        unit=unit,
        order=0,
    )
    test_session.add(ri)
    test_session.commit()
    return ri
```

### Auth Test Pattern (MANDATORY)

```python
def test_merge_returns_401_without_auth(client):
    response = client.post("/api/admin/ingredients/merge", json={
        "source_ids": ["fake-id"],
        "target_id": "fake-target",
    })
    assert response.status_code == 401

def test_merge_returns_403_for_regular_user(client, auth_token):
    response = client.post(
        "/api/admin/ingredients/merge",
        json={"source_ids": ["fake-id"], "target_id": "fake-target"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 403
```

### No Audit Logging in This Story

Audit logging is Story 4-1/4-2. Do NOT add audit logging to the merge endpoint. The PRD mentions "creates audit entry" for merges, but that's handled when audit infrastructure is built. Do NOT preemptively add it.

### No Frontend Changes in This Story

Frontend ingredient admin UI is Story 5-4. This story is backend-only.

### No New Dependencies

Everything needed is in stdlib + existing packages. No new pip installs.

### No Database Migrations

No schema changes needed. The merge operates on existing `recipe_ingredients` and `ingredients` tables.

### Anti-Patterns to Avoid

**DO NOT:**
- Create a new router file for merge (extend `admin.py`)
- Create a new service file (extend `ingredient_service.py`)
- Use CASCADE delete on ingredients (manually handle RecipeIngredient updates)
- Blindly update all `ingredient_id` without checking for same-recipe overlap
- Use multiple transactions (everything in ONE commit)
- Add audit logging (Story 4-1/4-2)
- Add rate limiting (architecture mentions it but it's not in scope for this story)
- Use `@pytest.mark.asyncio` (asyncio_mode=auto)
- Import describe/it/expect in tests

**DO:**
- Use `require_admin` dependency on the endpoint
- Use `detail` key in all HTTPExceptions
- Use existing test fixtures from conftest.py
- Check for same-recipe overlap before updating RecipeIngredient rows
- Delete source ingredients AFTER updating/deleting their RecipeIngredient rows
- Wrap everything in a single transaction (one `db.commit()`)
- Validate target exists, sources exist, target not in sources
- Return structured response with recipes_affected and sources_removed counts
- Handle the edge case of sources with zero recipe usage (they get deleted, 0 recipes affected)

### Project Structure Notes

- All changes extend existing files (except test file)
- No new dependencies
- No database migrations — no schema changes
- Single atomic transaction for the entire merge operation

### References

- [Source: docs/admin-panel-prd.md#FR-3.5.5 — Ingredient Merge requirements]
- [Source: docs/epics.md#Story 2.3 — Acceptance criteria]
- [Source: docs/admin-panel-architecture.md — ingredient_service.py, merge endpoint pattern]
- [Source: docs/project_context.md#Admin Panel Patterns — auth patterns, defensive coding, pre-review checklist]
- [Source: backend/app/models/recipe.py:108-124 — Ingredient model]
- [Source: backend/app/models/recipe.py:127-152 — RecipeIngredient junction table (NO unique constraint on recipe_id+ingredient_id)]
- [Source: backend/app/services/ingredient_service.py — existing CRUD + duplicate detection functions to extend]
- [Source: backend/app/routers/admin.py:176-259 — existing ingredient endpoints]
- [Source: backend/app/schemas/ingredient.py — existing schemas to extend]
- [Source: backend/tests/conftest.py — test fixtures]
- [Source: docs/sprint-artifacts/2-1-ingredient-admin-crud.md — Story 2-1 learnings]
- [Source: docs/sprint-artifacts/2-2-ingredient-duplicate-detection.md — Story 2-2 context (duplicate detection feeds merge)]

### Previous Story Intelligence (2-1 and 2-2)

**From Story 2-1 (Ingredient Admin CRUD):**
- IntegrityError handling is MANDATORY for all create/update — merge's DELETE of source ingredients should handle FK violations gracefully
- `ingredient_type` param uses `Query(alias="type")` — not relevant here but follow naming conventions
- Code review caught: missing auth tests (401+403), race conditions on delete, LIKE wildcard escaping
- Suite was at 412 tests after 2-1 completion (post code review #3)

**From Story 2-2 (Duplicate Detection):**
- Duplicate detection returns `DuplicateGroup` with `target` (highest usage) and `duplicates` — the merge endpoint's `target_id` and `source_ids` map directly to this output
- Story 2-2 intentionally designed its response schema to feed merge: `target.ingredient_id` → `target_id`, `[d.ingredient_id for d in duplicates]` → `source_ids`
- Route order matters: `/duplicates` must be before `/{id}` — `/merge` (POST) doesn't conflict with GET `/{id}` but place it near `/duplicates` for logical grouping
- No audit logging — consistent with 2-1 and 2-2

### Git Intelligence

```
acd1f9d fix: Use TRUE instead of 1 for boolean is_active in seed migration for PostgreSQL compatibility
428b5ea fix: Use TRUE/FALSE instead of 1/0 in admin migration for PostgreSQL compatibility
7af9393 feat: Add admin category CRUD, reorder, and soft-delete endpoints (Story 1-6)
```

All admin patterns established. Story 2-1 added ingredient CRUD. Story 2-2 (in-progress) adds duplicate detection. This story completes the Epic 2 trilogy with the merge action.

---

## Dev Agent Record

### Context Reference

Story context created by BMAD create-story workflow on 2026-04-08.

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

- Python 3.9 does not support `Tuple[int, int] | str` syntax — used `Union[Tuple[int, int], str]` instead
- SQLAlchemy ORM relationship tries to nullify FK on `db.delete(source)` even after RI rows were updated/deleted — added `db.flush()` before deleting source ingredients to persist RI changes first

### Completion Notes List

- ✅ Implemented `IngredientMergeRequest` and `IngredientMergeResponse` schemas
- ✅ Implemented `merge_ingredients()` service with same-recipe overlap handling, single-transaction atomicity
- ✅ Added `POST /admin/ingredients/merge` endpoint with `require_admin` auth
- ✅ 18 comprehensive tests covering auth (401/403), validation (404/400/422), happy path, same-recipe edge case, multi-source, data integrity, transaction rollback (AC-4), and duplicate source_id deduplication
- ✅ Full suite: 450 tests pass, 80% coverage, 0 regressions

### Change Log

- 2026-04-08: Implemented Story 2-3 Ingredient Merge — endpoint, service, schemas, 16 tests
- 2026-04-08: Code review fixes — fixed sources_removed count bug (len(source_ids)→len(sources)), added source_ids deduplication validator, replaced fragile string matching in router with prefix check, added rollback test (AC-4) and dedup test (+2 tests → 18 total)

### File List

- `backend/app/schemas/ingredient.py` — MODIFIED (added IngredientMergeRequest, IngredientMergeResponse)
- `backend/app/schemas/__init__.py` — MODIFIED (exported new schemas)
- `backend/app/services/ingredient_service.py` — MODIFIED (added merge_ingredients function)
- `backend/app/services/__init__.py` — MODIFIED (exported merge_ingredients)
- `backend/app/routers/admin.py` — MODIFIED (added POST /admin/ingredients/merge endpoint)
- `backend/tests/test_ingredient_merge.py` — CREATED (16 tests)
- `docs/sprint-artifacts/sprint-status.yaml` — MODIFIED (2-3 status: review)
