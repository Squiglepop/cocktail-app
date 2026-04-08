# Story 2.2: Ingredient Duplicate Detection

Status: Done

---

## Story

As an **admin**,
I want **to see potential duplicate ingredients detected automatically**,
So that **I can identify and clean up inconsistencies from AI extraction**.

---

## Acceptance Criteria

### AC-1: Duplicate Detection Endpoint

**Given** I am authenticated as an admin
**When** I call `GET /api/admin/ingredients/duplicates`
**Then** I receive groups of potential duplicate ingredients

### AC-2: Case-Insensitive Exact Match

**Given** the duplicate detection runs
**When** two ingredients have case-insensitive exact match (e.g., "Lime Juice" vs "lime juice")
**Then** they are grouped as duplicates
**And** the detection reason is "exact_match_case_insensitive"

### AC-3: Fuzzy Match

**Given** the duplicate detection runs
**When** two ingredients have >80% similarity (SequenceMatcher)
**Then** they are grouped as duplicates
**And** the detection reason is "fuzzy_match" with similarity score

### AC-4: Variation Pattern Match

**Given** the duplicate detection runs
**When** two ingredients match common variation patterns (e.g., "Fresh Lime Juice" vs "Lime Juice", "Lime Juice (fresh)" vs "Lime Juice")
**Then** they are grouped as duplicates
**And** the detection reason is "variation_pattern"

### AC-5: Duplicate Group Details

**Given** a duplicate group is returned
**When** I view the group
**Then** it includes:
- Suggested target (ingredient with highest usage count)
- List of potential duplicates with similarity scores
- Detection reason for each match
- Usage count for each ingredient

### AC-6: Authorization

**Given** I am NOT an admin (regular user or unauthenticated)
**When** I call `GET /api/admin/ingredients/duplicates`
**Then** I receive 401 (no token) or 403 (regular user)

---

## Tasks / Subtasks

### Task 1: Create Duplicate Detection Schemas (AC: #1, #5)

- [x] **1.1** Add schemas to `backend/app/schemas/ingredient.py`:
  - `DuplicateMatch`: `ingredient_id` (str), `name` (str), `type` (str), `similarity_score` (float), `detection_reason` (str — "exact_match_case_insensitive" | "fuzzy_match" | "variation_pattern"), `usage_count` (int)
  - `DuplicateGroup`: `target` (DuplicateMatch — ingredient with highest usage), `duplicates` (List[DuplicateMatch] — the other ingredients), `group_reason` (str — the highest-priority detection reason found among all pairs in the group, using priority: exact > variation > fuzzy)
  - `DuplicateDetectionResponse`: `groups` (List[DuplicateGroup]), `total_groups` (int), `total_duplicates` (int)
- [x] **1.2** Export new schemas from `backend/app/schemas/__init__.py`

### Task 2: Implement Duplicate Detection Service (AC: #2-5)

