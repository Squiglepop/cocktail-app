# Story 2.1: Ingredient Admin CRUD

Status: done

---

## Story

As an **admin**,
I want **to view, add, edit, and delete ingredients from the master list**,
So that **I can maintain a clean and accurate ingredient database**.

---

## Acceptance Criteria

### AC-1: List All Ingredients (Paginated)

**Given** I am authenticated as an admin
**When** I call `GET /api/admin/ingredients`
**Then** I receive a paginated list of all ingredients
**And** results include: id, name, type, spirit_category, description, common_brands
**And** pagination metadata (total, page, per_page) is included
**And** default pagination is page=1, per_page=50

### AC-2: Search Ingredients

**Given** I am authenticated as an admin
**When** I call `GET /api/admin/ingredients?search=lime`
**Then** I receive ingredients matching the search term
**And** search is case-insensitive on the `name` field
**And** search also filters by `type` if `?type=spirit` query param is provided

### AC-3: Create Ingredient

**Given** I am authenticated as an admin
**When** I call `POST /api/admin/ingredients` with valid data
**Then** a new ingredient is created with:
- `name`: required, unique (case-insensitive)
- `type`: required, must be valid IngredientType enum value
- `spirit_category`: optional, only meaningful if type=spirit
- `description`: optional text
- `common_brands`: optional text
**And** I receive 201 with the created ingredient

### AC-4: Duplicate Name Prevention

**Given** I try to create an ingredient with a name that already exists (case-insensitive)
**When** I submit the request
**Then** I receive a 409 Conflict response
**And** the duplicate is not created

### AC-5: Update Ingredient

**Given** I am authenticated as an admin
**When** I call `PUT /api/admin/ingredients/{id}`
**Then** I can update all fields (name, type, spirit_category, description, common_brands)
**And** if name is changed, uniqueness is still enforced (409 on conflict)

### AC-6: Delete Unused Ingredient

**Given** I am authenticated as an admin
**When** I call `DELETE /api/admin/ingredients/{id}` for an ingredient NOT used in any recipe
**Then** the ingredient is hard-deleted successfully
**And** I receive 200 with a success message

### AC-6.5: Get Single Ingredient

**Given** I am authenticated as an admin
**When** I call `GET /api/admin/ingredients/{id}`
**Then** I receive the full ingredient details (id, name, type, spirit_category, description, common_brands)
**And** if the ingredient does not exist, I receive 404

### AC-7: Delete Used Ingredient Blocked

**Given** I try to delete an ingredient that IS used in recipes
**When** I submit the request
**Then** I receive a 409 Conflict response
**And** the response includes the count of recipes using this ingredient
**And** the ingredient is NOT deleted

### AC-8: Authorization

**Given** I am NOT an admin (regular user or unauthenticated)
**When** I call any `/api/admin/ingredients/*` endpoint
**Then** I receive 401 (no token) or 403 (regular user)

---

## Tasks / Subtasks

### Task 1: Create Ingredient Admin Schemas (AC: #1-7)

- [x] **1.1** Create `backend/app/schemas/ingredient.py` with admin-specific schemas:
  - `IngredientAdminCreate`: `name` (str, required, min_length=1, max_length=255), `type` (Literal["spirit", "liqueur", "wine_fortified", "bitter", "syrup", "juice", "mixer", "dairy", "egg", "garnish", "other"]), `spirit_category` (Optional[str], max_length=50), `description` (Optional[str]), `common_brands` (Optional[str])
  - `IngredientAdminUpdate`: all fields optional (partial update)
  - `IngredientAdminResponse`: id, name, type, spirit_category, description, common_brands — `from_attributes = True`
  - `IngredientListResponse`: `items` (List[IngredientAdminResponse]), `total` (int), `page` (int), `per_page` (int)
  - `IngredientDeleteResponse`: `message` (str), `recipe_count` (int) — for blocked deletes too
- [x] **1.2** Export new schemas from `backend/app/schemas/__init__.py`

### Task 2: Create Ingredient Admin Service (AC: #1-7)

