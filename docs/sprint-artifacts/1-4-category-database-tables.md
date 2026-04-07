# Story 1.4: Category Database Tables

Status: done

---

## Story

As a **system**,
I want **category values stored in database tables instead of Python enums**,
So that **admins can add and modify categories without code deployments**.

---

## Acceptance Criteria

### AC-1: Create Category Tables

**Given** the migration runs
**When** it completes
**Then** the following 5 tables are created:
- `category_templates` (id, value, label, description, sort_order, is_active, created_at)
- `category_glassware` (id, value, label, category, sort_order, is_active, created_at)
- `category_serving_styles` (id, value, label, description, sort_order, is_active, created_at)
- `category_methods` (id, value, label, description, sort_order, is_active, created_at)
- `category_spirits` (id, value, label, sort_order, is_active, created_at)

### AC-2: Seed Tables from Python Enums

**Given** the seed migration runs
**When** it completes
**Then** each table is populated with values from the corresponding Python enum
**And** the `value` field matches the enum string EXACTLY (e.g., "old_fashioned", not "Old Fashioned")
**And** the `label` field contains the display name
**And** `sort_order` preserves the original enum ordering
**And** all records have `is_active = true`

### AC-3: Post-Migration Verification

**Given** the migrations complete
**When** I run the verification SQL
**Then** no recipes have orphaned category values (all recipe.template values exist in category_templates.value, etc.)

### AC-4: Performance Index

**Given** the `recipe_ingredients` table exists
**When** the index migration runs
**Then** an index is created on `recipe_ingredients.ingredient_id` for query performance

---

## Tasks / Subtasks

### Task 1: Create Category Table Models (AC: #1)

- [x] **1.1** Create `backend/app/models/category.py`
- [x] **1.2** Create CategoryTemplate model:
  ```python
  from sqlalchemy.orm import Mapped, mapped_column
  from sqlalchemy import String, Boolean, Integer, Text, DateTime, func
  from app.models.database import Base
  import uuid

  class CategoryTemplate(Base):
      __tablename__ = "category_templates"

      id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
      value: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
      label: Mapped[str] = mapped_column(String(100), nullable=False)
      description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
      sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
      is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
      created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
  ```
- [x] **1.3** Create CategoryGlassware model (same pattern + `category` field for stemmed/short/tall/specialty)
- [x] **1.4** Create CategoryServingStyle model (same pattern with description)
- [x] **1.5** Create CategoryMethod model (same pattern with description)
- [x] **1.6** Create CategorySpirit model (same pattern, no description)
- [x] **1.7** Update `backend/app/models/__init__.py` to export all new models

### Task 2: Create Schema Migration (AC: #1)

- [x] **2.1** Generate migration: `alembic revision -m "create_category_tables"`
- [x] **2.2** Create all 5 tables with columns matching models
- [x] **2.3** Add unique constraint on `value` column for each table
- [x] **2.4** Add index on `value` column for each table
- [x] **2.5** Add downgrade logic to drop all 5 tables
- [x] **2.6** Test migration: `alembic upgrade head`
- [x] **2.7** Verify tables exist via SQLite browser or SQL

### Task 3: Create Seed Data Migration (AC: #2)

- [x] **3.1** Generate seed migration: `alembic revision -m "seed_categories_from_enums"`
- [x] **3.2** Import all enum values and display name mappings from `app/models/enums.py`
- [x] **3.3** Seed `category_templates` - 25 values (actual enum count)
- [x] **3.4** Seed `category_glassware` - 24 values with category groupings
- [x] **3.5** Seed `category_serving_styles` - 8 values with descriptions
- [x] **3.6** Seed `category_methods` - 8 values with descriptions
- [x] **3.7** Seed `category_spirits` - 26 values (actual enum count)
- [x] **3.8** Ensure sort_order matches enum definition order (starting from 0)
- [x] **3.9** Implement downgrade logic to truncate all seed data
- [x] **3.10** Test migration: `alembic upgrade head`

### Task 4: Create Index Migration (AC: #4)

