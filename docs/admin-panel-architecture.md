---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
inputDocuments:
  - docs/admin-panel-prd.md
  - docs/project_context.md
  - docs/architecture-backend.md
workflowType: 'architecture'
lastStep: 8
status: 'complete'
completedAt: '2026-01-08'
project_name: 'Cocktail Shots - Admin Panel'
user_name: 'Deemo'
date: '2026-01-08'
hasProjectContext: true
---

# Admin Panel Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

---

## Project Context Analysis

### Requirements Overview

**Functional Requirements:**

- Admin Role Management: Single admin flag model with first-user-is-admin pattern
- Category Management: 5 database tables replacing Python enums with full CRUD
- Ingredient Management: CRUD for ingredient master list + duplicate detection + merge
- Recipe Management: Admin bypass for edit/delete ownership checks
- User Management: List, activate/deactivate, grant/revoke admin
- Audit Logging: Track all admin actions with entity state changes

**Non-Functional Requirements:**

- Security: Admin-only endpoints, rate limiting, self-protection
- Performance: Category caching with invalidation, <200ms response targets
- Data Integrity: Soft delete for categories, hard delete for recipes, usage checks

**Scale & Complexity:**

- Primary domain: Full-stack (FastAPI + Next.js)
- Complexity level: Medium
- Estimated components: 9 (5 category tables + ingredients admin + user fields + audit log + admin service)

### Technical Constraints & Dependencies

- SQLAlchemy 2.0 `Mapped[]` syntax required
- Alembic migrations only (never `create_all()`)
- Extend existing JWT auth system
- bcrypt pinned to 4.0.x for passlib compatibility
- React Query v5 object syntax on frontend
- Ingredient table already exists — no schema migration needed
- **Category seed values must match existing enum strings EXACTLY**

### Cross-Cutting Concerns

1. **Admin Authorization**: `require_admin` FastAPI dependency
2. **Cache Strategy**: React Query invalidation on category/ingredient mutations
3. **Audit Service**: Centralized logging for all admin actions
4. **Migration Sequencing**: User → Categories → Audit (critical order)
5. **Usage Checks**: Check recipe references before deleting categories/ingredients

### Code Analysis Findings

**Breaking Changes:**

- `categories.py` requires COMPLETE REWRITE — currently iterates Python enums, no DB queries
- All 6 category endpoints affected

**Modifications Required:**

- `recipes.py` lines 539-550, 631-642: Add admin bypass to ownership checks
- Pattern: `if recipe.user_id != current_user.id and not is_admin:`

**Missing Index (Performance):**

- `recipe_ingredients.ingredient_id` has NO INDEX
- Ingredient usage check will be full table scan without it
- Add migration: `op.create_index('ix_recipe_ingredients_ingredient_id', ...)`

**Safe Components:**

- Recipe model (categories stored as strings, no FK)
- Ingredient model (schema matches PRD)
- RecipeIngredient junction table
- Auth system (just add `is_admin` field)
- Image storage (no changes)

**Critical Verification:**

```sql
-- After seeding, verify no orphaned recipes:
SELECT DISTINCT template FROM recipes
WHERE template NOT IN (SELECT value FROM category_templates);
-- Must return 0 rows
```

### Ingredient Merge/Duplicate Implementation Notes

**Technical Decisions:**

- Use `difflib.SequenceMatcher` (stdlib) — no new dependencies
- Transaction safety covered by SQLAlchemy session
- Add explicit rollback test for merge failures

**Test Requirements:**

- 14 new test cases for duplicate detection + merge
- Edge cases: 0-usage merge, bulk merge 5+, same-recipe duplicate handling

**UX Requirements:**

- Duplicate list needs pagination/sort (by impact)
- Merge preview modal required before confirmation
- "Skip" button for false positives
- No undo needed — audit log sufficient

**Performance Note:**

