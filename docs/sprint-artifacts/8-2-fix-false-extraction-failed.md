# Story 8.2: Fix False "Extraction Failed" on Back-Navigation

Status: done

## Story

As a user,
I want to return to the upload page after viewing my recipe without seeing a false error,
so that I can upload another recipe or navigate freely without confusion.

## Acceptance Criteria

1. **Given** I have successfully uploaded and extracted a recipe, **When** I click "View Recipe" and then navigate back to `/upload` (browser back button), **Then** the upload page shows either the success state OR a clean idle state — no error message is displayed.

2. **Given** I am in enhance mode and enhancement completes successfully, **When** `handleEnhanceComplete` runs, **Then** the `UploadDropzone` does NOT flash an error state and the component remains in `'success'` state.

3. **Given** the `enhanceRecipeId` prop changes from a UUID to `undefined`, **When** `UploadDropzone` re-renders, **Then** the component does NOT trigger a stale `processFiles` invocation and the paste event listener is NOT re-registered in a way that causes side effects.

## Tasks / Subtasks

- [x] Task 1: Guard `processFiles` against re-invocation in terminal states (AC: #1, #2, #3)
  - [x] 1.1: In `UploadDropzone.tsx`, add early return at top of `processFiles` if `state` is `'success'` or `'error'` — prevents any stale callback from mutating state after a terminal outcome
  - [x] 1.2: Use a ref (`useRef`) for the current state value inside `processFiles` to avoid stale closure reads of `state`

- [x] Task 2: Stabilize `isEnhanceMode` as internal state (AC: #2, #3)
  - [x] 2.1: In `UploadDropzone.tsx`, replace `const isEnhanceMode = !!enhanceRecipeId` (line 42) with a `useState` initialized from the prop on mount
  - [x] 2.2: Add a `useEffect` that updates `isEnhanceMode` state ONLY when transitioning from `undefined` → a UUID (not the reverse). Ignore transitions from UUID → `undefined` while in `'success'` or `'error'` state
  - [x] 2.3: This prevents `router.replace('/upload')` from cascading through the dependency chain (`isEnhanceMode` → `doExtraction` → `processFiles` → paste listener re-register)

- [x] Task 3: Add tests for back-navigation regression (AC: #1, #2, #3)
  - [x] 3.1: In `UploadDropzone.test.tsx`, add test: component stays in success state when `enhanceRecipeId` prop changes from UUID to `undefined` after successful extraction
  - [x] 3.2: In `UploadDropzone.test.tsx`, add test: `processFiles` is a no-op when state is `'success'`
  - [x] 3.3: In `UploadDropzone.test.tsx`, add test: `processFiles` is a no-op when state is `'error'`
  - [x] 3.4: In `UploadDropzone.test.tsx`, add test: back-navigation scenario — rerender with `enhanceRecipeId=undefined` after success does not show error state (NOTE: `upload.test.tsx` mocks the entire UploadDropzone component so it CANNOT test this regression — the real component must be rendered)

- [x] Task 4: Verify no regressions in existing upload flows (AC: #1, #2, #3)
  - [x] 4.1: Run full existing test suite (`npm test`) — all 384 tests pass across 32 test files
  - [ ] 4.2: Manual smoke test: upload → success → "Upload Another" → upload again works
  - [ ] 4.3: Manual smoke test: upload → success → "View Recipe" → browser back → no error shown

## Dev Notes

### Root Cause Analysis

The bug is a **callback identity cascade** triggered by `router.replace('/upload')` in `handleEnhanceComplete`:

1. `handleEnhanceComplete` (upload/page.tsx:40-44) calls `router.replace('/upload')` to strip `?enhance=` query param
2. This changes `searchParams`, causing `enhanceRecipeId` to go from a UUID to `null`
3. `UploadDropzone` receives `enhanceRecipeId={undefined}` as new prop
4. `isEnhanceMode` at line 42 (`!!enhanceRecipeId`) flips from `true` to `false`
5. This recreates `doExtraction` (depends on `isEnhanceMode`, `enhanceRecipeId`) → recreates `processFiles` (depends on `doExtraction`) → paste `useEffect` (depends on `processFiles`) re-registers listener
6. The re-registration timing window can trigger stale/duplicate invocations that fail and set `state = 'error'`

### Fix Strategy (Two-Layer Defense)

**Layer 1 — Defensive guard (symptom fix):** Add early return in `processFiles` when state is already terminal (`'success'` or `'error'`). This is the most important fix — it prevents ANY stale callback from corrupting state regardless of cause.

**Layer 2 — Root cause fix:** Stabilize `isEnhanceMode` as `useState` instead of derived value. Only allow it to update when transitioning TO enhance mode (undefined → UUID), never when transitioning away during a terminal state.

### Additional Vulnerability: `handleUrlSubmit` (line 181-203)

`handleUrlSubmit` calls `processFiles` at line 198, so the Task 1 guard covers that path. BUT it also has its own `setState('error')` at line 200-202 in a separate catch block that runs OUTSIDE of `processFiles`. If the re-render cascade occurs during URL mode, this catch could fire independently. Verify that the back-navigation scenario cannot reach this code path in URL mode, or add a terminal-state guard to `handleUrlSubmit` as well.

### Additional Note: Paste Handler Stale Closure

The paste `useEffect` (line 138) has `if (state === 'uploading') return;` but this reads `state` from closure, which can be stale. The `stateRef` pattern from Task 1 fixes `processFiles`, but the paste handler's own guard still uses the closure value. Either update the paste handler to use `stateRef.current` for its guard too, or confirm that the `processFiles` guard makes this redundant (it should — `processFiles` is called inside the paste handler, so the guard there catches it before any state mutation).

### Key Files to Modify

| File | Change |
|------|--------|
| `frontend/components/upload/UploadDropzone.tsx` | Guard `processFiles`, stabilize `isEnhanceMode` as state |
| `frontend/tests/components/UploadDropzone.test.tsx` | Add regression tests for terminal state guard |
| `frontend/tests/pages/upload.test.tsx` | Add back-navigation regression test |

### Code Patterns to Follow

**State ref pattern for callback guards (avoids stale closures):**
```typescript
const stateRef = useRef(state);
stateRef.current = state;

const processFiles = useCallback(async (files: File[]) => {
  if (stateRef.current === 'success' || stateRef.current === 'error') return;
  // ... rest of existing logic
}, [/* existing deps */]);
```

**Stabilized isEnhanceMode pattern:**
```typescript
const [isEnhanceMode, setIsEnhanceMode] = useState(!!enhanceRecipeId);

useEffect(() => {
  // Only transition INTO enhance mode, never out during terminal state
  if (enhanceRecipeId) {
    setIsEnhanceMode(true);
  } else if (state === 'idle') {
    setIsEnhanceMode(false);
  }
  // When state is 'success' or 'error', ignore prop going to undefined
}, [enhanceRecipeId, state]);
```

**Test pattern — rerender with changed props:**

NOTE: `UploadDropzone.test.tsx` already has a `renderUploadDropzone` helper (line 12-18) that wraps with `AuthProvider`. Extend it to accept optional enhance props rather than creating a new render pattern:
```typescript
// Extend existing helper to support enhance mode
function renderUploadDropzone(
  onRecipeExtracted = vi.fn(),
  enhanceRecipeId?: string,
  onEnhanceComplete = vi.fn()
) {
  return render(
    <AuthProvider>
      <UploadDropzone
        onRecipeExtracted={onRecipeExtracted}
        enhanceRecipeId={enhanceRecipeId}
        onEnhanceComplete={onEnhanceComplete}
      />
    </AuthProvider>
  )
}

// Rerender test pattern:
it('stays in success state when enhanceRecipeId changes to undefined', async () => {
  const { rerender } = renderUploadDropzone(vi.fn(), 'some-uuid', vi.fn());
  // ... trigger success state ...
  
  rerender(
    <AuthProvider>
      <UploadDropzone
        onRecipeExtracted={vi.fn()}
        enhanceRecipeId={undefined}
        onEnhanceComplete={vi.fn()}
      />
    </AuthProvider>
  );
  
  // Should still show success, NOT error
  expect(screen.queryByText(/failed/i)).not.toBeInTheDocument();
});
```

**MSW mock pattern (existing in codebase):**
```typescript
const API_BASE = '*/api';
server.use(
  http.post(`${API_BASE}/upload/extract-immediate`, () => {
    return HttpResponse.json({ id: '5', name: 'Test', ingredients: [], ... });
  })
);
```

### Optimization Notes

**Task 2.2 `useEffect` over-firing:** The suggested `[enhanceRecipeId, state]` dependency array fires on EVERY state transition (`idle` → `checking` → `uploading` → `success`). This is harmless (the effect body only acts on `enhanceRecipeId` changes) but noisy. Consider using a ref for state inside this effect if performance matters, or accept the overhead since it's just a comparison check.

**`revokePreviewIfBlob` in dependency chain:** `processFiles` depends on `revokePreviewIfBlob` (line 119), which depends on `preview` (line 58). If `preview` changes during the re-render cascade, `processFiles` also gets recreated. Not the root cause of this bug, but part of the broader dependency chain instability. The Task 1 guard makes this safe regardless.

### What NOT to Do

- Do NOT remove the `router.replace('/upload')` call — it's a valid UX improvement (cleaning the URL). The fix should make the component resilient to prop changes during terminal states.
- Do NOT add `state` to the dependency array of `processFiles` useCallback — that would recreate the callback on every state change, defeating memoization. Use a ref instead.
- Do NOT omit vitest imports — the existing test files import `{ describe, it, expect, vi, beforeEach } from 'vitest'`. Follow the existing file pattern even though globals are enabled, to maintain consistency within each file.
- Do NOT mock `fetch` directly — use MSW handlers.
- Do NOT use `next/router` — this is App Router, use `next/navigation`.

### Previous Story Context

Story 8-1 (Fix False Offline Status) is independent and also `ready-for-dev`. No cross-story dependencies. Both are frontend-only fixes.

### Project Structure Notes

- All changes are in `frontend/` — no backend modifications needed
- Component location follows existing pattern: `components/upload/UploadDropzone.tsx`
- Tests follow existing pattern: `tests/components/UploadDropzone.test.tsx`, `tests/pages/upload.test.tsx`
- No new files needed — only modifications to existing files

### References

- [Source: docs/epic-8-frontend-ux-bugs.md#Story 8.2] — Full bug description and analysis
- [Source: docs/project_context.md#Testing Rules] — vitest globals, MSW patterns
- [Source: docs/project_context.md#Framework-Specific Rules] — Next.js App Router, `next/navigation`
- [Source: frontend/components/upload/UploadDropzone.tsx] — Primary fix target
- [Source: frontend/app/upload/page.tsx] — `handleEnhanceComplete` trigger

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

No debug issues encountered.

### Completion Notes List

- **Task 1:** Added `stateRef` (useRef) to track current state without stale closures. Added early return guard in `processFiles` when `stateRef.current` is `'success'` or `'error'`.
- **Task 2:** Converted `isEnhanceMode` from derived `!!enhanceRecipeId` to `useState` + `useEffect`. Effect only transitions OUT of enhance mode when state is `'idle'`, preventing cascade during terminal states.
- **Task 3:** Added 4 regression tests: (1) enhance mode stays in success after prop→undefined, (2) paste is no-op in success state, (3) paste is no-op in error state, (4) normal mode rerender with undefined enhanceRecipeId stays in success.
- **Task 4:** Full test suite: 384/384 tests pass, 32/32 test files pass. Zero regressions. Manual smoke tests (4.2, 4.3) left for user verification.

### Change Log

- 2026-04-14: Implemented two-layer defense against false "Extraction Failed" on back-navigation. Layer 1: `stateRef` + terminal state guard in `processFiles`. Layer 2: `isEnhanceMode` stabilized as internal state. 4 regression tests added.
- 2026-04-14: **Code Review (AI)** — 5 issues found (1 HIGH, 3 MEDIUM, 1 LOW). 3 fixed automatically:
  - Fixed HIGH: Added terminal state guard to `handleUrlSubmit` (documented vulnerability, unguarded catch block)
  - Fixed MEDIUM: Updated paste handler guard to use `stateRef.current` instead of closure `state`, added terminal state check
  - Fixed MEDIUM: Added terminal state guard to `proceedWithUpload` for consistency with two-layer defense
  - Remaining MEDIUM: Tasks 4.2/4.3 manual smoke tests still pending user verification
  - Remaining LOW: `isEnhanceMode` useEffect fires on every state transition (harmless, acknowledged)

### File List

- `frontend/components/upload/UploadDropzone.tsx` — Modified (added stateRef, processFiles guard, isEnhanceMode as useState)
- `frontend/tests/components/UploadDropzone.test.tsx` — Modified (extended renderUploadDropzone helper, added 4 regression tests)
- `docs/sprint-artifacts/sprint-status.yaml` — Modified (8-2 status: ready-for-dev → in-progress → review)
- `docs/sprint-artifacts/8-2-fix-false-extraction-failed.md` — Modified (task checkboxes, dev agent record, status)
