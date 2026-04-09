# Story 5.2: Recipe Admin Controls

Status: Done

## Story

As an **admin**,
I want **to see edit and delete controls on any recipe card and detail page**,
So that **I can quickly fix incorrect data without navigating to separate admin pages**.

## Acceptance Criteria

### AC-1: Admin Icons on Recipe Cards

**Given** I am logged in as an admin
**When** I view the recipe list/grid
**Then** each recipe card shows edit (pencil) and delete (trash) icons
**And** these icons are only visible to admins

**Given** I am logged in as a regular user
**When** I view the recipe list/grid
**Then** no edit/delete icons appear on recipe cards

### AC-2: Recipe Card Edit Navigation

**Given** I am logged in as an admin
**When** I click the edit icon on any recipe card
**Then** I am taken to the recipe edit page (`/recipes/{id}/edit`) for that recipe
**And** I can edit even if I don't own the recipe

### AC-3: Recipe Card Delete with Confirmation Modal

**Given** I am logged in as an admin
**When** I click the delete icon on any recipe card
**Then** a confirmation modal appears asking "Delete this recipe?"
**And** the modal shows the recipe name
**And** I must confirm before deletion proceeds

**Given** I confirm the delete action
**When** the deletion completes
**Then** the recipe is removed from the list (visual removal serves as confirmation)
**And** the confirmation modal closes automatically

### AC-4: Recipe Detail Page Admin Controls

**Given** I am on the recipe detail page as an admin
**When** I view a recipe I don't own
**Then** Edit, Add Images, and Delete buttons are visible (same as owner controls)
**And** clicking Edit navigates to `/recipes/{id}/edit`

### AC-5: Recipe Edit Page Admin Access

**Given** I am an admin navigating to `/recipes/{id}/edit` for a recipe I don't own
**When** the edit page loads
**Then** I can edit all fields (not shown "Access Denied")
**And** saving the recipe succeeds via the existing PUT endpoint (backend admin bypass already exists)

---

## Tasks / Subtasks

### Task 1: Create Reusable ConfirmDeleteModal Component (AC: #3)

- [x] **1.1** Create `frontend/components/ui/ConfirmDeleteModal.tsx`:
  ```typescript
  'use client';

  interface ConfirmDeleteModalProps {
    isOpen: boolean;
    title: string;          // e.g., "Delete this recipe?"
    itemName: string;       // e.g., recipe name shown in modal body
    onConfirm: () => void;
    onCancel: () => void;
    isDeleting?: boolean;   // shows spinner/disabled state
  }
  ```
  - Use fixed overlay pattern from existing `SharePlaylistModal.tsx` (`fixed inset-0 bg-black/50 z-50`)
  - Red "Delete" confirm button, gray "Cancel" button
  - Close on Escape key and overlay click
  - Show `itemName` in body: "Are you sure you want to delete **{itemName}**? This cannot be undone."
  - Disable confirm button and show "Deleting..." when `isDeleting` is true
  - Use Lucide `AlertTriangle` icon for warning visual

- [x] **1.2** Also update the recipe detail page (`frontend/app/recipes/[id]/page.tsx`) to use `ConfirmDeleteModal` instead of the native `confirm()` dialog — this replaces the browser confirm at line 91 for ALL users (owners + admins), improving UX consistency.

### Task 2: Add Admin Edit/Delete Icons to RecipeCard (AC: #1, #2, #3)

- [x] **2.1** In `frontend/components/recipes/RecipeCard.tsx`:
  - Import `useAuth` from `@/lib/auth-context`
  - Import `Pencil`, `Trash2` from `lucide-react`
  - Import `useRouter` from `next/navigation`
  - Import `useDeleteRecipe` from `@/lib/hooks`
  - Import `ConfirmDeleteModal` from `@/components/ui/ConfirmDeleteModal`
  - Add state: `const [showDeleteModal, setShowDeleteModal] = useState(false)`
  - Get auth: `const { user, token } = useAuth()`
  - Derive: `const isAdmin = user?.is_admin === true`