- Duplicate detection is O(n²) — acceptable for <1000 ingredients
- Consider caching or background job if ingredient list grows significantly

### Implementation Checklist

**Phase 1: User Model (6 items)**

- Add `is_admin`, `last_login_at` fields
- Migration + data migration for first user
- `require_admin` dependency
- Admin test fixtures

**Phase 2: Recipe Admin (5 items)**

- Admin bypass in update_recipe()
- Admin bypass in delete_recipe()
- Test coverage for admin paths

**Phase 3: Categories (9 items)**

- 5 category tables with seed migrations
- Rewrite categories.py for DB queries
- Add ingredient_id index
- Admin CRUD endpoints

**Phase 4: Ingredients (6 items)**

- Paginated list endpoint
- CRUD with usage checks
- Duplicate detection endpoint
- Merge endpoint with preview
- Test coverage (14 cases)

**Phase 5: User Management + Audit (8 items)**

- User list with pagination
- Activate/deactivate endpoints
- Admin grant/revoke
- Audit log table + service
- Audit log viewer

### Summary Metrics

| Metric | Count |
|--------|-------|
| Functional Requirement Areas | 6 |
| Breaking Changes | 1 (categories.py) |
| New Endpoints | ~15 |
| Test Cases Required | 35+ |
| New Dependencies | 0 |
| Migrations Required | ~8 |

---

## Starter Template Evaluation

### Status: Not Applicable (Brownfield Project)

This is a feature addition to an existing application, not a greenfield project.

**Existing Technology Stack:**

| Layer | Technology | Version |
|-------|------------|---------|
| Backend Runtime | Python | 3.9+ |
| Backend Framework | FastAPI | 0.104+ |
| ORM | SQLAlchemy | 2.0+ (Mapped[] syntax) |
| Migrations | Alembic | 1.12+ |
| Auth | JWT + bcrypt | 4.0.x (pinned) |
| Frontend Runtime | Node.js | 18+ |
| Frontend Framework | Next.js | 14 (App Router) |
| UI Library | React | 18 |
| Language | TypeScript | 5.3+ (strict mode) |
| Styling | Tailwind CSS | 3.4+ |
| Server State | React Query | v5 (object syntax) |
| Backend Testing | pytest | asyncio auto mode |
| Frontend Testing | vitest | globals enabled |
| Database (dev) | SQLite | - |
| Database (prod) | PostgreSQL | - |

**Architectural Patterns Already Established:**

- Layered backend: Router → Service → Model
- React Query for server state management
- App Router file-based routing
- Alembic-only database migrations
- JWT access/refresh token authentication

**No starter template selection required.** Architecture decisions will extend the existing patterns documented in `docs/project_context.md`.

---

## Core Architectural Decisions

### Foundational Decisions (Pre-Existing)

| Category | Decision | Source |
|----------|----------|--------|
| Database | PostgreSQL (prod) / SQLite (dev) | Project Context |
| ORM | SQLAlchemy 2.0 Mapped[] syntax | Project Context |
| Migrations | Alembic only | Project Context |
| Auth Method | JWT access/refresh tokens | Existing code |
| API Style | REST with FastAPI | Existing code |
| Frontend Framework | Next.js 14 App Router | Project Context |
| State Management | React Query v5 | Project Context |
| Category Tables | Separate per type (not polymorphic) | Context Analysis |
| First User Admin | Auto-set via migration | Context Analysis |
| Fuzzy Matching | `difflib.SequenceMatcher` (stdlib) | Party Mode |
| Ingredient Auto-Create | Keep existing behavior (AI can create new) | Context Analysis |

### Admin Panel Decisions (Step 4)

