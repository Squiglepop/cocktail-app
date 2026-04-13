# Story 7.2: Ingredient Row Click-to-Edit

Status: done

## Story

As an **admin**,
I want **to click anywhere on an ingredient row to open the edit modal**,
so that **the interaction is intuitive and I don't have to hunt for the tiny pencil button**.

## Background

In `frontend/app/admin/ingredients/page.tsx`, the `<tr>` element at line 174 has no `onClick` handler. The only way to trigger the edit modal is through the small pencil icon button in the Actions column (line 182). Users expect the row to be clickable — tapping it does nothing, which feels broken.

The backend is not involved at all. This is a pure frontend UX fix.

## Acceptance Criteria

### AC-1: Row Click Opens Edit Modal

**Given** I am on the ingredients admin page (`/admin/ingredients`)
**When** I click/tap anywhere on an ingredient table row
**Then** the edit modal opens pre-populated with that ingredient's data
**And** this is the same behavior as clicking the pencil icon

### AC-2: Visual Hover State

**Given** I hover over an ingredient row
**When** the cursor is over the row
**Then** the cursor changes to pointer, indicating clickability
**And** the existing `hover:bg-gray-50` highlight remains

### AC-3: Action Buttons Don't Double-Fire

**Given** I click the delete button on an ingredient row
**When** the click event fires
**Then** only the delete confirmation modal opens (not both delete + edit)
**And** the pencil edit button still works independently without double-firing

## Tasks / Subtasks

