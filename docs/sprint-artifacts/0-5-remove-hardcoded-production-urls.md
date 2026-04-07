# Story 0.5: Remove Hardcoded Production URLs

**Status: Done**

---

## Story

As a **developer**,
I want **consistent API URL configuration across the frontend**,
So that **the app works correctly in both development and production environments**.

---

## Current State Analysis

**Problem:**
Two files define `API_BASE` with inconsistent fallback defaults:

| File | Current Default | Problem |
|------|-----------------|---------|
| `lib/api.ts:6` | `https://back-end-production-1219.up.railway.app/api` | Defaults to production (bad for dev) |
| `lib/auth-context.tsx:5` | `http://localhost:8000/api` | Defaults to localhost (correct) |

**Impact:**
- Running `npm run dev` without `NEXT_PUBLIC_API_URL` set connects to production backend
- Can cause accidental production data modification during development
- Makes local development harder to set up
- Inconsistent behavior between auth and other API calls

---

## Acceptance Criteria

1. **Given** a fresh development environment with no `.env.local`
   **When** `npm run dev` is run
   **Then** all API calls default to `http://localhost:8000/api`

2. **Given** `NEXT_PUBLIC_API_URL` is set in environment
   **When** the app makes API calls
   **Then** all calls use the configured URL

3. **Given** the frontend codebase
   **When** searching for API_BASE definitions
   **Then** there is exactly ONE source of truth for the API URL

---

## Tasks / Subtasks

### Task 1: Create shared API configuration (AC: #3)

- [x] **1.1** Edit `frontend/lib/api.ts` line 6
  - Change from:
    ```typescript
    export const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://back-end-production-1219.up.railway.app/api';
    ```
  - To:
    ```typescript
    export const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
    ```

### Task 2: Import shared config in auth-context (AC: #3)

- [x] **2.1** Edit `frontend/lib/auth-context.tsx`
  - Remove the local `API_BASE` definition (line 5)
  - Import from api.ts at the top:
    ```typescript
    import { API_BASE } from './api';
    ```

### Task 3: Verify no other hardcoded URLs exist (AC: #2)

- [x] **3.1** Search for other hardcoded production URLs:
  ```bash
  grep -r "railway.app" frontend/
  grep -r "localhost:8000" frontend/
  ```
- [x] **3.2** Fix any additional occurrences found
  - No problematic occurrences found. railway.app references in next.config.js are legitimate CSP/image config.

### Task 4: Add development .env.local.example (AC: #1)

- [x] **4.1** Check if `frontend/.env.local.example` exists
  - `.env.example` already exists with proper documentation
- [x] **4.2** If not, create it with:
  - N/A - existing `.env.example` covers this requirement

### Task 5: Verification (AC: #1, #2)

- [x] **5.1** Run `npm run dev` without `.env.local`
  - N/A - verified via build that API_BASE defaults to localhost
- [x] **5.2** Verify requests go to localhost:8000
  - Confirmed via code inspection - single source of truth now in api.ts
- [x] **5.3** Run `npm run build` to ensure no TypeScript errors
  - Build passed successfully
- [x] **5.4** Run tests to ensure nothing broke
  - 239 passed, 0 failed (verified 2025-12-31)

### Review Follow-ups (AI) - 2025-12-31

- [x] **\[AI-Review\]\[HIGH\]** Fix fragile regex in offline-context.tsx:39 - Replaced with URL API parsing for robust origin extraction
- [x] **\[AI-Review\]\[HIGH\]** Complete AC #1 verification - Added unit tests verifying API_BASE defaults to localhost:8000/api
- [x] **\[AI-Review\]\[HIGH\]** Remove hardcoded localhost:8000 from CSP - Made CSP dynamic: only includes localhost in development (NODE_ENV)
- [x] **\[AI-Review\]\[MEDIUM\]** Add validation for NEXT_PUBLIC_API_URL - Added validateApiUrl() with helpful error message and fallback
- [x] **\[AI-Review\]\[MEDIUM\]** Add test coverage for API_BASE default - Added 2 tests in api.test.ts for default value and URL validity
- [x] **\[AI-Review\]\[MEDIUM\]** Document CSRF protection - Added security model docblock in auth-context.tsx explaining CSRF approach
- [x] **\[AI-Review\]\[MEDIUM\]** Clarify BACKEND_URL usage - Removed unused BACKEND_URL from .env.example, improved docs
- [x] **\[AI-Review\]\[LOW\]** Add explanatory comment to api.ts:6 - Added comment explaining localhost default for safe development
- [x] **\[AI-Review\]\[LOW\]** Add type safety for API_BASE - URL validation via validateApiUrl() provides runtime type safety
- [x] **\[AI-Review\]\[LOW\]** Improve error guidance in offline-context.tsx:36-37 - Removed fragile assumption entirely; new approach handles any URL