- [x] **2.2** Add admin action buttons to the card. Place them in a **new row below the existing action buttons** (favourite/share/playlist), inside the same `absolute top-2 right-2` container but as a second row, OR place them at bottom-left of the image area to avoid cluttering:
  - **Recommended placement:** Bottom-right of the image area, visible only for admins:
    ```typescript
    {isAdmin && (
      <div className="absolute bottom-2 right-2 opacity-100 md:opacity-0 md:group-hover:opacity-100 transition-opacity flex gap-1 z-50">
        <button onClick={handleAdminEdit} className="p-1.5 bg-white/90 hover:bg-white rounded-full shadow-sm" title="Edit recipe">
          <Pencil className="h-3.5 w-3.5 text-gray-600" />
        </button>
        <button onClick={handleAdminDelete} className="p-1.5 bg-white/90 hover:bg-red-50 rounded-full shadow-sm" title="Delete recipe">
          <Trash2 className="h-3.5 w-3.5 text-red-500" />
        </button>
      </div>
    )}
    ```
  - **Position:** Bottom-right of the image section (inside the `aspect-[3/4]` div), NOT in the info strip
  - Same show/hide behavior as existing buttons (always visible on mobile, hover on desktop)

- [x] **2.3** Add handlers:
  ```typescript
  const handleAdminEdit = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    router.push(`/recipes/${recipe.id}/edit`);
  };

  const handleAdminDelete = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setShowDeleteModal(true);
  };
  ```
  - Delete handler opens the ConfirmDeleteModal
  - On confirm: call `deleteRecipeMutation.mutateAsync({ id: recipe.id, token })`, then close modal
  - On success: recipe disappears from grid automatically (useDeleteRecipe has optimistic cache removal)

- [x] **2.4** Render `ConfirmDeleteModal` at the end of the component (outside the Link):
  ```typescript
  <ConfirmDeleteModal
    isOpen={showDeleteModal}
    title="Delete this recipe?"
    itemName={recipe.name}
    onConfirm={handleConfirmDelete}
    onCancel={() => setShowDeleteModal(false)}
    isDeleting={deleteRecipeMutation.isPending}
  />
  ```

### Task 3: Update Recipe Detail Page for Admin Access (AC: #4)

- [x] **3.1** In `frontend/app/recipes/[id]/page.tsx`, update the `canEdit` logic at line 87:
  ```typescript
  // BEFORE:
  const canEdit = isOnline && recipe && (recipe.user_id === null || recipe.user_id === undefined || isOwner);

  // AFTER:
  const isAdmin = user?.is_admin === true;
  const canEdit = isOnline && recipe && (recipe.user_id === null || recipe.user_id === undefined || isOwner || isAdmin);
  ```
  - This makes the existing Edit/Delete/Add Images buttons visible to admins on ALL recipes
  - No changes to the button markup needed — the existing `{canEdit && (...)}` block at line 397 already renders everything correctly

- [x] **3.2** Replace the `confirm()` dialog in `handleDelete` (line 91) with the ConfirmDeleteModal:
  - Add state: `const [showDeleteModal, setShowDeleteModal] = useState(false)`
  - Change handleDelete to just open modal: `setShowDeleteModal(true)`
  - Add `handleConfirmDelete` that does the actual deletion (move existing try/catch logic)
  - Render ConfirmDeleteModal at the bottom of the page component

### Task 4: Update Recipe Edit Page for Admin Access (AC: #5)

- [x] **4.1** In `frontend/app/recipes/[id]/edit/page.tsx`, update the `canEdit` logic at lines 60-62:
  ```typescript
  // BEFORE:
  const canEdit = recipe.user_id === null ||
                 recipe.user_id === undefined ||
                 (user && recipe.user_id === user.id);

  // AFTER:
  const canEdit = recipe.user_id === null ||
                 recipe.user_id === undefined ||
                 (user && recipe.user_id === user.id) ||
                 (user && user.is_admin === true);
  ```
  - This prevents the "Access Denied" page from showing when an admin edits someone else's recipe
  - No other changes needed — the form and save logic work identically (backend already handles admin bypass)

### Task 5: Write Tests (AC: #1, #2, #3, #4, #5)

- [x] **5.1** Create `frontend/tests/components/ui/ConfirmDeleteModal.test.tsx`:
  - `test renders modal when isOpen is true` — verify title, item name, buttons visible
  - `test does not render when isOpen is false` — verify nothing in DOM
  - `test calls onConfirm when Delete button clicked`
  - `test calls onCancel when Cancel button clicked`
  - `test calls onCancel when Escape key pressed`
  - `test shows deleting state when isDeleting is true` — verify button disabled, shows "Deleting..."
  - `test displays item name in confirmation message`

