# Story 0.1: Fix localStorage Token Storage

**Status: done**

---

## Story

As a **security-conscious developer**,
I want **auth tokens stored securely instead of localStorage**,
So that **XSS attacks cannot steal user credentials**.

---

## Acceptance Criteria

1. **Given** a user logs in
   **When** the token is issued
   **Then** the access token is NOT stored in localStorage
   **And** XSS scripts cannot access the refresh token

2. **Given** the app is refreshed
   **When** a valid session exists
   **Then** the user remains authenticated (via silent refresh)

3. **Given** a user logs out
   **When** the logout action completes
   **Then** both access and refresh tokens are invalidated
   **And** the httpOnly cookie is cleared

---

## Tasks / Subtasks

### Backend Tasks

- [x] **Task 1: Update token expiry configuration** (AC: #1)
  - [x] 1.1 Edit `backend/app/config.py` line 64
  - [x] 1.2 Change `access_token_expire_minutes` from `60 * 24 * 7` (7 days) to `30` (30 minutes)
  - [x] 1.3 Add `refresh_token_expire_days: int = 7` setting

- [x] **Task 2: Create refresh token function** (AC: #1, #2)
  - [x] 2.1 Edit `backend/app/services/auth.py`
  - [x] 2.2 Add `create_refresh_token(data: dict, expires_delta: timedelta = None) -> str` function
  - [x] 2.3 Use different claim structure to distinguish from access token (add `"type": "refresh"`)

- [x] **Task 3: Update login endpoint to set httpOnly cookie** (AC: #1)
  - [x] 3.1 Edit `backend/app/routers/auth.py` `/login` endpoint
  - [x] 3.2 Import `Response` from FastAPI
  - [x] 3.3 Create refresh token and set it as httpOnly cookie:
    ```python
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,  # Only send over HTTPS
        samesite="lax",  # CSRF protection
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        path="/api/auth"  # Only sent to auth endpoints
    )
    ```
  - [x] 3.4 Return only access_token in response body (not refresh token)

- [x] **Task 4: Create /auth/refresh endpoint** (AC: #2)
  - [x] 4.1 Add new endpoint `POST /api/auth/refresh` in `routers/auth.py`
  - [x] 4.2 Read refresh token from `request.cookies.get("refresh_token")`
  - [x] 4.3 Validate refresh token and check `type == "refresh"` claim
  - [x] 4.4 Issue new access token (short-lived)
  - [x] 4.5 Optionally rotate refresh token (issue new one, set new cookie)
  - [x] 4.6 Rate limit: `5/minute` to prevent brute force

- [x] **Task 5: Update logout to clear cookie** (AC: #3)
  - [x] 5.1 Create `POST /api/auth/logout` endpoint
  - [x] 5.2 Clear the refresh_token cookie:
    ```python
    response.delete_cookie(key="refresh_token", path="/api/auth")
    ```
  - [x] 5.3 Return success response

- [x] **Task 6: Update CORS for credentials** (AC: #1)
  - [x] 6.1 Edit `backend/app/main.py`
  - [x] 6.2 Add `allow_credentials=True` to CORS middleware (already present)
  - [x] 6.3 Ensure `allow_origins` is explicit list (not `*`) when using credentials (already configured)

### Frontend Tasks

- [x] **Task 7: Remove localStorage usage** (AC: #1)
  - [x] 7.1 Edit `frontend/lib/auth-context.tsx`
  - [x] 7.2 Remove `TOKEN_KEY` and `USER_KEY` constants
  - [x] 7.3 Remove ALL `localStorage.getItem()` calls
  - [x] 7.4 Remove ALL `localStorage.setItem()` calls
  - [x] 7.5 Remove ALL `localStorage.removeItem()` calls

- [x] **Task 8: Store access token in memory only** (AC: #1)
  - [x] 8.1 Access token stays in React state (`useState`)
  - [x] 8.2 Token is lost on page refresh (by design - we'll restore via refresh)

- [x] **Task 9: Update login to use credentials** (AC: #1, #2)
  - [x] 9.1 Update login fetch to include `credentials: 'include'`:
    ```typescript
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',  // Send/receive cookies
      body: JSON.stringify({ email, password }),
    });
    ```
  - [x] 9.2 Store returned access_token in state
  - [x] 9.3 Optionally cache user data in sessionStorage (not token!) - skipped, not needed

- [x] **Task 10: Implement silent refresh on page load** (AC: #2)
  - [x] 10.1 In `useEffect` initialization, call `/api/auth/refresh`
  - [x] 10.2 Use `credentials: 'include'` to send cookie
  - [x] 10.3 If successful, store new access token in state
  - [x] 10.4 If fails (401), user is logged out (no valid session)
  - [x] 10.5 Handle network errors gracefully (offline mode)

- [x] **Task 11: Update logout to call backend** (AC: #3)
  - [x] 11.1 Change logout to call `POST /api/auth/logout` with `credentials: 'include'`
  - [x] 11.2 Clear local state regardless of response
  - [x] 11.3 Backend clears the cookie

- [x] **Task 12: Update all API calls to include credentials** (AC: #1)
  - [x] 12.1 Review `frontend/lib/api.ts`
  - [x] 12.2 Add `credentials: 'include'` to fetch calls that need auth - N/A
  - [x] 12.3 Alternatively, keep using Authorization header for access token (simpler) - USED THIS APPROACH

### Testing Tasks

- [x] **Task 13: Test login/logout flow** (AC: #1, #2, #3)
  - [x] 13.1 Test login sets httpOnly cookie (check browser DevTools -> Application -> Cookies)
  - [x] 13.2 Verify localStorage is empty after login
  - [x] 13.3 Test page refresh maintains session
  - [x] 13.4 Test logout clears cookie

- [x] **Task 14: Test XSS resilience** (AC: #1)
  - [x] 14.1 Open browser console
  - [x] 14.2 Verify `document.cookie` does not show refresh_token (httpOnly)
  - [x] 14.3 Verify `localStorage` contains no tokens

### Review Follow-ups (AI)

- [x] **HIGH**: Write automated tests for POST /auth/refresh endpoint (tests/test_auth.py) - 8 tests added
- [x] **HIGH**: Write automated tests for POST /auth/logout endpoint (tests/test_auth.py) - 3 tests (Story 0.2)
- [x] **MEDIUM**: Implement database-backed refresh token revocation (completed by Story 0.2 dev)
- [ ] **LOW**: Fix deprecated `datetime.utcnow` in SQLAlchemy model defaults (user.py, recipe.py, collection.py, user_rating.py, refresh_token.py) - requires helper function and broader refactor, separate tech debt story recommended

---

## Dev Notes

### Implementation Approach Decision

**Recommended: Hybrid Memory + httpOnly Cookie**

Based on current security best practices (OWASP guidelines, industry consensus):

| Token Type | Storage | Lifespan | Access |
|------------|---------|----------|--------|
| Access Token | Memory (React state) | 15-30 min | JavaScript |
| Refresh Token | httpOnly Cookie | 7 days | Server only |

This approach:
- Prevents XSS from stealing long-lived tokens
- Handles page refresh gracefully via silent refresh
- Mitigates CSRF with `SameSite=Lax` cookie attribute
- No localStorage usage at all

### Current Code Analysis

**Files to modify:**

| File | Current Issue | Required Change |
|------|---------------|-----------------|
| `backend/app/config.py:64` | 7-day token expiry | Reduce to 30 min, add refresh token expiry |
| `backend/app/services/auth.py` | No refresh token | Add `create_refresh_token()` |
| `backend/app/routers/auth.py` | Returns token in body only | Set httpOnly cookie, add `/refresh` endpoint |
| `frontend/lib/auth-context.tsx:62,90,125,160` | localStorage usage | Remove entirely, use memory + silent refresh |
| `backend/app/main.py` | CORS without credentials | Add `allow_credentials=True` |

### Security Constraints (MUST FOLLOW)

1. **Cookie Attributes** (all required):
   - `httponly=True` - Prevents JS access
   - `secure=True` - HTTPS only (disable for localhost dev)
   - `samesite="lax"` - CSRF protection
   - `path="/api/auth"` - Limits cookie scope

2. **CORS Configuration**:
   - When using `credentials: 'include'`, cannot use `allow_origins=["*"]`
   - Must explicitly list allowed origins

3. **Token Differentiation**:
   - Add `"type": "access"` or `"type": "refresh"` claim to distinguish tokens
   - Prevents using refresh token as access token

4. **Rate Limiting**:
   - `/auth/register`: 5 requests/minute (prevent spam registrations)
   - `/auth/login`: 10 requests/minute (allow reasonable retries)
   - `/auth/token`: 10 requests/minute (OAuth2 form endpoint)
   - `/auth/refresh`: 5 requests/minute (prevent brute force)
   - Frontend should handle 429 responses gracefully (show "too many attempts" message)

### Project Structure Notes

Per architecture, auth changes span:
- **Router layer**: `routers/auth.py` - endpoint changes
- **Service layer**: `services/auth.py` - token generation logic
- **Config**: `config.py` - expiry settings
- **Frontend context**: `lib/auth-context.tsx` - state management

No database schema changes required (tokens are stateless JWT).

### References

- [Source: docs/project_context.md#Authentication] - Token handling patterns
- [Source: docs/architecture-backend.md#Authentication-Flow] - JWT flow
- [Source: docs/architecture-frontend.md#AuthContext] - Context patterns
- [Source: docs/epic-0-tech-debt.md#Story-0.1] - Original requirements

### Web Research Sources

- [OWASP JWT Storage Best Practices](https://www.cyberchief.ai/2023/05/secure-jwt-token-storage.html)
- [FastAPI HttpOnly Cookie Tutorial](https://www.fastapitutorial.com/blog/fastapi-jwt-httponly-cookie/)
- [Developer Guide to JWT Storage](https://www.descope.com/blog/post/developer-guide-jwt-storage)
- [FastAPI Access & Refresh Tokens 2025](https://codevoweb.com/restful-api-with-python-fastapi-access-and-refresh-tokens/)

---

## Coordination Notes

**Relationship to Story 0.2 (Refresh Tokens):**
This story (0.1) implements the basic secure storage pattern with refresh tokens as part of the solution. Story 0.2 adds advanced refresh token features:
- Token revocation (requires database storage)
- Refresh token rotation
- Token family tracking

**Recommendation:** Implement 0.1 first with stateless refresh tokens. Story 0.2 can add database-backed token management later if needed.

---

## Dev Agent Record

### Context Reference

Story context generated by create-story workflow on 2025-12-31.

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- Backend auth tests: 42/42 passed
- TypeScript compilation: No errors
- Frontend test failures are pre-existing (Story 0.4 - URL.createObjectURL mock missing)

### Completion Notes List

1. **Config changes**: Reduced access token expiry from 7 days to 30 minutes, added refresh token expiry (7 days)
2. **Auth service**: Added `create_refresh_token()` and `decode_refresh_token()` functions with type claim differentiation
3. **Login endpoints**: Both `/login` and `/token` now set httpOnly cookie with refresh token
4. **Refresh endpoint**: Created `POST /auth/refresh` with rate limiting (5/min), token rotation, and proper error handling
5. **Logout endpoint**: Created `POST /auth/logout` that clears the httpOnly cookie
6. **Frontend auth-context**: Complete rewrite - removed ALL localStorage, tokens now memory-only, added silent refresh on page load
7. **CORS**: Already configured correctly with `allow_credentials=True` and explicit origins

### File List

**Modified:**
- `cocktail-app/backend/app/config.py` - Updated token expiry settings
- `cocktail-app/backend/app/services/auth.py` - Added refresh token functions, fixed deprecated datetime.utcnow()
- `cocktail-app/backend/app/routers/auth.py` - Added refresh/logout endpoints, updated login
- `cocktail-app/backend/app/routers/upload.py` - Fixed deprecated datetime.utcnow()
- `cocktail-app/frontend/lib/auth-context.tsx` - Complete rewrite for secure token handling
- `cocktail-app/frontend/lib/favourites-context.tsx` - Removed dead getStoredToken() localStorage code
- `cocktail-app/frontend/tests/pages/register.test.tsx` - Fixed misleading localStorage auth mocks
- `cocktail-app/frontend/tests/pages/recipe-new.test.tsx` - Fixed misleading localStorage auth mocks

---

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-12-31 | Implemented secure token storage with httpOnly cookies and memory-only access tokens | Claude Opus 4.5 |
| 2025-12-31 | Code review: Fixed 8 issues - hardcoded prod URL, React hooks violation, cookie secure flag, error logging, stale token handling. Added 3 action items for test coverage. | Claude Opus 4.5 (Review) |
| 2025-12-31 | Added 8 TestRefresh tests, fixed rate limiting in test fixtures (auth router limiter). All 36 auth tests pass. | Claude Opus 4.5 (Review) |
| 2025-12-31 | Code review: Fixed 6 issues - dead getStoredToken() in favourites-context, deprecated datetime.utcnow() in auth.py/upload.py, misleading test mocks. Added action items for model datetime deprecation. | Claude Opus 4.5 (Review) |
| 2026-01-10 | Final adversarial review: All 3 ACs verified implemented. Security implementation solid (httpOnly, secure, samesite). Synced sprint-status.yaml (story → done, epic-0 → done). 1 LOW action item remains (datetime.utcnow deprecation - recommend separate tech debt story). Committed in d771d37. | Claude Opus 4.5 (Review) |
