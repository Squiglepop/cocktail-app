# Epic 7: Admin Panel Bug Fixes

Admin panel has three usability bugs discovered during manual testing that prevent core administrative workflows from being completed.

**Priority:** High — these are blocking bugs in shipped functionality.

## Bug Summary

| # | Area | Issue |
|---|------|-------|
| 7.1 | Category Management | Cannot reactivate deactivated categories |
| 7.2 | Ingredient Admin | Clicking ingredient row does nothing; only pencil button works |
| 7.3 | User Management | No way to edit user details (only toggles work) |

---

## Story 7.1: Category Reactivation

**As an** admin,
**I want** to reactivate previously deactivated categories,
**So that** deactivation is reversible and I can restore categories I soft-deleted by mistake.

### Background

In `CategoryManagementModal.tsx`, the action buttons (Edit/Delete) are only rendered when `cat.is_active === true` (line ~326). Deactivated categories appear grayed-out with line-through styling but have zero interactive controls — making deactivation a permanent one-way operation.

The backend already supports reactivation via `PUT /api/admin/categories/{type}/{id}` with `{ is_active: true }`. This is purely a frontend gap.

### Acceptance Criteria

**Given** I am in the category management modal
**When** I view a deactivated (inactive) category
**Then** I see a "Reactivate" button (or equivalent restore action)
**And** the deactivated item is visually distinct but still interactive

**Given** I click "Reactivate" on a deactivated category
**When** the action completes
**Then** the category's `is_active` is set back to `true`
**And** the category reappears in public filter dropdowns
**And** React Query cache is invalidated so the UI updates immediately

**Given** I reactivate a category
**When** I view the category management modal
**Then** the restored category appears with normal styling (no gray/line-through)
**And** standard Edit/Delete buttons are available again

### Technical Notes

- Backend endpoint already supports this — no backend changes needed
- Use the existing `updateCategory` mutation with `{ is_active: true }`
- Add a restore/undo icon button for inactive categories where action buttons currently don't render
- Consider a brief confirmation or just execute immediately (low risk action)

---

## Story 7.2: Ingredient Row Click-to-Edit

**As an** admin,
**I want** to click anywhere on an ingredient row to open the edit modal,
**So that** the interaction is intuitive and I don't have to hunt for the tiny pencil button.

### Background

In `frontend/app/admin/ingredients/page.tsx`, the `<tr>` element at line ~174 has no `onClick` handler. The only way to trigger the edit modal is through the small pencil icon button in the Actions column. Users expect the row to be clickable — tapping it does nothing, which feels broken.

The "search then click" workaround likely works because search results have a different rendering path or the user accidentally clicks the button.

### Acceptance Criteria

**Given** I am on the ingredients admin page (`/admin/ingredients`)
**When** I click/tap anywhere on an ingredient table row
**Then** the edit modal opens pre-populated with that ingredient's data
**And** this is the same behavior as clicking the pencil icon

**Given** I click on an ingredient row
**When** the edit modal opens
**Then** the row shows a visual hover state indicating clickability (cursor: pointer)

**Given** I click the pencil button specifically
**When** the click event fires
**Then** it still works as before (event doesn't double-fire)

### Technical Notes

- Add `onClick={() => { setEditingIngredient(ingredient); setShowForm(true); }}` to the `<tr>` element
- Add `cursor-pointer` to the row's className
- Use `e.stopPropagation()` on the delete button to prevent row click from triggering on delete
- Minimal change — this is a one-liner plus hover styling

---

## Story 7.3: User Edit Capability

**As an** admin,
**I want** to edit user details (display name, email) from the user management page,
**So that** I can correct user information without requiring direct database access.

### Background

In `frontend/app/admin/users/page.tsx`, the user table only has two interactive elements: the status toggle (active/inactive) and the admin privilege toggle. There is no edit button, no edit modal, and no form for modifying user profile fields.

The backend endpoint `PATCH /api/admin/users/{id}` exists and supports updating `is_active` and `is_admin`. It may need to be extended to support `display_name` and potentially `email` updates.

### Acceptance Criteria

**Given** I am on the user management page (`/admin/users`)
**When** I view the user table
**Then** each row has an Edit button/icon (pencil) in the Actions column

**Given** I click Edit on a user row
**When** the edit modal opens
**Then** I see a form pre-populated with the user's current `display_name`
**And** the email field is displayed (read-only or editable based on backend support)

**Given** I modify the display name and submit
**When** the update completes
**Then** the user table refreshes to show the new display name
**And** a success toast confirms the update
**And** an audit log entry is created

**Given** I try to edit my own user record
**When** I modify non-privilege fields (display_name)
**Then** the update proceeds normally (self-edit of profile data is allowed)

### Technical Notes

- **Backend:** Check if `PATCH /api/admin/users/{id}` supports `display_name` updates. If not, extend the endpoint schema to accept optional `display_name` field.
- **Frontend:** Create a `UserEditModal` component (similar to ingredient edit modal pattern)
- Add an `editingUser` state and pencil button to user rows
- Scope to `display_name` only for now — email changes have identity/auth implications (defer to Phase 2)

---

## Dependencies & Ordering

Stories are independent and can be worked in parallel:
- **7.1** — Frontend only, ~30 min
- **7.2** — Frontend only, ~15 min
- **7.3** — Frontend + possible backend extension, ~1-2 hours

## Related Epics

- Epic 1 (Story 1.6): Admin Category Management — original implementation
- Epic 2 (Story 2.1): Ingredient Admin CRUD — original implementation
- Epic 3 (Story 3.2): User Status Management — original implementation
- Epic 5 (Stories 5.3, 5.4, 5.5): Admin UI — where the frontend was built