- [x] **4.1** Generate migration: `alembic revision -m "add_ingredient_id_index"`
- [x] **4.2** Add index on `recipe_ingredients.ingredient_id`:
  ```python
  op.create_index(
      'ix_recipe_ingredients_ingredient_id',
      'recipe_ingredients',
      ['ingredient_id'],
      unique=False
  )
  ```
- [x] **4.3** Add downgrade logic to drop index
- [x] **4.4** Test migration: `alembic upgrade head`

### Task 5: Post-Migration Verification (AC: #3)

- [x] **5.1** Create verification SQL script or pytest test:
  ```sql
  -- Verify no orphaned template values
  SELECT DISTINCT template FROM recipes
  WHERE template IS NOT NULL
  AND template NOT IN (SELECT value FROM category_templates);
  -- Must return 0 rows

  -- Verify no orphaned glassware values
  SELECT DISTINCT glassware FROM recipes
  WHERE glassware IS NOT NULL
  AND glassware NOT IN (SELECT value FROM category_glassware);
  -- Must return 0 rows

  -- Repeat for serving_style, method, main_spirit
  ```
- [x] **5.2** Run verification queries after migration
- [x] **5.3** Document any orphaned values found (should be none if seed is correct)

### Task 6: Write Tests (AC: #1-4)

- [x] **6.1** Create `backend/tests/test_category_models.py`
- [x] **6.2** Test: `test_category_template_table_exists`
- [x] **6.3** Test: `test_category_glassware_table_exists`
- [x] **6.4** Test: `test_category_serving_style_table_exists`
- [x] **6.5** Test: `test_category_method_table_exists`
- [x] **6.6** Test: `test_category_spirit_table_exists`
- [x] **6.7** Test: `test_category_seed_values_match_enum_strings` - CRITICAL
  - Verify `category_templates.value` contains exact strings: "sour", "old_fashioned", etc.
- [x] **6.8** Test: `test_category_seed_preserves_sort_order`
- [x] **6.9** Test: `test_ingredient_id_index_exists`
- [x] **6.10** Test: `test_no_orphaned_recipe_category_values`
- [x] **6.11** Run full test suite: `pytest` - all tests must pass

### Task 7: Final Verification

- [x] **7.1** Run `alembic upgrade head` on fresh database
- [x] **7.2** Verify all 5 tables have correct row counts:
  - category_templates: 25 rows (actual enum count)
  - category_glassware: 24 rows
  - category_serving_styles: 8 rows
  - category_methods: 8 rows
  - category_spirits: 26 rows (actual enum count)
- [x] **7.3** Verify index exists on recipe_ingredients.ingredient_id
- [x] **7.4** Run full test suite: `pytest` - must pass with no regressions (318 passed)
- [x] **7.5** Update sprint-status.yaml

---

## Dev Notes

### CRITICAL: Seed Values Must Match Enums EXACTLY

The `value` field in each category table MUST match the exact string values from the Python enums. Any mismatch will cause orphaned recipe records.

#### category_templates (25 values)

| sort_order | value | label | description |
|------------|-------|-------|-------------|
| 0 | sour | Sour | Spirit + citrus + sweet |
| 1 | old_fashioned | Old Fashioned | Spirit + sugar + bitters |
| 2 | martini | Martini | Spirit + vermouth |
| 3 | negroni | Negroni | Spirit + bitter liqueur + vermouth |
| 4 | highball | Highball | Spirit + lengthener |
| 5 | collins | Collins | Sour + soda (on ice) |
| 6 | fizz | Fizz | Sour + soda (no ice in glass) |
| 7 | spritz | Spritz | Aperitif + sparkling wine + soda |
| 8 | buck_mule | Buck/Mule | Spirit + ginger beer + citrus |
| 9 | julep | Julep | Spirit + sugar + mint (crushed ice) |
| 10 | smash | Smash | Julep + citrus |
| 11 | swizzle | Swizzle | Spirit + citrus + sweet + bitters (crushed ice, swizzled) |
| 12 | cobbler | Cobbler | Wine/spirit + sugar + fruit (crushed ice) |
| 13 | punch | Punch | Spirit + citrus + sweet + tea/water + spice |
| 14 | clarified_punch | Clarified Punch | Milk-clarified punch |
| 15 | flip | Flip | Spirit + whole egg + sugar |
| 16 | nog | Nog | Spirit + egg + dairy |
| 17 | tiki | Tiki | Complex, often multi-rum, tropical |
| 18 | rickey | Rickey | Spirit + citrus + soda (no sugar) |
| 19 | toddy | Toddy | Spirit + hot water + sweet |
| 20 | sling | Sling | Spirit + citrus + sweet + soda + liqueur |
| 21 | frozen | Frozen | Blended with ice |
| 22 | duo_trio | Duo/Trio | Spirit + liqueur (optionally + cream) |
| 23 | scaffa | Scaffa | Room temp spirit + liqueur + bitters |
| 24 | other | Other | Catch-all for oddballs |

