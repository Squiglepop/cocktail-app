---
status: ready
priority: medium
created: 2025-12-31
source: code-review
---

# Epic 0: Tech Debt & Code Quality

## Overview

Technical debt items identified during code review on 2025-12-31. These are non-feature items that improve security, maintainability, and developer experience.

## Epic List

| # | Story | Priority | Effort | Status |
|---|-------|----------|--------|--------|
| 0.1 | Fix localStorage Token Storage | HIGH | Medium | draft |
| 0.2 | Implement Refresh Tokens | MEDIUM | Medium | draft |
| 0.3 | Fix Backend Test Dependencies | MEDIUM | Low | draft |
| 0.4 | Fix Frontend Test Mocks | MEDIUM | Low | draft |
| 0.5 | Remove Hardcoded Production URLs | LOW | Low | draft |
| 0.6 | Extract Ingredient Service | LOW | Medium | draft |

---

## Story 0.1: Fix localStorage Token Storage

As a **security-conscious developer**,
I want **auth tokens stored securely instead of localStorage**,
So that **XSS attacks cannot steal user credentials**.

**Files:** `frontend/lib/auth-context.tsx`

**Acceptance Criteria:**

- [ ] **Given** a user logs in
  **When** the token is issued
  **Then** it is NOT stored in localStorage
  **And** XSS scripts cannot access it

- [ ] **Given** the app is refreshed
  **When** a valid session exists
  **Then** the user remains authenticated

**Implementation Options:**
1. httpOnly cookies (backend sets, frontend doesn't handle)
2. Memory-only with refresh tokens (short-lived access token)

**Tasks:**
- [ ] Choose auth storage approach
- [ ] Implement backend changes (if cookie approach)
- [ ] Update auth-context.tsx
- [ ] Update API calls to handle new auth flow
- [ ] Test login/logout/refresh flows

---

## Story 0.2: Implement Refresh Tokens

As a **security-conscious developer**,
I want **short-lived access tokens with refresh capability**,
So that **compromised tokens have limited validity**.

**Files:** `backend/app/config.py`, `backend/app/services/auth.py`, `frontend/lib/auth-context.tsx`

**Acceptance Criteria:**

- [ ] **Given** an access token
  **When** it is issued
  **Then** it expires in 15-30 minutes (not 7 days)

- [ ] **Given** an access token is about to expire
  **When** the frontend detects this
  **Then** it silently refreshes using a refresh token

- [ ] **Given** a refresh token
  **When** it is compromised
  **Then** it can be revoked server-side

**Tasks:**
- [ ] Add refresh token model/storage
- [ ] Create `/auth/refresh` endpoint
- [ ] Reduce access token expiry to 15-30 min
- [ ] Add refresh token to login response
- [ ] Implement frontend token refresh logic
- [ ] Add refresh token rotation (optional)

**Note:** Often implemented together with Story 0.1.

---

## Story 0.3: Fix Backend Test Dependencies

As a **developer**,
I want **backend tests to run without errors**,
So that **CI/CD pipelines work and we have test coverage**.

**Files:** `backend/requirements.txt`, test venv

**Acceptance Criteria:**

- [ ] **Given** the test environment
  **When** `pytest` is run
  **Then** no `ModuleNotFoundError` occurs

- [ ] **Given** all dependencies installed
  **When** tests execute
  **Then** test collection succeeds

**Tasks:**
- [ ] Run `pip install filetype` in venv
- [ ] Verify filetype is in requirements.txt
- [ ] Run pytest and confirm tests collect
- [ ] Fix any other missing dependencies

---

## Story 0.4: Fix Frontend Test Mocks

As a **developer**,
I want **frontend tests to pass**,
So that **we have reliable test coverage**.

**Files:** `frontend/tests/setup.ts`, `frontend/vitest.config.ts`

**Acceptance Criteria:**

- [ ] **Given** the test environment
  **When** `npm test` is run
  **Then** no `URL.createObjectURL is not a function` errors

- [ ] **Given** all browser APIs are mocked
  **When** tests execute
  **Then** 237/237 tests pass (not 196/237)

**Tasks:**
- [ ] Add URL.createObjectURL mock to setup.ts
- [ ] Add URL.revokeObjectURL mock to setup.ts
- [ ] Run full test suite
- [ ] Fix any remaining mock issues

---

## Story 0.5: Remove Hardcoded Production URLs

As a **developer**,
I want **no hardcoded production URLs in the frontend**,
So that **development doesn't accidentally hit production**.

**Files:** `frontend/lib/api.ts:6`, `frontend/lib/auth-context.tsx:5`

**Acceptance Criteria:**

- [ ] **Given** NEXT_PUBLIC_API_URL is not set
  **When** the app starts in development
  **Then** it uses localhost:8000 OR throws an error

- [ ] **Given** the production deployment
  **When** the env var is set correctly
  **Then** behavior is unchanged

**Tasks:**
- [ ] Update API_BASE fallback to localhost or throw
- [ ] Update auth-context.tsx API_BASE similarly
- [ ] Test in dev without env var
- [ ] Verify production still works

---

## Story 0.6: Extract Ingredient Service

As a **developer**,
I want **ingredient handling logic in a single service**,
So that **code isn't duplicated across 5+ locations**.

**Files:** `backend/app/routers/upload.py`, `backend/app/routers/recipes.py`, `backend/app/services/` (new)

**Acceptance Criteria:**

- [ ] **Given** ingredient create-or-get logic
  **When** a recipe is created/updated
  **Then** a single service function is called

- [ ] **Given** the refactored code
  **When** tests run
  **Then** all existing functionality works

**Tasks:**
- [ ] Create `services/recipe_service.py`
- [ ] Extract `add_ingredients_to_recipe()` function
- [ ] Update upload.py to use service (3 locations)
- [ ] Update recipes.py to use service (2 locations)
- [ ] Run tests to verify no regressions