- [x] Task 1: Add onClick handler and cursor-pointer to `<tr>` (AC: #1, #2)
  - [x] 1.1 In `page.tsx` line 174, add `onClick` handler to `<tr>` that calls `setEditingIngredient(ingredient)` and `setFormError(null)`
  - [x] 1.2 Add `cursor-pointer` to the `<tr>` className (alongside existing `hover:bg-gray-50`)

- [x] Task 2: Prevent event bubbling on action buttons (AC: #3)
  - [x] 2.1 On the edit (pencil) button at line 182, add `e.stopPropagation()` before the existing handler
  - [x] 2.2 On the delete button at line 189, add `e.stopPropagation()` before the existing handler

- [x] Task 3: Add tests (AC: #1, #2, #3)
  - [x] 3.1 Test that clicking an ingredient row opens the edit modal with that ingredient's data
  - [x] 3.2 Test that clicking the delete button does NOT also open the edit modal (stopPropagation works)
  - [x] 3.3 Run existing edit-icon test (line 122-135) to confirm regression-free — verify pencil button still opens modal with correct ingredient data after stopPropagation is added

## Dev Notes

### This Is a Frontend-Only Change

**No backend changes needed.** The edit modal and `setEditingIngredient` state already work perfectly — we're just adding another trigger for it.

### Exact Code Location (The Bug)

**File:** `frontend/app/admin/ingredients/page.tsx`

**Line 174 — current code (no onClick):**
```typescript
<tr key={ingredient.id} className="hover:bg-gray-50">
```

**Fix — add onClick and cursor-pointer:**
```typescript
<tr
  key={ingredient.id}
  className="hover:bg-gray-50 cursor-pointer"
  onClick={() => { setEditingIngredient(ingredient); setFormError(null); }}
>
```

### Action Buttons — Add stopPropagation

**Line 182 — edit button (currently):**
```typescript
<button
  onClick={() => { setEditingIngredient(ingredient); setFormError(null); }}
```

**Fix:**
```typescript
<button
  onClick={(e) => { e.stopPropagation(); setEditingIngredient(ingredient); setFormError(null); }}
```

**Line 189 — delete button (currently):**
```typescript
<button
  onClick={() => { setDeletingIngredient(ingredient); setDeleteError(null); }}
```

**Fix:**
```typescript
<button
  onClick={(e) => { e.stopPropagation(); setDeletingIngredient(ingredient); setDeleteError(null); }}
```

### Why stopPropagation on the Edit Button Too

Even though both the row `onClick` and the edit button do the same thing (`setEditingIngredient`), without `stopPropagation` the handler fires twice — once from the button and once from the row. While functionally harmless in this case (same state set twice), it's sloppy and could cause unexpected behavior if the handler ever gains side effects (e.g., analytics tracking). Clean separation now.

### Existing State & Handlers Already Available

All of these are **already in the component** — no new state or hooks needed:

- `editingIngredient` state (line 31)
- `setEditingIngredient` setter (line 31)
- `setFormError` setter (line 33)
- `deletingIngredient` state (line 32)
- `setDeletingIngredient` setter (line 32)
- `setDeleteError` setter (line 34)
- `IngredientFormModal` renders when `editingIngredient !== null` (line 249)

### Test File Location

`frontend/tests/app/admin/IngredientsPage.test.tsx`

**Existing test to keep passing (line 122-135):**
- "clicking edit icon opens edit modal" — still works because the pencil button still calls `setEditingIngredient`

**New tests to add:**

```typescript
it('clicking ingredient row opens edit modal', async () => {
  const user = userEvent.setup()
  renderPage()

  await waitFor(() => {
    expect(screen.getByText('Lime Juice')).toBeInTheDocument()
  })

  // Click the row itself (on the name cell)
  await user.click(screen.getByText('Lime Juice'))

  expect(screen.getByText('Edit Ingredient')).toBeInTheDocument()
  expect(screen.getByDisplayValue('Lime Juice')).toBeInTheDocument()
})

it('clicking delete button does not open edit modal', async () => {
  const user = userEvent.setup()
  renderPage()

  await waitFor(() => {
    expect(screen.getByText('Lime Juice')).toBeInTheDocument()
  })

  const deleteButton = screen.getByLabelText('Delete Lime Juice')
  await user.click(deleteButton)

  // Delete confirmation should open
  expect(screen.getByText(/are you sure/i)).toBeInTheDocument()
  // Edit modal should NOT open
  expect(screen.queryByText('Edit Ingredient')).not.toBeInTheDocument()
})
```

### Files to Modify

| File | Change |
|------|--------|
| `frontend/app/admin/ingredients/page.tsx` | Add row onClick + cursor-pointer, add stopPropagation to action buttons |
| `frontend/tests/app/admin/IngredientsPage.test.tsx` | Add row-click and stopPropagation tests |

### Project Structure Notes

- All changes are modifications to existing files — no new files
- No new imports, hooks, state, or abstractions needed
- Total code delta: ~6 lines changed, ~20 lines of tests added

### Don't Do This

- Don't add a separate click handler function — the inline arrow is the same pattern used by the existing edit button
- Don't add hover styling beyond `cursor-pointer` — `hover:bg-gray-50` already exists on the `<tr>`
- Don't make the entire row a link/anchor — it's a table row with a click handler, consistent with the existing pattern
- Don't modify the `IngredientFormModal` — it already works correctly
- Don't add `role="button"` to the `<tr>` — it's a table row with existing interactive children; adding a role would confuse screen readers

### References

- [Source: docs/epic-7-admin-panel-bugs.md#Story 7.2] — Bug description and acceptance criteria
- [Source: frontend/app/admin/ingredients/page.tsx] — Component with the bug
- [Source: frontend/tests/app/admin/IngredientsPage.test.tsx] — Existing test suite

## Dev Agent Record

### Context Reference

<!-- Story context created by SM create-story workflow -->

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

None — clean implementation, no debugging needed.

### Completion Notes List

- Added `onClick` handler to `<tr>` calling `setEditingIngredient(ingredient)` and `setFormError(null)` (subtask 1.1)
- Added `cursor-pointer` to `<tr>` className alongside existing `hover:bg-gray-50` (subtask 1.2)
- Added `e.stopPropagation()` to edit (pencil) button onClick (subtask 2.1)
- Added `e.stopPropagation()` to delete button onClick (subtask 2.2)
- Added test "clicking ingredient row opens edit modal" — verifies row click opens modal with correct ingredient data (subtask 3.1)
- Added test "clicking delete button does not open edit modal" — verifies stopPropagation prevents double-fire (subtask 3.2)
- Existing test "clicking edit icon opens edit modal" passes unmodified — regression-free (subtask 3.3)
- Full test suite: 367/367 pass, 0 regressions

### Change Log

- 2026-04-13: Implemented story 7-2 — ingredient row click-to-edit with stopPropagation on action buttons
- 2026-04-13: Code review — 0 HIGH, 0 MEDIUM, 3 LOW findings. Fixed 1 (added cursor-pointer test assertion for AC-2). 2 LOW issues noted but not actioned (keyboard accessibility is by-design trade-off; act() warnings are pre-existing).

### Senior Developer Review (AI)

**Reviewer:** Claude Opus 4.6 (1M context)
**Date:** 2026-04-13
**Outcome:** Approve

**Findings (0 HIGH, 0 MEDIUM, 3 LOW):**

1. **(LOW, FIXED)** No test assertion for AC-2 (cursor-pointer class). Added `expect(row).toHaveClass('cursor-pointer')` to row-click test.
2. **(LOW, NOTED)** Keyboard accessibility gap — `<tr>` onClick has no tabIndex/onKeyDown. Acknowledged trade-off: pencil button remains keyboard-accessible. Story explicitly documents this decision.
3. **(LOW, NOTED)** Pre-existing `act()` warnings in test output from debounce timer. Not introduced by this story.

**Verification:**
- All 3 ACs implemented and verified against code
- All 6 subtasks marked [x] confirmed done with file:line evidence
- 15/15 tests pass (including new cursor-pointer assertion)
- Git diff matches story File List (3 files)
- Code follows existing patterns (inline arrows, stopPropagation)

### File List

- `frontend/app/admin/ingredients/page.tsx` — Added row onClick + cursor-pointer, added stopPropagation to edit and delete buttons
- `frontend/tests/app/admin/IngredientsPage.test.tsx` — Added 2 new tests (row click opens modal, delete doesn't trigger edit) + cursor-pointer assertion
- `docs/sprint-artifacts/sprint-status.yaml` — Updated 7-2-ingredient-row-click-to-edit status