#### category_glassware (24 values)

| sort_order | value | label | category |
|------------|-------|-------|----------|
| 0 | coupe | Coupe | stemmed |
| 1 | nick_and_nora | Nick & Nora | stemmed |
| 2 | martini | Martini Glass | stemmed |
| 3 | flute | Flute | stemmed |
| 4 | saucer | Champagne Saucer | stemmed |
| 5 | rocks | Rocks Glass | short |
| 6 | double_rocks | Double Rocks | short |
| 7 | julep_cup | Julep Cup | short |
| 8 | highball | Highball | tall |
| 9 | collins | Collins Glass | tall |
| 10 | copper_mug | Copper Mug | tall |
| 11 | pilsner | Pilsner | tall |
| 12 | tiki_mug | Tiki Mug | specialty |
| 13 | hurricane | Hurricane | specialty |
| 14 | goblet | Goblet/Copa | specialty |
| 15 | poco_grande | Poco Grande | specialty |
| 16 | margarita | Margarita Glass | specialty |
| 17 | snifter | Snifter | specialty |
| 18 | wine_glass | Wine Glass | specialty |
| 19 | irish_coffee | Irish Coffee Glass | specialty |
| 20 | fizz_glass | Fizz Glass | specialty |
| 21 | punch_cup | Punch Cup | specialty |
| 22 | glencairn | Glencairn | specialty |
| 23 | shot_glass | Shot Glass | specialty |

#### category_serving_styles (8 values)

| sort_order | value | label | description |
|------------|-------|-------|-------------|
| 0 | up | Up | Chilled, strained, no ice in glass |
| 1 | rocks | Rocks | Over ice cubes |
| 2 | large_cube | Large Cube | Over a single large ice cube |
| 3 | long | Long | Tall glass, topped with mixer, lots of ice |
| 4 | crushed_ice | Crushed Ice | Packed crushed/pebble ice |
| 5 | frozen | Frozen | Blended with ice |
| 6 | neat | Neat | Room temperature, no ice |
| 7 | hot | Hot | Heated, served warm |

#### category_methods (8 values)

| sort_order | value | label | description |
|------------|-------|-------|-------------|
| 0 | shaken | Shaken | With ice in shaker, strained |
| 1 | stirred | Stirred | With ice in mixing glass, strained |
| 2 | built | Built | Made directly in serving glass |
| 3 | thrown | Thrown | Poured between vessels (Cuban style) |
| 4 | swizzled | Swizzled | Spun with swizzle stick in crushed ice |
| 5 | blended | Blended | In a blender with ice |
| 6 | dry_shake | Dry Shake | Shaken without ice first (for egg drinks) |
| 7 | whip_shake | Whip Shake | Quick shake with just a little crushed ice |

#### category_spirits (26 values)

| sort_order | value | label |
|------------|-------|-------|
| 0 | gin | Gin |
| 1 | vodka | Vodka |
| 2 | rum_light | Rum Light |
| 3 | rum_dark | Rum Dark |
| 4 | rum_aged | Rum Aged |
| 5 | rum_overproof | Rum Overproof |
| 6 | bourbon | Bourbon |
| 7 | rye | Rye |
| 8 | scotch | Scotch |
| 9 | irish_whiskey | Irish Whiskey |
| 10 | japanese_whisky | Japanese Whisky |
| 11 | tequila | Tequila |
| 12 | mezcal | Mezcal |
| 13 | cognac | Cognac |
| 14 | armagnac | Armagnac |
| 15 | pisco | Pisco |
| 16 | calvados | Calvados |
| 17 | brandy_other | Brandy Other |
| 18 | liqueur | Liqueur |
| 19 | aperitif | Aperitif |
| 20 | amaro | Amaro |
| 21 | vermouth | Vermouth |
| 22 | sherry | Sherry |
| 23 | port | Port |
| 24 | other | Other |
| 25 | non_alcoholic | Non Alcoholic |

