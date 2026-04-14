# Epic 8: Frontend UX Bugs — False Offline & Upload State

Two user-facing bugs in the upload and connectivity flow that undermine trust in the application. Both were discovered during normal usage — uploading a recipe, viewing it, and navigating back.

**Priority:** High — these bugs make the app appear broken during core workflows.

## Bug Summary

| # | Area | Issue |
|---|------|-------|
| 8.1 | Connectivity Detection | False offline status shown on library page and recipe cards during/after upload |
| 8.2 | Upload Flow | "Extraction failed" error displayed on back-navigation despite successful extraction |

---

## Story 8.1: Fix False Offline Status During Upload

**As a** user,
**I want** the app to correctly show me as online while I'm actively uploading and viewing recipes,
**So that** I don't see confusing offline banners and disabled controls immediately after a successful upload.

### Background

The offline detection system (`frontend/lib/offline-context.tsx`) uses a health-check approach: it fetches `/health` every 15 seconds with a 3-second `AbortController` timeout. When the backend is busy processing a Claude Vision extraction (which can take 5-15 seconds), the health endpoint can be slow to respond. The 3-second timeout fires, and `isOnline` is set to `false`.

**Visible symptoms:**
- The global amber "You are offline" banner appears (`OfflineIndicator.tsx`)
- The recipe detail page shows "Viewing cached version (offline)" and hides edit/rating controls
- The library page (`app/page.tsx`) disables filters and shows cached-only recipes
- `RecipeCard` overrides navigation to use the offline viewer (`window.location.assign('/offline/recipe?id=...')`)

**Root cause chain:**
1. Health check timeout is only 3 seconds (`offline-context.tsx:41`) — too short when backend is busy with AI extraction
2. The health check runs every 15 seconds (`offline-context.tsx:79`) and also has a 2-second delayed initial check on mount
3. During/after upload, the backend may be saturated processing the image through Claude Vision, causing the health endpoint to respond slowly
4. A single failed health check flips `isOnline` to `false` immediately — no debouncing or retry

### Acceptance Criteria

**Given** I have just uploaded a recipe screenshot
**When** the backend is processing the extraction
**Then** the app does NOT show offline status / amber offline banner
**And** the recipe detail page does NOT show "Viewing cached version (offline)"

**Given** the health check fails once
**When** I was previously online
**Then** the app requires at least 2 consecutive failures before flipping to offline
**And** a single transient failure does not trigger offline mode

**Given** the backend is processing an upload
**When** the health check runs concurrently
**Then** the health check uses a timeout generous enough to accommodate a busy backend (e.g., 8 seconds)

**Given** the app transitions from online to offline
**When** the transition occurs
**Then** the transition is logged with debug output for troubleshooting

### Technical Notes

- **File:** `frontend/lib/offline-context.tsx`
- **Fix 1 — Increase timeout:** Change the `AbortController` timeout from 3000ms to 8000ms (line 41). The health endpoint is tiny — if it takes >8s, we're genuinely offline or the backend is down.
- **Fix 2 — Add consecutive-failure debounce:** Track a failure counter. Only set `isOnline = false` after 2+ consecutive failures. Reset counter on any success. This prevents a single slow response from flipping state.
- **Fix 3 — Consider pausing checks during upload:** If feasible, expose a `pauseHealthCheck` from the context that the upload page can call while an extraction is in-flight. This eliminates the race entirely.
- No backend changes needed.

---

## Story 8.2: Fix False "Extraction Failed" on Back-Navigation

**As a** user,
**I want** to return to the upload page after viewing my recipe without seeing a false error,
**So that** I can upload another recipe or navigate freely without confusion.

### Background

After a successful upload flow (upload screenshot -> extraction succeeds -> click "View Recipe" -> navigate to recipe detail page), if the user navigates back to `/upload`, they see "Failed to extract recipe" or "Extraction failed" even though extraction clearly succeeded.

