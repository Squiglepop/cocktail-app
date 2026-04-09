# Story 5.3: Category Management Modal

Status: Done

## Story

As an **admin**,
I want **to manage categories directly from filter dropdowns via a modal**,
So that **I can add, edit, reorder, and soft-delete category options without leaving the current page**.

## Acceptance Criteria

### AC-1: "Manage" Link in Filter Dropdowns (Admin Only)

**Given** I am logged in as an admin
**When** I view any filter dropdown (Template, Main Spirit, Glassware, Serving Style, Method)
**Then** a "Manage" link appears below the dropdown

**Given** I am logged in as a regular user
**When** I view any filter dropdown
**Then** no "Manage" link is shown

### AC-2: Modal Displays All Category Values

**Given** I click the "Manage" link for a category type
**When** the modal opens
**Then** I see a list of ALL category values (including inactive, grayed out)
**And** the list is ordered by `sort_order`
**And** inactive items are visually distinct (grayed out / strikethrough)

### AC-3: Add New Category

**Given** I am in the category management modal
**When** I click "Add New"
**Then** an inline form appears for entering a new category (label, description)
**And** the `value` field auto-generates snake_case from the label input (must match backend pattern `^[a-z][a-z0-9_]*$`)
**And** submitting creates the category via `POST /api/admin/categories/{type}`
**And** the new category appears at the end of the list

### AC-4: Inline Edit Display Name

**Given** I am in the category management modal
**When** I click on a category's label
**Then** I can edit the display name inline
**And** changes save on blur or Enter key via `PUT /api/admin/categories/{type}/{id}`

### AC-5: Reorder Categories

**Given** I am in the category management modal
**When** I click the up/down arrow buttons on a category row
**Then** the category moves up or down in the list
**And** the new order persists via `POST /api/admin/categories/{type}/reorder`

### AC-6: Delete with Usage Count Warning

**Given** I click the delete button on a category
**When** the delete request completes
**Then** the response shows the count of recipes using that category
**And** the item is marked inactive (soft-deleted) in the list

### AC-7: React Query Invalidation on Close

**Given** I close the category management modal after making changes
**When** I return to the filter dropdown
**Then** the dropdown reflects the changes immediately (public categories refreshed)

---

## Tasks / Subtasks

### Task 1: Add Admin Category API Functions (AC: #2, #3, #4, #5, #6)

- [x] **1.1** In `frontend/lib/api.ts`, add these admin category types and functions:
  ```typescript
  // Admin category types
  export interface AdminCategory {
    id: string;
    value: string;
    label: string;
    description: string | null;
    category: string | null;     // Only used by glassware (stemmed/short/tall/specialty)
    sort_order: number;
    is_active: boolean;
    created_at: string;
  }

  export interface AdminCategoryCreate {
    value: string;
    label: string;
    description?: string;
    category?: string;           // Only for glassware
  }

  export interface AdminCategoryUpdate {
    label?: string;
    description?: string;
    is_active?: boolean;
  }

  export interface CategoryDeleteResult {
    message: string;
    recipe_count: number;
  }
  ```

