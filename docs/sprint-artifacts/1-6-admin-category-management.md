# Story 1.6: Admin Category Management

Status: Done

---

## Story

As an **admin**,
I want **to add, edit, reorder, and soft-delete category values**,
So that **I can customize the filter options without deploying code changes**.

---

## Acceptance Criteria

### AC-1: Get All Categories (Including Inactive)

**Given** I am authenticated as an admin
**When** I call `GET /api/admin/categories/{type}`
**Then** I receive ALL category values (including inactive ones)
**And** inactive values are clearly marked with `is_active: false`
**And** results are ordered by `sort_order`

### AC-2: Create Category

**Given** I am authenticated as an admin
**When** I call `POST /api/admin/categories/{type}` with a new category
**Then** the category is created with:
- `value`: snake_case, unique, validated
- `label`: display name provided by admin
- `sort_order`: appended to end (highest existing + 1)
- `is_active`: true

### AC-3: Duplicate Prevention

**Given** I try to create a category with a `value` that already exists
**When** I submit the request
**Then** I receive a 409 Conflict response
**And** the duplicate is not created

### AC-4: Update Category

**Given** I am authenticated as an admin
**When** I call `PUT /api/admin/categories/{type}/{id}`
**Then** I can update `label`, `description`, `is_active`
**And** the `value` field is IMMUTABLE (cannot be changed)

### AC-5: Soft-Delete Category

**Given** I am authenticated as an admin
**When** I call `DELETE /api/admin/categories/{type}/{id}`
**Then** the category is soft-deleted (`is_active` set to false)
**And** the record is NOT physically removed

### AC-6: Usage Check Before Delete

**Given** a category is used by existing recipes
**When** I try to delete it
**Then** I receive a response showing the count of recipes using this category
**And** the soft-delete proceeds with the usage warning included in the response

### AC-7: Reorder Categories

**Given** I am authenticated as an admin
**When** I call `POST /api/admin/categories/{type}/reorder` with an array of IDs in new order
**Then** the `sort_order` values are updated to match the new sequence (0, 1, 2, ...)

### AC-8: Authorization

**Given** I am NOT an admin (regular user or unauthenticated)
**When** I call any `/api/admin/categories/*` endpoint
**Then** I receive a 403 Forbidden response

---

## Tasks / Subtasks

### Task 1: Create Admin Category Schemas (AC: #1-7)

- [x] **1.1** Create `backend/app/schemas/category.py` with admin-specific schemas:
  - `CategoryCreate`: `value` (str, required), `label` (str, required), `description` (Optional[str], default None)
  - `CategoryUpdate`: `label` (Optional[str]), `description` (Optional[str]), `is_active` (Optional[bool])
  - `CategoryAdminResponse`: `id` (str), `value` (str), `label` (str), `description` (Optional[str]), `sort_order` (int), `is_active` (bool), `created_at` (datetime)
  - `CategoryReorderRequest`: `ids` (List[str]) — ordered list of category IDs
  - `CategoryDeleteResponse`: `message` (str), `recipe_count` (int)
- [x] **1.2** Export new schemas from `backend/app/schemas/__init__.py`

### Task 2: Add Admin Methods to CategoryService (AC: #1-7)

- [x] **2.1** Add to `backend/app/services/category_service.py`:
  - `get_all_by_type(db, type_name) -> list` — returns ALL categories (active + inactive) ordered by `sort_order`
  - `get_by_id(db, type_name, id) -> model | None`
  - `create(db, type_name, data: CategoryCreate) -> model`
  - `update(db, type_name, id, data: CategoryUpdate) -> model | None`
  - `soft_delete(db, type_name, id) -> tuple[model, int]` — returns (category, recipe_usage_count)
  - `reorder(db, type_name, ids: list[str]) -> None`
  - `get_recipe_usage_count(db, type_name, value) -> int`
- [x] **2.2** Add `TYPE_MAP` dict to resolve type string → model class:
  ```python
  TYPE_MAP = {
      "templates": CategoryTemplate,
      "glassware": CategoryGlassware,
      "serving-styles": CategoryServingStyle,
      "methods": CategoryMethod,
      "spirits": CategorySpirit,
  }
  ```
