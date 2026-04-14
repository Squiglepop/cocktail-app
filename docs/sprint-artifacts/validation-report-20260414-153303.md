# Validation Report

**Document:** docs/sprint-artifacts/8-1-fix-false-offline-status.md
**Checklist:** .bmad/bmm/workflows/4-implementation/create-story/checklist.md
**Date:** 2026-04-14T15:33:03

## Summary
- Overall: 18/22 passed (82%)
- Critical Issues: 2
- Partial Issues: 2

---

## Section Results

### Step 1: Story Structure & Metadata
Pass Rate: 5/5 (100%)

[✓] **Story has valid status field**
Evidence: Line 3 — `Status: ready-for-dev`

[✓] **User story format (As a / I want / So that)**
Evidence: Lines 6-9 — proper Connextra format with user role, action, and value.

[✓] **Acceptance Criteria present with BDD format**
Evidence: Lines 12-44 — four ACs, all use Given/When/Then structure with clear assertions.

[✓] **Tasks/Subtasks broken into actionable items**
Evidence: Lines 46-67 — four tasks with 13 subtasks, each referencing specific AC numbers.

[✓] **Dev Notes section with implementation guidance**
Evidence: Lines 69-210 — comprehensive dev notes with code examples, anti-patterns, and references.

### Step 2: Source Document Alignment
Pass Rate: 4/4 (100%)

[✓] **Story aligns with Epic requirements**
Evidence: Epic 8.1 (docs/epic-8-frontend-ux-bugs.md lines 16-63) defines the same bug, same root cause, same ACs. Story's ACs are a superset of the epic's ACs (adds debug logging AC-4, which the epic only mentions loosely).

[✓] **Deliberate deviations from Epic are documented**
Evidence: Lines 183-185 — Epic suggests "Fix 3: Consider pausing checks during upload" but the story explicitly rejects this in "Don't Do This" section with reasoning: "unnecessary complexity... timeout increase + debounce fix the root cause."

[✓] **Architecture/project context alignment**
Evidence: Story correctly identifies `OfflineProvider` position in provider hierarchy (project_context.md line 192: Query → Auth → Offline → Favourites).

[✓] **Cross-story dependencies identified**
Evidence: Lines 141-151 — downstream impact table listing all components consuming `isOnline`. Line 205 references previous story 7-3 patterns.

### Step 3: Technical Specification Accuracy
Pass Rate: 4/6 (67%)

[✓] **Line number references match actual code**
Evidence: Story references line 41 for `setTimeout(() => controller.abort(), 3000)` — verified at offline-context.tsx:41. Story references line 57 for `setIsOnline(false)` — verified at offline-context.tsx:57. Story references line 79 for interval — verified at offline-context.tsx:79.

[✓] **Implementation pattern is syntactically correct**
Evidence: Lines 89-133 — TypeScript compiles, uses correct React hooks API, proper async/await.

[⚠] **Import changes documented**
Evidence: Story's implementation pattern uses `useRef` but current code (offline-context.tsx:3) only imports `useState, useEffect, useCallback, ReactNode`. **No task or subtask mentions adding `useRef` to the import line.** The dev agent must add `useRef` to the import or it will get a build error.
Impact: Dev agent following tasks literally will miss the import, causing `ReferenceError: useRef is not defined`.

[✗] **Testing approach aligns with project conventions**
Evidence: Story says (line 156): "MSW is NOT needed — Mock `fetch` directly". Project context (project_context.md line 389) says under "Don't Do This": "Mock fetch directly (use MSW handlers)". The story provides justification (line 156-157: "testing the fetch-based health check itself, not an API contract"), which is *valid reasoning*, but the dev agent will face a direct contradiction between the story and the project bible. The story must acknowledge this is an **intentional deviation from project_context.md** — not just say MSW isn't needed.
Impact: Dev agent may either (a) follow project_context.md and use MSW, adding unnecessary complexity, or (b) follow the story and get flagged in code review for violating project conventions. The story should explicitly say "This is an exception to the project_context.md MSW rule because..."

[✓] **Correct framework versions and patterns**
Evidence: Uses React 18 hooks (useRef, useState, useCallback), no deprecated APIs, no wrong library versions.

