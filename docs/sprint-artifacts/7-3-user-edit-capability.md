# Story 7.3: User Edit Capability

Status: done

## Story

As an **admin**,
I want **to edit user details (display name) from the user management page**,
so that **I can correct user information without requiring direct database access**.

## Background

In `frontend/app/admin/users/page.tsx`, the user table has two interactive elements: the status toggle (active/inactive) and the admin privilege toggle. There is no edit button, no edit modal, and no form for modifying user profile fields like `display_name`.

The backend endpoint `PATCH /api/admin/users/{id}` currently only supports `is_active` and `is_admin` fields. It **must be extended** to accept `display_name` updates. The User SQLAlchemy model already has a `display_name: Optional[String(255)]` column — no migration needed.

Email editing is explicitly **out of scope** — it has identity/auth implications (deferred to a future epic).

## Acceptance Criteria

### AC-1: Edit Button Visible on User Rows

**Given** I am on the user management page (`/admin/users`)
**When** I view the user table
**Then** each row has an Edit button/icon (pencil) in the Actions column

### AC-2: Edit Modal Opens with Pre-populated Data

**Given** I click Edit on a user row
**When** the edit modal opens
**Then** I see a form pre-populated with the user's current `display_name` (or empty if null)
**And** the email field is displayed as read-only context (not editable)

### AC-3: Display Name Update Succeeds

**Given** I modify the display name and submit
**When** the update completes
**Then** the user table refreshes to show the new display name
**And** a success toast/message confirms the update
**And** an audit log entry is created

### AC-4: Self-Edit of Display Name Allowed

**Given** I try to edit my own user record
**When** I modify the display_name field
**Then** the update proceeds normally (self-edit of profile data is allowed)

## Tasks / Subtasks