| # | Category | Decision | Rationale |
|---|----------|----------|-----------|
| 1 | Category Caching | React Query with role-based staleTime | Admin: 1 min, Users: 5 min — fresher data for admins without hammering DB |
| 2 | Rate Limiting | slowapi (FastAPI middleware) | Python-native decorators, in-memory default, Redis-upgradeable later |
| 3 | Admin State (Frontend) | Extend AuthContext with `isAdmin` | Single source of truth, `is_admin` is fundamentally an auth property |
| 4 | Audit Log Storage | Same database, dedicated table | Simple queries, joins available, low volume doesn't warrant external service |
| 5 | Audit Atomicity | Fire-and-forget pattern | Audit failure must not block admin operations |

### Implementation Notes

**Category Caching:**
```typescript
// Conditional staleTime based on admin status
useCategories({ staleTime: isAdmin ? 60000 : 300000 })
```
- Invalidate via `queryClient.invalidateQueries(['categories'])` on admin mutations
- No backend caching layer needed

**Rate Limiting:**
- Install: `pip install slowapi`
- Initialize in `main.py`: `Limiter(key_func=get_remote_address)`
- Apply to admin endpoints: `@limiter.limit("10/minute")`
- If multi-instance scaling needed later, swap to Redis backend (no code changes)

**Admin State:**
- Add `is_admin: boolean` to User type in frontend
- Backend `/me` endpoint returns `is_admin` field
- AuthContext exposes via `const { user } = useAuth(); user?.is_admin`

**Audit Logging:**
```python
# Fire-and-forget pattern
try:
    AuditService.log(action, entity, old_state, new_state)
except Exception as e:
    logger.error(f"Audit log failed: {e}")  # Don't block operation
```
- Table columns: `id`, `timestamp`, `admin_user_id`, `action`, `entity_type`, `entity_id`, `old_state`, `new_state`
- Retention policy deferred — revisit if table exceeds 100k rows

**Deferred:**
- Audit log viewer UI → Phase 5 design task

### Party Mode Findings (Round 2)

**From Amelia (Dev):**
- Decisions are implementation-ready
- slowapi: ~5 lines in main.py
- AuthContext extension: minimal change
- Audit service: ~80 lines new code total

**From Sally (UX):**
- Role-based caching approved
- Admin badge in nav now trivial: `{user?.is_admin && <AdminBadge />}`
- Audit viewer: paginated table with date/action/entity filters (Phase 5)

**From Murat (TEA):**
- New test case required: `test_audit_failure_does_not_block_operation`
- Mock `AuditService.log()` to raise exception
- Verify admin action still succeeds
- Verify error is logged (not swallowed silently)

---

## Implementation Patterns & Consistency Rules

> **Note:** General patterns are established in `docs/project_context.md`. This section covers only NEW patterns specific to the admin panel.

### Admin Authorization Pattern

All admin-only endpoints must use the `require_admin` dependency:

```python
from app.dependencies import require_admin

@router.post("/categories/templates")
async def create_template(
    data: CategoryCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)  # Enforces admin check
):
    # admin variable is the verified admin user
```

**Implementation of `require_admin`:**

```python
# app/dependencies.py
async def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
```

### Category Table Naming

All 5 new category tables use `category_` prefix:

| Table Name | Purpose |
|------------|---------|
| `category_templates` | Cocktail template/family |
| `category_glassware` | Glass types |
| `category_spirits` | Spirit types |
| `category_serving_styles` | Serving style options |
| `category_methods` | Preparation methods |

**Schema pattern:**

```python
class CategoryTemplate(Base):
    __tablename__ = "category_templates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    value: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    label: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
```

### Audit Action Naming

Action names follow `{entity}_{verb}` pattern in snake_case:

| Action | Description |
|--------|-------------|
| `category_create` | New category added |
| `category_update` | Category modified |
| `category_delete` | Category soft-deleted |
| `ingredient_create` | New ingredient added |
| `ingredient_update` | Ingredient modified |
| `ingredient_delete` | Ingredient deleted |
| `ingredient_merge` | Ingredients merged |
| `user_activate` | User activated |
| `user_deactivate` | User deactivated |
| `user_grant_admin` | Admin granted |
| `user_revoke_admin` | Admin revoked |
| `recipe_admin_update` | Admin edited another user's recipe |
| `recipe_admin_delete` | Admin deleted another user's recipe |

