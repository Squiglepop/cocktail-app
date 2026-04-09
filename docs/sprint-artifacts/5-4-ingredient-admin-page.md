# Story 5.4: Ingredient Admin Page

Status: done

## Story

As an **admin**,
I want **a dedicated page to manage ingredients with duplicate detection**,
So that **I can clean up the ingredient database efficiently**.

## Acceptance Criteria

### AC-1: Paginated Ingredient Table

**Given** I am logged in as an admin
**When** I navigate to `/admin/ingredients`
**Then** I see a paginated table of all ingredients
**And** columns include: Name, Type, Spirit Category, Usage Count, Actions

**Given** I am not logged in or not an admin
**When** I navigate to `/admin/ingredients`
**Then** I am redirected to the home page

### AC-2: Search and Filter

> **Note:** Epic AC-2 says "filters by ingredient name or type" in a single search box. This implementation splits into search box (name) + type dropdown because the backend `search` param only does ILIKE on `name`. Separate type dropdown provides cleaner UX and matches backend capability.

**Given** I am on the ingredients admin page
**When** I type in the search box
**Then** the table filters by ingredient name
**And** filtering is debounced (300ms delay)

**Given** I select a type from the type filter dropdown
**When** the filter is applied
**Then** only ingredients of that type are shown

### AC-3: Add Ingredient

**Given** I click "Add Ingredient"
**When** the form modal opens
**Then** I can enter name, type (dropdown), spirit_category (conditional on type=spirit), description, common_brands
**And** submitting creates the ingredient and refreshes the list

**Given** I submit a duplicate name
**When** the API returns 409
**Then** I see an error message "Ingredient name already exists"

### AC-4: Edit Ingredient

**Given** I click the edit icon on an ingredient row
**When** the form modal opens
**Then** it's pre-populated with the ingredient's current values
**And** I can update and save

### AC-5: Delete Ingredient

**Given** I click the delete icon on an ingredient row
**When** the ingredient has no recipe usage
**Then** a confirmation modal appears, and confirming deletes it

**Given** I click delete on an ingredient in use
**When** the API returns 409
**Then** I see "Cannot delete: used in {recipe_count} recipes"

### AC-6: Duplicate Detection

**Given** I click "Show Duplicates"
**When** duplicate detection completes
**Then** I see grouped lists of potential duplicates
**And** each group shows: suggested target (highest usage), duplicates with similarity scores, detection reason

### AC-7: Ingredient Merge

**Given** I select a duplicate group and click "Merge"
**When** the merge preview modal opens
**Then** I see the target ingredient and sources to be merged
**And** I see the count of recipes that will be affected
**And** I must confirm before merge executes

**Given** the merge completes
**When** the modal closes
**Then** the ingredient list refreshes
**And** a success message shows recipes updated count

---

## Tasks / Subtasks

### Task 1: Create Admin Layout and Route Protection (AC: #1)

- [x] **1.1** Create `frontend/app/admin/layout.tsx`:
  ```typescript
  'use client';

  import { useAuth } from '@/lib/auth-context';
  import { useRouter } from 'next/navigation';
  import { useEffect } from 'react';

  export default function AdminLayout({ children }: { children: React.ReactNode }) {
    const { user, isLoading } = useAuth();
    const router = useRouter();

    useEffect(() => {
      if (!isLoading && (!user || !user.is_admin)) {
        router.replace('/');
      }
    }, [user, isLoading, router]);

    if (isLoading) {
      return (
        <div className="flex items-center justify-center min-h-[50vh]">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-600" />
        </div>
      );
    }

    if (!user?.is_admin) return null;

    return <>{children}</>;
  }
  ```
  - Route protection via `useAuth()` + redirect
  - Loading spinner while auth resolves
  - Render nothing if not admin (prevents flash before redirect)

### Task 2: Add Admin Ingredient API Types and Functions (AC: #1, #3, #4, #5, #6, #7)

- [x] **2.1** In `frontend/lib/api.ts`, add admin ingredient types:
  ```typescript
  // Admin ingredient types
  export interface AdminIngredient {
    id: string;
    name: string;
    type: string;
    spirit_category: string | null;
    description: string | null;
    common_brands: string | null;
  }

  export interface AdminIngredientCreate {
    name: string;
    type: string;
    spirit_category?: string;
    description?: string;
    common_brands?: string;
  }

  export interface AdminIngredientUpdate {
    name?: string;
    type?: string;
    spirit_category?: string;
    description?: string;
    common_brands?: string;
  }

  export interface IngredientListResponse {
    items: AdminIngredient[];
    total: number;
    page: number;
    per_page: number;
  }

  // NOTE: No IngredientDeleteResponse type needed — deleteAdminIngredient returns
  // { success: boolean; recipe_count?: number } directly (see Task 2.2 delete function).

  export interface DuplicateMatch {
    ingredient_id: string;
    name: string;
    type: string;
    similarity_score: number;
    detection_reason: 'exact_match_case_insensitive' | 'fuzzy_match' | 'variation_pattern';
    usage_count: number;
  }

  export interface DuplicateGroup {
    target: DuplicateMatch;
    duplicates: DuplicateMatch[];
    group_reason: string;
  }

  export interface DuplicateDetectionResponse {
    groups: DuplicateGroup[];
    total_groups: number;
    total_duplicates: number;
  }

  export interface IngredientMergeRequest {
    source_ids: string[];
    target_id: string;
  }

  export interface IngredientMergeResponse {
    message: string;
    recipes_affected: number;
    sources_removed: number;
  }
  ```

