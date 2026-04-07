# Story 1.5: Public Category Endpoints Rewrite

Status: done

---

## Story

As a **user browsing the cocktail library**,
I want **filter dropdowns to show dynamically managed categories**,
So that **I see any new categories added by the admin immediately**.

---

## Acceptance Criteria

### AC-1: Database-Driven Category Queries

**Given** the `categories.py` router is rewritten
**When** a user calls `GET /api/categories/templates`
**Then** it queries the `category_templates` table (not the Python enum)
**And** returns only records where `is_active = true`
**And** results are ordered by `sort_order`

### AC-2: Response Format Compatibility

**Given** the public category endpoints
**When** called for any category type (templates, glassware, serving-styles, methods, spirits)
**Then** each returns the same response format as before
**And** existing frontend code continues to work without changes

### AC-3: Soft-Delete Filtering

**Given** an admin has soft-deleted a category (`is_active = false`)
**When** a user calls the public endpoint
**Then** the deleted category is NOT included in the response

### AC-4: Graceful Degradation for Inactive Categories

**Given** recipes exist with a now-inactive category value
**When** viewing those recipes
**Then** the category value still displays correctly (graceful degradation)
**And** the recipe detail page does NOT break

---

## Tasks / Subtasks

### Task 1: Create CategoryService (AC: #1, #3)

- [x] **1.1** Create `backend/app/services/category_service.py` (follow `cleanup.py` pattern — thin DB query wrapper)
- [x] **1.2** Implement `get_active_templates(db: Session) -> list[CategoryTemplate]`:
  - Query `category_templates` WHERE `is_active = true` ORDER BY `sort_order`
- [x] **1.3** Implement `get_active_glassware(db: Session) -> list[CategoryGlassware]`:
  - Query `category_glassware` WHERE `is_active = true` ORDER BY `sort_order`
- [x] **1.4** Implement `get_active_serving_styles(db: Session) -> list[CategoryServingStyle]`:
  - Query `category_serving_styles` WHERE `is_active = true` ORDER BY `sort_order`
- [x] **1.5** Implement `get_active_methods(db: Session) -> list[CategoryMethod]`:
  - Query `category_methods` WHERE `is_active = true` ORDER BY `sort_order`
- [x] **1.6** Implement `get_active_spirits(db: Session) -> list[CategorySpirit]`:
  - Query `category_spirits` WHERE `is_active = true` ORDER BY `sort_order`
- [x] **1.7** Implement `get_all_active_categories(db: Session) -> dict` returning `{"templates": list[CategoryTemplate], "spirits": list[CategorySpirit], "glassware": list[CategoryGlassware], "serving_styles": list[CategoryServingStyle], "methods": list[CategoryMethod]}` — all 5 in one call for the combined endpoint
- [x] **1.8** Import models from `app.models` (already re-exported via `__init__.py`), NOT from `app.models.category` directly

### Task 2: Rewrite categories.py Router (AC: #1, #2, #3)

- [x] **2.1** COMPLETE REWRITE of `backend/app/routers/categories.py`
- [x] **2.2** Remove ALL enum imports (CocktailTemplate, Glassware, ServingStyle, Method, SpiritCategory, all display name dicts). KEEP schema imports: `from app.schemas import CategoryItem, CategoryGroup, CategoriesResponse`
- [x] **2.3** Add `db: Session = Depends(get_db)` to every endpoint
- [x] **2.4** Rewrite `GET /api/categories` (combined endpoint):
  - Use CategoryService to query all 5 tables
  - Map DB records to existing `CategoryItem`/`CategoryGroup`/`CategoriesResponse` schemas
  - Glassware: group by `category` field (stemmed/short/tall/specialty), use `category.title()` as group name
- [x] **2.5** Rewrite `GET /api/categories/templates`:
  - Query `category_templates` via service
  - Return `[{"value": row.value, "display_name": row.label, "description": row.description}]`