### Rate Limiting Decorator Order

Rate limiter decorates AFTER route decorator:

```python
@router.post("/admin/ingredients/merge")
@limiter.limit("10/minute")  # ← After @router
async def merge_ingredients(...):
```

### Enforcement Guidelines

**All AI Agents MUST:**

1. Use `require_admin` dependency for all `/admin/*` endpoints
2. Follow `category_` prefix for category table names
3. Use `{entity}_{verb}` pattern for audit actions
4. Apply rate limiter after route decorator
5. Reference `docs/project_context.md` for all other patterns

---

## Project Structure & Boundaries

> This section shows NEW files/directories for the admin panel. Existing project structure is preserved.

### Backend Additions

```
backend/app/
├── models/
│   ├── __init__.py              # UPDATE: export new models
│   ├── user.py                  # MODIFY: add is_admin, last_login_at
│   ├── category.py              # ✨ NEW: 5 category table models
│   └── audit_log.py             # ✨ NEW: AuditLog model
├── schemas/
│   ├── __init__.py              # UPDATE: export new schemas
│   ├── admin.py                 # ✨ NEW: admin-specific schemas
│   ├── category.py              # ✨ NEW: CategoryCreate/Update/Response
│   ├── ingredient.py            # ✨ NEW: IngredientAdmin schemas
│   └── user.py                  # ✨ NEW: UserAdmin schemas
├── routers/
│   ├── admin.py                 # MODIFY: expand with full admin routes
│   └── categories.py            # MODIFY: rewrite for DB queries
├── services/
│   ├── admin_service.py         # ✨ NEW: Admin business logic
│   ├── audit_service.py         # ✨ NEW: Audit logging service
│   └── ingredient_service.py    # ✨ NEW: Duplicate detection, merge
└── dependencies.py              # ✨ NEW: require_admin dependency

backend/alembic/versions/
├── xxx_add_user_admin_fields.py       # ✨ NEW
├── xxx_create_category_tables.py      # ✨ NEW (5 tables)
├── xxx_seed_categories.py             # ✨ NEW (data migration)
├── xxx_create_audit_log.py            # ✨ NEW
└── xxx_add_ingredient_id_index.py     # ✨ NEW

backend/tests/
├── test_admin_auth.py           # ✨ NEW: require_admin tests
├── test_categories_db.py        # ✨ NEW: Category CRUD tests
├── test_ingredient_admin.py     # ✨ NEW: Duplicate/merge tests (14 cases)
├── test_user_admin.py           # ✨ NEW: User management tests
└── test_audit_service.py        # ✨ NEW: Audit logging tests
```

### Frontend Additions

```
frontend/
├── app/
│   └── admin/                   # ✨ NEW: Admin section
│       ├── page.tsx             # Admin dashboard
│       ├── layout.tsx           # Admin layout with nav
│       ├── categories/
│       │   └── page.tsx         # Category management
│       ├── ingredients/
│       │   └── page.tsx         # Ingredient management
│       └── users/
│           └── page.tsx         # User management
├── components/
│   ├── Header.tsx               # MODIFY: add AdminBadge conditional
│   └── admin/                   # ✨ NEW: Admin components
│       ├── AdminBadge.tsx
│       ├── CategoryTable.tsx
│       ├── CategoryModal.tsx
│       ├── IngredientTable.tsx
│       ├── DuplicatesList.tsx
│       ├── MergePreviewModal.tsx
│       ├── UserTable.tsx
│       └── AuditLogTable.tsx
├── lib/
│   ├── api.ts                   # MODIFY: add admin API functions
│   ├── auth-context.tsx         # MODIFY: add isAdmin to user type
│   └── hooks/
│       ├── use-admin-categories.ts   # ✨ NEW
│       ├── use-admin-ingredients.ts  # ✨ NEW
│       └── use-admin-users.ts        # ✨ NEW
└── tests/
    └── admin/                   # ✨ NEW: Admin tests
        ├── categories.test.tsx
        ├── ingredients.test.tsx
        └── users.test.tsx
```