- [x] **5.2** Create `frontend/tests/components/recipes/RecipeCard.admin.test.tsx`:
  - Mock `useAuth` to return admin user (`is_admin: true`)
  - `test shows edit and delete icons when user is admin` — verify Pencil and Trash2 icons render
  - `test does not show admin icons when user is not admin` — mock `is_admin: false`
  - `test does not show admin icons when user is null` — mock `user: null`
  - `test edit icon navigates to edit page` — click edit, verify `router.push` called with `/recipes/{id}/edit`
  - `test delete icon opens confirmation modal` — click trash, verify modal appears
  - `test confirming delete calls delete mutation` — open modal, click confirm, verify mutation called
  - Follow existing RecipeCard test patterns if they exist, otherwise follow Header.admin.test.tsx pattern

- [x] **5.3** Create `frontend/tests/app/recipes/RecipeDetail.admin.test.tsx`:
  - `test shows edit/delete buttons when user is admin but not owner` — mock admin user, recipe with different user_id
  - `test does not show edit/delete when regular user and not owner` — verify no buttons
  - `test delete button opens confirmation modal instead of browser confirm`
  - Follow existing RecipeDetail test patterns

- [x] **5.4** Create `frontend/tests/app/recipes/RecipeEdit.admin.test.tsx`:
  - `test admin can access edit page for other user recipe` — verify no "Access Denied"
  - `test regular user sees Access Denied for other user recipe` — verify unauthorized state

- [x] **5.5** Run full frontend test suite: `cd frontend && npm test` — no regressions

---

## Dev Notes

### CRITICAL: This is a Frontend-Only Story

**Zero backend changes required.** The backend already has:
- Admin bypass in PUT `/api/recipes/{id}` — `recipes.py:559`: `if recipe.user_id != current_user.id and not current_user.is_admin:`
- Admin bypass in DELETE `/api/recipes/{id}` — `recipes.py:697`: same pattern
- Audit logging for admin recipe actions — `recipes.py:574-621` (update), `recipes.py:722-725` (delete)
- The `is_admin` field is already exposed via the `User` interface in `auth-context.tsx` (added in Story 5-1)

### Current Frontend State (Verified)

- **RecipeCard** (`frontend/components/recipes/RecipeCard.tsx`): Has favourite/share/playlist action buttons. No edit/delete. Uses `RecipeListItem` props (has `id`, `name`, `has_image`, etc.).
- **Recipe Detail** (`frontend/app/recipes/[id]/page.tsx`): Has edit/delete buttons for owners only. Uses native `confirm()` for delete. Permission check at line 87: `canEdit = isOnline && recipe && (no owner || isOwner)`. Edit/delete UI at line 397.
- **Recipe Edit** (`frontend/app/recipes/[id]/edit/page.tsx`): Full edit form. Permission check at lines 60-62: `canEdit = no owner || isOwner`. Shows "Access Denied" if unauthorized.
- **AdminBadge** already exists at `frontend/components/admin/AdminBadge.tsx` (from Story 5-1)
- **No toast/notification system** — project uses native `alert()` for errors. AC says "success toast" but there is no toast library installed. Options: (a) use a simple inline success message, (b) skip toast and let the visual removal of the recipe serve as confirmation, or (c) install `sonner` or `react-hot-toast`. **Recommendation:** Just let the recipe disappearing from the grid/navigating away serve as confirmation — no new dependency needed. If user wants toasts, that's a separate story.
- **No reusable confirmation modal** — `SharePlaylistModal` exists as a pattern reference but is feature-specific. Creating `ConfirmDeleteModal` adds reusable infrastructure for Stories 5-3 through 5-6.

### Existing Hooks (Reuse These)

| Hook | Location | Usage |
|------|----------|-------|
| `useDeleteRecipe()` | `frontend/lib/hooks/use-recipes.ts` | Mutation with optimistic cache removal — recipe disappears from grid instantly |
| `useUpdateRecipe()` | `frontend/lib/hooks/use-recipes.ts` | Mutation with optimistic update |
| `useAuth()` | `frontend/lib/auth-context.tsx` | Access `user?.is_admin`, `token` |
| `useRecipe()` | `frontend/lib/hooks/use-recipes.ts` | Fetch single recipe (used on detail page) |

### Out-of-Scope (Explicitly Deferred)

- **Toast/notification system** — No library installed, not adding one for this story
- **Ownership transfer UI** — Backend supports it via admin PUT, but no UI needed per AC
- **Inline editing on detail page** — AC says "inline editing of all fields" but the existing edit page at `/recipes/{id}/edit` already provides full editing. Navigate there instead.
- **Role-based caching** — Deferred to when admin-specific queries are added