[✓] **File paths are correct**
Evidence: `frontend/lib/offline-context.tsx` exists (verified). `frontend/tests/lib/` directory exists (verified: contains api.test.ts and auth-context.test.tsx). Test file path `frontend/tests/lib/offline-context.test.tsx` follows existing convention.

### Step 4: Task Completeness
Pass Rate: 3/4 (75%)

[✓] **Task 1 (timeout increase) — complete and precise**
Evidence: Lines 48-49 — exact file, exact line, exact old value, exact new value.

[⚠] **Task 2 (debounce) — mostly complete, missing isOnlineRef**
Evidence: Lines 51-55 — correctly specifies `failureCountRef` with `useRef<number>`. However, the implementation pattern (line 92) also introduces `isOnlineRef = useRef(true)` which is used in Task 3 for debug logging. `isOnlineRef` is not mentioned anywhere in the task breakdown. The dev agent must infer its existence from the code example.
Impact: Minor — the code example is clear enough, but a task-driven dev agent that follows subtasks literally will miss `isOnlineRef` and then fail to implement Task 3 correctly.

[✓] **Task 3 (debug logging) — complete**
Evidence: Lines 57-61 — references correct debug function (`debug.log`), correct log messages, mentions stale closure issue with functional updater pattern.

[✓] **Task 4 (tests) — complete with specific scenarios**
Evidence: Lines 62-67 — five specific test cases covering single failure, double failure, reset, timeout value, and regression suite.

### Step 5: LLM Dev Agent Optimization
Pass Rate: 2/3 (67%)

[✓] **Actionable and specific — not vague**
Evidence: Tasks include exact line numbers, exact values, exact variable names. No ambiguity about what to change.

[✓] **Don't Do This section prevents common mistakes**
Evidence: Lines 183-191 — eight explicit anti-patterns covering over-engineering (pauseHealthCheck), timing changes, navigator.onLine, interface changes, useState misuse. Strong guardrails.

[✗] **Self-contained — dev agent doesn't need to resolve contradictions**
Evidence: The MSW vs fetch mock contradiction (see Step 3 above) means the dev agent must independently decide which authority to follow. A well-optimized story should resolve all contradictions so the dev agent doesn't waste tokens or make wrong choices.
Impact: Token waste and potential implementation error.

---

## Failed Items

### 1. Testing Approach Contradicts project_context.md (CRITICAL)

**Issue:** Story says mock fetch directly; project_context.md says never mock fetch directly.

**Recommendation:** Add an explicit note in the Testing Approach section:

```markdown
**Exception to project_context.md MSW rule:** This story mocks `fetch` directly instead
of using MSW because we are testing the health check mechanism itself (fetch + AbortController
timeout behavior), not an API contract. MSW intercepts at the network layer and would bypass
the AbortController timeout we need to test. This is the one case where direct fetch mocking
is the correct approach.
```

### 2. Story Not Self-Contained — Missing isOnlineRef Subtask (MODERATE)

**Issue:** `isOnlineRef` appears in the implementation pattern but has no corresponding subtask.

**Recommendation:** Add subtask 2.5:
```markdown
- [ ] 2.5 Add `isOnlineRef = useRef(true)` to mirror `isOnline` state for reading current value inside the `useCallback` without adding it as a dependency. Update it inline before each `setIsOnline()` call.
```

---

## Partial Items

### 1. Import Changes Not in Tasks (MINOR)

**Issue:** `useRef` needs to be added to the import on line 3 but no task mentions this.

**Recommendation:** Add to Task 2.1:
```markdown
- [ ] 2.1 Add `useRef` to the React import on line 3, then add a `useRef<number>` for `failureCount`...
```

### 2. isOnlineRef Missing from Task Breakdown (MODERATE)

See Failed Items #2 above.

---

## Recommendations

### 1. Must Fix (2 items)
1. **Add explicit MSW exception note** — Resolve the contradiction between story and project_context.md so the dev agent doesn't have to decide.
2. **Add `isOnlineRef` subtask** — Task 2 should include creating and maintaining the `isOnlineRef` that Task 3 depends on.

### 2. Should Improve (1 item)
1. **Add `useRef` import to Task 2.1** — Mention adding the import to prevent build errors.

### 3. Consider (0 items)
Story is well-structured and comprehensive. No optional improvements needed.