### Requirements → Structure Mapping

| PRD Requirement | Backend Location | Frontend Location |
|-----------------|------------------|-------------------|
| FR-1: Admin Role | `models/user.py`, `dependencies.py` | `lib/auth-context.tsx` |
| FR-2: Category CRUD | `routers/admin.py`, `models/category.py` | `app/admin/categories/` |
| FR-3: Recipe Admin | `routers/recipes.py` (modify lines 539-550, 631-642) | — (uses existing edit page) |
| FR-3.5: Ingredient Admin | `services/ingredient_service.py` | `app/admin/ingredients/` |
| FR-4: User Management | `routers/admin.py`, `schemas/user.py` | `app/admin/users/` |
| FR-5: Audit Logging | `services/audit_service.py`, `models/audit_log.py` | `components/admin/AuditLogTable.tsx` |

### Architectural Boundaries

**API Boundaries:**

- All admin endpoints: `/api/admin/*`
- Protected by: `require_admin` dependency
- Rate limited: slowapi decorators
- Public category endpoints remain at `/api/categories/*` (read-only)

**Component Boundaries:**

- Admin UI isolated in `app/admin/` (Next.js App Router)
- Admin components in `components/admin/`
- Admin hooks in `lib/hooks/use-admin-*.ts`
- Shared components (Header) conditionally render admin elements

**Data Boundaries:**

- Category tables: `category_templates`, `category_glassware`, `category_spirits`, `category_serving_styles`, `category_methods`
- Audit logs: `audit_logs` table
- User fields: `is_admin`, `last_login_at` added to existing `users` table
- No FK changes to `recipes` table (categories stored as strings)

### Migration Sequence (Critical)

Migrations must run in this order due to dependencies:

1. `xxx_add_user_admin_fields.py` — Add `is_admin`, `last_login_at` to users
2. `xxx_create_category_tables.py` — Create 5 category tables
3. `xxx_seed_categories.py` — Seed from existing enum values
4. `xxx_add_ingredient_id_index.py` — Performance index
5. `xxx_create_audit_log.py` — Audit log table (references users)

---

## Architecture Validation Results

### Coherence Validation ✅

**Decision Compatibility:**

- SQLAlchemy 2.0 + Alembic: Compatible
- FastAPI + slowapi: Compatible
- React Query v5 + Next.js 14: Compatible
- bcrypt 4.0.x + passlib: Pinned correctly

**Pattern Consistency:**

- All naming follows `docs/project_context.md`
- Admin patterns extend existing auth system
- Rate limiter decorator order documented

**No contradictory decisions identified.**

### Requirements Coverage Validation ✅

| PRD Requirement | Architectural Support |
|-----------------|----------------------|
| FR-1: Admin Role Management | `is_admin` field, `require_admin` dependency |
| FR-2: Category Management | 5 category tables, CRUD endpoints |
| FR-3: Recipe Admin Bypass | Modify `recipes.py` lines 539-550, 631-642 |
| FR-3.5: Ingredient Admin | `ingredient_service.py`, duplicate/merge |
| FR-4: User Management | Admin endpoints for activate/deactivate/grant/revoke |
| FR-5: Audit Logging | `audit_logs` table, fire-and-forget pattern |
| NFR: Rate Limiting | slowapi middleware |
| NFR: <200ms Response | React Query caching, `ingredient_id` index |

**All requirements covered.**

### Implementation Readiness Validation ✅