- [x] **1.2** Add API functions following the existing auth header pattern (`lib/api.ts`):
  ```typescript
  export async function fetchAdminCategories(type: string, token: string | null): Promise<AdminCategory[]> {
    const headers: Record<string, string> = {};
    if (token) { headers['Authorization'] = `Bearer ${token}`; }
    const res = await fetch(`${API_BASE}/admin/categories/${type}`, { headers });
    if (!res.ok) throw new Error('Failed to fetch admin categories');
    return res.json();
  }

  export async function createAdminCategory(type: string, data: AdminCategoryCreate, token: string | null): Promise<AdminCategory> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (token) { headers['Authorization'] = `Bearer ${token}`; }
    const res = await fetch(`${API_BASE}/admin/categories/${type}`, {
      method: 'POST', headers, body: JSON.stringify(data),
    });
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: 'Failed to create category' }));
      throw new Error(error.detail || 'Failed to create category');
    }
    return res.json();
  }

  export async function updateAdminCategory(type: string, id: string, data: AdminCategoryUpdate, token: string | null): Promise<AdminCategory> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (token) { headers['Authorization'] = `Bearer ${token}`; }
    const res = await fetch(`${API_BASE}/admin/categories/${type}/${id}`, {
      method: 'PUT', headers, body: JSON.stringify(data),
    });
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: 'Failed to update category' }));
      throw new Error(error.detail || 'Failed to update category');
    }
    return res.json();
  }

  export async function deleteAdminCategory(type: string, id: string, token: string | null): Promise<CategoryDeleteResult> {
    const headers: Record<string, string> = {};
    if (token) { headers['Authorization'] = `Bearer ${token}`; }
    const res = await fetch(`${API_BASE}/admin/categories/${type}/${id}`, {
      method: 'DELETE', headers,
    });
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: 'Failed to delete category' }));
      throw new Error(error.detail || 'Failed to delete category');
    }
    return res.json();
  }

  export async function reorderAdminCategories(type: string, ids: string[], token: string | null): Promise<void> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (token) { headers['Authorization'] = `Bearer ${token}`; }
    const res = await fetch(`${API_BASE}/admin/categories/${type}/reorder`, {
      method: 'POST', headers, body: JSON.stringify({ ids }),
    });
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: 'Failed to reorder categories' }));
      throw new Error(error.detail || 'Failed to reorder categories');
    }
  }
  ```

### Task 2: Add Admin Category Query Keys and Hooks (AC: #2, #7)

- [x] **2.1** In `frontend/lib/query-client.ts`, add admin staleTime and query keys:
  ```typescript
  // Add to STALE_TIMES:
  adminCategories: 60 * 1000,  // Admin views: 1 minute (architecture decision #1)
  ```
  Add admin category query keys:
  ```typescript
  // Inside queryKeys object, add:
  adminCategories: {
    all: ['admin-categories'] as const,
    byType: (type: string) => ['admin-categories', type] as const,
  },
  ```

- [x] **2.2** Create `frontend/lib/hooks/use-admin-categories.ts`:
  ```typescript
  'use client';

  import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
  import {
    AdminCategory, AdminCategoryCreate, AdminCategoryUpdate,
    fetchAdminCategories, createAdminCategory, updateAdminCategory,
    deleteAdminCategory, reorderAdminCategories,
  } from '@/lib/api';
  import { queryKeys, STALE_TIMES } from '@/lib/query-client';

  export function useAdminCategories(type: string, token: string | null) {
    return useQuery({
      queryKey: queryKeys.adminCategories.byType(type),
      queryFn: () => fetchAdminCategories(type, token),
      staleTime: STALE_TIMES.adminCategories,
      enabled: !!token,  // Don't fire without auth — prevents 401 on mount
    });
  }

  export function useCreateCategory(type: string) {
    const queryClient = useQueryClient();
    return useMutation({
      mutationFn: ({ data, token }: { data: AdminCategoryCreate; token: string | null }) =>
        createAdminCategory(type, data, token),
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: queryKeys.adminCategories.byType(type) });
      },
    });
  }

  export function useUpdateCategory(type: string) {
    const queryClient = useQueryClient();
    return useMutation({
      mutationFn: ({ id, data, token }: { id: string; data: AdminCategoryUpdate; token: string | null }) =>
        updateAdminCategory(type, id, data, token),
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: queryKeys.adminCategories.byType(type) });
      },
    });
  }

  export function useDeleteCategory(type: string) {
    const queryClient = useQueryClient();
    return useMutation({
      mutationFn: ({ id, token }: { id: string; token: string | null }) =>
        deleteAdminCategory(type, id, token),
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: queryKeys.adminCategories.byType(type) });
      },
    });
  }

  export function useReorderCategories(type: string) {
    const queryClient = useQueryClient();
    return useMutation({
      mutationFn: ({ ids, token }: { ids: string[]; token: string | null }) =>
        reorderAdminCategories(type, ids, token),
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: queryKeys.adminCategories.byType(type) });
      },
    });
  }
  ```