- [x] **2.1** Create `backend/app/services/ingredient_service.py` with:
  - `list_ingredients(db, page, per_page, search, type_filter) -> tuple[list[Ingredient], int]` — returns (items, total_count)
  - `get_by_id(db, id) -> Ingredient | None`
  - `create_ingredient(db, data) -> Ingredient | None` — returns None on IntegrityError (duplicate name)
  - `update_ingredient(db, id, data) -> Ingredient | None` — returns None ONLY on IntegrityError (duplicate name → caller returns 409). Router MUST call `get_by_id` first and return 404 if None before calling this method.
  - `delete_ingredient(db, id) -> tuple[bool, int]` — returns (deleted, recipe_count); False if ingredient in use
  - `get_recipe_usage_count(db, ingredient_id) -> int`
- [x] **2.2** Export from `backend/app/services/__init__.py`

### Task 3: Create Ingredient Admin Router Endpoints (AC: #1-8)

- [x] **3.1** Add ingredient admin endpoints to `backend/app/routers/admin.py` (extend existing router — DO NOT create new file)
- [x] **3.2** `GET /admin/ingredients` — paginated list with search and type filter:
  - Query params: `page` (int, default=1), `per_page` (int, default=50), `search` (Optional[str]), `type` (Optional[str])
  - Return `IngredientListResponse`
- [x] **3.3** `GET /admin/ingredients/{id}` — single ingredient by ID:
  - Return 404 if not found
  - Return `IngredientAdminResponse`
- [x] **3.4** `POST /admin/ingredients` — create new ingredient:
  - Return 201 with `IngredientAdminResponse`
  - Return 409 if name already exists (case-insensitive)
- [x] **3.5** `PUT /admin/ingredients/{id}` — update ingredient:
  - Return 404 if not found
  - Return 409 if updated name conflicts with existing
  - Return 200 with updated `IngredientAdminResponse`
- [x] **3.6** `DELETE /admin/ingredients/{id}` — delete ingredient:
  - Check recipe usage count via RecipeIngredient join
  - If used: return 409 with `IngredientDeleteResponse` including recipe_count
  - If not used: hard delete, return 200 with success message

### Task 4: Write Tests (AC: #1-8)

- [x] **4.1** Create `backend/tests/test_admin_ingredients.py`
- [x] **4.2** Auth tests:
  - `test_list_ingredients_returns_401_without_auth`
  - `test_list_ingredients_returns_403_for_regular_user`
  - `test_create_ingredient_returns_401_without_auth`
  - `test_create_ingredient_returns_403_for_regular_user`
  - `test_update_ingredient_returns_401_without_auth`
  - `test_update_ingredient_returns_403_for_regular_user`
  - `test_delete_ingredient_returns_401_without_auth`
  - `test_delete_ingredient_returns_403_for_regular_user`
- [x] **4.3** GET (list) tests:
  - `test_list_ingredients_returns_paginated_results`
  - `test_list_ingredients_search_by_name`
  - `test_list_ingredients_filter_by_type`
  - `test_list_ingredients_pagination_metadata`
  - `test_list_ingredients_empty_search_returns_all`
- [x] **4.4** GET (single) tests:
  - `test_get_ingredient_by_id`
  - `test_get_nonexistent_ingredient_returns_404`
- [x] **4.5** POST (create) tests:
  - `test_create_ingredient_returns_201`
  - `test_create_ingredient_with_all_fields`
  - `test_create_duplicate_name_returns_409`
  - `test_create_duplicate_name_case_insensitive_returns_409`
  - `test_create_ingredient_with_invalid_type_returns_422`
- [x] **4.6** PUT (update) tests:
  - `test_update_ingredient_name`
  - `test_update_ingredient_type`
  - `test_update_nonexistent_returns_404`
  - `test_update_to_duplicate_name_returns_409`
  - `test_update_ingredient_partial_fields` (update only description, verify other fields unchanged)
- [x] **4.7** DELETE tests:
  - `test_delete_unused_ingredient_succeeds`
  - `test_delete_used_ingredient_returns_409_with_count`
  - `test_delete_nonexistent_returns_404`
- [x] **4.8** Run full test suite: `pytest` — no regressions

### Task 5: Final Verification

- [x] **5.1** Run full backend test suite: `pytest`
- [x] **5.2** Verify all existing tests still pass
- [x] **5.3** Update `docs/sprint-artifacts/sprint-status.yaml`

---

## Dev Notes

### CRITICAL: Extend Existing Admin Router — DO NOT Create New Router File

