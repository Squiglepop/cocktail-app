# Story 0.4: Fix Frontend Test Mocks

**Status: done**

---

## Story

As a **developer**,
I want **frontend tests to pass**,
So that **we have reliable test coverage**.

---

## Current State Analysis

**Test Results (2025-12-31):**
- Total tests: **237**
- Passing: **172**
- Failing: **65**
- Target: **237/237 passing**

**Primary Issues:**
1. `TypeError: URL.createObjectURL is not a function` - Browser API not mocked
2. Missing MSW handlers for new auth endpoints (`/auth/refresh`, `/auth/logout`)
3. Missing `OfflineProvider` in test wrappers
4. React `act()` warnings (state updates outside of act)

---

## Acceptance Criteria

1. **Given** the test environment
   **When** `npm test` is run
   **Then** no `URL.createObjectURL is not a function` errors occur

2. **Given** all browser APIs are mocked
   **When** tests execute
   **Then** 237/237 tests pass (not 172/237)

3. **Given** the auth changes from Story 0.1
   **When** auth-related tests run
   **Then** new endpoints are properly mocked

---

## Tasks / Subtasks

### URL Mock Tasks (AC: #1)

- [x] **Task 1: Add URL.createObjectURL mock** (AC: #1)
  - [x] 1.1 Edit `frontend/tests/setup.ts`
  - [x] 1.2 Add URL mock after existing mocks:
    ```typescript
    // Mock URL.createObjectURL and URL.revokeObjectURL
    // Used by UploadDropzone for file previews
    Object.defineProperty(URL, 'createObjectURL', {
      writable: true,
      value: vi.fn((blob: Blob) => `blob:mock-url-${Math.random()}`),
    })

    Object.defineProperty(URL, 'revokeObjectURL', {
      writable: true,
      value: vi.fn(),
    })
    ```
  - [x] 1.3 Verify no TypeScript errors

### MSW Handler Tasks (AC: #3)

- [x] **Task 2: Add /auth/refresh handler** (AC: #3)
  - [x] 2.1 Edit `frontend/tests/mocks/handlers.ts`
  - [x] 2.2 Add after existing auth handlers:
    ```typescript
    http.post(`${API_BASE}/auth/refresh`, () => {
      // Return new access token (simulates cookie-based refresh)
      return HttpResponse.json({
        access_token: 'mock-jwt-token-refreshed',
        token_type: 'bearer',
      })
    }),
    ```
  - [x] 2.3 Add failure case handler for tests that need it:
    ```typescript
    // For tests that need refresh to fail
    http.post(`${API_BASE}/auth/refresh`, () => {
      return HttpResponse.json(
        { detail: 'No refresh token provided' },
        { status: 401 }
      )
    }, { once: true }),
    ```

- [x] **Task 3: Add /auth/logout handler** (AC: #3)
  - [x] 3.1 Add to handlers.ts:
    ```typescript
    http.post(`${API_BASE}/auth/logout`, () => {
      return HttpResponse.json({ message: 'Successfully logged out' })
    }),
    ```

### Test Wrapper Tasks (AC: #2)

- [x] **Task 4: Create comprehensive test wrapper** (AC: #2)
  - [x] 4.1 Check if `frontend/tests/utils/test-wrapper.tsx` exists
  - [x] 4.2 Create or update with all required providers:
    ```typescript
    import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
    import { AuthProvider } from '@/lib/auth-context'
    import { OfflineProvider } from '@/lib/offline-context'
    import { FavouritesProvider } from '@/lib/favourites-context'

    export function createTestWrapper() {
      const queryClient = new QueryClient({
        defaultOptions: {
          queries: { retry: false },
          mutations: { retry: false },
        },
      })

      return function TestWrapper({ children }: { children: React.ReactNode }) {
        return (
          <QueryClientProvider client={queryClient}>
            <AuthProvider>
              <OfflineProvider>
                <FavouritesProvider>
                  {children}
                </FavouritesProvider>
              </OfflineProvider>
            </AuthProvider>
          </QueryClientProvider>
        )
      }
    }
    ```

- [x] **Task 5: Update failing tests to use wrapper** (AC: #2)
  - [x] 5.1 Find tests with `useOffline must be used within an OfflineProvider`
  - [x] 5.2 Update render calls to use wrapper:
    ```typescript
    import { createTestWrapper } from '../utils/test-wrapper'

    render(<Component />, { wrapper: createTestWrapper() })
    ```

### Act Warning Tasks (AC: #2)

- [x] **Task 6: Fix React act() warnings** (AC: #2) *(partial - warnings reduced but some remain)*
  - [x] 6.1 Identify tests with state update warnings
  - [x] 6.2 Wrap async state updates in `act()`:
    ```typescript
    import { act } from '@testing-library/react'

    await act(async () => {
      // Code that causes state updates
      await waitFor(() => expect(...))
    })
    ```
  - [x] 6.3 Use `waitFor` properly for async operations

### Verification Tasks

- [x] **Task 7: Run full test suite** (AC: #2)
  - [x] 7.1 Run `npm test`
  - [x] 7.2 Verify 237/237 tests pass
  - [ ] 7.3 Verify no console errors/warnings *(some act() warnings remain)*

---

## Dev Notes

### Files to Modify

| File | Change |
|------|--------|
| `frontend/tests/setup.ts` | Add URL.createObjectURL/revokeObjectURL mocks |
| `frontend/tests/mocks/handlers.ts` | Add /auth/refresh, /auth/logout handlers |
| `frontend/tests/utils/test-wrapper.tsx` | Create/update with all providers |
| `frontend/tests/pages/recipe-detail.test.tsx` | Add wrapper, fix act warnings |
| `frontend/tests/components/UploadDropzone.test.tsx` | Uses URL.createObjectURL |

### Failing Test Files

Based on test run:
```
tests/pages/recipe-detail.test.tsx - Missing OfflineProvider
tests/pages/recipe-edit.test.tsx - Missing OfflineProvider
tests/pages/recipe-new.test.tsx - Missing OfflineProvider
tests/components/UploadDropzone.test.tsx - URL.createObjectURL
tests/lib/auth-context.test.tsx - Missing /auth/refresh handler
```

### Browser API Mocks Checklist

Current mocks in setup.ts:
- [x] `window.matchMedia`
- [x] `window.localStorage`
- [x] `window.IntersectionObserver`
- [x] `next/navigation`
- [x] `URL.createObjectURL` ✓
- [x] `URL.revokeObjectURL` ✓

### MSW Handlers Checklist

Current handlers:
- [x] `POST /auth/register`
- [x] `POST /auth/login`
- [x] `GET /auth/me`
- [x] `PUT /auth/me`
- [x] `POST /auth/refresh` ✓
- [x] `POST /auth/logout` ✓
- [x] Recipe CRUD endpoints
- [x] Category endpoints
- [x] Upload endpoints
- [x] `GET /health` ✓ (regex pattern for offline detection)

### Testing Commands

```bash
cd cocktail-app/frontend

# Run all tests
npm test

# Run with verbose output
npx vitest run --reporter=verbose

# Run specific test file
npx vitest run tests/components/UploadDropzone.test.tsx

# Run with coverage
npm run test:coverage
```

### Project Structure Notes

Per architecture:
- Tests in `frontend/tests/`
- Mocks in `frontend/tests/mocks/`
- Setup in `frontend/tests/setup.ts`
- Vitest config: `frontend/vitest.config.ts`

### Relationship to Story 0.1

Story 0.1 added new auth endpoints that broke existing tests:
- `POST /auth/refresh` - Silent token refresh
- `POST /auth/logout` - Server-side logout

The auth-context.tsx now calls `/auth/refresh` on mount, which triggers MSW errors in tests.

### References

- [Source: docs/project_context.md#Testing] - Vitest configuration
- [Source: docs/architecture-frontend.md#Testing] - Test patterns
- [Source: docs/epic-0-tech-debt.md#Story-0.4] - Original requirements

---

## Dev Agent Record

### Context Reference

Story context generated by create-story workflow on 2025-12-31.

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- Health check in jsdom fails due to timing/environment issues - mocked useOffline hook
- IndexedDB not available in jsdom - installed fake-indexeddb package
- Auth tests needed updates for cookie-based auth (no more localStorage token storage)

### Code Review (2025-12-31)

**Reviewer:** Claude Opus 4.5 (Adversarial Code Review)

**Findings Fixed:**
- Updated all task checkboxes to reflect completed work
- Added missing files to File List with cross-story note
- Changed status from "review" to "done"

**Known Issues (Deferred):**
- React act() warnings remain in 2 tests (recipe-detail, Header) - tests pass but console is noisy

**Verification:** 239/239 tests passing (2 new tests added since story creation)

### Code Review #2 (2025-12-31)

**Reviewer:** Claude Opus 4.5 (Adversarial Code Review - BMAD workflow)

**Issues Found & Fixed:**

1. ✅ **Sprint-status sync** - Updated sprint-status.yaml from "review" to "done" to match story status
2. ✅ **Documented act() warning scope** - Actually 50+ warnings across auth-context, login, recipe-detail, recipe-edit, recipe-new, Header tests (not just 2)

**Action Items (Future Tech Debt):**

- [x] Fix React act() warnings in auth-context.test.tsx (4+ warnings) - MEDIUM ✅ Fixed 2025-12-31
- [x] Fix React act() warnings in login.test.tsx (15+ warnings) - MEDIUM ✅ Fixed 2025-12-31
- [ ] Fix React act() warnings in FavouritesProvider/OfflineProvider test renders - LOW (deferred)

**Uncommitted Changes Note:**

The following files show uncommitted modifications (likely from parallel story work):

- `frontend/.env.example`, `frontend/lib/api.ts`, `frontend/lib/auth-context.tsx`
- `frontend/next.config.js`, `frontend/tests/lib/api.test.ts`

These should be committed as part of their respective stories (0.1, 0.5).

**Verification:** 239/239 tests passing (confirmed)

### Tech Debt Fix Session (2025-12-31)

**Reopened story to address act() warning tech debt from Code Review #2.**

**Changes Made:**

1. **auth-context.test.tsx:**
   - Added `flushPromises()` helper using `act()` to flush pending async operations
   - Added `afterEach` cleanup that flushes before `cleanup()`
   - Wrapped login/register/logout button clicks in `act()` blocks
   - Added `await flushPromises()` after initial waitFor to let AuthProvider settle

2. **login.test.tsx:**
   - Added same `flushPromises()` helper pattern
   - Added `afterEach` cleanup with `flushPromises()`
   - Wrapped all user interactions (type + click) in single `act()` blocks to batch state updates

**Result:** Eliminated ~40 act() warnings from auth-context and login tests. Remaining ~42 warnings are LOW priority (FavouritesProvider/OfflineProvider) and deferred.

### Completion Notes List

1. **URL.createObjectURL mock added** - Added to setup.ts for UploadDropzone tests
2. **MSW handlers added** - `/auth/refresh` and `/auth/logout` handlers in handlers.ts
3. **OfflineProvider added to test wrapper** - Updated test-utils.tsx with full provider stack
4. **Auth tests updated** - Replaced localStorage mocks with refresh token approach
5. **fake-indexeddb installed** - Polyfills IndexedDB for jsdom environment
6. **useOffline hook mocked** - Health check unreliable in jsdom, mocked to always return online
7. **Health endpoint handler added** - Regex pattern `/.*\/health.*/` for offline detection
8. **RecipeCard image test fixed** - Updated to match URL-encoded Next.js Image src

### File List

| File | Change |
|------|--------|
| `frontend/tests/setup.ts` | Added URL mocks, fake-indexeddb, useOffline mock |
| `frontend/tests/mocks/handlers.ts` | Added /auth/refresh, /auth/logout, /health handlers |
| `frontend/tests/utils/test-utils.tsx` | Added OfflineProvider, createTestWrapper function |
| `frontend/tests/lib/auth-context.test.tsx` | Updated for cookie-based auth; added flushPromises + act() wrappers to fix act() warnings |
| `frontend/tests/pages/login.test.tsx` | Removed localStorage expectations; added flushPromises + act() wrappers to fix act() warnings |
| `frontend/tests/pages/home.test.tsx` | Added refresh token handler in beforeEach |
| `frontend/tests/pages/recipe-detail.test.tsx` | Updated auth tests for refresh token approach |
| `frontend/tests/pages/recipe-edit.test.tsx` | Updated auth setup in beforeEach |
| `frontend/tests/components/Header.test.tsx` | Updated logged-in tests for refresh tokens |
| `frontend/tests/components/RecipeCard.test.tsx` | Fixed image URL assertion, added beforeEach |
| `frontend/package.json` | Added fake-indexeddb dev dependency |
| `frontend/package-lock.json` | Updated (auto-generated) |

**Note:** The following files were also modified as part of related auth changes (Stories 0.1/0.2/0.5):
- `frontend/lib/auth-context.tsx` - Refresh token implementation
- `frontend/lib/api.ts` - Removed hardcoded production URL
- `frontend/lib/offline-context.tsx` - Health check updates
- `frontend/lib/hooks/use-recipes.ts` - Auth header updates
- `frontend/app/page.tsx` - Home page updates
- `frontend/.env.example` - Environment variable documentation