- [x] **2.3** Export from `frontend/lib/hooks/index.ts`:
  ```typescript
  export {
    useAdminCategories,
    useCreateCategory,
    useUpdateCategory,
    useDeleteCategory,
    useReorderCategories,
  } from './use-admin-categories';
  ```

### Task 3: Create CategoryManagementModal Component (AC: #2, #3, #4, #5, #6, #7)

- [x] **3.1** Create `frontend/components/admin/CategoryManagementModal.tsx`:
  - Props:
    ```typescript
    interface CategoryManagementModalProps {
      isOpen: boolean;
      categoryType: string;      // 'templates' | 'glassware' | 'serving-styles' | 'methods' | 'spirits'
      categoryLabel: string;     // Display name: "Templates", "Glassware", etc.
      onClose: () => void;
    }
    ```
  - Use `useAuth()` to get token
  - Fetch admin categories via `useAdminCategories(categoryType, token)`
  - Display modal overlay using same pattern as `SharePlaylistModal` (`fixed inset-0 bg-black/50 z-50`)

- [x] **3.2** Category list display:
  - Show all categories ordered by `sort_order`
  - Active items: normal text
  - Inactive items: `text-gray-400 line-through` styling
  - Each row shows: label, value (small gray text), up/down arrows, edit (pencil), delete (trash)
  - Glassware items also show their `category` grouping

- [x] **3.3** Add New Category form:
  - "Add New" button at top of list
  - When clicked, show inline form fields: label (text input), description (optional text input)
  - Auto-generate `value` from label: `label.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^[^a-z]+/, '').replace(/_$/, '')`
    - This strips leading non-letters to match backend validation: `^[a-z][a-z0-9_]*$`
  - Show generated value as preview below label input (read-only)
  - If generated value is empty (e.g., label is all digits/symbols), show inline error "Label must contain at least one letter"
  - For glassware type, also show a `category` dropdown with options: stemmed, short, tall, specialty
  - "Save" button calls `useCreateCategory` mutation — **disable Save if generated value is empty or invalid**
  - "Cancel" button hides the form
  - On success: form clears, new item appears in list
  - On 409 error: show "Category value already exists" message
  - On invalid value (empty after sanitization): show "Label must start with a letter" — do NOT submit

- [x] **3.4** Inline label editing:
  - Click on label text → converts to input field
  - On blur or Enter → calls `useUpdateCategory` with `{ label: newValue }`
  - On Escape → cancel edit, revert to original
  - Show subtle loading indicator during save

- [x] **3.5** Reorder with up/down arrows:
  - `ChevronUp` / `ChevronDown` icons from lucide-react
  - First item: up arrow disabled. Last item: down arrow disabled
  - On click: swap items locally, then call `useReorderCategories` with full ID array in new order
  - Disable buttons during reorder mutation (prevent double-clicks)
  - **No drag-and-drop library** — arrow buttons are sufficient and avoid a new dependency

- [x] **3.6** Delete (soft-delete):
  - Trash icon per row
  - On click: call `useDeleteCategory` directly (backend returns `recipe_count`)
  - On success: show brief inline message "{value} deactivated. {recipe_count} recipes affected."
  - Item stays in list but becomes grayed out / inactive
  - Already-inactive items: hide the delete button (already deleted)

- [x] **3.7** On modal close:
  - Invalidate public categories query to refresh filter dropdowns:
    ```typescript
    const queryClient = useQueryClient();
    const handleClose = () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.categories.all });
      onClose();
    };
    ```
  - Close on Escape key and overlay click

### Task 4: Add "Manage" Links to FilterSidebar (AC: #1)

