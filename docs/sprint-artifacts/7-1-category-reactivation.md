# Story 7.1: Category Reactivation

Status: done

## Story

As an **admin**,
I want **to reactivate previously deactivated categories**,
so that **deactivation is reversible and I can restore categories I soft-deleted by mistake**.

## Background

In `CategoryManagementModal.tsx`, the action buttons (Edit/Delete) are wrapped in `{cat.is_active && (...)}` at line ~326. When a category is inactive, **zero interactive controls render** — making deactivation permanent. The backend already supports reactivation via `PUT /api/admin/categories/{type}/{id}` with `{ is_active: true }`. This is purely a frontend fix.

## Acceptance Criteria

### AC-1: Reactivate Button Visible on Inactive Categories

**Given** I am in the category management modal
**When** I view a deactivated (inactive) category
**Then** I see a "Reactivate" button (restore icon)
**And** the deactivated item is visually distinct but interactive

### AC-2: Reactivation Executes Successfully

**Given** I click "Reactivate" on a deactivated category
**When** the action completes
**Then** the category's `is_active` is set back to `true`
**And** React Query cache is invalidated so the UI updates immediately
**And** the category reappears in public filter dropdowns

### AC-3: Restored Category Returns to Normal State

**Given** I reactivate a category
**When** I view the category management modal
**Then** the restored category appears with normal styling (no gray/line-through)
**And** standard Edit/Delete buttons are available again

## Tasks / Subtasks