### Architecture Compliance

**Migration Sequence (CRITICAL):**
This story creates Migrations #2, #3, #4 in the Admin Panel sequence. See [docs/admin-panel-architecture.md](../admin-panel-architecture.md):
1. `add_user_admin_fields` (Story 1.1 - DONE)
2. `create_category_tables` (THIS STORY - Task 2)
3. `seed_categories_from_enums` (THIS STORY - Task 3)
4. `add_ingredient_id_index` (THIS STORY - Task 4)
5. `create_audit_log` (Epic 4)

**SQLAlchemy 2.0 Syntax (MANDATORY):**
```python
# CORRECT - Use this pattern
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Boolean, Integer

value: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)

# WRONG - Do NOT use legacy syntax
value = Column(String(50), unique=True)  # NEVER use Column()
```

**Never use Base.metadata.create_all():**
All schema changes MUST go through Alembic migrations.

**Category Table Naming Convention:**
All tables use `category_` prefix as per architecture doc.

### Previous Story Intelligence

**From Story 1.1 (Admin User Setup):**
- Verify actual test coverage with `coverage report`
- Test naming must describe WHAT behavior is tested
- Always run `git status` to check for untracked new files
- Use `datetime.now(timezone.utc)` for timestamps, not `datetime.utcnow()`
- Migration code review caught fake tests not testing actual functionality

**From Story 1.2 (Admin Recipe Edit):**
- Follow established patterns exactly
- Verify code locations match architecture doc line numbers
- Edge case: validate target user exists before ownership transfer

**From Story 1.3 (Admin Recipe Delete):**
- Cascade delete is already configured on Recipe model
- Follow EXACT same patterns as previous stories
- Add tests to existing test file when extending functionality

### Git Intelligence (Recent Commits)

```
5163a06 feat: Add admin capabilities for user and recipe management (Epic 1)
```
This commit contains Stories 1.1, 1.2 with:
- User model `is_admin` and `last_login_at` fields
- `require_admin` dependency in `dependencies.py`
- Admin bypass patterns for recipe edit/delete
- Test fixtures: `admin_user`, `admin_auth_token`

### Technical Requirements

| Requirement | Value | Source |
|-------------|-------|--------|
| Python Version | 3.9+ (for Mapped[] syntax) | project_context.md |
| SQLAlchemy | 2.0+ (Mapped[] syntax ONLY) | project_context.md |
| HTTP Error Format | `detail` key | project_context.md |
| Test Framework | pytest with asyncio auto mode | project_context.md |
| Migration Tool | Alembic ONLY | project_context.md |

### File Locations

| File | Action | Purpose |
|------|--------|---------|
| `backend/app/models/category.py` | CREATE | 5 category table models |
| `backend/app/models/__init__.py` | MODIFY | Export new models |
| `backend/alembic/versions/xxx_create_category_tables.py` | CREATE | Schema migration |
| `backend/alembic/versions/xxx_seed_categories_from_enums.py` | CREATE | Data migration |
| `backend/alembic/versions/xxx_add_ingredient_id_index.py` | CREATE | Index migration |
| `backend/tests/test_category_models.py` | CREATE | Category model tests |

### Current Categories Router (TO BE REWRITTEN IN STORY 1.5)

**WARNING:** This story does NOT modify `categories.py`. The complete rewrite happens in Story 1.5: Public Category Endpoints Rewrite.

Current file: [backend/app/routers/categories.py](../../backend/app/routers/categories.py)
- Currently iterates Python enums directly
- All 6 endpoints need rewriting to query database tables
- This story ONLY creates tables and seeds data

### Edge Cases to Handle