- [x] Task 1: Extend backend PATCH endpoint to support display_name (AC: #3)
  - [x] 1.1 In `backend/app/schemas/user.py`, add `display_name: Optional[str] = Field(None, max_length=255)` to `UserStatusUpdate` schema (import `Field` from pydantic)
  - [x] 1.2 Update the `at_least_one_field` model_validator to include `display_name` in the check
  - [x] 1.3 In `backend/app/services/user_service.py` `update_user_status()` (line ~87), add `if data.display_name is not None: user.display_name = data.display_name`
  - [x] 1.4 In `backend/app/routers/admin.py` (line ~410), capture `old_display_name = user.display_name` before the update call. After line ~423, add audit block for display_name changes
  - [x] 1.5 Add backend tests: PATCH with display_name returns updated name, PATCH with only display_name works, PATCH with 256-char display_name returns 422, 401/403 auth tests

- [x] Task 2: Update frontend API types (AC: #3)
  - [x] 2.1 In `frontend/lib/api.ts`, add `display_name?: string` to `UserStatusUpdate` interface (line ~1033)

- [x] Task 3: Create UserEditModal component (AC: #2, #3)
  - [x] 3.1 Create `frontend/components/admin/UserEditModal.tsx` following `IngredientFormModal` pattern
  - [x] 3.2 Modal shows: email (read-only), display_name input (editable), Save/Cancel buttons
  - [x] 3.3 Form initializes with user's current display_name (or empty string if null)
  - [x] 3.4 Submit calls `onSave({ display_name: value })` — only sends changed field

- [x] Task 4: Add edit button and modal to users page (AC: #1, #2, #4)
  - [x] 4.1 Add `editingUser: AdminUser | null` state variable to `users/page.tsx`
  - [x] 4.2 Add pencil icon button in a new Actions column (after Last Login column)
  - [x] 4.3 Wire pencil click: `setEditingUser(user)`
  - [x] 4.4 Add `handleEditSave` handler that calls `updateStatus.mutateAsync({ id, data: { display_name } })`, sets success message on completion, sets `editError` on failure (NOT page-level `error`)
  - [x] 4.5 Render `UserEditModal` at bottom of component, controlled by `editingUser` state
  - [x] 4.6 Add `successMessage` state (auto-clear after 3s) and `editError` state (modal-scoped, cleared on open/close)

- [x] Task 5: Add frontend tests (AC: #1, #2, #3, #4)
  - [x] 5.1 Test that edit button (pencil) renders on each user row
  - [x] 5.2 Test that clicking edit opens modal with user's display_name pre-populated
  - [x] 5.3 Test that submitting modal calls PATCH with `{ display_name: "New Name" }`
  - [x] 5.4 Test that modal shows email as read-only context
  - [x] 5.5 Test self-edit is allowed (current user can edit own display_name)
  - [x] 5.6 Test success message appears after saving and auto-clears
  - [x] 5.7 Run full test suite to confirm 0 regressions

## Dev Notes

### Backend Changes Required

**This is NOT frontend-only.** The backend PATCH endpoint must be extended.

**File: `backend/app/schemas/user.py`** — Extend `UserStatusUpdate`:
```python
from pydantic import BaseModel, Field, model_validator

class UserStatusUpdate(BaseModel):
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    display_name: Optional[str] = Field(None, max_length=255)  # NEW — matches DB String(255)

    @model_validator(mode="after")
    def at_least_one_field(self):
        if self.is_active is None and self.is_admin is None and self.display_name is None:
            raise ValueError("At least one of is_active, is_admin, or display_name must be provided")
        return self
```

**File: `backend/app/services/user_service.py`** — Add display_name handling in `update_user_status()` (after line ~95, the `is_admin` block):
```python
if data.display_name is not None and data.display_name != user.display_name:
    user.display_name = data.display_name
    changes.append(f"display_name updated to '{data.display_name}'")
```

**File: `backend/app/routers/admin.py`** — Audit logging for display_name. The router handles audit logging (NOT the service). Add `old_display_name` capture and a new audit block:

At line ~410 (alongside existing old state captures):
```python
old_is_active = user.is_active
old_is_admin = user.is_admin
old_display_name = user.display_name  # NEW
```

After line ~423 (after the existing `is_admin` audit block):
```python
if data.display_name is not None and data.display_name != old_display_name:
    _audit_log(db, admin.id, "user_update_profile", "user", user.id,
               {"email": updated_user.email, "field": "display_name",
                "old_value": old_display_name, "new_value": updated_user.display_name})
```

### Self-Modification Rules

The existing `update_user_status` service (line ~80-84) prevents self-deactivation and self-admin-revoke. **Self-edit of display_name IS allowed** — no security implication. The `if user.id == admin_id:` block in the service does NOT need modification — it only checks `is_active` and `is_admin`.

### Frontend UserEditModal Pattern

Follow the `IngredientFormModal` pattern exactly:

**File: `frontend/components/admin/IngredientFormModal.tsx`** — Reference for:
- Modal overlay with backdrop click to close
- `useEffect` to initialize form state when modal opens
- Escape key handler to close
- Form with controlled inputs
- Save/Cancel buttons with loading state

**UserEditModal props:**
```typescript
interface UserEditModalProps {
  isOpen: boolean;
  user: AdminUser | null;
  onClose: () => void;
  onSave: (data: { display_name: string }) => void;
  isSaving: boolean;
  error: string | null;
}
```

**Key behaviors:**
- `isOpen` controlled by `editingUser !== null`
- Email displayed as read-only `<p>` or disabled input (not editable)
- Display name input pre-populated from `user.display_name ?? ''`, with `maxLength={255}`
- Submit button disabled while `isSaving`
- Cancel button and backdrop click call `onClose`

### Users Page Changes

**File: `frontend/app/admin/users/page.tsx`**

**New state (add near line 23):**
```typescript
const [editingUser, setEditingUser] = useState<AdminUser | null>(null);
```

**New Actions column in table header (after Last Login, around line 172):**
```tsx
<th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
```

**New Actions cell in table body (after Last Login cell):**
```tsx
<td className="px-6 py-4 whitespace-nowrap">
  <button
    onClick={() => { setEditingUser(user); setEditError(null); }}
    className="p-1 text-gray-400 hover:text-gray-600"
    title="Edit user"
  >
    <Pencil className="h-4 w-4" />
  </button>
</td>
```

**New state (add near line 23, alongside existing `error`):**
```typescript
const [successMessage, setSuccessMessage] = useState<string | null>(null);
const [editError, setEditError] = useState<string | null>(null);
```

**Auto-clear success message (add inside existing useEffect or as new effect):**
```typescript
useEffect(() => {
  if (successMessage) {
    const timer = setTimeout(() => setSuccessMessage(null), 3000);
    return () => clearTimeout(timer);
  }
}, [successMessage]);
```

**handleEditSave handler:**
```typescript
async function handleEditSave(data: { display_name: string }) {
  if (!editingUser) return;
  try {
    await updateStatus.mutateAsync({
      id: editingUser.id,
      data: { display_name: data.display_name },
      token,
    });
    setSuccessMessage(`Updated display name for ${editingUser.email}`);
    setEditError(null);
    setEditingUser(null);
  } catch (err: unknown) {
    setEditError(err instanceof Error ? err.message : 'Failed to update user');
  }
}
```

**Render success message (above the table, alongside existing error display):**
```tsx
{successMessage && (
  <div className="flex items-center gap-2 p-3 bg-green-50 border border-green-200 rounded-lg text-green-800 text-sm">
    <CheckCircle className="h-4 w-4" />
    {successMessage}
  </div>
)}
```

**Render modal at bottom of component:**
```tsx
<UserEditModal
  isOpen={editingUser !== null}
  user={editingUser}
  onClose={() => { setEditingUser(null); setEditError(null); }}
  onSave={handleEditSave}
  isSaving={updateStatus.isPending}
  error={editError}
/>
```

### Import Additions

**users/page.tsx:**
- Add `Pencil` to `lucide-react` import
- Add `UserEditModal` import from `@/components/admin/UserEditModal`

### Existing Hooks & Mutations — Reuse Everything

- `useUpdateUserStatus()` → `updateStatus` mutation — already exists, already invalidates cache on success
- `useAuth()` → `token`, `currentUser` — already imported
- `error` / `setError` state — already exists at line 24 (used for page-level alerts like self-edit prevention; do NOT reuse for the modal)
- **NEW:** `successMessage` / `setSuccessMessage` state — add for AC-3 success feedback (auto-clears after 3s)
- **NEW:** `editError` / `setEditError` state — modal-scoped error state (follows `formError` pattern from ingredients page). Cleared on modal open/close. Prevents dual-display with page-level error banner.
- No new hooks, no new API functions, no new mutations needed

### Frontend API Type Change

**File: `frontend/lib/api.ts`** — Add `display_name?: string` to `UserStatusUpdate` interface (line ~1033). The `updateUserStatus` function (line ~1064) already sends `data` as JSON body — no changes needed to the function itself.

### Audit Logging

Audit logging for user updates is handled in the **router** (`backend/app/routers/admin.py` lines 416-423), NOT the service. The router has explicit conditional blocks for `is_active` and `is_admin` changes. A new audit block must be added for `display_name` changes using action name `user_update_profile` (follows project convention `{entity}_{verb}`). See the router code example above in "Backend Changes Required."

### Test File Locations

| Area | File |
|------|------|
| Backend PATCH tests | `backend/tests/test_admin_users.py` (or add to existing admin test file) |
| Frontend page tests | `frontend/tests/app/admin/UsersPage.test.tsx` |
| Frontend modal tests | Can be added to `UsersPage.test.tsx` (modal renders inline) |

**Backend test additions:**
```python
def test_update_user_display_name(client, admin_headers, test_user):
    response = client.patch(
        f"/api/admin/users/{test_user.id}",
        json={"display_name": "New Display Name"},
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["display_name"] == "New Display Name"

def test_update_user_display_name_only(client, admin_headers, test_user):
    """display_name alone satisfies at_least_one_field validator."""
    response = client.patch(
        f"/api/admin/users/{test_user.id}",
        json={"display_name": "Solo Field"},
        headers=admin_headers,
    )
    assert response.status_code == 200

def test_update_user_display_name_too_long(client, admin_headers, test_user):
    """display_name exceeding 255 chars returns 422."""
    response = client.patch(
        f"/api/admin/users/{test_user.id}",
        json={"display_name": "x" * 256},
        headers=admin_headers,
    )
    assert response.status_code == 422
```

**Frontend test additions (MSW handler):**
```typescript
// Add to existing mock handlers:
http.patch('*/api/admin/users/:id', async ({ request }) => {
  const data = await request.json();
  return HttpResponse.json({
    id: '1',
    email: 'admin@test.com',
    display_name: data.display_name ?? 'Admin User',
    is_active: data.is_active ?? true,
    is_admin: data.is_admin ?? true,
    message: 'User updated',
  });
}),
```

### Project Structure Notes

| File | Action |
|------|--------|
| `backend/app/schemas/user.py` | Modify — add display_name with Field(max_length=255) to UserStatusUpdate |
| `backend/app/services/user_service.py` | Modify — handle display_name update in changes list |
| `backend/app/routers/admin.py` | Modify — capture old_display_name, add audit block for display_name changes |
| `backend/tests/test_auth.py` (or new test file) | Add — backend PATCH tests for display_name (including 256-char 422 test) |
| `frontend/lib/api.ts` | Modify — add display_name to UserStatusUpdate interface |
| `frontend/components/admin/UserEditModal.tsx` | **Create** — new modal component |
| `frontend/app/admin/users/page.tsx` | Modify — add edit state, successMessage state, button, handler, modal |
| `frontend/tests/app/admin/UsersPage.test.tsx` | Modify — add edit modal tests |

### Don't Do This

- Don't make email editable — explicitly out of scope (auth implications)
- Don't create a new API endpoint — extend the existing PATCH endpoint
- Don't create a new mutation hook — `useUpdateUserStatus` already handles PATCH
- Don't add a confirmation dialog for display_name edits — low-risk action, save directly
- Don't add row-click-to-edit on user rows — the toggles already use row clicks; adding would conflict with the status/admin toggles
- Don't add `role="button"` or keyboard handlers to the pencil — it's already a `<button>` element
- Don't guard self-edit of display_name — only self-deactivation and self-admin-revoke are restricted
- Don't modify the ConfirmActionModal — it's for status/admin changes, not profile edits
- Don't use react-hook-form — project uses controlled components with useState (per project_context.md)

### References

- [Source: docs/epic-7-admin-panel-bugs.md#Story 7.3] — Bug description and acceptance criteria
- [Source: docs/project_context.md#Admin Panel Patterns] — Admin authorization, caching, audit patterns
- [Source: docs/project_context.md#Defensive Coding Patterns] — Service→Router error convention, SAVEPOINT pattern
- [Source: docs/sprint-artifacts/7-1-category-reactivation.md] — Previous story: reactivation pattern, code review learnings
- [Source: docs/sprint-artifacts/7-2-ingredient-row-click-to-edit.md] — Previous story: row click pattern, stopPropagation, cursor-pointer
- [Source: frontend/components/admin/IngredientFormModal.tsx] — Reference modal implementation pattern
- [Source: backend/app/services/user_service.py] — Service with self-modification guards and audit logging
- [Source: backend/app/schemas/user.py] — Current UserStatusUpdate schema (needs extension)

## Dev Agent Record

### Context Reference

<!-- Story context created by SM create-story workflow -->

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

### Completion Notes List

- Task 1: Extended `UserStatusUpdate` schema with `display_name: Optional[str] = Field(None, max_length=255)`, updated validator, service, and router with audit logging (`user_update_profile` action). 4 backend tests added covering PATCH with display_name, display_name only, 256-char rejection, and self-edit.
- Task 2: Added `display_name?: string` to frontend `UserStatusUpdate` interface.
- Task 3: Created `UserEditModal` component following `IngredientFormModal` pattern — email read-only, display_name input with maxLength=255, escape/backdrop close, save/cancel buttons.
- Task 4: Added edit pencil button in Actions column, `editingUser`/`successMessage`/`editError` state, `handleEditSave` handler, auto-clear success after 3s, rendered `UserEditModal`.
- Task 5: Added 6 frontend tests (edit button renders, modal pre-populates, PATCH called, email read-only, self-edit allowed, success auto-clears). Updated MSW handler. Full suite: 373 frontend + 556 backend = 0 regressions.

### Change Log

- 2026-04-13: Implemented Story 7-3 User Edit Capability — backend PATCH extension + frontend edit modal with full test coverage.
- 2026-04-13: Code review fixes — (H2) `_audit_log` SAVEPOINT pattern, (H1) audit log test for `user_update_profile`, (M1) edit modal error state test, (M2) suppress false success message when no change applied.

### File List

- `backend/app/schemas/user.py` — Modified: added `display_name` field with `Field(max_length=255)` to `UserStatusUpdate`
- `backend/app/services/user_service.py` — Modified: handle `display_name` update in changes list
- `backend/app/routers/admin.py` — Modified: capture `old_display_name`, add `user_update_profile` audit block
- `backend/tests/test_admin_user_status.py` — Modified: added 4 display_name tests
- `frontend/lib/api.ts` — Modified: added `display_name?: string` to `UserStatusUpdate` interface
- `frontend/components/admin/UserEditModal.tsx` — **Created**: new modal component
- `frontend/app/admin/users/page.tsx` — Modified: added edit state, pencil button, handler, success message, modal render
- `frontend/tests/app/admin/UsersPage.test.tsx` — Modified: added 6 edit modal tests
- `frontend/tests/mocks/handlers.ts` — Modified: added `display_name` handling to PATCH mock