- [x] **2.2** Add API functions following existing auth header pattern:
  ```typescript
  export async function fetchAdminIngredients(
    params: { page?: number; per_page?: number; search?: string; type?: string },
    token: string | null
  ): Promise<IngredientListResponse> {
    const headers: Record<string, string> = {};
    if (token) { headers['Authorization'] = `Bearer ${token}`; }
    const query = new URLSearchParams();
    if (params.page) query.set('page', String(params.page));
    if (params.per_page) query.set('per_page', String(params.per_page));
    if (params.search) query.set('search', params.search);
    if (params.type) query.set('type', params.type);
    const res = await fetch(`${API_BASE}/admin/ingredients?${query}`, { headers });
    if (!res.ok) throw new Error('Failed to fetch ingredients');
    return res.json();
  }

  export async function createAdminIngredient(
    data: AdminIngredientCreate, token: string | null
  ): Promise<AdminIngredient> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (token) { headers['Authorization'] = `Bearer ${token}`; }
    const res = await fetch(`${API_BASE}/admin/ingredients`, {
      method: 'POST', headers, body: JSON.stringify(data),
    });
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: 'Failed to create ingredient' }));
      throw new Error(error.detail || 'Failed to create ingredient');
    }
    return res.json();
  }

  export async function updateAdminIngredient(
    id: string, data: AdminIngredientUpdate, token: string | null
  ): Promise<AdminIngredient> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (token) { headers['Authorization'] = `Bearer ${token}`; }
    const res = await fetch(`${API_BASE}/admin/ingredients/${id}`, {
      method: 'PUT', headers, body: JSON.stringify(data),
    });
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: 'Failed to update ingredient' }));
      throw new Error(error.detail || 'Failed to update ingredient');
    }
    return res.json();
  }

  export async function deleteAdminIngredient(
    id: string, token: string | null
  ): Promise<{ success: boolean; recipe_count?: number }> {
    const headers: Record<string, string> = {};
    if (token) { headers['Authorization'] = `Bearer ${token}`; }
    const res = await fetch(`${API_BASE}/admin/ingredients/${id}`, {
      method: 'DELETE', headers,
    });
    if (res.status === 409) {
      const body = await res.json();
      return { success: false, recipe_count: body.recipe_count };
    }
    if (!res.ok) throw new Error('Failed to delete ingredient');
    return { success: true };
  }

  export async function fetchDuplicateIngredients(
    token: string | null
  ): Promise<DuplicateDetectionResponse> {
    const headers: Record<string, string> = {};
    if (token) { headers['Authorization'] = `Bearer ${token}`; }
    const res = await fetch(`${API_BASE}/admin/ingredients/duplicates`, { headers });
    if (!res.ok) throw new Error('Failed to detect duplicates');
    return res.json();
  }

  export async function mergeIngredients(
    data: IngredientMergeRequest, token: string | null
  ): Promise<IngredientMergeResponse> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (token) { headers['Authorization'] = `Bearer ${token}`; }
    const res = await fetch(`${API_BASE}/admin/ingredients/merge`, {
      method: 'POST', headers, body: JSON.stringify(data),
    });
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: 'Failed to merge ingredients' }));
      throw new Error(error.detail || 'Failed to merge ingredients');
    }
    return res.json();
  }
  ```

  **NOTE:** The delete function returns `{ success: boolean, recipe_count?: number }` instead of throwing. On 409, `success` is `false` and `recipe_count` tells the UI how many recipes use this ingredient. This avoids parsing error message strings.

### Task 3: Add Admin Ingredient Query Keys and Hooks (AC: #1, #2, #3, #4, #5, #6, #7)

- [x] **3.1** In `frontend/lib/query-client.ts`, add admin ingredient query keys:
  ```typescript
  // Inside queryKeys object, add:
  adminIngredients: {
    all: ['admin-ingredients'] as const,
    lists: () => ['admin-ingredients', 'list'] as const,
    list: (filters: Record<string, unknown>) => ['admin-ingredients', 'list', filters] as const,
    duplicates: () => ['admin-ingredients', 'duplicates'] as const,
  },
  ```