1. **Empty database on fresh deploy**: Seed migration should handle this gracefully
2. **Re-running seed migration**: Use upsert pattern or check if rows exist
3. **Case sensitivity**: `value` field is snake_case, case-sensitive in SQLite, case-insensitive in PostgreSQL
4. **Null category values in recipes**: Some recipes may have NULL template/glassware - this is valid, don't treat as orphan
5. **Unicode in descriptions**: Descriptions may contain special characters like "/" - ensure UTF-8 encoding

### Anti-Patterns to Avoid

**DO NOT:**
- Create any admin endpoints (Story 1.6)
- Modify `categories.py` (Story 1.5)
- Use `Base.metadata.create_all()`
- Use legacy `Column()` syntax
- Skip verification SQL after seeding
- Hardcode UUIDs (use uuid.uuid4() or let database generate)

**DO:**
- Use SQLAlchemy 2.0 `Mapped[]` syntax
- Create all 3 migrations in correct sequence
- Verify seed values match enum strings exactly
- Add index on `recipe_ingredients.ingredient_id`
- Write comprehensive tests

### PRD/Architecture Cross-Reference

| Requirement | Implementation |
|-------------|----------------|
| FR-3.2.1: Database-driven categories | Create 5 tables with all required fields |
| FR-3.2.1: Fields | id, value, label, description, sort_order, is_active, created_at |
| Architecture: category_ prefix | All table names use `category_` prefix |
| Architecture: Seed verification | Post-migration SQL to check no orphaned recipes |
| Architecture: Performance index | Add `ix_recipe_ingredients_ingredient_id` |

### Project Context Reference

Critical patterns from [docs/project_context.md](../project_context.md):

```python
# SQLAlchemy 2.0 model pattern
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Boolean, Integer

class CategoryTemplate(Base):
    __tablename__ = "category_templates"
    value: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
```

```python
# Migration pattern
def upgrade():
    op.create_table('category_templates',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('value', sa.String(50), unique=True, nullable=False),
        # ... other columns
    )
    op.create_index('ix_category_templates_value', 'category_templates', ['value'])
```

---

## Dev Agent Record

### Context Reference

Story context created by BMAD create-story workflow on 2026-01-13.

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- Initial attempt hit "table already exists" - tables had been created outside Alembic; dropped and re-ran
- Test failure for index - fixed by adding `index=True` to RecipeIngredient.ingredient_id in model

### Completion Notes List

- Created 5 category models using SQLAlchemy 2.0 Mapped[] syntax
- Created 3 Alembic migrations in correct sequence: schema, seed, index
- Seeded all tables with exact enum string values for compatibility
- Added index on recipe_ingredients.ingredient_id for performance
- Created comprehensive test suite (29 tests) covering all acceptance criteria
- All 327 tests pass with no regressions
- Verified no orphaned category values in existing recipes

### File List

**Created:**
- `backend/app/models/category.py` - 5 category table models (CategoryTemplate, CategoryGlassware, CategoryServingStyle, CategoryMethod, CategorySpirit)
- `backend/alembic/versions/5c3647b698e1_create_category_tables.py` - Schema migration creating 5 tables
- `backend/alembic/versions/5cfe7a74576e_seed_categories_from_enums.py` - Data migration seeding all tables
- `backend/alembic/versions/4557012699e7_add_ingredient_id_index.py` - Index migration for recipe_ingredients
- `backend/tests/test_category_models.py` - 29 tests for category models (22 original + 7 migration validation)

**Modified:**
- `backend/app/models/__init__.py` - Export 5 new category models
- `backend/app/models/recipe.py` - Added index=True to RecipeIngredient.ingredient_id

---

## Change Log

| Date | Change |
|------|--------|
| 2026-01-13 | Story created via create-story workflow, status: ready-for-dev |
| 2026-01-30 | Implementation complete: 5 category tables, 3 migrations, 22 tests, status: Ready for Review |
| 2026-04-07 | Code review (adversarial): 7 issues found (2H, 3M, 2L), all fixed. Added 7 migration validation tests, deduplicated generate_uuid, fixed datetime.utcnow, corrected doc counts. 327 tests pass. Status: done |