`backend/app/routers/admin.py` already exists with `router = APIRouter(prefix="/admin", tags=["admin"])`. Add ingredient endpoints here. The router is already mounted at `/api/admin` via `main.py`. Follow the exact same pattern as the category endpoints above them.

### Ingredient Model Already Exists — NO Migration Needed

The Ingredient model is defined in `backend/app/models/recipe.py` (lines 108-124):

```python
class Ingredient(Base):
    __tablename__ = "ingredients"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    spirit_category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    common_brands: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recipe_ingredients: Mapped[List["RecipeIngredient"]] = relationship(...)
```

**DO NOT create any migrations.** The table and all columns already exist.

### RecipeIngredient Junction Table (for usage checks)

Defined in `backend/app/models/recipe.py` (lines 127-152). Key fields:
- `ingredient_id`: FK to `ingredients.id` (indexed via `ix_recipe_ingredients_ingredient_id`)
- `recipe_id`: FK to `recipes.id` (CASCADE delete)

Usage count query:
```python
from sqlalchemy import func
count = db.query(func.count(RecipeIngredient.id)).filter(
    RecipeIngredient.ingredient_id == ingredient_id
).scalar()
```

### Case-Insensitive Name Uniqueness

The DB has a UNIQUE constraint on `name`, but it's case-sensitive in SQLite. For case-insensitive duplicate detection, query before insert:

```python
existing = db.query(Ingredient).filter(
    func.lower(Ingredient.name) == func.lower(data.name)
).first()
if existing:
    return None  # Caller returns 409
```

Also wrap `db.commit()` in `IntegrityError` handler for race conditions:

```python
from sqlalchemy.exc import IntegrityError

try:
    db.commit()
    db.refresh(record)
    return record
except IntegrityError:
    db.rollback()
    return None  # Caller returns 409
```

### Existing Ingredient Schemas (DO NOT MODIFY)

`backend/app/schemas/recipe.py` has `IngredientBase`, `IngredientCreate`, `IngredientResponse`. These are used by the recipe creation flow (AI extraction). **DO NOT modify them.** Create new admin-specific schemas in a new file `backend/app/schemas/ingredient.py`.

### Existing Ingredient Helper Functions (DO NOT MODIFY)

`backend/app/services/recipe_service.py` has `get_or_create_ingredient()`, `add_ingredients_to_recipe()`, `replace_recipe_ingredients()`. These are used by recipe creation/update. **DO NOT modify them.** Create a new `ingredient_service.py` for admin operations.

### IngredientType Enum Values (VALIDATED in Schema)

From `backend/app/models/enums.py`:
```
spirit, liqueur, wine_fortified, bitter, syrup, juice, mixer, dairy, egg, garnish, other
```

Use `Literal` type in `IngredientAdminCreate` to enforce valid values at the Pydantic layer. Invalid types return 422 automatically. This matches AC-3 ("must be valid IngredientType enum value").

### Pagination Pattern (First Paginated Endpoint)

Use SQLAlchemy `.offset()` / `.limit()`. Return `(items, total)` tuple. Apply `ilike` for search, exact match for type filter. Order by `Ingredient.name`.

### Hard Delete (NOT Soft Delete)

Unlike categories (soft-deleted), ingredients are **hard-deleted** — ONLY if zero recipe usage. Used ingredients → 409 BLOCKED. No CASCADE on `RecipeIngredient.ingredient_id`.

### Router Patterns (Copy from Category Endpoints)

- Use `require_admin` + `get_db` via `Depends` on ALL endpoints
- Query params: `page: int = Query(default=1, ge=1)`, `per_page: int = Query(default=50, ge=1, le=100)`, `search: Optional[str]`, `type: Optional[str]`
- Always use `detail` key in HTTPException: `raise HTTPException(status_code=404, detail="Ingredient not found")`
- For update endpoints: call `get_by_id` first → 404 if None, then `update_ingredient` → 409 if None (duplicate name)

### Test Fixtures Available (from conftest.py)

- `client` — TestClient with DB overrides
- `admin_user` — User with `is_admin=True`
- `admin_auth_token` — JWT for admin user
- `sample_user` — Regular user
- `auth_token` — JWT for regular user (for 403 tests)
- `sample_ingredient` — Tequila ingredient (`type="spirit"`, `spirit_category="tequila"`)
- `sample_recipe` — Margarita with `sample_ingredient` attached via RecipeIngredient