- [x] **2.6** Rewrite `GET /api/categories/spirits`:
  - Query `category_spirits` via service
  - Return `[{"value": row.value, "display_name": row.label}]`
- [x] **2.7** Rewrite `GET /api/categories/glassware`:
  - Query `category_glassware` via service
  - Group by `category` field, return `[{"category": cat, "name": cat.title(), "items": [...]}]`
- [x] **2.8** Rewrite `GET /api/categories/serving-styles`:
  - Query `category_serving_styles` via service
  - Return `[{"value": row.value, "display_name": row.label, "description": row.description}]`
- [x] **2.9** Rewrite `GET /api/categories/methods`:
  - Query `category_methods` via service
  - Return `[{"value": row.value, "display_name": row.label, "description": row.description}]`

### Task 3: Add seeded_categories Fixture to conftest.py (AC: #1-4)

- [x] **3.1** Add `seeded_categories` fixture to `backend/tests/conftest.py` (NOT in individual test files — both test files need it)
  - Populates all 5 category tables using the same seeding pattern from `test_category_models.py:seeded_session`
  - Takes `test_session` as parameter, seeds all tables, commits, yields the session

### Task 4: Update Existing test_categories.py (AC: #1-4) — CRITICAL REGRESSION FIX

- [x] **4.1** MUST UPDATE `backend/tests/test_categories.py` — this existing file (222 lines, 10 tests) tests all 6 category endpoints and will BREAK after the rewrite because DB tables will be empty without seeding
- [x] **4.2** Add `seeded_categories` fixture dependency to every test in this file (either per-test or via class-level `@pytest.mark.usefixtures("seeded_categories")`)
- [x] **4.3** The existing tests assert `"category" in group` on glassware (line 134) — this must continue to pass. The individual `/glassware` endpoint MUST return the `category` key (see Glassware section below)
- [x] **4.4** Run `pytest backend/tests/test_categories.py` — all 10 existing tests must pass

### Task 5: Write New Tests (AC: #1-4)

- [x] **5.1** Create `backend/tests/test_categories_router.py` (new DB-specific integration tests)
- [x] **5.2** Tests use `seeded_categories` fixture from conftest.py
- [x] **5.3** Test: `test_get_all_categories_returns_200` — combined endpoint returns all 5 category types
- [x] **5.4** Test: `test_get_templates_returns_database_values` — templates come from DB, not enum
- [x] **5.5** Test: `test_get_templates_ordered_by_sort_order` — results respect sort_order
- [x] **5.6** Test: `test_get_templates_excludes_inactive` — inactive records filtered out
- [x] **5.7** Test: `test_get_glassware_grouped_by_category` — glassware grouped into stemmed/short/tall/specialty
- [x] **5.8** Test: `test_get_glassware_individual_has_category_key` — individual endpoint returns `category` field
- [x] **5.9** Test: `test_get_spirits_returns_database_values`
- [x] **5.10** Test: `test_get_serving_styles_returns_database_values`
- [x] **5.11** Test: `test_get_methods_returns_database_values`
- [x] **5.12** Test: `test_combined_endpoint_format_matches_frontend_contract` — validate CategoriesResponse schema shape
- [x] **5.13** Test: `test_empty_table_returns_empty_list` — graceful empty state (no seeded fixture)
- [x] **5.14** Test: `test_all_inactive_returns_empty_list` — all soft-deleted returns empty
- [x] **5.15** Run full test suite: `pytest` — all tests pass, no regressions

### Task 6: Verify Frontend Compatibility (AC: #2, #4)

- [x] **6.1** Start backend with `uvicorn app.main:app --reload`
- [x] **6.2** Call `GET http://localhost:8000/api/categories` and verify response shape matches `Categories` interface in `frontend/lib/api.ts:86`
- [x] **6.3** Verify filter dropdowns still work in frontend (`npm run dev`)
- [x] **6.4** Verify recipe display still works for recipes with any category value

### Task 7: Final Verification