- [x] **3.2** Create `frontend/lib/hooks/use-admin-ingredients.ts`:
  ```typescript
  'use client';

  import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
  import {
    fetchAdminIngredients, createAdminIngredient, updateAdminIngredient,
    deleteAdminIngredient, fetchDuplicateIngredients, mergeIngredients,
    AdminIngredientCreate, AdminIngredientUpdate, IngredientMergeRequest,
  } from '@/lib/api';
  import { queryKeys } from '@/lib/query-client';

  export function useAdminIngredients(
    params: { page?: number; per_page?: number; search?: string; type?: string },
    token: string | null
  ) {
    return useQuery({
      queryKey: queryKeys.adminIngredients.list(params),
      queryFn: () => fetchAdminIngredients(params, token),
      staleTime: 60_000,  // Admin: 1 minute
    });
  }

  export function useCreateIngredient() {
    const queryClient = useQueryClient();
    return useMutation({
      mutationFn: ({ data, token }: { data: AdminIngredientCreate; token: string | null }) =>
        createAdminIngredient(data, token),
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: queryKeys.adminIngredients.all });
      },
    });
  }

  export function useUpdateIngredient() {
    const queryClient = useQueryClient();
    return useMutation({
      mutationFn: ({ id, data, token }: { id: string; data: AdminIngredientUpdate; token: string | null }) =>
        updateAdminIngredient(id, data, token),
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: queryKeys.adminIngredients.all });
      },
    });
  }

  export function useDeleteIngredient() {
    const queryClient = useQueryClient();
    return useMutation({
      mutationFn: ({ id, token }: { id: string; token: string | null }) =>
        deleteAdminIngredient(id, token),
      onSuccess: (result) => {
        if (result.success) {
          queryClient.invalidateQueries({ queryKey: queryKeys.adminIngredients.all });
        }
      },
    });
  }

  export function useDuplicateDetection(token: string | null, enabled: boolean) {
    return useQuery({
      queryKey: queryKeys.adminIngredients.duplicates(),
      queryFn: () => fetchDuplicateIngredients(token),
      staleTime: 60_000,
      enabled,  // Only fetch when user clicks "Show Duplicates"
    });
  }

  export function useMergeIngredients() {
    const queryClient = useQueryClient();
    return useMutation({
      mutationFn: ({ data, token }: { data: IngredientMergeRequest; token: string | null }) =>
        mergeIngredients(data, token),
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: queryKeys.adminIngredients.all });
      },
    });
  }
  ```

- [x] **3.3** Export from `frontend/lib/hooks/index.ts`:
  ```typescript
  export {
    useAdminIngredients,
    useCreateIngredient,
    useUpdateIngredient,
    useDeleteIngredient,
    useDuplicateDetection,
    useMergeIngredients,
  } from './use-admin-ingredients';
  ```

### Task 4: Create IngredientFormModal Component (AC: #3, #4)

- [x] **4.1** Create `frontend/components/admin/IngredientFormModal.tsx`:
  - Props:
    ```typescript
    interface IngredientFormModalProps {
      isOpen: boolean;
      ingredient: AdminIngredient | null;  // null = create mode, object = edit mode
      onClose: () => void;
      onSave: (data: AdminIngredientCreate | AdminIngredientUpdate) => void;
      isSaving: boolean;
      error: string | null;
    }
    ```
  - Form fields:
    - `name` (text input, required)
    - `type` (select dropdown, required): `spirit`, `liqueur`, `wine_fortified`, `bitter`, `syrup`, `juice`, `mixer`, `dairy`, `egg`, `garnish`, `other`
    - `spirit_category` (select dropdown, **only shown when type === 'spirit'**): values from existing spirit category enum
    - `description` (textarea, optional)
    - `common_brands` (textarea, optional)
  - Use same modal overlay pattern as `ConfirmDeleteModal` (`fixed inset-0 bg-black/50 z-50`)
  - Pre-populate fields in edit mode
  - Show error message below form on 409
  - Close on Escape key and overlay click
  - Disable save button while `isSaving`

  **CRITICAL: Spirit category values** — match backend enum exactly: `gin`, `vodka`, `rum_light`, `rum_dark`, `rum_aged`, `whiskey_bourbon`, `whiskey_rye`, `whiskey_scotch`, `whiskey_irish`, `whiskey_japanese`, `tequila_blanco`, `tequila_reposado`, `tequila_anejo`, `mezcal`, `brandy`, `cognac`, `pisco`, `aquavit`, `absinthe`, `cachaca`, `baijiu`, `soju`, `sake`, `other`. Use `formatEnumValue()` for display labels — import from `@/lib/api` (NOT `@/lib/utils`).

### Task 5: Create Ingredients Admin Page (AC: #1, #2, #3, #4, #5)

- [x] **5.1** Create `frontend/app/admin/ingredients/page.tsx`:
  - `'use client'` directive
  - Use `useAuth()` for token
  - State: `page` (number, default 1), `search` (string), `debouncedSearch` (string, 300ms debounce), `typeFilter` (string), `editingIngredient` (AdminIngredient | null), `showCreateForm` (boolean)
  - Use `useAdminIngredients({ page, per_page: 50, search: debouncedSearch, type: typeFilter }, token)`
  - Render:
    - Page title: "Ingredient Management"
    - Search input with 300ms debounce (use `setTimeout`/`clearTimeout` in a `useEffect`)
    - Type filter dropdown (all ingredient types + "All Types" option)
    - "Add Ingredient" button → opens `IngredientFormModal` in create mode
    - Table with columns: Name, Type, Spirit Category (show "-" if null), Actions (Edit pencil, Delete trash)
    - **Usage count column**: The epic AC-1 specifies "columns include: Name, Type, Spirit Category, Usage Count, Actions" but the backend `IngredientAdminResponse` does NOT include `usage_count`. **Decision: Intentionally omit usage count from the main table** — this is a known deviation from the epic AC. Usage count is shown on delete attempt (409 response) and in duplicate detection results. Adding it to the list endpoint would require a backend change (separate story).
    - Pagination controls: Previous/Next buttons, "Page X of Y" indicator
    - Total count display: "Showing X ingredients"