- [x] **4.1** In `frontend/components/recipes/FilterSidebar.tsx`:
  - Import `useAuth` from `@/lib/auth-context`
  - Import `Settings` icon from `lucide-react`
  - Import `CategoryManagementModal` from `@/components/admin/CategoryManagementModal`
  - Add state: `const [managingCategory, setManagingCategory] = useState<{ type: string; label: string } | null>(null)`
  - Get auth: `const { user } = useAuth()`
  - Derive: `const isAdmin = user?.is_admin === true`

- [x] **4.2** Add "Manage" link below each category `<select>` element (both sidebar and tile variants):
  ```typescript
  {isAdmin && (
    <button
      onClick={() => setManagingCategory({ type: 'templates', label: 'Templates' })}
      className="text-xs text-amber-600 hover:text-amber-700 flex items-center gap-1 mt-1"
    >
      <Settings className="h-3 w-3" />
      Manage
    </button>
  )}
  ```
  - Repeat for each category dropdown with correct type/label:
    - Template → `{ type: 'templates', label: 'Templates' }`
    - Main Spirit → `{ type: 'spirits', label: 'Spirits' }`
    - Glassware → `{ type: 'glassware', label: 'Glassware' }`
    - Serving Style → `{ type: 'serving-styles', label: 'Serving Styles' }`
    - Method → `{ type: 'methods', label: 'Methods' }`

- [x] **4.3** Render CategoryManagementModal at the end of the component:
  ```typescript
  {managingCategory && (
    <CategoryManagementModal
      isOpen={true}
      categoryType={managingCategory.type}
      categoryLabel={managingCategory.label}
      onClose={() => setManagingCategory(null)}
    />
  )}
  ```

### Task 5: Write Tests (AC: #1, #2, #3, #4, #5, #6, #7)

- [x] **5.1** Add MSW handlers for admin category endpoints in `frontend/tests/mocks/handlers.ts`:
  ```typescript
  // Admin category mock data
  export const mockAdminCategories = [
    { id: '1', value: 'sour', label: 'Sour', description: 'Spirit, citrus, sweetener', category: null, sort_order: 0, is_active: true, created_at: '2026-01-01T00:00:00Z' },
    { id: '2', value: 'old_fashioned', label: 'Old Fashioned', description: 'Spirit, sugar, bitters', category: null, sort_order: 1, is_active: true, created_at: '2026-01-01T00:00:00Z' },
    { id: '3', value: 'flip', label: 'Flip', description: 'Egg-based', category: null, sort_order: 2, is_active: false, created_at: '2026-01-01T00:00:00Z' },
  ];

  // Add handlers:
  http.get(`${API_BASE}/admin/categories/:type`, ({ request }) => {
    const authHeader = request.headers.get('Authorization');
    if (!authHeader) return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 });
    return HttpResponse.json(mockAdminCategories);
  }),

  http.post(`${API_BASE}/admin/categories/:type`, async ({ request }) => {
    const authHeader = request.headers.get('Authorization');
    if (!authHeader) return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 });
    const body = await request.json() as { value: string; label: string; description?: string };
    if (body.value === 'sour') return HttpResponse.json({ detail: 'Category value already exists' }, { status: 409 });
    return HttpResponse.json({ id: '99', ...body, category: null, sort_order: 99, is_active: true, created_at: new Date().toISOString() }, { status: 201 });
  }),

  http.put(`${API_BASE}/admin/categories/:type/:id`, async ({ params, request }) => {
    const authHeader = request.headers.get('Authorization');
    if (!authHeader) return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 });
    const body = await request.json() as Record<string, unknown>;
    const existing = mockAdminCategories.find(c => c.id === params.id);
    if (!existing) return HttpResponse.json({ detail: 'Category not found' }, { status: 404 });
    return HttpResponse.json({ ...existing, ...body });
  }),

  http.delete(`${API_BASE}/admin/categories/:type/:id`, ({ params, request }) => {
    const authHeader = request.headers.get('Authorization');
    if (!authHeader) return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 });
    return HttpResponse.json({ message: `Category deactivated`, recipe_count: 3 });
  }),

  http.post(`${API_BASE}/admin/categories/:type/reorder`, ({ request }) => {
    const authHeader = request.headers.get('Authorization');
    if (!authHeader) return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 });
    return HttpResponse.json({ message: 'Categories reordered successfully' });
  }),
  ```