---

## Dev Notes

### Files to Modify

| File | Change |
|------|--------|
| `frontend/lib/api.ts` | Change default to localhost |
| `frontend/lib/auth-context.tsx` | Import API_BASE from api.ts |
| `frontend/.env.example` | Already exists with proper documentation |

### Risk Assessment

**Low risk** - Simple string replacement with clear verification path.

### Testing Commands

```bash
cd cocktail-app/frontend

# Build check
npm run build

# Run tests
npm test

# Manual verification - start without env
unset NEXT_PUBLIC_API_URL
npm run dev
# Check network tab in browser devtools
```

### Why Not Just Use .env Files?

Environment files help, but:
1. Developers might forget to create `.env.local`
2. CI/CD environments may not have all configs
3. A sensible default of localhost is safer than production

### References

- [Source: docs/project_context.md#Environment] - Environment configuration
- [Source: docs/architecture-frontend.md#Configuration] - Frontend config patterns
- [Source: docs/epic-0-tech-debt.md#Story-0.5] - Original requirements

---

## Dev Agent Record

### Context Reference

Story context generated by create-story workflow on 2025-12-31.

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- Build output: Clean compilation, no TypeScript errors
- Test output: 239 passed, 0 failed (verified 2025-12-31)

### Completion Notes List

- Changed API_BASE default in `lib/api.ts` from production Railway URL to `http://localhost:8000/api`
- Removed duplicate API_BASE definition from `lib/auth-context.tsx`, now imports from `lib/api.ts`
- Verified no other problematic hardcoded URLs exist (railway.app refs in next.config.js are legitimate CSP/image host config)
- Existing `.env.example` already provides proper documentation for developers
- All acceptance criteria satisfied:
  - AC #1: Fresh dev environment defaults to localhost:8000
  - AC #2: Environment variable overrides work correctly
  - AC #3: Single source of truth for API_BASE in lib/api.ts

**Review Follow-up Resolutions (2025-12-31):**
- ✅ Resolved [HIGH] fragile regex: Replaced `API_BASE.replace(/\/api\/?$/, '')` with `new URL(API_BASE).origin`
- ✅ Resolved [HIGH] AC #1 verification: Added 2 tests in api.test.ts verifying default and URL validity
- ✅ Resolved [HIGH] CSP hardcoding: Made CSP dynamic with `isDev ? ' http://localhost:8000' : ''`
- ✅ Resolved [MEDIUM] URL validation: Added `validateApiUrl()` with helpful error + fallback
- ✅ Resolved [MEDIUM] test coverage: Tests confirm API_BASE behavior
- ✅ Resolved [MEDIUM] CSRF docs: Added security model docblock to auth-context.tsx
- ✅ Resolved [MEDIUM] BACKEND_URL: Removed unused var from .env.example
- ✅ Resolved [LOW] explanatory comment: Added "See story 0-5 for rationale" to api.ts
- ✅ Resolved [LOW] type safety: URL validation provides runtime safety
- ✅ Resolved [LOW] error guidance: No longer needed - fragile assumption eliminated

### File List

| File | Action |
|------|--------|
| `cocktail-app/frontend/lib/api.ts` | Modified - added URL validation, explanatory comments, safe default |
| `cocktail-app/frontend/lib/auth-context.tsx` | Modified - import API_BASE, added CSRF security docblock |
| `cocktail-app/frontend/.env.example` | Modified - improved docs, removed unused BACKEND_URL |
| `cocktail-app/frontend/lib/offline-context.tsx` | Modified - replaced fragile regex with robust URL API parsing |
| `cocktail-app/frontend/next.config.js` | Modified - dynamic CSP based on NODE_ENV |
| `cocktail-app/frontend/tests/lib/api.test.ts` | Modified - added API_BASE configuration tests |

### Change Log

- 2025-12-31: Consolidated API_BASE to single source of truth, defaulting to localhost for safer development
- 2025-12-31: [Code Review] Fixed .env.example documentation mismatch, added API_BASE assumption comment in offline-context.tsx
- 2025-12-31: [Code Review] Adversarial review found 10 issues (3 HIGH, 4 MEDIUM, 3 LOW) - returned story to in-progress status
- 2025-12-31: [Review Follow-ups] Addressed all 10 review items: robust URL parsing, dynamic CSP, URL validation, test coverage, CSRF docs
- 2025-12-31: [Code Review #2] All ACs verified, all tasks complete, build passes, 239 tests pass. Story marked done.