- [x] **2.3** Add `RECIPE_FIELD_MAP` dict to resolve type string → Recipe field:
  ```python
  RECIPE_FIELD_MAP = {
      "templates": Recipe.template,
      "glassware": Recipe.glassware,
      "serving-styles": Recipe.serving_style,
      "methods": Recipe.method,
      "spirits": Recipe.main_spirit,
  }
  ```
- [x] **2.4** Export new functions from `backend/app/services/__init__.py`

### Task 3: Create Admin Category Router Endpoints (AC: #1-8)

- [x] **3.1** Add category admin endpoints to `backend/app/routers/admin.py` (DO NOT create a new router file — extend existing admin router)
- [x] **3.2** `GET /admin/categories/{type}` — list all categories (active + inactive):
  ```python
  @router.get("/categories/{type}")
  def get_admin_categories(
      type: str,
      db: Session = Depends(get_db),
      admin: User = Depends(require_admin),
  ):
  ```
  - Validate `type` is one of: templates, glassware, serving-styles, methods, spirits
  - Return 400 if invalid type
  - Return list of `CategoryAdminResponse`
- [x] **3.3** `POST /admin/categories/{type}` — create new category:
  - Validate type
  - Check uniqueness of `value` — return 409 if duplicate
  - Auto-assign `sort_order` = max existing + 1
  - Generate UUID for `id`
  - Return 201 with `CategoryAdminResponse`
- [x] **3.4** `PUT /admin/categories/{type}/{id}` — update category:
  - Validate type and find by id — return 404 if not found
  - Apply only provided fields (partial update)
  - `value` field is IMMUTABLE — ignore if included in payload
  - Return 200 with updated `CategoryAdminResponse`
- [x] **3.5** `DELETE /admin/categories/{type}/{id}` — soft-delete:
  - Validate type and find by id — return 404 if not found
  - Check recipe usage count via `RECIPE_FIELD_MAP`
  - Set `is_active = false` (NEVER hard delete)
  - Return 200 with `CategoryDeleteResponse` including `recipe_count`
- [x] **3.6** `POST /admin/categories/{type}/reorder` — reorder:
  - Validate type
  - Validate all IDs exist and belong to this type
  - Update `sort_order` = index position (0, 1, 2, ...)
  - Return 200 with success message
- [x] **3.7** Add type validation helper:
  ```python
  VALID_TYPES = {"templates", "glassware", "serving-styles", "methods", "spirits"}
  
  def validate_category_type(type: str) -> None:
      if type not in VALID_TYPES:
          raise HTTPException(status_code=400, detail=f"Invalid category type: {type}. Must be one of: {', '.join(sorted(VALID_TYPES))}")
  ```

### Task 4: Write Tests (AC: #1-8)

- [x] **4.1** Create `backend/tests/test_admin_categories.py`
- [x] **4.2** Use fixtures: `client`, `admin_user`, `admin_auth_token`, `seeded_categories`
- [x] **4.3** Auth tests:
  - `test_admin_categories_returns_403_without_auth` (no token)
  - `test_admin_categories_returns_403_for_regular_user` (non-admin token)
- [x] **4.4** GET tests:
  - `test_get_all_templates_includes_inactive` — seed an inactive entry, verify it's returned
  - `test_get_all_templates_ordered_by_sort_order`
  - `test_get_invalid_type_returns_400`
- [x] **4.5** POST (create) tests:
  - `test_create_template_returns_201`
  - `test_create_template_auto_assigns_sort_order`
  - `test_create_duplicate_value_returns_409`
  - `test_create_template_with_description`
  - `test_create_spirit_without_description` (spirits have no description column)
- [x] **4.6** PUT (update) tests:
  - `test_update_template_label`
  - `test_update_template_description`
  - `test_update_template_deactivate`
  - `test_update_nonexistent_returns_404`
  - `test_update_value_field_is_immutable` — send value in payload, verify it's unchanged
- [x] **4.7** DELETE (soft-delete) tests:
  - `test_delete_template_soft_deletes`
  - `test_delete_returns_recipe_count` — create a recipe using the category, verify count > 0
  - `test_delete_nonexistent_returns_404`
- [x] **4.8** Reorder tests:
  - `test_reorder_templates`
  - `test_reorder_with_invalid_ids_returns_400`
- [x] **4.9** Run full test suite: `pytest` — no regressions