Use `sample_recipe` fixture to test delete-blocked-by-usage scenario (it links to `sample_ingredient`).

### Test Auth Pattern (MANDATORY for ALL endpoints)

```python
def test_endpoint_returns_401_without_auth(client):
    response = client.get("/api/admin/ingredients")
    assert response.status_code == 401

def test_endpoint_returns_403_for_regular_user(client, auth_token):
    response = client.get(
        "/api/admin/ingredients",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 403
```

### No Audit Logging in This Story

Audit logging infrastructure is Story 4-1. Do NOT add audit logging here.

### No Frontend Changes in This Story

Frontend ingredient admin UI is Story 5-4. This story is backend-only.

### Project Structure Notes

| File | Action | Purpose |
|------|--------|---------|
| `backend/app/schemas/ingredient.py` | CREATE | Admin ingredient schemas |
| `backend/app/schemas/__init__.py` | MODIFY | Export new schemas |
| `backend/app/services/ingredient_service.py` | CREATE | Admin ingredient CRUD logic |
| `backend/app/services/__init__.py` | MODIFY | Export new service functions |
| `backend/app/routers/admin.py` | MODIFY | Add ingredient admin endpoints |
| `backend/tests/test_admin_ingredients.py` | CREATE | Admin ingredient tests |

### Anti-Patterns to Avoid

**DO NOT:**
- Create a separate `admin_ingredients.py` router file — use existing `admin.py`
- Modify existing `IngredientBase`/`IngredientCreate`/`IngredientResponse` schemas in `recipe.py`
- Modify existing `get_or_create_ingredient` or `add_ingredients_to_recipe` or `replace_recipe_ingredients` in `recipe_service.py`
- Create any Alembic migrations (table already exists)
- Soft-delete ingredients (use hard delete with usage check)
- Delete ingredients that are used in recipes (block with 409)
- Skip IntegrityError handling on create/update
- Use `Base.metadata.create_all()`
- Use `@pytest.mark.asyncio` (asyncio_mode=auto)
- Import describe/it/expect in tests
- Add audit logging (Story 4-1)
- Add rate limiting decorators
- Create frontend code (Story 5-4)

**DO:**
- Extend existing `admin.py` router
- Use `require_admin` dependency on ALL endpoints
- Use `detail` key in all HTTPExceptions
- Use existing test fixtures (`admin_auth_token`, `sample_ingredient`, `sample_recipe`)
- Handle case-insensitive name uniqueness
- Wrap commits in IntegrityError handler
- Return 201 for creates, 200 for everything else
- Hard delete only unused ingredients
- Validate pagination params (page >= 1, per_page 1-100)

### References