- [x] **5.2** Search debounce implementation:
  ```typescript
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search);
      setPage(1); // Reset to page 1 on search change
    }, 300);
    return () => clearTimeout(timer);
  }, [search]);
  ```

- [x] **5.3** Handle create/edit:
  - Create: `useCreateIngredient` mutation, on success close modal
  - Edit: `useUpdateIngredient` mutation, on success close modal
  - Error handling: 409 → show "name already exists" in modal

- [x] **5.4** Handle delete (two-step UX):
  - **Step 1 — Confirmation:** Open `ConfirmDeleteModal` with props: `title="Delete Ingredient"`, `itemName={ingredient.name}`, `isDeleting={deleteMutation.isPending}`
  - **Step 2 — API call:** On confirm, call `useDeleteIngredient`
    - If `result.success === true`: list refreshes automatically via query invalidation, close modal
    - If `result.success === false`: close the modal, show **inline error** above the table: "Cannot delete: used in {recipe_count} recipes" (do NOT show this inside the modal)
  - On cancel: close modal, no action

### Task 6: Create DuplicateDetectionPanel Component (AC: #6, #7)

- [x] **6.1** Create `frontend/components/admin/DuplicateDetectionPanel.tsx`:
  - Props:
    ```typescript
    interface DuplicateDetectionPanelProps {
      token: string | null;
    }
    ```
  - State: `showDuplicates` (boolean, default false), `mergingGroup` (DuplicateGroup | null)
  - "Show Duplicates" button sets `showDuplicates = true`, which enables `useDuplicateDetection(token, showDuplicates)` — the query does NOT fire until the user clicks the button (React Query `enabled: false` → `enabled: true` transition triggers the fetch)
  - Display results:
    - Summary: "Found {total_groups} groups with {total_duplicates} potential duplicates"
    - Each group shows:
      - **Target** (green highlight): name, type, usage count, "(suggested target)"
      - **Duplicates**: name, type, similarity score (as percentage), detection reason badge, usage count
      - "Merge" button per group
    - Detection reason display mapping:
      - `exact_match_case_insensitive` → "Exact Match"
      - `fuzzy_match` → "Fuzzy Match (XX%)"
      - `variation_pattern` → "Variation Pattern"
  - Empty state: "No duplicates detected" when groups is empty

- [x] **6.2** Create `frontend/components/admin/MergePreviewModal.tsx`:
  - Props:
    ```typescript
    interface MergePreviewModalProps {
      isOpen: boolean;
      group: DuplicateGroup;
      onConfirm: () => void;
      onCancel: () => void;
      isMerging: boolean;
    }
    ```
  - Show target ingredient prominently
  - List source ingredients that will be merged (deleted)
  - Show total recipes that will be affected (sum of source usage_counts)
  - Warning text: "This will update all recipes using the source ingredients to use '{target.name}' instead. Source ingredients will be deleted."
  - Confirm/Cancel buttons (disable during merge)
  - Use same modal pattern as `ConfirmDeleteModal`

- [x] **6.3** In the ingredients page, integrate the DuplicateDetectionPanel:
  - Place below the main ingredients table
  - Merge flow: click "Merge" on group → open MergePreviewModal → confirm → call `useMergeIngredients` → on success show "Merged: {recipes_affected} recipes updated, {sources_removed} ingredients removed" → close modal → invalidate both ingredients list and duplicates queries

### Task 7: Write Tests (AC: #1, #2, #3, #4, #5, #6, #7)