- [x] **2.1** Add duplicate detection functions to `backend/app/services/ingredient_service.py`:
  - `detect_duplicates(db) -> List[DuplicateGroup]` — orchestrates all three detection strategies
  - `_find_exact_case_matches(ingredients) -> List[tuple[Ingredient, Ingredient, float, str]]` — groups by `lower(name)` on **raw** (unnormalized) names, returns pairs with 2+ members. Each tuple: `(ingredient_a, ingredient_b, 1.0, "exact_match_case_insensitive")`. Use triangular iteration (`for i in range(n): for j in range(i+1, n)`) to avoid self-comparison and duplicate (A,B)/(B,A) pairs.
  - `_find_fuzzy_matches(ingredients, threshold=0.8) -> List[tuple[Ingredient, Ingredient, float, str]]` — pairwise `SequenceMatcher` on `lower(name)`, returns pairs above threshold. Each tuple: `(ingredient_a, ingredient_b, ratio, "fuzzy_match")`. **CRITICAL:** Use triangular iteration (`for i in range(n): for j in range(i+1, n)`) — a naive full loop compares ingredients with themselves (ratio=1.0, false match) and generates duplicate pairs.
  - `_find_variation_matches(ingredients) -> List[tuple[Ingredient, Ingredient, float, str]]` — normalizes names via `_normalize_for_variation()` (see Dev Notes), then matches on normalized forms. Each tuple: `(ingredient_a, ingredient_b, 1.0, "variation_pattern")`. Use triangular iteration. Note: this detects "Fresh Lime Juice" vs "Lime Juice" as a variation, NOT as an exact match — exact match only operates on raw names.
  - `_normalize_for_variation(name: str) -> str` — **Lowercase FIRST**, then strip prefixes, suffixes, and parentheticals. Returns cleaned name for comparison. Order matters: lowercasing before stripping ensures "FRESH Lime Juice" matches "Lime Juice".
  - `_build_groups(usage_counts, exact_matches, fuzzy_matches, variation_matches) -> List[DuplicateGroup]` — merges matches from all three strategies, deduplicates pairs (same pair found by multiple strategies uses priority: exact > variation > fuzzy), uses Union-Find to build connected components (if A matches B and B matches C, group {A, B, C}), picks target by highest usage count, builds response schemas
- [x] **2.2** Use `difflib.SequenceMatcher` (stdlib) — **NO new dependencies**
- [x] **2.3** Load ALL ingredients once, run detection in-memory (not per-pair DB queries)
- [x] **2.4** Export new functions from `backend/app/services/__init__.py`

### Task 3: Add Duplicate Detection Endpoint (AC: #1, #6)

- [x] **3.1** Add endpoint to `backend/app/routers/admin.py`:
  - `GET /admin/ingredients/duplicates` — returns `DuplicateDetectionResponse`
  - **Router responsibility:** The service returns `List[DuplicateGroup]`. The **router** wraps it into `DuplicateDetectionResponse` by computing `total_groups = len(groups)` and `total_duplicates = sum(len(g.duplicates) for g in groups)`. This keeps the service layer free of HTTP/response concerns.
  - CRITICAL: Place this route BEFORE `GET /admin/ingredients/{id}` to avoid path conflict (FastAPI matches routes in order — `/duplicates` would match `{id}` if placed after)
  - Uses `require_admin` + `get_db` via `Depends`
- [x] **3.2** Import `detect_duplicates` from ingredient_service
- [x] **3.3** Import `DuplicateDetectionResponse` in admin.py

### Task 4: Write Tests (AC: #1-6)

- [x] **4.1** Create `backend/tests/test_ingredient_duplicates.py`
- [x] **4.2** Auth tests:
  - `test_duplicates_returns_401_without_auth`
  - `test_duplicates_returns_403_for_regular_user`
- [x] **4.3** Exact match tests:
  - `test_detects_case_insensitive_exact_match` (e.g., "Lime Juice" vs "lime juice")
  - `test_exact_match_shows_correct_reason` (reason = "exact_match_case_insensitive")
- [x] **4.4** Fuzzy match tests:
  - `test_detects_fuzzy_match_above_threshold` (e.g., "Lime Juice" vs "Lime Juic")
  - `test_ignores_fuzzy_match_below_threshold` (e.g., "Lime" vs "Vodka" — too different)
  - `test_fuzzy_match_includes_similarity_score`
- [x] **4.5** Variation pattern tests:
  - `test_detects_fresh_prefix_variation` (e.g., "Fresh Lime Juice" vs "Lime Juice")
  - `test_detects_parenthetical_variation` (e.g., "Lime Juice (fresh)" vs "Lime Juice")
- [x] **4.6** Group structure tests:
  - `test_target_is_highest_usage_count`
  - `test_group_includes_usage_counts`
  - `test_response_includes_total_counts`
- [x] **4.7** Detection reason priority tests:
  - `test_same_pair_uses_highest_priority_reason` (e.g., "lime juice" vs "Lime Juice" — detected by both exact and fuzzy, result must show "exact_match_case_insensitive")