- [x] **5.2** Create `frontend/tests/components/admin/CategoryManagementModal.test.tsx`:
  - **IMPORTANT:** Mock auth context at top of file — see "Mock auth context for admin tests" pattern in Testing Requirements below.
  - `test renders modal with category list when open` — verify all categories shown
  - `test does not render when isOpen is false`
  - `test shows inactive categories with visual distinction` — verify grayed/strikethrough styling
  - `test add new category form appears on button click` — click "Add New", verify form renders
  - `test auto-generates snake_case value from label` — type label, verify value preview
  - `test creates category on form submit` — fill form, submit, verify API call
  - `test shows error on duplicate value (409)` — submit existing value, verify error message
  - `test shows validation error when label produces invalid value` — type digit-only label, verify Save disabled and error shown
  - `test inline edit label on click` — click label, verify input appears
  - `test saves label on Enter key` — edit label, press Enter, verify API call
  - `test cancels edit on Escape key` — edit label, press Escape, verify original value
  - `test reorder up button moves item up` — click up arrow, verify reorder API called
  - `test reorder up disabled for first item` — verify first item's up arrow is disabled
  - `test delete button deactivates category` — click delete, verify API call and inline message
  - `test invalidates public categories on close` — close modal, verify categories query invalidated
  - `test closes on Escape key`
  - `test closes on overlay click`
  - `test renders empty state when no categories returned` — mock empty array response, verify appropriate message

- [x] **5.3** Create `frontend/tests/components/recipes/FilterSidebar.admin.test.tsx`:
  - **IMPORTANT:** Mock auth context — admin tests need `is_admin: true`, non-admin tests need `is_admin: false`. See pattern in Testing Requirements below.
  - `test shows Manage links when user is admin` — mock admin user, verify 5 "Manage" links visible
  - `test does not show Manage links when user is not admin` — mock regular user, verify no "Manage" links
  - `test does not show Manage links when user is null` — mock unauthenticated, verify no "Manage" links
  - `test clicking Manage opens CategoryManagementModal` — click "Manage" under Template, verify modal renders with type="templates"
  - Follow existing FilterSidebar test patterns at `frontend/tests/components/FilterSidebar.test.tsx`

- [x] **5.4** Run full frontend test suite: `cd frontend && npm test` — no regressions

---

## Dev Notes

### CRITICAL: This is a Frontend-Only Story

**Zero backend changes required.** The backend already has:
- Full admin category CRUD at `/api/admin/categories/{type}` (`backend/app/routers/admin.py:127-219`)
- GET returns all categories including inactive, ordered by sort_order
- POST creates with snake_case value validation (`backend/app/schemas/category.py:20-27`)
- PUT updates label/description/is_active (value is immutable)
- DELETE performs soft-delete, returns `{ message, recipe_count }`
- POST reorder accepts `{ ids: string[] }` and updates sort_order
- All endpoints protected by `require_admin` dependency
- Valid types: `templates`, `glassware`, `serving-styles`, `methods`, `spirits`

### Current Frontend State