- [x] **7.1** Add MSW handlers for admin ingredient endpoints in `frontend/tests/mocks/handlers.ts`:
  ```typescript
  // Admin ingredient mock data
  export const mockAdminIngredients = [
    { id: '1', name: 'Lime Juice', type: 'juice', spirit_category: null, description: 'Fresh lime juice', common_brands: null },
    { id: '2', name: 'Simple Syrup', type: 'syrup', spirit_category: null, description: '1:1 sugar water', common_brands: null },
    { id: '3', name: 'London Dry Gin', type: 'spirit', spirit_category: 'gin', description: 'Classic gin style', common_brands: 'Beefeater, Tanqueray' },
  ];

  export const mockDuplicateResponse = {
    groups: [
      {
        target: { ingredient_id: '1', name: 'Lime Juice', type: 'juice', similarity_score: 1.0, detection_reason: 'exact_match_case_insensitive', usage_count: 15 },
        duplicates: [
          { ingredient_id: '10', name: 'lime juice', type: 'juice', similarity_score: 1.0, detection_reason: 'exact_match_case_insensitive', usage_count: 3 },
        ],
        group_reason: 'exact_match_case_insensitive',
      },
    ],
    total_groups: 1,
    total_duplicates: 1,
  };

  // Handlers:
  http.get(`${API_BASE}/admin/ingredients`, ({ request }) => {
    const authHeader = request.headers.get('Authorization');
    if (!authHeader) return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 });
    const url = new URL(request.url);
    const search = url.searchParams.get('search');
    let items = mockAdminIngredients;
    if (search) items = items.filter(i => i.name.toLowerCase().includes(search.toLowerCase()));
    return HttpResponse.json({ items, total: items.length, page: 1, per_page: 50 });
  }),

  http.post(`${API_BASE}/admin/ingredients`, async ({ request }) => {
    const authHeader = request.headers.get('Authorization');
    if (!authHeader) return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 });
    const body = await request.json() as { name: string; type: string };
    if (body.name.toLowerCase() === 'lime juice') {
      return HttpResponse.json({ detail: 'Ingredient with this name already exists' }, { status: 409 });
    }
    return HttpResponse.json({ id: '99', ...body, spirit_category: null, description: null, common_brands: null }, { status: 201 });
  }),

  http.put(`${API_BASE}/admin/ingredients/:id`, async ({ params, request }) => {
    const authHeader = request.headers.get('Authorization');
    if (!authHeader) return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 });
    const body = await request.json() as Record<string, unknown>;
    const existing = mockAdminIngredients.find(i => i.id === params.id);
    if (!existing) return HttpResponse.json({ detail: 'Ingredient not found' }, { status: 404 });
    return HttpResponse.json({ ...existing, ...body });
  }),

  http.delete(`${API_BASE}/admin/ingredients/:id`, ({ params, request }) => {
    const authHeader = request.headers.get('Authorization');
    if (!authHeader) return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 });
    if (params.id === '1') {
      return HttpResponse.json({ message: 'Cannot delete ingredient used in recipes', recipe_count: 15 }, { status: 409 });
    }
    return new HttpResponse(null, { status: 200 });
  }),

  http.get(`${API_BASE}/admin/ingredients/duplicates`, ({ request }) => {
    const authHeader = request.headers.get('Authorization');
    if (!authHeader) return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 });
    return HttpResponse.json(mockDuplicateResponse);
  }),

  http.post(`${API_BASE}/admin/ingredients/merge`, async ({ request }) => {
    const authHeader = request.headers.get('Authorization');
    if (!authHeader) return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 });
    return HttpResponse.json({ message: 'Ingredients merged', recipes_affected: 3, sources_removed: 1 });
  }),
  ```

- [x] **7.2** Create `frontend/tests/components/admin/IngredientFormModal.test.tsx`:
  - `test renders create form when ingredient is null` — verify empty fields, "Add Ingredient" title
  - `test renders edit form when ingredient is provided` — verify pre-populated fields
  - `test shows spirit_category dropdown only when type is spirit`
  - `test hides spirit_category dropdown when type is not spirit`
  - `test calls onSave with form data on submit`
  - `test shows error message when error prop is set`
  - `test disables save button when isSaving`
  - `test closes on Escape key`
  - `test closes on overlay click`

- [x] **7.3** Create `frontend/tests/components/admin/DuplicateDetectionPanel.test.tsx`:
  - `test shows "Show Duplicates" button initially`
  - `test loads and displays duplicate groups`
  - `test shows detection reason badges`
  - `test shows empty state when no duplicates found`
  - `test opens merge preview modal on Merge click`

- [x] **7.4** Create `frontend/tests/components/admin/MergePreviewModal.test.tsx`:
  - `test renders target and source ingredients`
  - `test shows affected recipe count`
  - `test calls onConfirm when Merge button clicked`
  - `test disables buttons when isMerging`
  - `test closes on Cancel`

- [x] **7.5** Create `frontend/tests/app/admin/IngredientsPage.test.tsx`:
  - `test renders ingredient table with data` — verify 3 mock ingredients shown
  - `test redirects non-admin users` — mock non-admin auth, verify redirect
  - `test search filters ingredients with debounce` — type search, wait 300ms, verify filtered results
  - `test type filter shows filtered results` — select type, verify filter applied
  - `test clicking Add opens create modal` — click "Add Ingredient", verify modal
  - `test clicking edit icon opens edit modal` — click pencil, verify pre-populated modal
  - `test successful create refreshes list` — submit form, verify list refreshes
  - `test 409 on create shows error` — submit duplicate name, verify error in modal
  - `test delete shows confirmation then removes` — click trash, confirm, verify removed
  - `test delete of in-use ingredient shows error` — delete ingredient with recipes, verify error message
  - `test pagination controls work` — verify Previous/Next/page display
  - `test shows error message when API returns 500` — override MSW handler to return 500, verify error UI renders:

    ```typescript
    server.use(
      http.get('*/api/admin/ingredients', () => new HttpResponse(null, { status: 500 }))
    );
    render(<IngredientsPage />);
    expect(await screen.findByText(/error/i)).toBeInTheDocument();
    ```

  - `test handles 401 API response gracefully` — override MSW handler to return 401 (simulating expired token), verify error or redirect behavior:

    ```typescript
    server.use(
      http.get('*/api/admin/ingredients', () => HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 }))
    );
    render(<IngredientsPage />);
    expect(await screen.findByText(/error|unauthorized/i)).toBeInTheDocument();
    ```

- [x] **7.6** Run full frontend test suite: `cd frontend && npm test` — no regressions

---

## Dev Notes

### CRITICAL: This is a Frontend-Only Story

