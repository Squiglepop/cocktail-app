---
project_name: 'Coctail Shots'
user_name: 'Deemo'
date: '2025-12-30'
sections_completed: ['technology_stack', 'language_rules', 'framework_rules', 'testing_rules', 'code_quality', 'dev_workflow', 'critical_rules']
---

# Project Context for AI Agents

_This file contains critical rules and patterns that AI agents must follow when implementing code in this project. Focus on unobvious details that agents might otherwise miss._

---

## Technology Stack & Versions

### Backend (Python 3.9+)
- Python 3.9+ required (for Mapped[] type hint syntax)
- FastAPI ≥0.104.0
- SQLAlchemy ≥2.0.0 (modern Mapped[] syntax, NOT legacy Column())
- Pydantic ≥2.5.0
- Anthropic ≥0.39.0 - uses **messages API** (`client.messages.create()`), NOT deprecated completions API
- Alembic ≥1.12.0
- **bcrypt 4.0.x ONLY** - pinned for passlib 1.7.4 compatibility

### Frontend (Node.js 18+)
- Next.js ^14.2.35 (App Router, standalone output)
- React ^18.2.0
- TypeScript ^5.3.0 (strict mode)
- **@tanstack/react-query ^5.x** - v5 object syntax (see examples below)
- Tailwind CSS ^3.4.0 + `clsx` + `tailwind-merge` for conditional classes
- Vitest ^1.0.0 (globals enabled - don't import describe/it/expect)
- idb ^8.0.3 (async/await patterns, not callbacks)

### Critical Patterns by Scenario

**When writing backend code:**
- Database URL is env-driven: PostgreSQL (prod via `DATABASE_URL`), SQLite (dev fallback)
- NEVER use `Base.metadata.create_all()` in prod - Alembic migrations only
- All routes mount under `/api` prefix (e.g., `prefix="/recipes"` → `/api/recipes`)
- Update CORS in `main.py` when adding new frontend origins

**When writing frontend code:**
- `@/*` path alias is frontend-only (don't use in Python)
- `.env.local` required: `NEXT_PUBLIC_API_URL=http://localhost:8000/api`
- Use `clsx`/`tailwind-merge` for conditional Tailwind classes, NOT string concatenation

**When writing tests:**
- Backend pytest: asyncio auto mode - NO `@pytest.mark.asyncio` decorators
- Frontend vitest: globals enabled - NO imports for describe/it/expect
- Test setup: `frontend/tests/setup.ts` - don't duplicate

**When deploying:**
- `output: 'standalone'` in next.config.js - DO NOT CHANGE
- Railway auto-injects `DATABASE_URL` - never hardcode connection strings

### Code Examples

**React Query (v5 syntax):**
```typescript
// ❌ WRONG (v4 positional args)
useQuery('recipes', fetchRecipes)

// ✅ RIGHT (v5 object syntax)
useQuery({ queryKey: ['recipes'], queryFn: fetchRecipes })
```

**Conditional Tailwind classes:**
```typescript
// ❌ WRONG
className={`btn ${isActive ? 'bg-blue-500' : 'bg-gray-500'}`}

// ✅ RIGHT
import { clsx } from 'clsx'
className={clsx('btn', isActive ? 'bg-blue-500' : 'bg-gray-500')}
```

### Version Constraints Summary
- ⚠️ Python 3.9+ required
- ⚠️ bcrypt 4.0.x only (passlib compatibility)
- ⚠️ SQLAlchemy 2.0+ (Mapped[] syntax)
- ⚠️ React Query v5 (object syntax)
- ⚠️ Next.js standalone output (Railway)

---

## Language-Specific Rules

### TypeScript (Frontend)

**Type Discipline:**
- Strict mode enabled - no implicit `any`
- Explicit return types on all API functions: `Promise<Recipe>`, `Promise<void>`
- Use `interface` for object shapes, `type` for unions/aliases

**File Naming:**
- Components: `PascalCase.tsx` (RecipeCard.tsx)
- Utilities: `kebab-case.ts` (offline-storage.ts)
- Tests: `*.test.ts` or `*.test.tsx`

**API Call Pattern (follow exactly):**
```typescript
const headers: Record<string, string> = {};
if (token) {
  headers['Authorization'] = `Bearer ${token}`;
}
```

**Nullish & Enum Handling:**
- Use `??` for nullish coalescing (handles `null` from API)
- Enum values stay snake_case: `old_fashioned`, `rum_dark`
- Use `formatEnumValue()` for display only

**Context Usage:**
```typescript
// ✅ Use custom hooks
const { user, token } = useAuth();

// ❌ No direct useContext()
```

**Component Location:**
- Page-specific: colocate in `app/[page]/`
- Shared: `components/` at root
- Feature-grouped: `components/recipes/`, `components/playlists/`

**Testing (MSW 2.x):**
```typescript
// ✅ MSW handler pattern
http.get('*/api/recipes', () => HttpResponse.json(mockRecipes))

// ❌ Don't mock fetch directly
```

### Python (Backend)

**File Naming:**
- All files: `snake_case.py`
- Tests: `test_*.py` in `tests/` directory

**Type Hints:**
- SQLAlchemy 2.0 `Mapped[]` syntax required
- Use `Optional[T]` not `T | None`
- Python 3.9 compatibility: use `Union[X, Y]` not `X | Y`, `Optional[X]` not `X | None`, `Tuple[X, Y]` not `tuple[X, Y]` — union syntax requires 3.10+

**Import Order:**
```python
# 1. Standard library
# 2. Third-party
# 3. Local
```

**Architecture Boundaries:**
- **Models**: Database entities
- **Schemas**: Pydantic API contracts
- **Services**: Business logic
- **Routers**: Thin orchestration only

**Error Pattern:**
```python
# Always use 'detail' key
raise HTTPException(status_code=404, detail="Recipe not found")
```

**Testing:**
```python
# ✅ Use fixtures from conftest.py
def test_create_recipe(test_db, client):

# ❌ Don't create your own sessions
```

### Where to Put New Code

| Need | Location |
|------|----------|
| New API function | `lib/api.ts` - copy existing pattern |
| New endpoint | Router + Schema + Service (if complex) |
| New React hook | `lib/hooks/` + export from index.ts |
| New component (shared) | `components/` |
| New component (feature) | `components/[feature]/` |

---

## Framework-Specific Rules

### Next.js 14 (App Router)

**Routing & Structure:**
- File-based routing in `app/` directory
- Dynamic routes: `[param]` folder pattern
- `'use client'` directive required for hooks/interactivity
- Provider hierarchy: Query → Auth → Offline → Favourites (order matters)

**Testing (App Router):**
```typescript
// ✅ Mock next/navigation (App Router)
vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn() }),
  usePathname: () => '/recipes',
}))

// ❌ Don't mock next/router (that's Pages Router)
```

### FastAPI

**Lifespan:**
- Use `@asynccontextmanager` lifespan, NOT `@app.on_event`

**Pydantic v2:**
- `model_validate()`, `model_dump()`, `ConfigDict`

**Testing:**
- TestClient uses `httpx`, not `requests`

**Logic Placement:**

| Logic Type | Location |
|------------|----------|
| Validation/auth | Router (via `Depends`) |
| Business rules | Service |
| Database queries | Service |

### React Query (TanStack Query v5)

**Query Patterns:**
```typescript
queryKey: ['recipes']
queryKey: ['recipes', id]
```

**Testing:**
```typescript
// ✅ Fresh QueryClient per test
const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } }
})
```

**State Handling (always handle all three):**
```typescript
if (isLoading) return <Skeleton />;
if (error) return <ErrorMessage />;
return <RecipeGrid recipes={data} />;
```

### Auth & Offline

- Token in memory, passed explicitly (no localStorage)
- Check `isOffline` before API calls
- New offline pages need SW cache update

### Forms

- No form library - controlled components with `useState`
- Don't introduce react-hook-form/formik without discussion

### New API Endpoint Checklist

1. Schema in `app/schemas/`
2. Router function in `app/routers/`
3. Service if complex logic
4. Mount router in `main.py` (if new file)
5. Add to `lib/api.ts`
6. Add React Query hook if needed

---

## Testing Rules

### Test Configuration

| Stack | Framework | Config | Key Settings |
|-------|-----------|--------|--------------|
| Backend | pytest | `pytest.ini` | asyncio auto, coverage |
| Frontend | vitest | `vitest.config.ts` | jsdom, globals |

### Backend (pytest)

**Use existing fixtures from `conftest.py`:**
- `test_db` - in-memory SQLite
- `client` - TestClient with overrides
- `test_user` - authenticated user
- `auth_headers` - Bearer token

**Test naming - describe WHAT:**
```python
def test_create_recipe_returns_201_with_valid_data():
def test_create_recipe_returns_400_when_name_missing():
def test_delete_recipe_returns_401_when_unauthorized():
def test_delete_recipe_returns_403_when_not_owner():
```

**Mock the extractor (never hit Anthropic API):**
```python
@pytest.fixture
def mock_extractor(mocker):
    return mocker.patch(
        'app.services.extractor.RecipeExtractor.extract_from_file',
        return_value=mock_extracted_recipe
    )
```

### Frontend (vitest)

**Test isolation (every test):**
```typescript
beforeEach(() => { queryClient.clear() })
afterEach(() => { cleanup(); vi.clearAllMocks() })
```

**Centralize mock data in `tests/utils/mocks.ts`:**
```typescript
export const mockRecipe: Recipe = { ... }
export const mockRecipes: Recipe[] = [ ... ]
```

**Always test error states:**
```typescript
server.use(
  http.get('*/api/recipes', () => new HttpResponse(null, { status: 500 }))
)
expect(await screen.findByText(/error/i)).toBeInTheDocument()
```

### Required Test Categories

| Category | Why |
|----------|-----|
| Happy path | Basic functionality |
| Error states (4xx, 5xx) | Production resilience |
| Auth boundaries (401, 403) | Security |
| Offline mode | PWA functionality |

### Coverage Target: 80%

```bash
# Backend (auto via pytest.ini)
pytest

# Frontend
npm run test:coverage
```

---

## Code Quality & Style

### Import Organization

```python
# Python: stdlib → third-party → local
import os              # stdlib
from fastapi import HTTPException  # third-party
from app.models import Recipe      # local
```

```typescript
// TypeScript: react → external → internal → relative
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { RecipeCard } from './RecipeCard';
```

### Architecture Boundaries (Enforce)

| Layer | Responsibility | NOT Allowed |
|-------|---------------|-------------|
| Router | Thin orchestration, auth via `Depends` | Business logic |
| Service | Business logic, DB queries | HTTP concerns |
| Schema | API contracts (Pydantic) | DB models |
| Model | Database entities | Validation logic |

### Code Discipline

- **Read before write**: Study existing patterns in file before adding code
- No implicit `any` (TypeScript strict mode)
- Error responses: always use `detail` key in HTTPException
- 3 similar lines > 1 premature abstraction
- Comments only for non-obvious "why", not "what"

### Don't Do This

- Dump business logic in routers (use Services)
- Invent new patterns when existing ones exist
- Add dependencies without explicit approval
- Create helpers/utilities for one-time operations
- Mock fetch directly (use MSW handlers)
- Skip reading existing code before implementing

---

## Development Workflow

### Environment Setup (One-Time)

```bash
# Backend
cd cocktail-app/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Add ANTHROPIC_API_KEY

# Frontend
cd cocktail-app/frontend
npm install
cp .env.local.example .env.local  # Set NEXT_PUBLIC_API_URL
```

### Daily Development

```bash
# Backend (terminal 1)
cd cocktail-app/backend && source venv/bin/activate
uvicorn app.main:app --reload  # localhost:8000

# Frontend (terminal 2)
cd cocktail-app/frontend && npm run dev  # localhost:3000
```

### Pre-Commit Checklist

| Check | Backend | Frontend |
|-------|---------|----------|
| Tests pass | `pytest` | `npm test` |
| Lint clean | - | `npm run lint` |
| Types check | - | `npx tsc --noEmit` |
| No debug code | No `print()` | No `console.log` |

### Database Migration Protocol

1. Modify model in `app/models/`
2. Generate: `alembic revision --autogenerate -m "description"`
3. **REVIEW** generated file - autogenerate misses edge cases
4. Test locally: `alembic upgrade head`
5. Production (Railway): `railway run alembic upgrade head`

⚠️ **NEVER** use `Base.metadata.create_all()` - Alembic only

### Deployment (Railway)

- Push to main triggers auto-deploy
- Verify: Check Railway dashboard logs
- Rollback: `railway rollback` or redeploy previous commit
- Env vars: Set in Railway dashboard, NOT in code

---

## Critical Don't-Miss Rules

> **Quick reference for the gotchas that break builds. Scan before implementing.**

### Version Constraints (Will Break If Wrong)

| Constraint | Correct | Wrong |
|------------|---------|-------|
| bcrypt | `bcrypt==4.0.1` | Any 4.1+ (passlib breaks) |
| SQLAlchemy | `Mapped[str]` | `Column(String)` |
| React Query | `useQuery({ queryKey, queryFn })` | `useQuery(key, fn)` |
| Anthropic | `client.messages.create()` | `client.completions.create()` |
| Next.js nav | `next/navigation` | `next/router` |
| idb | `await db.get()` | callbacks |

### Copy-Paste Patterns

```python
# Anthropic API (messages, not completions)
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[{"role": "user", "content": prompt}]
)

# Error response
raise HTTPException(status_code=404, detail="Not found")
```

```typescript
// React Query v5
useQuery({ queryKey: ['recipes', id], queryFn: () => fetchRecipe(id) })

// Provider order (matters!)
<QueryProvider>
  <AuthProvider>
    <OfflineProvider>
      <FavouritesProvider>
```

### Absolute Never List

| Action | Consequence |
|--------|-------------|
| `Base.metadata.create_all()` in prod | Bypasses migrations, schema drift |
| Hardcode DATABASE_URL | Credentials in git |
| Mock fetch directly | Tests break on API changes |
| Business logic in routers | Untestable, unmaintainable |
| `@pytest.mark.asyncio` | Redundant, asyncio_mode=auto |
| Import describe/it/expect in vitest | Globals enabled, will error |
| New CORS origin without main.py update | Silent 403 failures |

---

## Admin Panel Patterns

> Added 2026-01-08. See `docs/admin-panel-architecture.md` for full details.

### Admin Authorization

**Backend - Use `require_admin` dependency:**
```python
from app.dependencies import require_admin

@router.post("/admin/categories/templates")
async def create_template(
    data: CategoryCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)  # Returns 403 if not admin
):
    return CategoryService.create(db, "template", data, admin.id)
```

**Frontend - Check `isAdmin` from AuthContext:**
```typescript
const { user } = useAuth();

// Guard admin routes
if (!user?.is_admin) {
  return <Navigate to="/" />;
}

// Conditional admin UI
{user?.is_admin && <AdminNavLink />}
```

### Role-Based Caching

```typescript
// Admin views: 1 minute (frequent updates)
useCategories({ staleTime: 60_000 })

// User views: 5 minutes (stable data)
useCategories({ staleTime: 300_000 })

// Pattern: derive from auth context
const staleTime = user?.is_admin ? 60_000 : 300_000;
```

### Fire-and-Forget Audit Logging

```python
# Audit failures NEVER block the main operation
def update_category(db, category_id, data, admin_id):
    old_state = get_category(db, category_id)
    result = perform_update(db, category_id, data)

    # Fire and forget - catch and log failures
    try:
        AuditService.log(
            action="category_update",
            entity_type="category",
            entity_id=category_id,
            old_state=old_state.model_dump(),
            new_state=result.model_dump(),
            user_id=admin_id
        )
    except Exception as e:
        logger.error(f"Audit log failed: {e}")  # Don't re-raise!

    return result
```

**Required test case:**
```python
def test_audit_failure_does_not_block_operation(test_db, mock_audit_failure):
    """Verify category creation succeeds even if audit logging fails."""
    # Arrange: mock audit service to raise
    mock_audit_failure.side_effect = Exception("DB connection lost")

    # Act: create category
    result = CategoryService.create(test_db, "template", valid_data, admin_id)

    # Assert: operation succeeded despite audit failure
    assert result.id is not None
```

### Category Table Naming

```python
# All category tables use category_ prefix
category_templates      # Not 'templates'
category_glassware      # Not 'glassware'
category_serving_styles # Not 'serving_styles'
category_methods        # Not 'methods'
category_ice_types      # Not 'ice_types'
```

### Audit Action Naming

```python
# Pattern: {entity}_{verb}
# Entities: category, user, recipe
# Verbs: create, update, delete, merge

"category_create"   # ✅
"create_category"   # ❌
"CategoryCreate"    # ❌
```

### Migration Sequence (Admin Panel)

When running admin panel migrations, execute in this order:
1. `add_user_admin_fields` - Add `is_admin`, `is_active` to users
2. `create_category_tables` - Create 5 category tables
3. `seed_categories_from_enums` - Populate from existing enums
4. `add_category_indexes` - Performance indexes
5. `create_audit_log_table` - Audit logging infrastructure

### Adversarial Code Review Guidance

> Added from Epic 2 Retrospective (2026-04-08). Calibrates expectations for multi-round reviews.

- Review Rounds 1-2 catch real bugs (crash bugs, security gaps, missing error handling). These findings are high-value.
- Review Round 3+ tends to find polish/refactoring items (method signature cleanup, null validators, naming consistency). Still valuable, but evaluate by **actual impact**, not severity label.
- The adversarial mandate to "always find 3-10 problems" can inflate severity labels on later rounds. Reviewers should be honest about actual severity.
- Pre-review checklist reduces high-severity findings but doesn't eliminate edge-case bugs — those require adversarial thinking.

### Pre-Review Verification Checklist

> Added from Epic 1 Retrospective (2026-04-08). Every story must pass this checklist before marking "ready for review." These items were the top code review findings across all 6 Epic 1 stories.

**Test Quality Verification:**

- [ ] Run `coverage report --include=<new/modified files>` — verify every new function/method has actual test coverage (not just test names that sound right)
- [ ] For every endpoint with `require_admin` or `get_current_user`: verify there is a **401 test** (no token) AND a **403 test** (regular user token)
- [ ] For every `HTTPException` raised in new code: verify there is a test that triggers that exact error path
- [ ] Test names describe the **behavior** being tested, not just the function name (e.g., `test_delete_returns_403_for_non_admin` not `test_delete_recipe`)

**Code Quality Verification:**

- [ ] Run `git status` — check for untracked new files that should be committed
- [ ] Any service method that does INSERT with a unique constraint MUST handle `IntegrityError` and return the appropriate HTTP error (e.g., 409) instead of letting a 500 propagate
- [ ] Verify docstrings/comments match the actual code (not copy-pasted from a previous story)

**Coverage Verification Command:**

```bash
# Run after implementation, before requesting review
coverage run -m pytest tests/test_<your_new_test_file>.py
coverage report --include="app/<files_you_changed>.py"
# Expect 100% on new code paths
```

### Defensive Coding Patterns

> Added from Epic 1 Retrospective (2026-04-08), updated from Epic 2 & 3 Retrospectives.

**SQLAlchemy `flush()` Before Delete (MANDATORY when modifying + deleting related records):**
```python
# When deleting a parent record after modifying/deleting related FK rows,
# db.flush() is required BEFORE db.delete() to prevent ORM FK nullification.

# ❌ WRONG — ORM may nullify FKs on related rows even after you updated them
for child in children:
    child.parent_id = new_parent_id
db.delete(old_parent)  # ORM re-nullifies child.parent_id!

# ✅ RIGHT — flush commits child changes to DB before parent delete
for child in children:
    child.parent_id = new_parent_id
db.flush()  # Persist child changes first
db.delete(old_parent)  # Now safe — children already point elsewhere
db.commit()
```

**Service→Router Error Convention (MANDATORY for all services):**
```python
# Services use these patterns consistently:
# - return None → caller raises 404 or 409
# - raise ValueError → caller catches and raises 400
# - raise LookupError → caller catches and raises 404

# ❌ WRONG — returning error strings, caller does string matching
return "Target not found"  # Fragile — message change breaks routing

# ✅ RIGHT — exceptions with clear semantics
raise LookupError("Target not found")   # → 404
raise ValueError("Cannot do X to self") # → 400
return None                              # → 404 or 409 depending on context
```

**SAVEPOINT Isolation for Fire-and-Forget Operations (MANDATORY when flushing inside another transaction):**
```python
# When a secondary operation (e.g., audit logging) calls db.flush() inside
# the caller's transaction, a flush failure leaves the session in
# PendingRollbackError state — poisoning the caller's already-committed work.
# Use db.begin_nested() (SAVEPOINT) to isolate the secondary operation.

# ❌ WRONG — flush failure poisons the entire session
try:
    entry = AuditLog(...)
    db.add(entry)
    db.flush()  # If this fails, caller's session is now broken
except Exception:
    pass  # Session is in PendingRollbackError — next db operation crashes

# ✅ RIGHT — SAVEPOINT isolates the failure
try:
    with db.begin_nested():  # Creates a SAVEPOINT
        entry = AuditLog(...)
        db.add(entry)
        # flush happens at SAVEPOINT exit
    # On failure, only the SAVEPOINT rolls back — caller's session is clean
except Exception as e:
    logger.error(f"Secondary operation failed: {e}")  # Session still usable
```

**When to use `db.begin_nested()`:**

- Any `db.flush()` or `db.add()` inside a try/except within another transaction
- Fire-and-forget patterns (audit logging, notifications, analytics)
- Any operation where failure should NOT roll back the caller's work

**Unique Constraint Handling (MANDATORY for all create/insert operations):**
```python
from sqlalchemy.exc import IntegrityError

def create(db: Session, data: CreateSchema) -> Model | None:
    record = Model(**data.model_dump())
    db.add(record)
    try:
        db.commit()
        db.refresh(record)
        return record
    except IntegrityError:
        db.rollback()
        return None  # Caller returns 409

# In router:
result = service.create(db, data)
if result is None:
    raise HTTPException(status_code=409, detail="Value already exists")
```

**Auth Test Pattern (MANDATORY for all protected endpoints):**
```python
# For EVERY endpoint that uses require_admin or get_current_user,
# include BOTH of these tests:

def test_endpoint_returns_401_without_auth(client):
    """No token → 401."""
    response = client.get("/api/admin/resource")
    assert response.status_code == 401

def test_endpoint_returns_403_for_regular_user(client, auth_token):
    """Regular user token → 403."""
    response = client.get(
        "/api/admin/resource",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 403
```

### Admin Panel Don't-Miss Rules

| Action | Consequence |
|--------|-------------|
| Skip `require_admin` dependency | Any authenticated user can access admin |
| Raise in audit `except` block | Admin operations fail on audit errors |
| Use 5-min cache for admin views | Admins see stale data after changes |
| Forget migration order | Foreign key constraint violations |
| Name tables without `category_` prefix | Inconsistent schema, confusing queries |
| Skip pre-review checklist | Code review catches functional gaps → slower cycle |
| INSERT without IntegrityError handling | Race conditions cause 500 instead of 409 |
| Test only one auth rejection path | Missing 401 or 403 coverage = security gap |
| Return error strings from services | Fragile string-matching in router; use exceptions (ValueError/LookupError) |
| Skip `db.flush()` before deleting parent with modified children | ORM re-nullifies FK columns, corrupting related records |
| `db.flush()` inside try/except without `begin_nested()` | Session poisoning — PendingRollbackError kills caller's transaction |