- [x] **7.1** Run full backend test suite: `pytest` — no regressions
- [x] **7.2** Run frontend build: `npm run build` — no type errors
- [x] **7.3** Update `docs/sprint-artifacts/sprint-status.yaml`

---

## Dev Notes

### CRITICAL: This Is a COMPLETE REWRITE of categories.py

The current `backend/app/routers/categories.py` (160 lines) iterates Python enums directly. Every line must be replaced. The new version queries the 5 category database tables created in Story 1.4.

**Current state** (to be fully replaced):
- Imports all enums and display name dicts from `app.models.enums`
- 6 endpoints, each iterating Python enums
- No database dependency (`get_db`) at all

**New state** (what this story creates):
- Imports category models from `app.models.category`
- Imports `get_db` from `app.services.database`
- Each endpoint queries DB through CategoryService
- Filters by `is_active = true`, orders by `sort_order`

### Canonical Response Format (MUST NOT CHANGE)

The frontend AND existing tests enforce these exact shapes. Breaking these breaks the filter UI and test suite.

**DB column → API field mapping:**
| DB Column | Response Field | Notes |
|-----------|---------------|-------|
| `value` | `value` | Direct passthrough |
| `label` | `display_name` | Column is `label` in DB, response key is `display_name` |
| `description` | `description` | Only on templates, serving_styles, methods. Spirits have NO description. |
| `category` | `category` / `name` | Glassware only — see glassware section below |

**Per-endpoint response format:**

| Endpoint | Response Shape |
|----------|---------------|
| `GET /api/categories` | `CategoriesResponse` schema: `{"templates": [...], "spirits": [...], "glassware": [CategoryGroup], "serving_styles": [...], "methods": [...]}` |
| `GET /api/categories/templates` | `[{"value": "sour", "display_name": "Sour", "description": "Spirit + citrus + sweet"}, ...]` |
| `GET /api/categories/spirits` | `[{"value": "gin", "display_name": "Gin"}, ...]` |
| `GET /api/categories/glassware` | `[{"category": "stemmed", "name": "Stemmed", "items": [{"value": "coupe", "display_name": "Coupe"}, ...]}, ...]` |
| `GET /api/categories/serving-styles` | `[{"value": "up", "display_name": "Up", "description": "Chilled, strained, no ice in glass"}, ...]` |
| `GET /api/categories/methods` | `[{"value": "shaken", "display_name": "Shaken", "description": "With ice in shaker, strained"}, ...]` |

**CRITICAL: Glassware has TWO different shapes depending on endpoint:**
- **Combined endpoint** (`/api/categories`): Uses `CategoryGroup` schema → `{"name": "Stemmed", "items": [...]}` (no `category` key)
- **Individual endpoint** (`/api/categories/glassware`): Returns raw dict → `{"category": "stemmed", "name": "Stemmed", "items": [...]}` (WITH `category` key)
- Existing test at `test_categories.py:134` asserts `"category" in group` — this MUST pass

### Glassware Grouping Logic

Glassware is the tricky one. Two different shapes needed:

**Combined endpoint** (`/api/categories`) — uses `CategoryGroup` schema (no `category` key):
```python
groups = {}
for g in glassware_records:
    groups.setdefault(g.category, []).append(
        CategoryItem(value=g.value, display_name=g.label)
    )
return [CategoryGroup(name=cat.title(), items=items) for cat, items in groups.items()]
```

**Individual endpoint** (`/api/categories/glassware`) — returns raw dict WITH `category` key:
```python
groups = {}
for g in glassware_records:
    groups.setdefault(g.category, []).append(
        {"value": g.value, "display_name": g.label}
    )
return [{"category": cat, "name": cat.title(), "items": items} for cat, items in groups.items()]
```

**Group ordering**: Groups appear in the order their first item is encountered (by `sort_order`). Seeded data in Story 1.4 has sort_order 0-4=stemmed, 5-7=short, 8-11=tall, 12-23=specialty. So group order will be: Stemmed → Short → Tall → Specialty.