**Root cause:** In `frontend/app/upload/page.tsx`, `handleEnhanceComplete` (line 40-45) calls `router.replace('/upload')` to strip the `?enhance=` query parameter. This changes `searchParams`, which causes `enhanceRecipeId` to go from a UUID to `null`. The `UploadDropzone` component receives `enhanceRecipeId={undefined}` as a new prop value.

Inside `UploadDropzone` (`frontend/components/upload/UploadDropzone.tsx`), `isEnhanceMode` is derived directly from the prop: `const isEnhanceMode = !!enhanceRecipeId` (line 42). When the prop changes from a UUID to `undefined`, this flips `isEnhanceMode` from `true` to `false`, which changes the identity of `doExtraction` and `processFiles` callbacks (they have `isEnhanceMode` and `enhanceRecipeId` in their dependency arrays). This triggers the paste event `useEffect` (line 136-162) to unregister and re-register its listener — creating a timing window for stale/duplicate invocations that can fail and set `state = 'error'`.

Additionally, the `useEffect` at line 20-30 of `upload/page.tsx` fires when `enhanceRecipeId` transitions from a value to `null`. While it skips the body (null check), the effect teardown/re-run is part of the same re-render cascade that destabilizes the dropzone's callback chain.

**Visible symptom:** The upload page shows a red error UI — "Failed to extract recipe" with the `AlertCircle` icon — despite the recipe being successfully extracted and viewable.

### Acceptance Criteria

**Given** I have successfully uploaded and extracted a recipe
**When** I click "View Recipe" and then navigate back to `/upload` (browser back button)
**Then** the upload page shows either the success state OR a clean idle state
**And** no error message is displayed

**Given** I am in enhance mode and enhancement completes successfully
**When** `handleEnhanceComplete` runs
**Then** the `UploadDropzone` does NOT flash an error state
**And** the component remains in `'success'` state

**Given** the `enhanceRecipeId` prop changes from a UUID to `undefined`
**When** `UploadDropzone` re-renders
**Then** the component does NOT trigger a stale `processFiles` invocation
**And** the paste event listener is NOT re-registered in a way that causes side effects

### Technical Notes

- **Files:** `frontend/app/upload/page.tsx` (lines 40-45), `frontend/components/upload/UploadDropzone.tsx` (lines 42, 60-82, 136-162)
- **Fix approach — Stabilize `isEnhanceMode` as internal state:**
  - In `UploadDropzone`, change `isEnhanceMode` from a derived value (`!!enhanceRecipeId`) to a `useState` that is initialized from the prop on mount, and only updated explicitly (not re-derived on every render).
  - This prevents `router.replace('/upload')` from cascading through the callback dependency chain while the component is in `'success'` state.
- **Alternative fix — Guard `processFiles` against re-invocation in terminal states:**
  - Add an early return in `processFiles` if `state === 'success'` or `state === 'error'`. This prevents any stale callback re-invocation from changing the state after a terminal outcome.
  - This is a simpler, more defensive fix that addresses the symptom directly.
- **Alternative fix — Delay `router.replace`:**
  - Don't call `router.replace('/upload')` in `handleEnhanceComplete`. Let the URL stay as `/upload?enhance=<id>` until the user explicitly clicks "Upload Another" or navigates away. The query param is harmless.
- **Recommended:** Combine the guard in `processFiles` (defensive) with stabilizing `isEnhanceMode` (root cause). The `router.replace` change is optional but cleanest.

---

## Dependencies & Ordering

Stories are independent and can be worked in parallel:
- **8.1** — Frontend only, ~45 min (health check logic + testing offline transitions)
- **8.2** — Frontend only, ~30 min (state management fix in upload flow)

## Related Epics

- Epic 5 (Story 5.3): Category Management Modal — original frontend implementation
- Epic 7: Admin Panel Bug Fixes — prior bug fix epic (same pattern: frontend UX bugs found during testing)