- [Source: docs/admin-panel-prd.md#FR-3.5.1 — Ingredient CRUD requirements]
- [Source: docs/admin-panel-prd.md#FR-3.5.2 — Ingredient fields]
- [Source: docs/admin-panel-prd.md#FR-3.5.3 — Ingredient constraints]
- [Source: docs/admin-panel-architecture.md#Project Structure — ingredient_service.py]
- [Source: docs/epics.md#Story 2.1 — Acceptance criteria]
- [Source: docs/project_context.md#Admin Panel Patterns — auth patterns, defensive coding]
- [Source: backend/app/models/recipe.py:108-124 — Ingredient model]
- [Source: backend/app/models/recipe.py:127-152 — RecipeIngredient junction table]
- [Source: backend/app/models/enums.py:159-172 — IngredientType enum values]
- [Source: backend/app/services/recipe_service.py:11-54 — existing get_or_create_ingredient]
- [Source: backend/app/schemas/recipe.py:21-66 — existing ingredient schemas]
- [Source: backend/app/routers/admin.py — existing admin router with category endpoints]
- [Source: backend/tests/conftest.py — test fixtures (admin_user, sample_ingredient, sample_recipe)]

### Previous Story Intelligence (1-6)

From Story 1-6 (Admin Category Management — last story in Epic 1):
- Admin router pattern well-established: `require_admin` on all endpoints, `validate_category_type` helper for validation
- Category service uses `TYPE_MAP` dict for type→model resolution — ingredient service won't need this (single model)
- IntegrityError handling added in code review #2 — MANDATORY for all create/insert operations
- All auth endpoints need BOTH 401 (no token) AND 403 (regular user) tests — code review caught missing 403 tests twice
- `max_length` constraints on Pydantic schemas should match DB column sizes
- Full suite at 373 passed after Story 1-6

### Git Intelligence

```
7af9393 feat: Add admin category CRUD, reorder, and soft-delete endpoints (Story 1-6)
fcb86f7 feat: Rewrite public category endpoints to use database tables (Story 1-5)
f269abc feat: Add category database tables, BMAD framework, and project docs
```

Epic 1 established all admin patterns. This story follows the same patterns for a different entity (ingredients).

---

## Dev Agent Record

### Context Reference

Story context created by BMAD create-story workflow on 2026-04-08.

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

None — clean implementation, no issues encountered.

### Completion Notes List

- Created 5 Pydantic schemas in `ingredient.py`: `IngredientAdminCreate`, `IngredientAdminUpdate`, `IngredientAdminResponse`, `IngredientListResponse`, `IngredientDeleteResponse`
- Created `ingredient_service.py` with 6 functions: `list_ingredients`, `get_by_id`, `create_ingredient`, `update_ingredient`, `delete_ingredient`, `get_recipe_usage_count`
- Extended existing `admin.py` router with 6 ingredient endpoints (GET list, GET single, POST, PUT, DELETE)
- Case-insensitive duplicate name detection using `func.lower()` with IntegrityError race condition handling
- Delete endpoint uses `JSONResponse` for 409 to include `recipe_count` in structured response body
- Pagination implemented with `offset`/`limit`, ordered by `Ingredient.name`
- Hard delete only for unused ingredients; used ingredients return 409 with recipe count
- 28 tests written covering all ACs: 8 auth tests (401/403), 5 list tests, 2 get tests, 5 create tests, 5 update tests, 3 delete tests
- Full suite: 401 passed, 0 failures, no regressions
- Post code review #2: 36 story tests, 409 total suite, ingredient_service.py at 97% coverage
- Post code review #3: 39 story tests, 412 total suite, ingredient_service.py at 100% coverage

### Change Log

- 2026-04-08: Implemented Story 2-1 Ingredient Admin CRUD — all tasks complete, 28 tests passing, 401 total suite passing
- 2026-04-08: Code review fixes — Added 2 missing auth tests for GET-by-id (H1), fixed -1 recipe_count leak in delete race condition (M1), added combined search+type filter test (M4). 31 story tests, 404 total suite passing
- 2026-04-08: Code review #2 fixes — H1: Added IntegrityError handler to delete_ingredient commit (race condition crash). H2: Added None guard in update_ingredient (AttributeError crash). M1: Added 3 IntegrityError fallback path tests (create/update/delete). M2: Added type filter validation returning 400 for invalid types. M3: Escaped SQL LIKE wildcards in search. L1: Renamed `type` param to `ingredient_type` with alias to avoid shadowing builtin. Added 5 new tests. 36 story tests, 409 total suite passing
- 2026-04-08: Code review #3 fixes — H1: Added model_validator to IngredientAdminUpdate rejecting null for name/type (was triggering misleading 409 from NOT NULL constraint). M1: Refactored update_ingredient to accept Ingredient object instead of ID (eliminates redundant DB query). M2: Removed magic -1 sentinel from delete_ingredient, now accepts Ingredient object (router pre-guards 404). M3: Dead code paths removed by M1/M2 refactors, ingredient_service.py now at 100% coverage. L1: Added OpenAPI 409 response docs to delete endpoint. L2: Added empty update body no-op test. Added 3 new tests. 39 story tests, 412 total suite passing

### File List

| File | Action |
|------|--------|
| `backend/app/schemas/ingredient.py` | CREATED |
| `backend/app/schemas/__init__.py` | MODIFIED |
| `backend/app/services/ingredient_service.py` | CREATED |
| `backend/app/services/__init__.py` | MODIFIED |
| `backend/app/routers/admin.py` | MODIFIED |
| `backend/tests/test_admin_ingredients.py` | CREATED |
| `docs/sprint-artifacts/sprint-status.yaml` | MODIFIED |