**Zero backend changes required.** The backend already has all 6 endpoints fully implemented and tested:

| Endpoint | Router Location | Description |
|----------|----------------|-------------|
| `GET /api/admin/ingredients` | `admin.py:225-242` | Paginated list, search, type filter |
| `GET /api/admin/ingredients/duplicates` | `admin.py:245-255` | Three detection strategies |
| `POST /api/admin/ingredients` | `admin.py:299-309` | Create with 409 on duplicate name |
| `GET /api/admin/ingredients/{id}` | `admin.py:287-296` | Single ingredient detail |
| `PUT /api/admin/ingredients/{id}` | `admin.py:312-340` | Update with 409 on name conflict |
| `DELETE /api/admin/ingredients/{id}` | `admin.py:343-372` | Hard delete or 409 with recipe_count |
| `POST /api/admin/ingredients/merge` | `admin.py:258-284` | Merge sources into target |

All protected by `require_admin`. All audit-logged.

### Backend API Contract Details

**GET `/api/admin/ingredients`** query params:
- `page` (int, default=1, min=1)
- `per_page` (int, default=50, min=1, max=100)
- `search` (optional string — case-insensitive ILIKE on name)
- `type` (optional string — alias for `ingredient_type` in backend)

**Response `IngredientAdminResponse`** fields: `id`, `name`, `type`, `spirit_category` (nullable), `description` (nullable), `common_brands` (nullable). Note: **NO `usage_count` in list response** — usage count is only available in duplicate detection results and delete 409 response.

**DELETE 409 response** uses `JSONResponse` (not HTTPException), returns: `{ "message": "...", "recipe_count": int }`

**Merge request**: `source_ids` (list, min 1 item), `target_id` (string). Backend auto-deduplicates source_ids. Raises 400 if target in sources, 404 if any ID not found.

**Duplicate Detection** returns groups with:
- `target`: ingredient with highest usage count in group
- `duplicates`: other ingredients in the group
- Each match has `similarity_score`, `detection_reason`, `usage_count`
- Three strategies: exact_match_case_insensitive, fuzzy_match (>0.8), variation_pattern

### Ingredient Type Values

Match backend `IngredientAdminCreate.type` Literal exactly:
```
spirit, liqueur, wine_fortified, bitter, syrup, juice, mixer, dairy, egg, garnish, other
```

Display labels: use `formatEnumValue()` from `@/lib/api` (e.g., `wine_fortified` → "Wine Fortified")

### This is the FIRST Admin Page

No `frontend/app/admin/` directory exists yet. This story creates:
- `app/admin/layout.tsx` — admin route protection (reused by Stories 5-5, 5-6)
- `app/admin/ingredients/page.tsx` — ingredients page

**Important:** Do NOT create `app/admin/page.tsx` (admin dashboard) — that's not part of this story. The layout just protects routes; navigating to `/admin` will show a 404 which is fine for now.

### Current Frontend State

- **AdminBadge** exists at `components/admin/AdminBadge.tsx` (from Story 5-1)
- **ConfirmDeleteModal** exists at `components/ui/ConfirmDeleteModal.tsx` (from Story 5-2) — **REUSE for ingredient delete confirmation**
- **`is_admin: boolean`** on User interface in `auth-context.tsx` (from Story 5-1)
- **No admin ingredient API functions** in `lib/api.ts` — must create
- **No admin ingredient hooks** — must create
- **No admin pages** — `app/admin/` directory doesn't exist yet

### Key Implementation Decisions

1. **Omit usage count from main table** — Backend `IngredientAdminResponse` doesn't include it. Adding it would require a backend change (new story). Show it only in delete error and duplicate detection.
2. **No drag-and-drop** — Not in AC. Table with standard sort.
3. **Search debounce: 300ms** — Per AC. Use `setTimeout`/`clearTimeout` in `useEffect`.
4. **Admin staleTime: 60 seconds** — Per architecture decision #1.
5. **Reuse ConfirmDeleteModal** from Story 5-2 for delete confirmation.
6. **Duplicate detection is on-demand** — "Show Duplicates" button, not loaded by default (can be slow with many ingredients).
7. **Admin layout creates redirect pattern** — Will be reused by Stories 5-5 and 5-6.
8. **Delete returns structured response** — Not a thrown error. `{ success: boolean, recipe_count?: number }` so UI can show recipe count on 409.

### Dependency on Previous Stories

| Story | Dependency | Status |
|-------|-----------|--------|
| 5-1 | `is_admin` on User interface, AdminBadge | Done (review) |
| 5-2 | ConfirmDeleteModal component | In-progress |

**If Story 5-2 is not yet merged:** Create `ConfirmDeleteModal` locally or inline a simple confirmation. The component is small (~80 lines). Check if the file exists before importing; if not, create a minimal version.

### Out-of-Scope (Explicitly Deferred)

- **Admin dashboard page** (`/admin`) — Not part of this story
- **Admin sidebar navigation** — Can be added in a later story when multiple admin pages exist
- **Ingredient usage count in table** — Requires backend change
- **Bulk delete/export** — Per PRD, deferred to Phase 2
- **Inline editing in table rows** — AC specifies modal-based edit, not inline

### Architecture Compliance