- [x] **4.8** Edge case tests:
  - `test_no_duplicates_returns_empty` (all unique ingredients)
  - `test_zero_ingredients_returns_empty` (no ingredients in DB at all)
  - `test_single_ingredient_returns_empty` (only 1 ingredient — no pairs possible)
  - `test_multiple_duplicate_groups` (several groups detected at once)
  - `test_ingredient_appears_in_only_one_group` (no cross-group overlap)
  - `test_duplicates_detected_when_both_in_same_recipe` (two case-different ingredients both used in the same recipe — detection must still find them; matters for merge story 2.3)
  - `test_ingredient_matching_multiple_others_via_different_strategies` (e.g., "Fresh Lime Juice" matches "Lime Juice" via variation AND "Fresh lime juice" via exact — verify correct grouping and priority)
- [x] **4.9** Run full test suite: `pytest` — no regressions

### Task 5: Final Verification

- [x] **5.1** Run full backend test suite: `pytest`
- [x] **5.2** Verify all existing tests still pass (including 2-1 ingredient tests)
- [x] **5.3** Update `docs/sprint-artifacts/sprint-status.yaml` — mark 2-2 as done

---

## Dev Notes

### CRITICAL: Route Order in admin.py

FastAPI matches routes in declaration order. The existing `GET /admin/ingredients/{id}` will match `/admin/ingredients/duplicates` if the duplicates route is declared AFTER it (`duplicates` gets treated as an `{id}` value). **Place the duplicates endpoint BEFORE the `{id}` endpoint.**

```python
# CORRECT ORDER:
@router.get("/ingredients/duplicates", ...)   # <-- FIRST
@router.get("/ingredients/{id}", ...)          # <-- AFTER
```

### Use `difflib.SequenceMatcher` (stdlib)

Architecture doc explicitly says: "Use `difflib.SequenceMatcher` (stdlib) — no new dependencies." Do NOT install `python-Levenshtein`, `fuzzywuzzy`, `rapidfuzz`, or any third-party fuzzy matching library.

```python
from difflib import SequenceMatcher

ratio = SequenceMatcher(None, name_a.lower(), name_b.lower()).ratio()
if ratio > 0.8:
    # fuzzy match detected
```

### Variation Patterns to Detect

Common ingredient naming variations from AI extraction:

```python
import re

STRIP_PREFIXES = [
    "fresh ", "freshly squeezed ", "freshly pressed ",
]
STRIP_SUFFIXES = [
    " (fresh)", " (freshly squeezed)", " (chilled)",
]
PAREN_PATTERN = r'\s*\([^)]*\)\s*$'

def _normalize_for_variation(name: str) -> str:
    """CRITICAL: Lowercase FIRST, then strip. Order matters."""
    name = name.lower().strip()
    for prefix in STRIP_PREFIXES:
        if name.startswith(prefix):
            name = name[len(prefix):]
            break  # Only strip one prefix
    for suffix in STRIP_SUFFIXES:
        if name.endswith(suffix):
            name = name[:-len(suffix)]
            break
    name = re.sub(PAREN_PATTERN, '', name)
    return name.strip()
```

Compare `_normalize_for_variation(name_a) == _normalize_for_variation(name_b)` — if equal AND the raw names differ, it's a "variation_pattern" detection. If normalized forms are identical to the lowered raw names (no stripping happened), skip — that's an exact match, not a variation.

### In-Memory Detection Strategy

Load ALL ingredients in a single query, run detection in-memory. This avoids O(n^2) DB queries. Note: `_find_fuzzy_matches` is O(n^2) pairwise — acceptable for cocktail app scale (hundreds of ingredients), but would need optimization (e.g., blocking by first character) if ingredient count exceeds ~1000. Architecture doc mentions pagination for the duplicate list endpoint — intentionally omitted here because duplicate groups are expected to be small (<50 groups for <1000 ingredients). Frontend can sort/filter client-side in Story 5-4. Revisit if ingredient count grows significantly.