**Category values in DB** (seeded in Story 1.4): `stemmed`, `short`, `tall`, `specialty`
**Group name format**: `.title()` → `Stemmed`, `Short`, `Tall`, `Specialty`

### Architecture Compliance

**Service Layer Pattern (MANDATORY):**
- Business logic goes in `CategoryService`, NOT in the router
- Router is thin orchestration only: get DB session, call service, return response
- Follow `app/services/cleanup.py` pattern — thin DB query wrapper, similar complexity

**Database Dependency:**

```python
from app.services.database import get_db
from sqlalchemy.orm import Session
from fastapi import Depends

@router.get("/templates")
def get_templates(db: Session = Depends(get_db)):
    ...
```

**No 404 handling needed** — all public category endpoints return lists. Empty table = empty list, not 404.

### Existing Pydantic Schemas (REUSE — DO NOT RECREATE)

These schemas already exist in `backend/app/schemas/recipe.py` and are exported from `backend/app/schemas/__init__.py`:

```python
class CategoryItem(BaseModel):
    value: str
    display_name: str
    description: Optional[str] = None

class CategoryGroup(BaseModel):
    name: str
    items: List[CategoryItem]

class CategoriesResponse(BaseModel):
    templates: List[CategoryItem]
    spirits: List[CategoryItem]
    glassware: List[CategoryGroup]
    serving_styles: List[CategoryItem]
    methods: List[CategoryItem]
```

**DO NOT create new schemas.** Map DB models to these existing schemas.

### Frontend Contract (DO NOT MODIFY)

The frontend `fetchCategories()` in `frontend/lib/api.ts:149-152`:
```typescript
export async function fetchCategories(): Promise<Categories> {
  const res = await fetch(`${API_BASE}/categories`);
  if (!res.ok) throw new Error('Failed to fetch categories');
  return res.json();
}
```

Frontend interfaces in `frontend/lib/api.ts:75-92`:
```typescript
interface CategoryItem { value: string; display_name: string; description?: string; }
interface CategoryGroup { name: string; items: CategoryItem[]; }
interface Categories { templates: CategoryItem[]; spirits: CategoryItem[]; glassware: CategoryGroup[]; serving_styles: CategoryItem[]; methods: CategoryItem[]; }
```

**Zero frontend changes required.** The API response must be identical in shape.

### Previous Story Intelligence

**From Story 1.4 (Category Database Tables) — directly relevant:**
- 5 category tables created: `category_templates`, `category_glassware`, `category_serving_styles`, `category_methods`, `category_spirits`
- Column `label` (not `display_name`) stores the display text
- Glassware has extra `category` column (stemmed/short/tall/specialty)
- Spirits table has NO `description` column
- All seeded with exact enum string values in `value` column
- 327 tests passing as of Story 1.4 completion

**From Story 1.1-1.3 (Admin Foundation):**
- `require_admin` dependency in `app/dependencies.py` (NOT needed for public endpoints, but know it exists for Story 1.6)
- Test fixtures: `admin_user`, `admin_auth_token` available in conftest.py
- Use `datetime.now(timezone.utc)` not `datetime.utcnow()`

### Git Intelligence

```
f269abc feat: Add category database tables, BMAD framework, and project docs
```
This most recent commit created the 5 category tables and their seed data. All migration files are in `backend/alembic/versions/`.

### Technical Requirements

| Requirement | Value | Source |
|-------------|-------|--------|
| Python Version | 3.9+ | project_context.md |
| SQLAlchemy | 2.0+ (Mapped[] queries) | project_context.md |
| HTTP Error Format | `detail` key | project_context.md |
| Test Framework | pytest, asyncio auto mode | project_context.md |
| No `@pytest.mark.asyncio` | Redundant — auto mode | project_context.md |
| Router prefix | `/categories` (mounted under `/api`) | main.py |

### File Locations