| Requirement | Implementation |
|-------------|----------------|
| Admin state check | `user?.is_admin === true` [Source: docs/admin-panel-architecture.md — Decision #3] |
| Route protection | Admin layout with `useEffect` redirect [Source: docs/admin-panel-architecture.md — Component Boundaries] |
| Role-based caching | `staleTime: 60_000` for admin queries [Source: docs/admin-panel-architecture.md — Decision #1] |
| Admin component location | `components/admin/` [Source: docs/admin-panel-architecture.md — Frontend Additions] |
| Admin hooks location | `lib/hooks/use-admin-ingredients.ts` [Source: docs/admin-panel-architecture.md — Frontend Additions] |
| Admin page location | `app/admin/ingredients/page.tsx` [Source: docs/admin-panel-architecture.md — Frontend Additions] |
| Query invalidation | Invalidate `adminIngredients.all` on mutations [Source: docs/admin-panel-architecture.md — Category Caching] |

### Library/Framework Requirements

- **No new dependencies.** Uses existing packages only.
- Lucide React icons: `Search`, `Plus`, `Pencil`, `Trash2`, `ChevronLeft`, `ChevronRight`, `X`, `Loader2`, `AlertTriangle`, `GitMerge` (or similar for merge) — all already in project
- TypeScript strict mode — all props and return types typed
- Tailwind CSS for all styling — use `clsx` for conditional classes
- React Query v5 object syntax for all hooks

### File Structure Requirements

| File | Action | Description |
|------|--------|-------------|
| `frontend/app/admin/layout.tsx` | CREATE | Admin route protection layout |
| `frontend/app/admin/ingredients/page.tsx` | CREATE | Ingredients admin page |
| `frontend/lib/api.ts` | MODIFY | Add admin ingredient types and API functions |
| `frontend/lib/query-client.ts` | MODIFY | Add `adminIngredients` query keys |
| `frontend/lib/hooks/use-admin-ingredients.ts` | CREATE | Admin ingredient hooks (1 query + 5 mutations) |
| `frontend/lib/hooks/index.ts` | MODIFY | Export admin ingredient hooks |
| `frontend/components/admin/IngredientFormModal.tsx` | CREATE | Create/edit ingredient form modal |
| `frontend/components/admin/DuplicateDetectionPanel.tsx` | CREATE | Duplicate detection UI |
| `frontend/components/admin/MergePreviewModal.tsx` | CREATE | Merge confirmation modal |
| `frontend/tests/mocks/handlers.ts` | MODIFY | Add admin ingredient MSW handlers |
| `frontend/tests/components/admin/IngredientFormModal.test.tsx` | CREATE | Form modal tests (9 cases) |
| `frontend/tests/components/admin/DuplicateDetectionPanel.test.tsx` | CREATE | Duplicate panel tests (5 cases) |
| `frontend/tests/components/admin/MergePreviewModal.test.tsx` | CREATE | Merge modal tests (4 cases) |
| `frontend/tests/app/admin/IngredientsPage.test.tsx` | CREATE | Full page integration tests (13 cases) |

**NOTE on test directories:** `tests/components/admin/` may already exist from previous stories. `tests/app/admin/` is new — create it. Previous stories used `.admin.test.tsx` suffix for admin tests on EXISTING components; these are NEW admin-only components so plain `.test.tsx` naming is correct.

### Testing Requirements

**Test framework:** vitest (globals enabled — do NOT import describe/it/expect)
**Test setup:** `frontend/tests/setup.ts` already configured — don't duplicate
**Mock pattern:** MSW 2.x handlers for API mocking:
```typescript
http.get('*/api/admin/ingredients', () => HttpResponse.json({ items: mockAdminIngredients, total: 3, page: 1, per_page: 50 }))
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

**Mock next/navigation for admin page tests:**
```typescript
const mockPush = vi.fn();
const mockReplace = vi.fn();
vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush, replace: mockReplace }),
  usePathname: () => '/admin/ingredients',
}))
```

**Coverage target:** 100% on new code paths

### Previous Story Intelligence

**From Story 5-3 (Category Management Modal — ready-for-dev):**
- Admin category hooks pattern: `useAdminCategories(type, token)` with 60s staleTime
- Query key pattern: `adminCategories.byType(type)`
- Modal pattern: fixed overlay, Escape/overlay close, loading states
- API function pattern: auth header via `Record<string, string>`
- Test pattern: MSW handlers with auth check, separate test files per component

**From Story 5-2 (Recipe Admin Controls — in progress):**
- `ConfirmDeleteModal` at `components/ui/ConfirmDeleteModal.tsx` — reuse this
- Admin action pattern: `const isAdmin = user?.is_admin === true`
- Separate `.admin.test.tsx` files for admin tests

**From Story 5-1 (Admin State & Indicator — review):**
- `is_admin: boolean` on User interface
- AdminBadge at `components/admin/AdminBadge.tsx`
- Mock user has `is_admin: false` in `tests/mocks/handlers.ts`

**From Epic 4→5 Prep (`d8e8c5b`):**
- Frontend test suite clean: 238+ tests pass, build succeeds

### Git Intelligence

**Recent commits:**
- `d8e8c5b` fix: Epic 4→5 prep — fix 23 frontend test failures, verify toolchain
- `3bf2553` feat: Epic 4 — Audit Trail & Compliance (stories 4-1, 4-2)

**Key insight:** Frontend is clean. Stories 5-1 and 5-2 may have added new files/tests (5-1 is in review, 5-2 in-progress). Run `npm test` early to verify baseline.

### Project Context Reference

See `docs/project_context.md` for:
- TypeScript strict mode rules (no implicit `any`)
- React Query v5 object syntax — `useQuery({ queryKey, queryFn })`
- MSW 2.x test handler pattern — `http.get('*/api/...', () => HttpResponse.json(...))`
- Component file naming: PascalCase.tsx
- `clsx` for conditional Tailwind classes
- Provider hierarchy: Query -> Auth -> Offline -> Favourites
- Admin authorization pattern: `user?.is_admin`
- Admin staleTime: 60_000 (1 min)
- Service->Router error convention: ValueError -> 400, LookupError -> 404, None -> 409

### References

- [Source: backend/app/routers/admin.py:225-372 — Admin ingredient CRUD + merge + duplicate endpoints]
- [Source: backend/app/schemas/ingredient.py — IngredientAdminCreate/Update/Response, DuplicateGroup, MergeRequest/Response]
- [Source: backend/app/services/ingredient_service.py — Duplicate detection (3 strategies), merge logic, CRUD]
- [Source: frontend/lib/api.ts:18-24 — Existing public Ingredient interface]
- [Source: frontend/lib/query-client.ts:26-28 — Existing query key patterns]
- [Source: frontend/lib/hooks/index.ts — Hook export pattern]
- [Source: frontend/components/ui/ConfirmDeleteModal.tsx — Reusable delete confirmation modal (Story 5-2)]
- [Source: frontend/components/playlists/SharePlaylistModal.tsx — Modal pattern reference]
- [Source: docs/admin-panel-architecture.md — Decision #1 (caching), #3 (admin state), Frontend Additions]
- [Source: docs/admin-panel-prd.md — FR-3.5.1-3.5.5 (ingredient admin requirements)]
- [Source: docs/epics.md:806-849 — Story 5.4 acceptance criteria]

---

## Dev Agent Record

### Context Reference

Story context created by BMAD create-story workflow on 2026-04-09.

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

- Initial test run: 286 tests passing (baseline)
- Post-implementation: 338 tests passing (+32 story-specific new), 1 pre-existing failure in login.test.tsx (not from this story)
- Fixed 3 test assertion issues (duplicate element text matches in modal tests)
- Code review: added non-admin redirect test (+1), fixed grammar in DuplicateDetectionPanel, updated test assertion

### Completion Notes List

- Task 1: Created `app/admin/layout.tsx` with useAuth + redirect pattern for admin route protection
- Task 2: Added 8 admin ingredient types + 6 API functions to `lib/api.ts` following existing auth header pattern
- Task 3: Added `adminIngredients` query keys to `query-client.ts`, created `use-admin-ingredients.ts` with 4 queries/mutations + 2 hooks (duplicate detection, merge), exported from hooks index
- Task 4: Created `IngredientFormModal` with create/edit modes, conditional spirit_category dropdown, Escape/overlay close, error display
- Task 5: Created ingredients admin page with search (300ms debounce), type filter, paginated table, CRUD integration, delete error banner
- Task 6: Created `DuplicateDetectionPanel` with on-demand loading (React Query enabled flag), detection reason badges, merge flow. Created `MergePreviewModal` with target/source display and affected recipe count
- Task 7: Added 6 MSW handlers + mock data to handlers.ts. Created 4 test files with 32 total tests covering all ACs (+1 added in code review = 33). Full suite: 338 pass, 1 pre-existing failure

### File List

**Created:**
- frontend/app/admin/layout.tsx
- frontend/app/admin/ingredients/page.tsx
- frontend/components/admin/IngredientFormModal.tsx
- frontend/components/admin/DuplicateDetectionPanel.tsx
- frontend/components/admin/MergePreviewModal.tsx
- frontend/lib/hooks/use-admin-ingredients.ts
- frontend/tests/components/admin/IngredientFormModal.test.tsx
- frontend/tests/components/admin/DuplicateDetectionPanel.test.tsx
- frontend/tests/components/admin/MergePreviewModal.test.tsx
- frontend/tests/app/admin/IngredientsPage.test.tsx

**Modified:**
- frontend/lib/api.ts (added admin ingredient types + API functions)
- frontend/lib/query-client.ts (added adminIngredients query keys)
- frontend/lib/hooks/index.ts (added admin ingredient hook exports)
- frontend/tests/mocks/handlers.ts (added admin ingredient MSW handlers + mock data)
- docs/sprint-artifacts/sprint-status.yaml (5-4 status: ready-for-dev → in-progress → review)

### Change Log

- 2026-04-10: Story 5-4 implemented — admin ingredient page with CRUD, search/filter, duplicate detection, merge flow. 10 files created, 4 modified. 32 new tests.
- 2026-04-10: Code review fixes — added non-admin redirect test (H1), fixed plural grammar in DuplicateDetectionPanel (M1), corrected test count claims (M2).