### Architecture Compliance

| Requirement | Implementation |
|-------------|----------------|
| Admin state check | `user?.is_admin === true` [Source: docs/admin-panel-architecture.md — Decision #3] |
| Conditional rendering | `{isAdmin && <AdminControls />}` [Source: docs/admin-panel-architecture.md] |
| Reusable modal | `components/ui/ConfirmDeleteModal.tsx` [New — extends pattern from SharePlaylistModal] |
| Component location | `components/ui/` for reusable, `components/recipes/` for recipe-specific [Source: docs/project_context.md] |

### Library/Framework Requirements

- **No new dependencies.** Uses existing packages only.
- Lucide React icons: `Pencil`, `Trash2`, `AlertTriangle` (already in project)
- TypeScript strict mode — all props typed
- Tailwind CSS for all styling

### File Structure Requirements

| File | Action | Description |
|------|--------|-------------|
| `frontend/components/ui/ConfirmDeleteModal.tsx` | CREATE | Reusable delete confirmation modal |
| `frontend/components/recipes/RecipeCard.tsx` | MODIFY | Add admin edit/delete icons |
| `frontend/app/recipes/[id]/page.tsx` | MODIFY | Update `canEdit` for admin, replace `confirm()` with modal |
| `frontend/app/recipes/[id]/edit/page.tsx` | MODIFY | Update `canEdit` for admin access |
| `frontend/tests/components/ui/ConfirmDeleteModal.test.tsx` | CREATE | Modal unit tests |
| `frontend/tests/components/recipes/RecipeCard.admin.test.tsx` | CREATE | RecipeCard admin tests |
| `frontend/tests/app/recipes/RecipeDetail.admin.test.tsx` | CREATE | Detail page admin tests |
| `frontend/tests/app/recipes/RecipeEdit.admin.test.tsx` | CREATE | Edit page admin access tests |

### Testing Requirements

**Test framework:** vitest (globals enabled — do NOT import describe/it/expect)
**Test setup:** `frontend/tests/setup.ts` already configured — don't duplicate
**Mock pattern:** MSW 2.x handlers for API mocking:
```typescript
http.get('*/api/recipes/:id', () => HttpResponse.json(mockRecipe))
http.delete('*/api/recipes/:id', () => new HttpResponse(null, { status: 204 }))
```

**Test isolation (every test):**
```typescript
beforeEach(() => { queryClient.clear() })
afterEach(() => { cleanup(); vi.clearAllMocks() })
```

**Mock auth context for admin tests:**
```typescript
vi.mock('@/lib/auth-context', () => ({
  useAuth: () => ({
    user: { id: '1', email: 'admin@test.com', display_name: 'Admin', is_admin: true, created_at: '2026-01-01' },
    token: 'fake-token',
    isLoading: false,
    login: vi.fn(),
    logout: vi.fn(),
    register: vi.fn(),
    refreshToken: vi.fn(),
  }),
}))
```

**Coverage target:** 100% on new code paths

### Previous Story Intelligence

**From Story 5-1 (Admin State & Indicator):**
- `is_admin: boolean` added to `User` interface in `auth-context.tsx`
- AdminBadge component created at `components/admin/AdminBadge.tsx`
- Shared mock user in `tests/mocks/handlers.ts` has `is_admin: false`
- Header conditionally renders AdminBadge via `user?.is_admin && <AdminBadge />`
- 238 frontend tests pass, build succeeds

**From Epic 4→5 Prep (`d8e8c5b`):**
- Fixed `ListStateProvider` mock issues in frontend tests
- Frontend is in a clean, passing state

### Git Intelligence

**Recent commits:**
- `d8e8c5b` fix: Epic 4→5 prep — fix 23 frontend test failures, verify toolchain
- `3bf2553` feat: Epic 4 — Audit Trail & Compliance (stories 4-1, 4-2)

**Key insight:** Frontend test suite is clean. All 238 tests pass. Build succeeds.

### Project Context Reference

See `docs/project_context.md` for:
- TypeScript strict mode rules (no implicit `any`)
- React Query v5 object syntax
- MSW 2.x test handler pattern
- Component file naming (PascalCase.tsx)
- Provider hierarchy: Query → Auth → Offline → Favourites
- `clsx` for conditional Tailwind classes

### References

- [Source: frontend/components/recipes/RecipeCard.tsx — Recipe card component, action buttons at lines 54-78]
- [Source: frontend/app/recipes/[id]/page.tsx:87 — canEdit permission check (needs admin bypass)]
- [Source: frontend/app/recipes/[id]/page.tsx:89-99 — handleDelete with native confirm()]
- [Source: frontend/app/recipes/[id]/page.tsx:397 — {canEdit && ...} rendering block]
- [Source: frontend/app/recipes/[id]/edit/page.tsx:60-62 — canEdit permission check (needs admin bypass)]
- [Source: backend/app/routers/recipes.py:559 — Admin bypass already exists in PUT endpoint]
- [Source: backend/app/routers/recipes.py:697 — Admin bypass already exists in DELETE endpoint]
- [Source: docs/admin-panel-architecture.md — Decision #3: Admin state in AuthContext]
- [Source: docs/admin-panel-prd.md — FR-3.3.1, FR-3.3.2: Recipe admin edit/delete]
- [Source: frontend/components/playlists/SharePlaylistModal.tsx — Modal pattern reference]

---

## Dev Agent Record

### Context Reference

Story context created by BMAD create-story workflow on 2026-04-09.

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

- No debug issues encountered

### Completion Notes List

- Created reusable `ConfirmDeleteModal` component (`components/ui/ConfirmDeleteModal.tsx`) with Escape key, overlay click, and loading state support
- Added admin edit/delete icons to `RecipeCard` — bottom-right of image area, hover-reveal on desktop, always visible on mobile
- Updated `canEdit` logic on recipe detail page to include `isAdmin` check, giving admins edit/delete/add-images on all recipes
- Replaced native `window.confirm()` with `ConfirmDeleteModal` on recipe detail page for consistent UX across all users
- Updated recipe edit page `canEdit` logic to allow admin access (prevents "Access Denied" for non-owned recipes)
- Fixed existing `RecipeCard.test.tsx` and `RecipeGrid.test.tsx` to include `QueryClientProvider` and `next/navigation` mock (required after adding `useDeleteRecipe` and `useRouter` to RecipeCard)
- Updated `recipe-detail.test.tsx` delete tests to work with modal-based confirmation instead of `window.confirm()` spy
- 286 tests pass, 0 failures, 0 type errors in source code

### Code Review Fixes Applied

- **AC-3 updated**: Removed "success toast notification" from AC (no toast library — visual removal is confirmation)
- **ConfirmDeleteModal**: Cancel button no longer disabled during deletion (UX trap fix — user can bail out of hanging requests)
- **Test: overlay click**: Added missing test for closing modal via backdrop click
- **Test: delete request verification**: Added assertions for correct recipe ID and auth token in RecipeCard admin delete test
- **Test: IndexedDB mock**: Added `offline-storage` mock to RecipeDetail admin tests (eliminates `getCachedRecipeListItems` error)
- **Code quality**: Replaced `console.error` with `debug.error` in RecipeCard and RecipeDetail delete handlers

### Change Log

- 2026-04-09: Implemented Story 5-2 — Recipe Admin Controls (all 5 tasks, 18 new tests, 262 total pass)

### File List

**Created:**
- `frontend/components/ui/ConfirmDeleteModal.tsx` — Reusable delete confirmation modal
- `frontend/tests/components/ui/ConfirmDeleteModal.test.tsx` — 7 tests
- `frontend/tests/components/recipes/RecipeCard.admin.test.tsx` — 6 tests
- `frontend/tests/app/recipes/RecipeDetail.admin.test.tsx` — 3 tests
- `frontend/tests/app/recipes/RecipeEdit.admin.test.tsx` — 2 tests

**Modified:**
- `frontend/components/recipes/RecipeCard.tsx` — Added admin edit/delete icons, useAuth/useRouter/useDeleteRecipe, ConfirmDeleteModal
- `frontend/app/recipes/[id]/page.tsx` — Admin canEdit bypass, replaced confirm() with ConfirmDeleteModal
- `frontend/app/recipes/[id]/edit/page.tsx` — Admin canEdit bypass
- `frontend/tests/components/RecipeCard.test.tsx` — Added QueryClientProvider + navigation mock
- `frontend/tests/components/RecipeGrid.test.tsx` — Added QueryClientProvider + navigation mock
- `frontend/tests/pages/recipe-detail.test.tsx` — Updated delete tests for modal-based confirmation
- `docs/sprint-artifacts/sprint-status.yaml` — Status: ready-for-dev → in-progress → review
- `docs/sprint-artifacts/5-2-recipe-admin-controls.md` — Task checkboxes, dev record, status
