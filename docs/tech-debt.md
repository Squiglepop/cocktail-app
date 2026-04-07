# Tech Debt Backlog

_Generated from code review on 2025-12-31_

---

## TD-1: JWT Tokens Stored in localStorage (XSS Vulnerable)
**Severity:** HIGH
**Effort:** Medium
**Files:** `frontend/lib/auth-context.tsx`

**Problem:** Tokens stored in `localStorage` can be stolen via XSS attacks. The project_context.md says "Token in memory, passed explicitly" but implementation uses localStorage.

**Options:**
1. **httpOnly cookies** - Backend sets cookie, frontend doesn't handle token directly. Requires CORS/cookie config changes.
2. **sessionStorage** - Slightly better (cleared on tab close) but still XSS-vulnerable.
3. **Memory-only with refresh tokens** - Token in React state, short expiry, refresh token in httpOnly cookie.

**Recommendation:** Option 3 if you want proper security, Option 1 if simpler.

---

## TD-2: Long JWT Expiry Without Refresh Tokens
**Severity:** MEDIUM
**Effort:** Medium
**Files:** `backend/app/config.py`, `backend/app/services/auth.py`, `frontend/lib/auth-context.tsx`

**Problem:** `access_token_expire_minutes = 60 * 24 * 7` (7 days). If token is compromised, attacker has a week of access.

**Fix:**
- Reduce access token to 15-30 minutes
- Implement refresh token endpoint (`/auth/refresh`)
- Frontend silently refreshes before expiry

**Note:** Often tackled together with TD-1.

---

## TD-3: Backend Tests Broken - Missing Dependency
**Severity:** MEDIUM
**Effort:** Low (5 min)
**Files:** `backend/requirements.txt` or venv

**Problem:**
```
ModuleNotFoundError: No module named 'filetype'
```

**Fix:**
```bash
cd backend && source venv/bin/activate && pip install filetype
```

Or ensure `filetype` is in `requirements.txt` (it should be - just needs venv reinstall).

---

## TD-4: Frontend Tests Failing (41 of 237)
**Severity:** MEDIUM
**Effort:** Low-Medium
**Files:** `frontend/tests/setup.ts`, `frontend/vitest.config.ts`

**Problem:**
```
TypeError: URL.createObjectURL is not a function
```

Tests don't mock browser APIs properly.

**Fix:** Add to `tests/setup.ts`:
```typescript
global.URL.createObjectURL = vi.fn(() => 'blob:mock-url');
global.URL.revokeObjectURL = vi.fn();
```

---

## TD-5: Hardcoded Production URL Fallback
**Severity:** LOW
**Effort:** Low
**Files:** `frontend/lib/api.ts:6`, `frontend/lib/auth-context.tsx:5`

**Problem:**
```typescript
const API_BASE = process.env.NEXT_PUBLIC_API_URL ||
  'https://back-end-production-1219.up.railway.app/api';
```

Silent fallback to prod if env var missing. Could cause confusion during dev.

**Options:**
1. Throw error if env var missing in dev
2. Use `localhost:8000` as fallback instead
3. Leave as-is (it works, just surprising)

---

## TD-6: Ingredient Handling Code Duplication
**Severity:** LOW
**Effort:** Medium
**Files:** `backend/app/routers/upload.py`, `backend/app/routers/recipes.py`

**Problem:** The same "get-or-create ingredient + create RecipeIngredient" loop is copy-pasted 5+ times:
- `upload.py` lines 277-305, 430-457, 589-616
- `recipes.py` lines 442-471, 524-552

**Fix:** Extract to a service function:
```python
# services/recipe_service.py
def add_ingredients_to_recipe(db: Session, recipe: Recipe, ingredients_data: List[IngredientInput]) -> None:
    ...
```

---

## Summary

| ID | Issue | Severity | Effort |
|----|-------|----------|--------|
| TD-1 | localStorage tokens | HIGH | Medium |
| TD-2 | Long JWT expiry | MEDIUM | Medium |
| TD-3 | Backend tests broken | MEDIUM | Low |
| TD-4 | Frontend tests failing | MEDIUM | Low-Medium |
| TD-5 | Hardcoded prod URL | LOW | Low |
| TD-6 | Code duplication | LOW | Medium |

**Quick wins:** TD-3, TD-4, TD-5
**Tackle together:** TD-1 + TD-2 (auth overhaul)
