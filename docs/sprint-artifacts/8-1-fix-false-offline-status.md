# Story 8.1: Fix False Offline Status During Upload

Status: Done

## Story

As a **user**,
I want **the app to correctly show me as online while I'm actively uploading and viewing recipes**,
so that **I don't see confusing offline banners and disabled controls immediately after a successful upload**.

## Acceptance Criteria

### AC-1: No False Offline During Upload

**Given** I have just uploaded a recipe screenshot
**When** the backend is processing the extraction (5-15 seconds)
**Then** the app does NOT show offline status or the amber offline banner
**And** the recipe detail page does NOT show "Viewing cached version (offline)"
**And** filters, navigation, and controls remain fully enabled

### AC-2: Consecutive Failure Debounce

**Given** the health check fails once
**When** I was previously online
**Then** the app requires at least 2 consecutive failures before flipping to offline
**And** a single transient failure does NOT trigger offline mode
**And** the failure counter resets to 0 on any successful health check

### AC-3: Generous Health Check Timeout

**Given** the backend is processing an upload (Claude Vision extraction takes 5-15s)
**When** the health check runs concurrently
**Then** the health check uses an 8-second timeout (up from 3 seconds)
**And** the `/health` endpoint still responds within this window under normal load

### AC-4: Debug Logging for State Transitions

**Given** the app transitions from online to offline (or vice versa)
**When** the transition occurs
**Then** the transition is logged via `offlineDebug` with:
  - Previous state
  - New state
  - Failure count at time of transition
  - Reason (e.g., "2 consecutive health check failures")

## Tasks / Subtasks