- **FilterSidebar** (`frontend/components/recipes/FilterSidebar.tsx`): Renders 5 category dropdowns (Template, Main Spirit, Glassware, Serving Style, Method). Has two variants: sidebar (desktop) and tile (mobile dropdown). Uses `useCategories()` hook for public category data. Does NOT currently import `useAuth`.
- **useCategories hook** (`frontend/lib/hooks/use-recipes.ts:22-29`): Fetches public categories from `/api/categories` endpoint. 24-hour staleTime. Uses `queryKeys.categories.all`.
- **No admin category API functions exist** in `lib/api.ts` — these must be created.
- **No admin category hooks exist** — these must be created.
- **AdminBadge** exists at `components/admin/AdminBadge.tsx` (from Story 5-1).
- **ConfirmDeleteModal** may exist at `components/ui/ConfirmDeleteModal.tsx` (from Story 5-2, in-progress). Not needed for this story — category delete is simpler (no confirmation modal, just inline status message, since it's a soft-delete).
- **SharePlaylistModal** (`components/playlists/SharePlaylistModal.tsx`) — Modal pattern reference: uses `fixed inset-0 bg-black/50 z-50`, `X` close button, Escape key close.
- **No drag-and-drop library installed** — use up/down arrow buttons for reorder.

### Backend API Contract (from `backend/app/schemas/category.py`)

| Schema | Fields |
|--------|--------|
| `CategoryCreate` | `value` (snake_case, max 50), `label` (max 100), `description?`, `category?` (glassware only) |
| `CategoryUpdate` | `label?`, `description?`, `is_active?` |
| `CategoryAdminResponse` | `id`, `value`, `label`, `description?`, `category?`, `sort_order`, `is_active`, `created_at` |
| `CategoryReorderRequest` | `ids: string[]` |
| `CategoryDeleteResponse` | `message`, `recipe_count` |

### Category Type Mapping

| Dropdown Label | API Type Parameter | Notes |
|----------------|-------------------|-------|
| Template | `templates` | |
| Main Spirit | `spirits` | |
| Glassware | `glassware` | Has `category` field (stemmed/short/tall/specialty) |
| Serving Style | `serving-styles` | Note: hyphenated in API URL |
| Method | `methods` | |

### Key Implementation Decisions

1. **No drag-and-drop** — Arrow buttons for reorder. No new dependency. Simpler, accessible, works on mobile. *(Deliberate deviation from PRD UX-5.2 "Drag-to-reorder" — arrow buttons chosen for simplicity and zero-dependency.)*
2. **No delete confirmation modal** — Category delete is a soft-delete (reversible). Just show inline result message with recipe_count. Keeps it lightweight. *(Deliberate deviation from PRD UX-5.2 "Delete with confirmation" — soft-delete is inherently safe, no confirmation needed.)*
3. **Auto-generate snake_case value** — From label input: `label.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^[^a-z]+/, '').replace(/_$/, '')`. Strips leading non-letters to match backend `^[a-z][a-z0-9_]*$`. Preview shown as read-only. Disable submit if result is empty.
4. **Admin staleTime: 60 seconds** — Per architecture decision #1 (role-based caching). Admin category queries use 1-minute cache.
5. **Invalidate public categories on modal close** — Not on every mutation (would flicker dropdowns while modal is open). Single invalidation on close is cleaner.
6. **Both sidebar and tile variants need Manage links** — FilterSidebar has two rendering paths (sidebar for desktop, tile for mobile). Both need the admin links.

### Dependency on Story 5-2

Story 5-2 is in-progress. This story does NOT depend on 5-2's code — no shared components used. The `ConfirmDeleteModal` from 5-2 is NOT needed here (category delete is a soft-delete with inline feedback, not a destructive action requiring modal confirmation).

### Out-of-Scope (Explicitly Deferred)

- **Restore inactive categories** — Can be done via PUT with `{ is_active: true }`, but no "Restore" button in this story. Admin can use the label edit flow to reactivate.
- **Category description editing in modal** — AC only specifies inline label editing. Description edit can be added later.
- **Glassware category grouping in modal** — The modal shows a flat list. Glassware `category` field is shown but grouping UI is not required.
- **Real drag-and-drop** — Arrow buttons are sufficient. Can upgrade to @dnd-kit later if users request it.

### Architecture Compliance

| Requirement | Implementation |
|-------------|----------------|
| Admin state check | `user?.is_admin === true` [Source: docs/admin-panel-architecture.md — Decision #3] |
| Role-based caching | `STALE_TIMES.adminCategories` (60s) for admin queries [Source: docs/admin-panel-architecture.md — Decision #1] |
| Conditional rendering | `{isAdmin && <ManageLink />}` [Source: docs/admin-panel-architecture.md] |
| Admin component location | `components/admin/CategoryManagementModal.tsx` [Source: docs/admin-panel-architecture.md — Frontend Additions] |
| Admin hooks location | `lib/hooks/use-admin-categories.ts` [Source: docs/admin-panel-architecture.md — Frontend Additions] |
| Query invalidation | Invalidate `categories.all` on modal close [Source: docs/admin-panel-architecture.md — Category Caching] |

### Library/Framework Requirements

- **No new dependencies.** Uses existing packages only.
- Lucide React icons: `Settings`, `ChevronUp`, `ChevronDown`, `Plus`, `Pencil`, `Trash2`, `X`, `Loader2` (already in project)
- TypeScript strict mode — all props and return types typed
- Tailwind CSS for all styling — use `clsx` for conditional classes
- React Query v5 object syntax for all hooks

### File Structure Requirements

| File | Action | Description |
|------|--------|-------------|
| `frontend/lib/api.ts` | MODIFY | Add admin category types and API functions |
| `frontend/lib/query-client.ts` | MODIFY | Add `adminCategories` query keys |
| `frontend/lib/hooks/use-admin-categories.ts` | CREATE | Admin category hooks (query + 4 mutations) |
| `frontend/lib/hooks/index.ts` | MODIFY | Export admin category hooks |
| `frontend/components/admin/CategoryManagementModal.tsx` | CREATE | Category management modal component |
| `frontend/components/recipes/FilterSidebar.tsx` | MODIFY | Add admin "Manage" links + modal state |
| `frontend/tests/mocks/handlers.ts` | MODIFY | Add admin category MSW handlers |
| `frontend/tests/components/admin/CategoryManagementModal.test.tsx` | CREATE | Modal tests (16 cases) |
| `frontend/tests/components/recipes/FilterSidebar.admin.test.tsx` | CREATE | FilterSidebar admin tests (4 cases) |

### Testing Requirements

**Test framework:** vitest (globals enabled — do NOT import describe/it/expect)
**Test setup:** `frontend/tests/setup.ts` already configured — don't duplicate
**Mock pattern:** MSW 2.x handlers for API mocking:
```typescript
http.get('*/api/admin/categories/:type', () => HttpResponse.json(mockAdminCategories))
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

**From Story 5-2 (Recipe Admin Controls — in progress):**
- Created `ConfirmDeleteModal` at `components/ui/ConfirmDeleteModal.tsx` (reusable)
- Admin action pattern: `const isAdmin = user?.is_admin === true`
- Admin icons use lucide-react (Pencil, Trash2)
- Modal overlay pattern: `fixed inset-0 bg-black/50 z-50`
- Test pattern: separate `.admin.test.tsx` files for admin-specific tests

**From Story 5-1 (Admin State & Indicator):**
- `is_admin: boolean` on User interface in `auth-context.tsx`
- AdminBadge component at `components/admin/AdminBadge.tsx`
- Shared mock user has `is_admin: false` in `tests/mocks/handlers.ts`

**From Epic 4→5 Prep (`d8e8c5b`):**
- Frontend test suite clean: 238+ tests pass, build succeeds

### Git Intelligence

**Recent commits:**
- `d8e8c5b` fix: Epic 4→5 prep — fix 23 frontend test failures, verify toolchain
- `3bf2553` feat: Epic 4 — Audit Trail & Compliance (stories 4-1, 4-2)

**Key insight:** Frontend is clean. Story 5-2 may have added new tests/components — run `npm test` early to verify baseline.

### Project Context Reference

See `docs/project_context.md` for:
- TypeScript strict mode rules (no implicit `any`)
- React Query v5 object syntax
- MSW 2.x test handler pattern
- Component file naming (PascalCase.tsx)
- `clsx` for conditional Tailwind classes
- Provider hierarchy: Query → Auth → Offline → Favourites
- Admin authorization pattern: `user?.is_admin`
- Admin staleTime: 60_000 (1 min)

### References

- [Source: frontend/components/recipes/FilterSidebar.tsx — Filter dropdowns, two variants (sidebar/tile)]
- [Source: frontend/lib/hooks/use-recipes.ts:22-29 — useCategories hook, 24h staleTime]
- [Source: frontend/lib/query-client.ts:26-28 — categories.all query key]
- [Source: frontend/lib/api.ts:75-92 — CategoryItem, CategoryGroup, Categories types]
- [Source: backend/app/routers/admin.py:127-219 — Admin category CRUD endpoints]
- [Source: backend/app/schemas/category.py — CategoryCreate, CategoryUpdate, CategoryAdminResponse schemas]
- [Source: frontend/components/playlists/SharePlaylistModal.tsx — Modal pattern reference]
- [Source: docs/admin-panel-architecture.md — Decision #1: Role-based caching, Decision #3: Admin state]
- [Source: docs/admin-panel-prd.md — FR-3.2.2: Category CRUD, UX-5.2: Category Management Modal]
- [Source: docs/epics.md:763-803 — Story 5.3 acceptance criteria]

---

## Dev Agent Record

### Context Reference

Story context created by BMAD create-story workflow on 2026-04-09.

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

- Sidebar variant was initially missing Manage links — the replace_all edit only matched the tile variant due to different indentation. Fixed by explicitly adding links to the sidebar section.
- FilterSidebar admin tests required mocking both `@/lib/auth-context` and `@/lib/favourites-context` to avoid provider dependency issues.

### Completion Notes List

- Added 4 admin category types (AdminCategory, AdminCategoryCreate, AdminCategoryUpdate, CategoryDeleteResult) and 5 API functions to `lib/api.ts`
- Created `use-admin-categories.ts` with 5 React Query hooks (query + 4 mutations) using 60s admin staleTime
- Added `adminCategories` query keys to `query-client.ts`
- Created CategoryManagementModal component with full CRUD: add (with snake_case auto-gen), inline label edit, up/down reorder, soft-delete with recipe count feedback
- Added "Manage" links below all 5 category dropdowns in BOTH sidebar and tile variants of FilterSidebar
- Modal invalidates public categories cache on close for immediate dropdown refresh
- 17 modal tests + 4 FilterSidebar admin tests = 21 new tests, all passing
- Full test suite: 283 tests pass, 0 failures, 0 regressions

### Change Log

- 2026-04-09: Implemented Story 5-3 — Category Management Modal (all tasks complete)
- 2026-04-09: Code review fixes — fixed toSnakeCase regex (strip leading non-letters), added value validation with inline error, added enabled guard on query hook, added STALE_TIMES.adminCategories to centralized config, replaced alert() with inline error feedback, added 3 missing tests (validation, reorder, empty state). 289 tests pass, 0 regressions.

### File List

- `frontend/lib/api.ts` — MODIFIED: Added admin category types and 5 API functions
- `frontend/lib/query-client.ts` — MODIFIED: Added adminCategories query keys
- `frontend/lib/hooks/use-admin-categories.ts` — CREATED: Admin category React Query hooks
- `frontend/lib/hooks/index.ts` — MODIFIED: Exported admin category hooks
- `frontend/components/admin/CategoryManagementModal.tsx` — CREATED: Category management modal
- `frontend/components/recipes/FilterSidebar.tsx` — MODIFIED: Added admin "Manage" links + modal state (both variants)
- `frontend/tests/mocks/handlers.ts` — MODIFIED: Added admin category MSW handlers and mock data
- `frontend/tests/components/admin/CategoryManagementModal.test.tsx` — CREATED: 17 modal tests
- `frontend/tests/components/recipes/FilterSidebar.admin.test.tsx` — CREATED: 4 admin filter tests