| Check | Status |
|-------|--------|
| Migration sequence defined | ✅ 5 migrations in order |
| Test cases identified | ✅ 36+ cases total |
| Breaking changes documented | ✅ `categories.py` rewrite |
| Code locations specified | ✅ Line numbers for recipe bypass |
| Seed verification SQL | ✅ Post-migration check included |

### Gap Analysis

**Critical Gaps:** None

**Important Gaps (Acceptable):**

- Audit log viewer UI → Deferred to Phase 5
- E2E tests → Can add post-MVP

### Party Mode Findings (Final Review)

**From Amelia (Dev):**

- Migration sequence confirmed correct
- `categories.py` full rewrite required (currently iterates enums)
- Recipe bypass: simple condition change

**From Sally (UX):**

- Admin dashboard should include quick stats:
  - Total users count
  - Total recipes count
  - Recent audit entries (last 5)
  - Pending ingredient duplicates indicator
- `layout.tsx` handles route protection + sidebar nav

**From Murat (TEA):**

- 36 test cases mapped to requirements
- Added: `test_category_seed_matches_enum_values()` for migration verification

### Architecture Completeness Checklist

**✅ Requirements Analysis**

- [x] Project context thoroughly analyzed
- [x] Scale and complexity assessed
- [x] Technical constraints identified
- [x] Cross-cutting concerns mapped

**✅ Architectural Decisions**

- [x] Critical decisions documented with versions
- [x] Technology stack fully specified
- [x] Integration patterns defined
- [x] Performance considerations addressed

**✅ Implementation Patterns**

- [x] Naming conventions established
- [x] Structure patterns defined
- [x] Communication patterns specified
- [x] Process patterns documented

**✅ Project Structure**

- [x] Complete directory structure defined
- [x] Component boundaries established
- [x] Integration points mapped
- [x] Requirements to structure mapping complete

### Architecture Readiness Assessment

**Overall Status:** READY FOR IMPLEMENTATION

**Confidence Level:** HIGH

**Key Strengths:**

- Brownfield project with established patterns
- Zero new dependencies (except slowapi)
- Low-risk migration strategy (no FK changes to recipes)
- Comprehensive test coverage planned

**Areas for Future Enhancement:**

- Redis for rate limiting (if multi-instance scaling needed)
- Audit log retention policy (if table grows large)
- Admin dashboard analytics (post-MVP)

---

## Architecture Completion Summary

### Workflow Completion

**Architecture Decision Workflow:** COMPLETED ✅
**Total Steps Completed:** 8
**Date Completed:** 2026-01-08
**Document Location:** `docs/admin-panel-architecture.md`

### Final Architecture Deliverables

**Complete Architecture Document:**

- 15 architectural decisions documented
- 5 admin-specific implementation patterns defined
- ~25 new files/directories specified
- 6 PRD requirements fully supported
- 36+ test cases identified

**Implementation Ready Foundation:**

- Migration sequence defined (5 migrations)
- Breaking changes documented (`categories.py` rewrite)
- Code modification locations specified (line numbers)
- Seed verification SQL provided

### Implementation Handoff

**For AI Agents:**

This architecture document is your complete guide for implementing the Cocktail Shots Admin Panel. Follow all decisions, patterns, and structures exactly as documented.

**First Implementation Priority:**

1. Create migration: `xxx_add_user_admin_fields.py`
2. Add `is_admin` and `last_login_at` to User model
3. Create `require_admin` dependency in `dependencies.py`

**Development Sequence:**

1. Phase 1: User admin fields + `require_admin` dependency
2. Phase 2: Recipe admin bypass (modify `recipes.py`)
3. Phase 3: Category tables + rewrite `categories.py`
4. Phase 4: Ingredient admin (duplicate detection, merge)
5. Phase 5: User management + Audit logging

---

**Architecture Status:** READY FOR IMPLEMENTATION ✅

**Next Phase:** Create epics and stories using `/bmad:bmm:workflows:create-epics-stories`