```python
def detect_duplicates(db: Session) -> list:
    all_ingredients = db.query(Ingredient).all()
    
    # Pre-compute usage counts in bulk
    usage_counts = dict(
        db.query(
            RecipeIngredient.ingredient_id,
            func.count(RecipeIngredient.id)
        ).group_by(RecipeIngredient.ingredient_id).all()
    )
    
    # Run detection strategies
    exact_matches = _find_exact_case_matches(all_ingredients)
    fuzzy_matches = _find_fuzzy_matches(all_ingredients, threshold=0.8)
    variation_matches = _find_variation_matches(all_ingredients)
    
    # Merge, deduplicate, build groups
    return _build_groups(all_ingredients, usage_counts, exact_matches, fuzzy_matches, variation_matches)
```

### Group Building Logic

1. Collect all match pairs from all three strategies — each pair is `(ingredient_a, ingredient_b, score, reason)`
2. **Deduplicate pairs:** The same pair (e.g., "Fresh Lime Juice" vs "Lime Juice") may be found by both variation AND fuzzy matchers. When the same `(id_a, id_b)` pair appears multiple times, keep only the highest-priority reason: exact > variation > fuzzy
3. **Transitive grouping via Union-Find:** If A matches B and B matches C, group {A, B, C}. Use a `parent: dict[str, str]` mapping ingredient IDs to group leaders. For each matched pair, union their groups. Then collect all ingredients sharing the same root leader into one group. This naturally prevents cross-group overlap.

```python
# Union-Find implementation sketch
parent = {ing.id: ing.id for ing in all_matched_ingredients}

def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]  # Path compression
        x = parent[x]
    return x

def union(a, b):
    ra, rb = find(a), find(b)
    if ra != rb:
        parent[ra] = rb

# Union all matched pairs
for ing_a, ing_b, score, reason in deduplicated_pairs:
    union(ing_a.id, ing_b.id)

# Collect groups by root
from collections import defaultdict
groups = defaultdict(list)
for ing_id in parent:
    groups[find(ing_id)].append(ing_id)
```

4. For each group, pick target = ingredient with highest `usage_counts.get(id, 0)`
5. Build `DuplicateMatch` objects for each non-target member with their detection reason and score
6. Set `group_reason` = highest-priority detection reason found among all pairs in the group

**Key distinction:** `_find_exact_case_matches` compares **raw** names. `_find_variation_matches` compares **normalized** names (after stripping prefixes/suffixes/parentheticals). They detect fundamentally different things — "lime juice" vs "Lime Juice" is exact; "Fresh Lime Juice" vs "Lime Juice" is variation.

### Priority Order for Detection Reasons

When the same pair is detected by multiple strategies, use this priority:
1. `exact_match_case_insensitive` (strongest signal)
2. `variation_pattern`
3. `fuzzy_match` (weakest — could be false positive)

### Extend Existing Files — DO NOT Create New Router/Service Files

| File | Action | What to Add |
|------|--------|-------------|
| `backend/app/schemas/ingredient.py` | MODIFY | Add 3 new schemas (DuplicateMatch, DuplicateGroup, DuplicateDetectionResponse) |
| `backend/app/schemas/__init__.py` | MODIFY | Export new schemas |
| `backend/app/services/ingredient_service.py` | MODIFY | Add detect_duplicates + helper functions |
| `backend/app/services/__init__.py` | MODIFY | Export detect_duplicates |
| `backend/app/routers/admin.py` | MODIFY | Add GET /admin/ingredients/duplicates endpoint (BEFORE {id} route) |
| `backend/tests/test_ingredient_duplicates.py` | CREATE | Duplicate detection tests |

### Test Fixture Strategy

Reuse existing `conftest.py` fixtures:
- `client` — TestClient with DB overrides
- `admin_auth_token` — JWT for admin user
- `auth_token` — JWT for regular user (for 403 tests)
- `sample_ingredient` — existing Tequila ingredient

Create test-local ingredients directly in each test to set up duplicate scenarios:

```python
def _create_ingredient(client, admin_auth_token, name, type="spirit"):
    return client.post(
        "/api/admin/ingredients",
        json={"name": name, "type": type},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
```

For usage count testing, use the `sample_recipe` fixture which links `sample_ingredient` to a recipe via RecipeIngredient.

### Auth Test Pattern (MANDATORY)

```python
def test_duplicates_returns_401_without_auth(client):
    response = client.get("/api/admin/ingredients/duplicates")
    assert response.status_code == 401

def test_duplicates_returns_403_for_regular_user(client, auth_token):
    response = client.get(
        "/api/admin/ingredients/duplicates",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 403
```

### No Audit Logging in This Story

Audit logging is Story 4-1. Do NOT add audit logging.

### No Frontend Changes in This Story

Frontend ingredient admin UI is Story 5-4. This story is backend-only.

### Project Structure Notes

- All changes extend existing files (except test file)
- No new dependencies — `difflib` is stdlib
- No database migrations — no schema changes
- Route order in admin.py is CRITICAL (duplicates before {id})

### Anti-Patterns to Avoid

**DO NOT:**
- Install third-party fuzzy matching libraries (use `difflib.SequenceMatcher`)
- Create a new router file for duplicates (extend `admin.py`)
- Create a new service file (extend `ingredient_service.py`)
- Make per-pair database queries for matching (load all, match in-memory)
- Place `/duplicates` route after `/{id}` route (path conflict)
- Use `@pytest.mark.asyncio` (asyncio_mode=auto)
- Import describe/it/expect in tests
- Add audit logging (Story 4-1)
- Modify existing CRUD functions in ingredient_service.py
- Add rate limiting

**DO:**
- Use `require_admin` dependency on the endpoint
- Use `detail` key in all HTTPExceptions
- Use existing test fixtures from conftest.py
- Use `difflib.SequenceMatcher` for fuzzy matching
- Load all ingredients once, match in-memory
- Pre-compute usage counts in bulk
- Handle edge case of 0 or 1 total ingredients (return empty groups)
- Strip/normalize ingredient names before comparison
- Deduplicate matches across strategies
- Prioritize detection reason: exact > variation > fuzzy

### References