- [x] Task 1: Add Reactivate button for inactive categories (AC: #1, #3)
  - [x] 1.1 In `CategoryManagementModal.tsx` line ~326, replace `{cat.is_active && (...)}` with conditional rendering: show Edit+Delete for active categories, show Reactivate for inactive categories
  - [x] 1.2 Import `RotateCcw` (or `Undo2`) icon from `lucide-react` for the reactivate button
  - [x] 1.3 Add reactivate click handler using existing `updateMutation` with `{ is_active: true }`

- [x] Task 2: Implement reactivation handler (AC: #2)
  - [x] 2.1 Create `handleReactivate(cat)` function that calls `updateMutation.mutateAsync({ id: cat.id, data: { is_active: true }, token })`
  - [x] 2.2 The existing `useUpdateCategory` hook already invalidates `queryKey: adminCategories.byType(type)` on success — no extra cache work needed

- [x] Task 3: Add tests (AC: #1, #2, #3)
  - [x] 3.1 Test that inactive categories render a Reactivate button
  - [x] 3.2 Test that clicking Reactivate calls the update API with `{ is_active: true }`
  - [x] 3.3 Test that active categories still show Edit/Delete buttons (regression)
  - [x] 3.4 Update existing test at line ~346-356 that expects only 2 delete buttons — now inactive categories should show Reactivate instead

## Dev Notes

### This Is a Frontend-Only Change

**No backend changes needed.** The `PUT /api/admin/categories/{type}/{id}` endpoint already accepts `{ is_active: true }`. Verified in `AdminCategoryUpdate` schema.

### Exact Code Location (The Bug)

**File:** `frontend/components/admin/CategoryManagementModal.tsx`

**Lines 325-344 — current broken code:**
```typescript
{/* Actions */}
{cat.is_active && (
  <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
    <button onClick={() => handleEditStart(cat)} className="p-1 text-gray-400 hover:text-gray-600" title="Edit label">
      <Pencil className="h-3.5 w-3.5" />
    </button>
    <button onClick={() => handleDelete(cat)} disabled={deleteMutation.isPending} className="p-1 text-gray-400 hover:text-red-600" title="Deactivate">
      <Trash2 className="h-3.5 w-3.5" />
    </button>
  </div>
)}
```

**Fix pattern — replace with:**
```typescript
{/* Actions */}
<div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
  {cat.is_active ? (
    <>
      <button onClick={() => handleEditStart(cat)} className="p-1 text-gray-400 hover:text-gray-600" title="Edit label">
        <Pencil className="h-3.5 w-3.5" />
      </button>
      <button onClick={() => handleDelete(cat)} disabled={deleteMutation.isPending} className="p-1 text-gray-400 hover:text-red-600" title="Deactivate">
        <Trash2 className="h-3.5 w-3.5" />
      </button>
    </>
  ) : (
    <button onClick={() => handleReactivate(cat)} disabled={updateMutation.isPending} className="p-1 text-gray-400 hover:text-green-600" title="Reactivate">
      <RotateCcw className="h-3.5 w-3.5" />
    </button>
  )}
</div>
```

### Reactivation Handler

```typescript
async function handleReactivate(cat: AdminCategory) {
  try {
    await updateMutation.mutateAsync({ id: cat.id, data: { is_active: true }, token });
  } catch {
    // updateMutation.onError handles error display if configured
  }
}
```

### Existing Hooks & Imports Already Available

All of these are **already imported and initialized** in `CategoryManagementModal.tsx`:

- `useUpdateCategory(type)` → `updateMutation` (line ~35)
- `token` from `useAuth()` (line ~25)
- `AdminCategoryUpdate` interface supports `is_active?: boolean`
- Query invalidation on success is automatic (hook handles it)

**Only new import needed:** `RotateCcw` from `lucide-react` (add to existing import at line ~3)

### Inactive Category Styling (Already Exists — Don't Change)

- Row: `opacity-50` (line ~266)
- Text: `line-through text-gray-400` (line ~310)
- Click-to-edit prevention on label: `onClick={() => cat.is_active && handleEditStart(cat)}` (line ~313) — leave this as-is

### Test File Location

`frontend/tests/components/admin/CategoryManagementModal.test.tsx`

**Existing test to update:**
- Line ~346-356: Currently expects only 2 delete buttons for 3 categories (Flip is inactive). After fix, inactive categories show Reactivate instead. Update assertion to expect 2 delete buttons AND 1 reactivate button.

**Mock handler for PUT already exists** in test mocks — `updateAdminCategory` returns updated category.

### Reference Pattern: User Reactivation in users/page.tsx

The admin users page at `frontend/app/admin/users/page.tsx` lines 42-74 implements a similar toggle pattern with `is_active`. However, that uses a confirmation dialog — for category reactivation, execute immediately (low risk action, per epic spec).

### Files to Modify

| File | Change |
|------|--------|
| `frontend/components/admin/CategoryManagementModal.tsx` | Add reactivate button + handler |
| `frontend/tests/components/admin/CategoryManagementModal.test.tsx` | Add reactivation tests, update existing assertions |

### Project Structure Notes

- All changes are modifications to existing files — no new files
- Follows existing component patterns in `CategoryManagementModal.tsx`
- Uses existing hooks, mutations, and API functions — no new abstractions

### Don't Do This

- Don't add a confirmation dialog — reactivation is low-risk (per epic spec)
- Don't modify the backend — it already works
- Don't change inactive category styling — keep existing opacity-50 + line-through
- Don't add a new API function — `updateAdminCategory` already supports `is_active`
- Don't create a new hook — `useUpdateCategory` is already imported and initialized

### References

- [Source: docs/epic-7-admin-panel-bugs.md#Story 7.1] — Bug description and acceptance criteria
- [Source: docs/admin-panel-architecture.md#Category Table Naming] — Category schema pattern
- [Source: docs/project_context.md#Admin Panel Patterns] — Admin authorization and caching patterns
- [Source: docs/sprint-artifacts/6-1-code-review-remediation.md] — Previous story learnings (debug module, IntegrityError patterns)

## Dev Agent Record

### Context Reference

<!-- Story context created by SM create-story workflow -->

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

None — clean implementation, no debugging needed.

### Completion Notes List

- Imported `RotateCcw` icon from lucide-react (subtask 1.2)
- Added `handleReactivate(cat)` function using existing `updateMutation.mutateAsync` with `{ is_active: true }` (task 2)
- Replaced `{cat.is_active && (...)}` guard with ternary: active → Edit+Delete, inactive → Reactivate (subtask 1.1)
- Reactivate button uses green hover color (`hover:text-green-600`) and is disabled while mutation is pending
- Updated existing test "hides delete button for inactive items" → now also asserts 1 Reactivate button exists
- Added 3 new tests: Reactivate renders on inactive, click calls API with `is_active: true`, active items show Edit+Delete (regression)
- Full test suite: 365/365 pass, 0 regressions

### Code Review Fixes (2026-04-13)

- **[H1-Fixed]** Reactivation test now intercepts PUT request via MSW spy and asserts payload `{ is_active: true }` — was previously a no-op assertion
- **[M1-Fixed]** `handleReactivate` now shows success/error feedback via `setDeleteMessage()` — was silently swallowing errors with empty catch
- **[L1-Fixed]** Added API payload verification to reactivation test via request capture
- **[L2-Fixed]** Reactivation now shows inline success message (`"flip reactivated."`) matching deactivation feedback pattern
- **[New Test]** Added error feedback test — verifies `"Failed to reactivate category"` displays on 500 response
- **[M2-Noted]** `act()` warnings are systemic across all 24 tests (React Query + test setup issue) — pre-existing, not introduced by this story

### Change Log

- 2026-04-13: Implemented story 7-1 — category reactivation button for inactive categories
- 2026-04-13: Code review fixes — H1 test verification, M1 error feedback, L2 success feedback, new error test

### File List

- `frontend/components/admin/CategoryManagementModal.tsx` — Added RotateCcw import, handleReactivate handler with success/error feedback, replaced is_active guard with ternary rendering
- `frontend/tests/components/admin/CategoryManagementModal.test.tsx` — Updated existing assertion test, added 5 reactivation tests (render, API payload verification, regression, success feedback, error feedback)
- `docs/sprint-artifacts/sprint-status.yaml` — Updated 7-1-category-reactivation status