### Task 5: Verify Public Endpoints Still Work (AC: regression)

- [x] **5.1** Run `pytest backend/tests/test_categories.py` — all 10 existing tests pass
- [x] **5.2** Run `pytest backend/tests/test_categories_router.py` — all 12 existing tests pass
- [x] **5.3** Verify public endpoints still only return active categories

### Task 6: Final Verification

- [x] **6.1** Run full backend test suite: `pytest`
- [x] **6.2** Start backend, manually test admin endpoints with curl or httpie
- [x] **6.3** Update `docs/sprint-artifacts/sprint-status.yaml`

---

## Dev Notes

### CRITICAL: Extend Existing Admin Router — DO NOT Create New Router File

`backend/app/routers/admin.py` already exists with `router = APIRouter(prefix="/admin", tags=["admin"])`. Add category endpoints here. The router is already mounted at `/api/admin` via `main.py`.

### Category Type URL Parameter

Use hyphenated URL paths that match the existing public endpoint patterns:
- `templates`, `glassware`, `serving-styles`, `methods`, `spirits`

Map these to model classes internally. The `serving-styles` URL path maps to `CategoryServingStyle` model.

### Recipe → Category Relationship (String-Based, No FK)

Categories are stored as **plain string values** on the Recipe model:

```python
# backend/app/models/recipe.py
template:     Mapped[Optional[str]] = mapped_column(String(50))
main_spirit:  Mapped[Optional[str]] = mapped_column(String(50))
glassware:    Mapped[Optional[str]] = mapped_column(String(50))
serving_style: Mapped[Optional[str]] = mapped_column(String(50))
method:       Mapped[Optional[str]] = mapped_column(String(50))
```

No foreign keys — soft-deleting a category does NOT break recipes. Usage count query:

```python
db.query(func.count(Recipe.id)).filter(
    RECIPE_FIELD_MAP[type_name] == category.value
).scalar()
```

### Model Column Differences Per Type

| Model | Has `description` | Has `category` | Notes |
|-------|:-:|:-:|-------|
| CategoryTemplate | Yes | No | |
| CategoryGlassware | No | Yes | `category` = stemmed/short/tall/specialty |
| CategoryServingStyle | Yes | No | |
| CategoryMethod | Yes | No | |
| CategorySpirit | No | No | Simplest model |