- [Source: docs/admin-panel-prd.md#FR-3.5.4 — Duplicate Detection requirements]
- [Source: docs/admin-panel-prd.md#FR-3.5.5 — Ingredient Merge (next story, but informs response schema)]
- [Source: docs/epics.md#Story 2.2 — Acceptance criteria]
- [Source: docs/admin-panel-architecture.md — "Use difflib.SequenceMatcher (stdlib)", "14 new test cases for duplicate detection + merge"]
- [Source: docs/project_context.md#Admin Panel Patterns — auth patterns, defensive coding, pre-review checklist]
- [Source: backend/app/models/recipe.py:108-124 — Ingredient model]
- [Source: backend/app/models/recipe.py:127-152 — RecipeIngredient junction table]
- [Source: backend/app/services/ingredient_service.py — existing CRUD functions to extend]
- [Source: backend/app/routers/admin.py:171-258 — existing ingredient endpoints]
- [Source: backend/app/schemas/ingredient.py — existing schemas to extend]
- [Source: backend/tests/conftest.py — test fixtures]
- [Source: docs/sprint-artifacts/2-1-ingredient-admin-crud.md — previous story learnings]

### Previous Story Intelligence (2-1)

Key learnings from Story 2-1 code reviews:
- Code review caught: missing auth tests (401+403), race conditions on delete, LIKE wildcard escaping — ensure this story doesn't repeat those gaps
- `ingredient_type` param uses `Query(alias="type")` to avoid shadowing builtin — follow same pattern if adding query params
- Suite was at 412 tests after 2-1 completion (post code review #3) — verify no regression

### Git Intelligence

```
428b5ea fix: Use TRUE/FALSE instead of 1/0 in admin migration for PostgreSQL compatibility
7af9393 feat: Add admin category CRUD, reorder, and soft-delete endpoints (Story 1-6)
fcb86f7 feat: Rewrite public category endpoints to use database tables (Story 1-5)
```

All admin patterns established. This story is read-only (GET endpoint) — simpler than CRUD stories.

---

## Dev Agent Record

### Context Reference

Story context created by BMAD create-story workflow on 2026-04-08.

### Agent Model Used

Claude Opus 4.6 (1M context)

### Implementation Plan

- Three-strategy duplicate detection: exact case-insensitive, fuzzy (SequenceMatcher >0.8), variation pattern (prefix/suffix/parenthetical stripping)
- Union-Find for transitive grouping (A matches B, B matches C → group {A, B, C})
- Deduplication across strategies with priority: exact > variation > fuzzy
- All ingredients loaded once, matched in-memory (no per-pair DB queries)
- Usage counts pre-computed in bulk via GROUP BY
- Route placed BEFORE `{id}` to avoid FastAPI path conflict

### Debug Log References

- Tests initially failed because `create_ingredient` API rejects case-insensitive duplicates (409). Fixed by inserting test ingredients directly into DB via `_create_ingredient_db` helper.

### Completion Notes List

- Implemented `DuplicateMatch`, `DuplicateGroup`, `DuplicateDetectionResponse` schemas
- Added `detect_duplicates()` orchestrator + 5 helper functions to `ingredient_service.py`
- Added `GET /admin/ingredients/duplicates` endpoint with `require_admin` auth
- 20 new tests covering auth (401/403), all 3 detection strategies, group structure, reason priority, and 7 edge cases
- Full suite: 432 passed, 0 failed, 80% coverage

### Senior Developer Review (AI)

**Review Date:** 2026-04-08
**Reviewer:** Claude Opus 4.6 (adversarial code-review workflow)
**Outcome:** Changes Requested → Fixed

**Issues Found:** 0 High, 4 Medium, 3 Low — all resolved.

**Action Items:**

- [x] [M1] `detection_reason`/`group_reason` use bare `str` → add `Literal` type constraint
- [x] [M2] Fuzzy match tests missing `detection_reason` assertion → added
- [x] [M3] No unit tests for `_normalize_for_variation` edge cases → added 3 tests (freshly squeezed, chilled, freshly pressed)
- [x] [M4] `test_ignores_fuzzy_match_below_threshold` too trivial → added near-boundary threshold test
- [x] [L1] Unreachable dead code default in `_build_groups` → replaced with `next()` generator
- [x] [L2] `_find_variation_matches` generates redundant case-only pairs → added per-pair transform check
- [x] [L3] Target `similarity_score=1.0` semantics unclear → added Field description

**Post-Fix Results:** 454 passed, 0 failed, 80% coverage. ingredient_service.py at 99% coverage.

### Change Log

- 2026-04-08: Story 2-2 implemented — ingredient duplicate detection endpoint with 3-strategy detection, Union-Find grouping, and 20 tests
- 2026-04-08: Code review — 7 findings (4M, 3L) all fixed: Literal types on schema fields, fuzzy reason assertions, 4 new tests, dead code removal, variation pair optimization, field documentation

### File List

- `backend/app/schemas/ingredient.py` — MODIFIED (added DuplicateMatch, DuplicateGroup, DuplicateDetectionResponse; added Literal type + Field description)
- `backend/app/schemas/__init__.py` — MODIFIED (exported new schemas)
- `backend/app/services/ingredient_service.py` — MODIFIED (added detect_duplicates + 5 helpers; review fixes: dead code, variation optimization)
- `backend/app/services/__init__.py` — MODIFIED (exported detect_duplicates)
- `backend/app/routers/admin.py` — MODIFIED (added GET /admin/ingredients/duplicates endpoint)
- `backend/tests/test_ingredient_duplicates.py` — CREATED (24 tests: 20 original + 4 from review)
- `docs/sprint-artifacts/sprint-status.yaml` — MODIFIED (2-2 status → done)