| File | Action | Purpose |
|------|--------|---------|
| `backend/app/services/category_service.py` | CREATE | Service layer for DB queries |
| `backend/app/services/__init__.py` | MODIFY | Export new service functions (follow existing pattern) |
| `backend/app/routers/categories.py` | COMPLETE REWRITE | Replace enum iteration with DB queries |
| `backend/tests/conftest.py` | MODIFY | Add `seeded_categories` fixture |
| `backend/tests/test_categories.py` | MODIFY | Add `seeded_categories` dependency to all existing tests |
| `backend/tests/test_categories_router.py` | CREATE | New DB-specific integration tests |

### Anti-Patterns to Avoid

**DO NOT:**
- Import ANY enums in the rewritten `categories.py` (remove `CocktailTemplate`, `Glassware`, `ServingStyle`, `Method`, `SpiritCategory`, all display name dicts)
- Delete the schema imports (`CategoryItem`, `CategoryGroup`, `CategoriesResponse`) — these STAY
- Create new Pydantic schemas — reuse existing ones from `app/schemas`
- Put query logic in the router — use CategoryService
- Create admin endpoints (that's Story 1.6)
- Modify any frontend code
- Use `Base.metadata.create_all()`
- Return inactive categories in public endpoints
- Change the response field names (`display_name` must stay, even though DB column is `label`)
- Hardcode category counts in tests (use `len(CocktailTemplate)` etc.)
- Forget to update existing `test_categories.py` with `seeded_categories` fixture
- Add 404 error handling — these endpoints return lists, not single items

**DO:**

- Create a CategoryService with clean query methods (follow `cleanup.py` pattern)
- Import models from `app.models` (already re-exported), not `app.models.category`
- Map `label` → `display_name` in service or router
- Filter `is_active = true` on every query
- Order by `sort_order` on every query
- Group glassware by `category` column
- Return `category` key in individual `/glassware` endpoint (existing tests assert on it)
- Reuse existing Pydantic schemas from `app/schemas`
- Add `seeded_categories` fixture to `conftest.py`
- Update both test files to use the fixture
- Export new service from `services/__init__.py`

### Testing Strategy

**Fixture location**: `seeded_categories` goes in `conftest.py` — both `test_categories.py` and `test_categories_router.py` need it.

**Fixture pattern** (reuse seeding logic from `test_category_models.py:seeded_session` fixture, lines 38-96):

```python
# In conftest.py
@pytest.fixture
def seeded_categories(test_session: Session):
    """Seed all 5 category tables for endpoint tests."""
    # Same seeding logic as test_category_models.py:seeded_session
    # Seeds from Python enums: CocktailTemplate, Glassware, ServingStyle, Method, SpiritCategory
    ...
    test_session.commit()
    return test_session
```

**Test pattern** — use dynamic counts, not magic numbers:

```python
from app.models.enums import CocktailTemplate

def test_get_templates_returns_database_values(client, seeded_categories):
    response = client.get("/api/categories/templates")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == len(CocktailTemplate)  # NOT hardcoded 25
    assert data[0]["value"] == "sour"  # First by sort_order
    assert data[0]["display_name"] == "Sour"
    assert "description" in data[0]
```

**CRITICAL: Existing test file** `backend/tests/test_categories.py` (222 lines, 10 tests) must be updated to depend on `seeded_categories`. Without this, every `assert len(data["templates"]) > 0` will fail because DB tables are empty.

### Edge Cases

1. **Empty category tables**: Return empty lists, not errors
2. **All categories inactive**: Return empty lists
3. **Glassware with unknown category value**: Default to "specialty" group or skip — don't crash
4. **NULL descriptions**: Return `null` in JSON (schema allows `Optional[str]`)
5. **Database connection issues**: Let FastAPI's default 500 handler catch — don't over-engineer

### Project Context Reference

Critical patterns from [docs/project_context.md](../project_context.md):

```python
# SQLAlchemy query pattern
db.query(CategoryTemplate).filter(
    CategoryTemplate.is_active == True
).order_by(CategoryTemplate.sort_order).all()

# Router with DB dependency
@router.get("/templates")
def get_templates(db: Session = Depends(get_db)):
    ...
```

---

## Dev Agent Record

### Context Reference

Story context created by BMAD create-story workflow on 2026-04-07.

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Implementation Plan

- Created `CategoryService` as thin DB query wrapper (6 functions) following `cleanup.py` pattern
- Complete rewrite of `categories.py` router — removed all enum imports, replaced with DB queries through service layer
- Maintained two glassware response shapes: `CategoryGroup` schema (combined endpoint, no `category` key) vs raw dict (individual endpoint, with `category` key)
- Mapped DB `label` column → API `display_name` field in router layer
- All queries filter `is_active=True` and order by `sort_order`

### Debug Log References

- 339 tests passed (327 pre-existing + 12 new), 0 failures
- `category_service.py` and `categories.py` both at 100% test coverage
- Frontend build clean — no type errors

### Completion Notes List

- ✅ Task 1: CategoryService created with 6 query functions, exported from `services/__init__.py`
- ✅ Task 2: Complete rewrite of `categories.py` — all enum imports removed, DB-driven via service
- ✅ Task 3: `seeded_categories` fixture added to `conftest.py` (shared across test files)
- ✅ Task 4: All 10 existing tests in `test_categories.py` updated with `@pytest.mark.usefixtures("seeded_categories")` — all pass
- ✅ Task 5: 14 integration tests in `test_categories_router.py` — sort order, inactive filtering, empty states, schema shape, category key, AC-4 graceful degradation
- ✅ Task 6: Frontend contract verified — response shapes match `Categories` interface exactly
- ✅ Task 7: Full test suite 339 passed, frontend build clean
- ✅ Code Review: 5 issues fixed (3 MEDIUM, 2 LOW), 341 tests passing

### File List

| File | Action |
|------|--------|
| `backend/app/services/category_service.py` | CREATED |
| `backend/app/services/__init__.py` | MODIFIED (added category_service exports) |
| `backend/app/routers/categories.py` | REWRITTEN (enum→DB) |
| `backend/tests/conftest.py` | MODIFIED (added seeded_categories fixture + category imports) |
| `backend/tests/test_categories.py` | MODIFIED (added @pytest.mark.usefixtures to all 6 classes) |
| `backend/tests/test_categories_router.py` | CREATED (12 new tests) |
| `docs/sprint-artifacts/sprint-status.yaml` | MODIFIED (1-5 status updated) |
| `docs/sprint-artifacts/1-5-public-category-endpoints-rewrite.md` | MODIFIED (tasks checked, record updated) |

---

## Change Log

| Date | Change |
|------|--------|
| 2026-04-07 | Story created via create-story workflow, status: ready-for-dev |
| 2026-04-07 | Adversarial validation (Sonnet): 5 critical fixes, 4 enhancements, 3 optimizations applied. Key fixes: existing test_categories.py regression prevention, glassware category key inconsistency, seeded_categories fixture in conftest.py, services/__init__.py export, hardcoded count removal |
| 2026-04-07 | Implementation complete: CategoryService created, categories.py fully rewritten (enum→DB), 12 new tests + 10 existing tests passing, 339 total tests green, frontend build clean. Status → Ready for Review |
| 2026-04-07 | Code review (Opus 4.6): 5 issues found (3M, 2L), all fixed. M1: Router imports aligned to package interface pattern. M2: Added 2 AC-4 regression tests (recipe with inactive category). M3: SQLAlchemy boolean filters modernized. L1+L2: typing imports modernized, return type specified. 341 tests passing. Status → done |
| 2026-04-07 | Code review #2 (Opus 4.6, fresh context): 5 issues found (0H, 3M, 2L). M1: Added response_model to 4/5 individual endpoints (glassware excluded — schema lacks category key). M2: Fixed stale test count in Dev Agent Record (12→14). M3: Added glassware group count assertion to combined endpoint test. L1+L2: documented only (spirits description gap, 5-query perf note). 341 tests passing. Status remains done |