**Implication for create/update**: When creating spirits or glassware, the `description` field from `CategoryCreate` should be ignored (those models don't have it). Handle this gracefully:

```python
# In service create method:
fields = {"id": str(uuid4()), "value": data.value, "label": data.label, "sort_order": next_sort_order}
if hasattr(model_class, 'description') and data.description:
    fields["description"] = data.description
if hasattr(model_class, 'category') and hasattr(data, 'category'):
    fields["category"] = data.category
```

**Glassware special case**: `CategoryCreate` may need an optional `category` field for glassware (stemmed/short/tall/specialty). Either:
- Add `category: Optional[str] = None` to `CategoryCreate` schema
- Or default new glassware to `category = "specialty"`

Recommend defaulting to `"specialty"` for simplicity unless explicitly provided.

### UUID Generation for New Categories

Existing category records use UUID strings (36-char). Use:

```python
from uuid import uuid4
id = str(uuid4())
```

### Sort Order Auto-Assignment

When creating a new category, assign `sort_order` = max existing + 1:

```python
max_order = db.query(func.max(model_class.sort_order)).scalar() or 0
new_record.sort_order = max_order + 1
```

### Reorder Logic

The reorder endpoint receives a list of IDs in the desired order. Update each:

```python
for index, id in enumerate(request.ids):
    record = db.query(model_class).filter(model_class.id == id).first()
    if not record:
        raise HTTPException(status_code=400, detail=f"ID {id} not found")
    record.sort_order = index
db.commit()
```

### Existing CategoryService Functions (DO NOT MODIFY)

These public read functions already exist and MUST NOT be changed:

```python
get_active_templates(db)      # filters is_active=True, orders by sort_order
get_active_glassware(db)
get_active_serving_styles(db)
get_active_methods(db)
get_active_spirits(db)
get_all_active_categories(db)
```

Add new admin functions alongside these. Do NOT rename or modify existing signatures.

### Admin Auth Pattern (Copy Exactly)

```python
from app.dependencies import require_admin
from app.services.database import get_db

@router.get("/categories/{type}")
def get_admin_categories(
    type: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
```

`require_admin` already validates `is_active` via `get_current_user`, then checks `is_admin`. Returns 403 if either fails. Import path: `from app.dependencies import require_admin`.

### Error Response Pattern

Always use `detail` key (project convention):

```python
raise HTTPException(status_code=400, detail="Invalid category type")
raise HTTPException(status_code=404, detail="Category not found")
raise HTTPException(status_code=409, detail="Category value already exists")
```

### Test Setup Pattern

Use existing fixtures from `conftest.py`:

```python
def test_create_template(client, admin_auth_token, seeded_categories):
    response = client.post(
        "/api/admin/categories/templates",
        json={"value": "new_template", "label": "New Template"},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 201
```

For non-admin rejection tests:

```python
def test_returns_403_for_regular_user(client, auth_token, seeded_categories):
    response = client.get(
        "/api/admin/categories/templates",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 403
```

### No Audit Logging in This Story

Audit logging infrastructure is Story 4-1. Do NOT add audit logging here. Keep this story focused on CRUD + reorder.

### No Rate Limiting in This Story

Rate limiting pattern exists (`slowapi` in main.py) but is not a requirement for this story. Admin endpoints will inherit the existing rate limiter configuration.

### No Frontend Changes in This Story

Frontend admin UI is Epic 5 (Story 5-3: Category Management Modal). This story is backend-only.

### Project Structure Notes

| File | Action | Purpose |
|------|--------|---------|
| `backend/app/schemas/category.py` | CREATE | Admin category schemas |
| `backend/app/schemas/__init__.py` | MODIFY | Export new schemas |
| `backend/app/services/category_service.py` | MODIFY | Add admin CRUD methods |
| `backend/app/services/__init__.py` | MODIFY | Export new service functions |
| `backend/app/routers/admin.py` | MODIFY | Add category admin endpoints |
| `backend/tests/test_admin_categories.py` | CREATE | Admin category tests |

### Anti-Patterns to Avoid

**DO NOT:**
- Create a separate `admin_categories.py` router file — use existing `admin.py`
- Hard-delete categories — ALWAYS soft-delete (set `is_active = false`)
- Allow `value` field mutation — it's the string stored in recipes
- Add audit logging (that's Story 4-1)
- Add rate limiting decorators (not scoped to this story)
- Modify existing public category endpoints or CategoryService read functions
- Create frontend code (that's Epic 5)
- Use `Base.metadata.create_all()`
- Use `@pytest.mark.asyncio` (asyncio_mode=auto)
- Import describe/it/expect in tests

**DO:**
- Extend existing `admin.py` router
- Use `require_admin` dependency on ALL endpoints
- Use `detail` key in all HTTPExceptions
- Use existing `admin_user`/`admin_auth_token`/`seeded_categories` fixtures
- Handle model column differences (spirits has no description, glassware has category)
- Generate UUIDs for new category IDs
- Return 201 for creates, 200 for everything else
- Validate category type on every endpoint

### References

- [Source: docs/admin-panel-architecture.md#Phase 3: Categories]
- [Source: docs/epics.md#Story 1.6]
- [Source: docs/project_context.md#Admin Panel Patterns]
- [Source: backend/app/routers/admin.py — existing admin router]
- [Source: backend/app/services/category_service.py — existing read functions]
- [Source: backend/app/models/category.py — category model definitions]
- [Source: backend/app/models/recipe.py:51-55 — recipe category string fields]

### Previous Story Intelligence (1-5)

From Story 1-5 (Public Category Endpoints Rewrite):
- `CategoryService` created as thin DB query wrapper following `cleanup.py` pattern
- DB `label` column maps to API `display_name` field — admin endpoints should use `label` directly (no mapping needed for admin response)
- All public queries filter `is_active=True` and order by `sort_order` — admin GET returns ALL regardless of `is_active`
- 339 tests passing as of Story 1-5 completion
- Models imported from `app.models` (re-exported via `__init__.py`), NOT from `app.models.category`

### Git Intelligence

```
f269abc feat: Add category database tables, BMAD framework, and project docs
5163a06 feat: Add admin capabilities for user and recipe management (Epic 1)
```

Story 1-4 created the 5 category tables + seed data. Story 1-5 rewrote public endpoints to query those tables. This story adds the admin write endpoints.

---

## Dev Agent Record

### Context Reference

Story context created by BMAD create-story workflow on 2026-04-07.

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References

None — clean implementation, all 361 tests passing on first run.

### Completion Notes List

- Created admin category schemas: CategoryCreate, CategoryUpdate, CategoryAdminResponse, CategoryReorderRequest, CategoryDeleteResponse
- Added TYPE_MAP and RECIPE_FIELD_MAP dicts to category_service.py for type→model and type→recipe-field resolution
- Implemented 7 admin service methods: get_all_by_type, get_by_id, create, update, soft_delete, reorder, get_recipe_usage_count
- Extended existing admin.py router with 5 endpoints: GET/POST/PUT/DELETE + reorder
- Handled model column differences: spirits has no description, glassware has category field (defaults to "specialty")
- Value field immutability enforced — CategoryUpdate schema excludes value, so it's never applied
- 20 new tests covering auth (AC-8), GET (AC-1), POST/create (AC-2,3), PUT/update (AC-4), DELETE/soft-delete (AC-5,6), reorder (AC-7)
- All 24 existing public category tests pass — zero regressions
- Full suite: 361 passed, 0 failed

### Code Review Fixes (2026-04-08)

- **H1**: Added snake_case Pydantic `field_validator` on `CategoryCreate.value` — enforces `^[a-z][a-z0-9_]*$` (AC-2 compliance)
- **H2**: Fixed `test_update_value_field_is_immutable` — now sends `value` in payload to actually test immutability
- **H3**: Added 5 auth rejection tests for POST/PUT/DELETE/reorder endpoints (was only tested on GET)
- **M1**: Renamed `test_admin_categories_returns_403_without_auth` → `_401_` to match actual assertion
- **M2**: Added 2 glassware creation tests — covers `category` field default ("specialty") and explicit value
- **M2**: Added `test_create_category_rejects_non_snake_case_value` for validation coverage
- **M3**: Refactored `reorder()` to use single `WHERE id IN (...)` query instead of N+1 queries
- Full suite after review: 369 passed, 0 failed. `category_service.py` now at 100% coverage

### Code Review Fixes #2 (2026-04-08)

- **H1**: Added 3 missing 403 tests for regular users on PUT, DELETE, and reorder endpoints (AC-8 full coverage)
- **M1**: Wrapped `create()` commit in `IntegrityError` handler — race condition duplicates now return `None` (409) instead of crashing (500)
- **M2**: `reorder()` now validates ALL category IDs of the type are present — partial reorder returns 400 instead of silently creating duplicate sort_orders
- **M2**: Added `test_reorder_with_partial_ids_returns_400` test
- **M3**: Added `max_length` constraints to `CategoryCreate` (`value`=50, `label`=100, `category`=50) and `CategoryUpdate` (`label`=100) matching DB column sizes
- Full suite after review #2: 373 passed, 0 failed. `admin.py` at 100% coverage

### Change Log

- 2026-04-07: Implemented Story 1.6 — Admin Category Management (all 8 ACs satisfied)
- 2026-04-08: Code review fixes — 3 HIGH, 3 MEDIUM issues resolved, 8 new tests added
- 2026-04-08: Code review #2 fixes — 1 HIGH, 3 MEDIUM issues resolved, 4 new tests added (373 total)

### File List

- `backend/app/schemas/category.py` — CREATED — Admin category Pydantic schemas (+ snake_case validator)
- `backend/app/schemas/__init__.py` — MODIFIED — Export new category schemas
- `backend/app/services/category_service.py` — MODIFIED — Added TYPE_MAP, RECIPE_FIELD_MAP, admin CRUD methods, optimized reorder
- `backend/app/services/__init__.py` — MODIFIED — Export new admin service functions
- `backend/app/routers/admin.py` — MODIFIED — Added 5 category admin endpoints + type validation helper
- `backend/tests/test_admin_categories.py` — CREATED — 28 tests for admin category endpoints
- `docs/sprint-artifacts/sprint-status.yaml` — MODIFIED — Status updated to review
- `docs/sprint-artifacts/1-6-admin-category-management.md` — MODIFIED — Story file updated