- [x] Task 1: Increase health check timeout (AC: #3)
  - [x] 1.1 In `frontend/lib/offline-context.tsx` line 41, change `setTimeout(() => controller.abort(), 3000)` to `setTimeout(() => controller.abort(), 8000)`

- [x] Task 2: Add consecutive-failure debounce (AC: #1, #2)
  - [x] 2.1 Add `useRef` to the React import on line 3: `import React, { createContext, useContext, useState, useEffect, useCallback, useRef, ReactNode } from 'react';`
  - [x] 2.2 Add a `useRef<number>` for `failureCount` (initialized to 0) inside `OfflineProvider`
  - [x] 2.3 Add `isOnlineRef = useRef(true)` to mirror the `isOnline` state. This allows reading the current online status inside the `useCallback` without adding `isOnline` as a dependency (which would cause stale closures). Update `isOnlineRef.current` inline before each `setIsOnline()` call.
  - [x] 2.4 In `checkRealConnectivity`, on success: reset `failureCount.current = 0`, update `isOnlineRef.current = true`, and call `setIsOnline(true)`
  - [x] 2.5 In `checkRealConnectivity`, on failure: increment `failureCount.current++`. Only call `setIsOnline(false)` and set `isOnlineRef.current = false` when `failureCount.current >= 2`
  - [x] 2.6 Use `useRef` (not `useState`) for both the counter and the online mirror to avoid re-renders and stale closures in the `useCallback`

- [x] Task 3: Add state transition debug logging (AC: #4)
  - [x] 3.1 In the success path, if `isOnlineRef.current` was previously `false`, log: `debug.log('ONLINE transition: health check passed, failureCount reset')`
  - [x] 3.2 In the failure path, log current `failureCount` on every failure. When transitioning to offline (failureCount hits threshold), log: `debug.log('OFFLINE transition: ${failureCount.current} consecutive failures')`
  - [x] 3.3 Use `isOnlineRef.current` (from Task 2.3) to read the current online state inside the callback — do NOT use the `isOnline` state variable directly (stale closure)

- [x] Task 4: Frontend tests (AC: #1, #2, #3, #4)
  - [x] 4.1 Test: single health check failure does NOT flip `isOnline` to false
  - [x] 4.2 Test: two consecutive health check failures DO flip `isOnline` to false
  - [x] 4.3 Test: a success after one failure resets the counter (subsequent single failure doesn't trigger offline)
  - [x] 4.4 Test: verify `AbortController` timeout is 8000ms (not 3000ms)
  - [x] 4.5 Run full frontend test suite: `npm test` — confirm 0 regressions (380/380 pass)

## Dev Notes

### This is frontend-only. No backend changes needed.

### Single File Change

**File:** `frontend/lib/offline-context.tsx`

This is the ONLY production file that needs modification. The fix is entirely within the `OfflineProvider` component.

### Current Code (What's Wrong)

The health check at line 33-58 has two problems:

1. **Timeout too short (line 41):** `setTimeout(() => controller.abort(), 3000)` — 3 seconds is too aggressive when the backend is busy with Claude Vision extraction (5-15 seconds). The `/health` endpoint is tiny, but when the single-threaded backend is saturated processing an image, even small requests queue.

2. **No debounce (line 57):** `setIsOnline(false)` fires immediately on a single failure. One slow health check = instant offline mode across the entire app.

### Implementation Pattern

```typescript
// Inside OfflineProvider, before checkRealConnectivity:
const failureCountRef = useRef(0);
const isOnlineRef = useRef(true);  // Track current value for logging inside useCallback

const checkRealConnectivity = useCallback(async () => {
  try {
    const healthUrl = `/health?_=${Date.now()}`;
    debug.log(`Checking connectivity: ${healthUrl}`);

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 8000);  // Was 3000

    const response = await fetch(healthUrl, {
      method: 'GET',
      cache: 'no-store',
      signal: controller.signal,
    });
    clearTimeout(timeout);

    if (!response.ok) throw new Error('Health check failed');

    // Success: reset failure counter
    failureCountRef.current = 0;
    if (!isOnlineRef.current) {
      debug.log('ONLINE transition: health check passed, failureCount reset');
    }
    debug.log('Health check passed - ONLINE');
    isOnlineRef.current = true;
    setIsOnline(true);
  } catch (error) {
    failureCountRef.current++;
    debug.log(`Health check failed (${failureCountRef.current} consecutive)`, error);

    if (failureCountRef.current >= 2) {
      if (isOnlineRef.current) {
        debug.log(`OFFLINE transition: ${failureCountRef.current} consecutive failures`);
      }
      isOnlineRef.current = false;
      setIsOnline(false);
    } else {
      debug.log('Single failure — not transitioning to offline yet');
    }
  }
}, []);
```

### Why `useRef` and NOT `useState` for failureCount

- `useState` would make `failureCount` a dependency of `useCallback`, which would recreate `checkRealConnectivity` on every failure, which would re-register the interval, which would reset timing. Refs avoid this entirely.
- `isOnlineRef` mirrors the `isOnline` state to allow reading the current value inside the callback without adding it as a dependency (stale closure issue).

### Downstream Impact — Components That Consume `isOnline`

These components react to `isOnline` from `useOffline()`. No changes needed — they'll automatically benefit from more stable online/offline state:

| Component | What it does with `isOnline` |
|-----------|------------------------------|
| `OfflineIndicator.tsx` | Shows/hides amber "Offline mode" banner |
| `app/page.tsx` (library) | Disables filters, switches to cached recipes, disables infinite scroll |
| `RecipeCard.tsx` | Redirects to `/offline/recipe?id=...` instead of normal navigation |
| `app/recipes/[id]/page.tsx` | (Does NOT use isOnline — safe) |

### Testing Approach

Test the `OfflineProvider` component by mocking `fetch` to control health check outcomes. Use `vi.useFakeTimers()` to advance through the 2-second initial delay and 15-second intervals.

**Exception to project_context.md MSW rule:** This story mocks `fetch` directly instead of using MSW. This is an intentional deviation because we are testing the health check mechanism itself — specifically the `AbortController` timeout behavior and fetch failure handling. MSW intercepts at the network layer and would bypass the `AbortController` timeout we need to verify. This is the one case where direct fetch mocking is the correct approach. Do NOT use MSW for these tests.

**Test file:** `frontend/tests/lib/offline-context.test.tsx` (new file)

**Test wrapper pattern:**
```typescript
function TestConsumer() {
  const { isOnline } = useOffline();
  return <div data-testid="status">{isOnline ? 'online' : 'offline'}</div>;
}

function renderWithProvider() {
  return render(
    <OfflineProvider>
      <TestConsumer />
    </OfflineProvider>
  );
}
```

**Key test scenarios:**
1. Initial state is `online` (true) — no flash of offline during hydration
2. Single fetch failure: status stays `online`
3. Two consecutive fetch failures: status transitions to `offline`
4. Fetch succeeds after one failure: counter resets, stays `online`
5. After going offline (2 failures), single success brings back `online`

### Don't Do This

- Don't add a `pauseHealthCheck` mechanism tied to the upload flow — it's unnecessary complexity. The timeout increase + debounce fix the root cause without coupling the offline context to the upload page.
- Don't change the health check interval (15 seconds) — it's already a good balance for battery life
- Don't change the initial delay (2 seconds) — it prevents competing with page load
- Don't add `navigator.onLine` as a secondary signal — the epic description explicitly says browser events are unreliable and used only as triggers
- Don't add any new context values or exported functions — the `OfflineContextType` interface stays exactly the same
- Don't use `useState` for the failure counter — see "Why `useRef`" section above
- Don't import or use `useEffect` to sync `isOnlineRef` — just update it inline in the callback before `setIsOnline`

### Project Structure Notes

| File | Action |
|------|--------|
| `frontend/lib/offline-context.tsx` | Modify — timeout, debounce, logging |
| `frontend/tests/lib/offline-context.test.tsx` | **Create** — new test file for health check logic |

No new dependencies. No new components. No API changes. No migrations.

### References

- [Source: docs/epic-8-frontend-ux-bugs.md#Story 8.1] — Bug description, root cause analysis, acceptance criteria
- [Source: docs/project_context.md#Auth & Offline] — Offline context patterns and provider order
- [Source: docs/project_context.md#Testing Rules] — vitest globals, test isolation patterns
- [Source: docs/sprint-artifacts/7-3-user-edit-capability.md] — Previous story learnings: modal patterns, test approach
- [Source: frontend/lib/offline-context.tsx] — Current health check implementation (lines 33-58)
- [Source: frontend/components/OfflineIndicator.tsx] — Amber banner component consuming isOnline

## Dev Agent Record

### Context Reference

<!-- Story context created by SM create-story workflow -->

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

- No debug log issues encountered during implementation.

### Completion Notes List

- **Task 1:** Changed AbortController timeout from 3000ms to 8000ms in `checkRealConnectivity`. This prevents false aborts when the backend is busy processing Claude Vision extraction (5-15s).
- **Task 2:** Added `failureCountRef` and `isOnlineRef` refs to implement consecutive-failure debounce. Single health check failures no longer trigger offline mode — requires 2 consecutive failures. Counter resets on any success. Used useRef (not useState) to avoid stale closures and unnecessary re-renders in the useCallback.
- **Task 3:** Added debug logging for state transitions: logs "ONLINE transition" when recovering from offline, logs "OFFLINE transition" with failure count when going offline, logs every failure with current consecutive count, logs single-failure non-transition.
- **Task 4:** Created 7 tests covering: initial online state, 8000ms timeout verification, single failure stays online, two consecutive failures go offline, success-after-failure resets counter, recovery from offline on single success, state transition debug logging (AC-4). Used direct fetch mocking (not MSW) per story Dev Notes to test AbortController behavior.
- **Full regression:** 32 test files, 385 tests — all passing, 0 regressions.

### File List

- `frontend/lib/offline-context.tsx` — Modified: timeout increase, debounce refs, transition logging
- `frontend/tests/lib/offline-context.test.tsx` — Created: 6 tests for health check debounce behavior
- `docs/sprint-artifacts/sprint-status.yaml` — Modified: story status updates
- `docs/sprint-artifacts/8-1-fix-false-offline-status.md` — Modified: task checkboxes, dev agent record

### Change Log

- 2026-04-14: Implemented false offline status fix — health check timeout 3s→8s, consecutive-failure debounce (2 failures required), state transition debug logging. 6 new tests, 380 total passing.
- 2026-04-14: **Code Review Fixes** — (1) Fixed clearTimeout leak on failure path by hoisting controller/timeout before try-catch. (2) Fixed test `vi.restoreAllMocks()` → `vi.clearAllMocks()` to preserve offline-storage mock between tests. (3) Added AC-4 debug logging test verifying OFFLINE/ONLINE transition logs and failure count reporting. 7 tests, 385 total passing.
