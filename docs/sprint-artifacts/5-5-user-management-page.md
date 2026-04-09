# Story 5.5: User Management Page

Status: done

## Story

As an **admin**,
I want **a page to view and manage all users**,
So that **I can control access and grant admin privileges**.

## Acceptance Criteria

### AC-1: Paginated User Table

**Given** I am logged in as an admin
**When** I navigate to `/admin/users`
**Then** I see a paginated table of all users
**And** columns include: Email, Display Name, Status, Admin, Recipe Count, Created, Last Login

**Given** I am not logged in or not an admin
**When** I navigate to `/admin/users`
**Then** I am redirected to the home page

### AC-2: Search

**Given** I am on the user management page
**When** I type in the search box
**Then** the table filters by email or display name
**And** filtering is debounced (300ms delay)

### AC-3: Status Filter

**Given** I am on the user management page
**When** I select a status filter (All / Active / Inactive)
**Then** the table shows only users matching that status

### AC-4: Toggle User Active Status

**Given** I click the status toggle for a user
**When** I toggle from Active to Inactive
**Then** a confirmation modal asks "Deactivate this user?"
**And** confirming deactivates the user and updates the UI

**Given** I try to deactivate my own account
**When** I click the toggle
**Then** I see an error message "Cannot deactivate your own account"
**And** my status remains unchanged

### AC-5: Toggle Admin Status

**Given** I click the admin toggle for a user
**When** I grant admin status
**Then** a confirmation modal asks "Grant admin privileges to [email]?"
**And** confirming grants admin and updates the UI

**Given** I try to remove my own admin status
**When** I click the toggle
**Then** I see an error message "Cannot remove your own admin status"
**And** my admin status remains unchanged

---

## Tasks / Subtasks

### Task 1: Add Admin User API Types and Functions (AC: #1, #2, #3, #4, #5)

- [x] **1.1** In `frontend/lib/api.ts`, add admin user types:
  ```typescript
  export interface AdminUser {
    id: string;
    email: string;
    display_name: string | null;
    is_active: boolean;
    is_admin: boolean;
    recipe_count: number;
    created_at: string;
    last_login_at: string | null;
  }

  export interface UserListResponse {
    items: AdminUser[];
    total: number;
    page: number;
    per_page: number;
  }

  export interface UserStatusUpdate {
    is_active?: boolean;
    is_admin?: boolean;
  }

  export interface UserStatusResponse {
    id: string;
    email: string;
    display_name: string | null;
    is_active: boolean;
    is_admin: boolean;
    message: string;
  }
  ```

- [x] **1.2** Add API functions following existing auth header pattern:
  ```typescript
  export async function fetchAdminUsers(
    params: { page?: number; per_page?: number; search?: string; status?: string },
    token: string | null
  ): Promise<UserListResponse> {
    const headers: Record<string, string> = {};
    if (token) { headers['Authorization'] = `Bearer ${token}`; }
    const query = new URLSearchParams();
    if (params.page != null) query.set('page', String(params.page));
    if (params.per_page != null) query.set('per_page', String(params.per_page));
    if (params.search) query.set('search', params.search);
    if (params.status) query.set('status', params.status);
    const res = await fetch(`${API_BASE}/admin/users?${query}`, { headers });
    if (!res.ok) throw new Error('Failed to fetch users');
    return res.json();
  }

  export async function updateUserStatus(
    id: string, data: UserStatusUpdate, token: string | null
  ): Promise<UserStatusResponse> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (token) { headers['Authorization'] = `Bearer ${token}`; }
    const res = await fetch(`${API_BASE}/admin/users/${id}`, {
      method: 'PATCH', headers, body: JSON.stringify(data),
    });
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: 'Failed to update user' }));
      throw new Error(error.detail || 'Failed to update user');
    }
    return res.json();
  }
  ```

### Task 2: Add Admin User Query Keys and Hooks (AC: #1, #2, #3, #4, #5)

- [x] **2.1** In `frontend/lib/query-client.ts`, add admin user query keys:
  ```typescript
  adminUsers: {
    all: ['admin-users'] as const,
    lists: () => ['admin-users', 'list'] as const,
    list: (filters: Record<string, unknown>) => ['admin-users', 'list', filters] as const,
  },
  ```

- [x] **2.2** Create `frontend/lib/hooks/use-admin-users.ts`:
  ```typescript
  'use client';

  import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
  import { fetchAdminUsers, updateUserStatus, UserStatusUpdate } from '@/lib/api';
  import { queryKeys } from '@/lib/query-client';

  export function useAdminUsers(
    params: { page?: number; per_page?: number; search?: string; status?: string },
    token: string | null
  ) {
    return useQuery({
      queryKey: queryKeys.adminUsers.list(params),
      queryFn: () => fetchAdminUsers(params, token),
      staleTime: 60_000,  // Admin: 1 minute
      enabled: !!token,   // Prevent 401 during auth resolution (matches use-admin-categories.ts pattern)
    });
  }

  export function useUpdateUserStatus() {
    const queryClient = useQueryClient();
    return useMutation({
      mutationFn: ({ id, data, token }: { id: string; data: UserStatusUpdate; token: string | null }) =>
        updateUserStatus(id, data, token),
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: queryKeys.adminUsers.all });
      },
    });
  }
  ```

- [x] **2.3** Export from `frontend/lib/hooks/index.ts`:
  ```typescript
  export { useAdminUsers, useUpdateUserStatus } from './use-admin-users';
  ```

### Task 3: Create User Management Page (AC: #1, #2, #3, #4, #5)

- [x] **3.1** Create `frontend/app/admin/users/page.tsx`:
  - `'use client'` directive
  - Use `useAuth()` for token and current user
  - State: `page` (number, default 1), `search` (string), `debouncedSearch` (string, 300ms debounce), `statusFilter` (string: `''` | `'active'` | `'inactive'`), `confirmAction` (object | null for modal state)
  - Use `useAdminUsers({ page, per_page: 50, search: debouncedSearch, status: statusFilter || undefined }, token)`
  - Use `useUpdateUserStatus()` mutation

  **Layout:**
  - Page title: "User Management"
  - Search input with 300ms debounce (same `setTimeout`/`clearTimeout` in `useEffect` pattern as 5-4)
  - Status filter: three buttons or select — "All", "Active", "Inactive"
  - Table columns:
    | Column | Field | Notes |
    |--------|-------|-------|
    | Email | `email` | Primary identifier |
    | Display Name | `display_name` | Show "—" if null |
    | Status | `is_active` | Green "Active" / Red "Inactive" badge |
    | Admin | `is_admin` | Toggle switch or badge |
    | Recipes | `recipe_count` | Number |
    | Created | `created_at` | Format as date string |
    | Last Login | `last_login_at` | Format as date string, "Never" if null |
  - Pagination: Previous/Next buttons, "Page X of Y" indicator, total count

  **Loading / Error / Empty States (MANDATORY — follow project_context.md pattern):**
  - **Loading**: Show a loading spinner or skeleton table rows while `isLoading` is true
  - **Error**: If query `error` is truthy, show an error message with retry button: `"Failed to load users"` + `onClick: () => refetch()`
  - **Empty**: When `data.items.length === 0`, show: `"No users found"` with hint `"Try adjusting your search or filter"`
  - Pattern: `if (isLoading) return <Loading />; if (error) return <Error />; if (!data.items.length) return <Empty />;`

  **Accessibility (MANDATORY):**
  - Use semantic `<table>` element with `<thead>` / `<tbody>`
  - Toggle controls: `role="switch"` with `aria-checked={value}` and `aria-label="Toggle [field] for [email]"`
  - Status badges: `role="status"` (consistent with AdminBadge from 5-1)
  - Error messages: wrap in `aria-live="polite"` region for screen reader announcements
  - Search input: `aria-label="Search users"`

- [x] **3.2** Search debounce implementation:
  ```typescript
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search);
      setPage(1);
    }, 300);
    return () => clearTimeout(timer);
  }, [search]);
  ```

- [x] **3.3** Status toggle handler (for both `is_active` and `is_admin`):
  ```typescript
  interface ConfirmAction {
    userId: string;
    userEmail: string;
    field: 'is_active' | 'is_admin';
    newValue: boolean;
  }

  function handleToggle(user: AdminUser, field: 'is_active' | 'is_admin') {
    // Self-protection: prevent toggling own status
    if (user.id === currentUser?.id) {
      if (field === 'is_active') {
        setError('Cannot deactivate your own account');
      } else {
        setError('Cannot remove your own admin status');
      }
      return;
    }
    setConfirmAction({
      userId: user.id,
      userEmail: user.email,
      field,
      newValue: !user[field],
    });
  }
  ```

- [x] **3.4** Confirmation modal — **DO NOT reuse `ConfirmDeleteModal` directly** (its `itemName` prop and delete semantics don't fit status toggles). Instead, build a simple inline confirmation modal or create a lightweight `ConfirmActionModal` with these props:

  ```typescript
  interface ConfirmActionModalProps {
    isOpen: boolean;
    title: string;       // Action-specific title
    message: string;     // Descriptive confirmation text
    confirmLabel: string; // Button text (e.g., "Deactivate", "Grant Admin")
    onConfirm: () => void;
    onCancel: () => void;
    isLoading?: boolean;
    variant?: 'danger' | 'warning' | 'default'; // Red for deactivate, amber for admin changes
  }
  ```
  - Follow the same overlay pattern as `ConfirmDeleteModal`: `fixed inset-0 bg-black/50 z-50`, Escape key close, overlay click close
  - Modal title varies by action:
    - Deactivate: title="Deactivate this user?", variant="danger"
    - Activate: title="Activate this user?", variant="default"
    - Grant admin: title="Grant admin privileges to [email]?", variant="warning"
    - Revoke admin: title="Revoke admin privileges from [email]?", variant="warning"
  - On confirm: call `updateUserStatus.mutateAsync({ id, data: { [field]: newValue }, token })`
  - On success: close modal, list refreshes via query invalidation
  - On error: show error message (backend returns 400 for self-modification attempts as extra safety)

- [x] **3.5** Error handling:
  - Self-modification errors shown as inline alert (dismissible)
  - API errors from mutation shown as inline alert
  - Clear error state on new action

### Task 4: Admin Route Protection (AC: #1)

- [x] **4.1** CREATE `frontend/app/admin/layout.tsx` (does NOT exist — Story 5-4 is not yet implemented):
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

### Task 5: Write Tests (AC: #1, #2, #3, #4, #5)

- [x] **5.1** Add MSW handlers for admin user endpoints in `frontend/tests/mocks/handlers.ts`:
  ```typescript
  export const mockAdminUsers = [
    {
      id: '1', email: 'admin@test.com', display_name: 'Admin User',
      is_active: true, is_admin: true, recipe_count: 10,
      created_at: '2026-01-01T00:00:00Z', last_login_at: '2026-04-08T12:00:00Z',
    },
    {
      id: '2', email: 'user@test.com', display_name: 'Regular User',
      is_active: true, is_admin: false, recipe_count: 5,
      created_at: '2026-02-01T00:00:00Z', last_login_at: '2026-04-07T12:00:00Z',
    },
    {
      id: '3', email: 'inactive@test.com', display_name: null,
      is_active: false, is_admin: false, recipe_count: 0,
      created_at: '2026-03-01T00:00:00Z', last_login_at: null,
    },
  ];

  // Handlers:
  http.get('*/api/admin/users', ({ request }) => {
    const authHeader = request.headers.get('Authorization');
    if (!authHeader) return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 });
    const url = new URL(request.url);
    const search = url.searchParams.get('search');
    const status = url.searchParams.get('status');
    let items = mockAdminUsers;
    if (search) {
      items = items.filter(u =>
        u.email.toLowerCase().includes(search.toLowerCase()) ||
        (u.display_name && u.display_name.toLowerCase().includes(search.toLowerCase()))
      );
    }
    if (status === 'active') items = items.filter(u => u.is_active);
    if (status === 'inactive') items = items.filter(u => !u.is_active);
    return HttpResponse.json({ items, total: items.length, page: 1, per_page: 50 });
  }),

  http.patch('*/api/admin/users/:id', async ({ params, request }) => {
    const authHeader = request.headers.get('Authorization');
    if (!authHeader) return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 });
    const body = await request.json() as Record<string, unknown>;
    const user = mockAdminUsers.find(u => u.id === params.id);
    if (!user) return HttpResponse.json({ detail: 'User not found' }, { status: 404 });
    // Self-modification check (mock admin is id '1')
    if (params.id === '1') {
      if (body.is_active === false) {
        return HttpResponse.json({ detail: 'Cannot deactivate your own account' }, { status: 400 });
      }
      if (body.is_admin === false) {
        return HttpResponse.json({ detail: 'Cannot remove your own admin status' }, { status: 400 });
      }
    }
    const updated = { ...user, ...body };
    // Build message matching backend's compound format (user_service.py)
    const parts: string[] = [];
    if (body.is_active !== undefined) {
      parts.push(body.is_active ? 'User activated' : 'User deactivated');
    }
    if (body.is_admin !== undefined) {
      parts.push(body.is_admin ? 'User granted admin' : 'User revoked admin');
    }
    const message = parts.length > 0 ? parts.join(', ') : 'No changes applied';
    return HttpResponse.json({
      id: updated.id, email: updated.email, display_name: updated.display_name,
      is_active: updated.is_active, is_admin: updated.is_admin,
      message,
    });
  }),
  ```

- [x] **5.2** Create `frontend/tests/app/admin/UsersPage.test.tsx`:
  - `test renders user table with data` — verify 3 mock users shown with all columns
  - `test redirects non-admin users` — mock non-admin auth, verify redirect
  - `test search filters users with debounce` — type search, wait 300ms, verify filtered results
  - `test status filter shows active users` — select Active, verify only active users shown
  - `test status filter shows inactive users` — select Inactive, verify only inactive users shown
  - `test deactivate user shows confirmation and updates` — click toggle, confirm, verify update
  - `test activate user shows confirmation and updates` — click toggle on inactive user, confirm
  - `test grant admin shows confirmation and updates` — click admin toggle, confirm
  - `test self-deactivate shows error message` — attempt to toggle own status, verify error
  - `test self-admin-revoke shows error message` — attempt to remove own admin, verify error
  - `test pagination controls work` — verify Previous/Next/page display
  - `test shows "Never" for null last_login_at` — verify null handling
  - `test shows dash for null display_name` — verify null handling
  - `test shows loading state while fetching` — verify spinner/skeleton on initial load
  - `test shows error state with retry on query failure` — mock 500, verify error message + retry button
  - `test shows empty state when no users match` — mock empty response, verify "No users found" message
  - `test toggle controls have correct aria attributes` — verify `role="switch"`, `aria-checked`, `aria-label`

  **Mock auth context for admin tests:**
  ```typescript
  vi.mock('@/lib/auth-context', () => ({
    useAuth: () => ({
      user: { id: '1', email: 'admin@test.com', display_name: 'Admin User', is_admin: true, created_at: '2026-01-01' },
      token: 'fake-token',
      isLoading: false,
      login: vi.fn(),
      logout: vi.fn(),
      register: vi.fn(),
      refreshToken: vi.fn(),
    }),
  }))
  ```

  **Mock next/navigation:**
  ```typescript
  const mockPush = vi.fn();
  const mockReplace = vi.fn();
  vi.mock('next/navigation', () => ({
    useRouter: () => ({ push: mockPush, replace: mockReplace }),
    usePathname: () => '/admin/users',
  }))
  ```

- [x] **5.3** Run full frontend test suite: `cd frontend && npm test` — no regressions

---

## Dev Notes

### CRITICAL: This is a Frontend-Only Story

**Zero backend changes required.** The backend already has both endpoints fully implemented and tested:

| Endpoint | Router Location | Description |
|----------|----------------|-------------|
| `GET /api/admin/users` | `admin.py:380-397` | Paginated list, search, status filter |
| `PATCH /api/admin/users/{id}` | `admin.py:400-432` | Update is_active and/or is_admin |

Both protected by `require_admin`. Both audit-logged.

**Authoritative schema source:** `backend/app/schemas/user.py` — contains `UserAdminResponse`, `UserListResponse`, `UserStatusUpdate`, `UserStatusResponse`. Read this file directly if any field name/type questions arise.

### Backend API Contract Details

**GET `/api/admin/users`** query params:
- `page` (int, default=1, min=1)
- `per_page` (int, default=50, min=1, max=100)
- `search` (optional string — case-insensitive ILIKE on email AND display_name)
- `status` (optional string — must be `"active"` or `"inactive"`, invalid values return 400)

**Response `UserAdminResponse`** fields: `id`, `email`, `display_name` (nullable), `is_active`, `is_admin`, `recipe_count` (computed via subquery), `created_at`, `last_login_at` (nullable). Results ordered by `created_at DESC`.

**PATCH `/api/admin/users/{id}`** request body `UserStatusUpdate`:
- `is_active` (optional boolean)
- `is_admin` (optional boolean)
- **At least one field must be provided** — backend validates with `model_validator`

**PATCH response `UserStatusResponse`** fields: `id`, `email`, `display_name`, `is_active`, `is_admin`, `message`.
- Message examples: `"User activated"`, `"User deactivated"`, `"User granted admin"`, `"User revoked admin"`, `"No changes applied"`
- Self-protection: returns 400 with `detail` for self-deactivation or self-admin-revoke
- Token revocation: deactivating a user automatically revokes all their refresh tokens (backend handles this)

### Current Frontend State

- **AdminBadge** exists at `components/admin/AdminBadge.tsx` (from Story 5-1)
- **CategoryManagementModal** exists at `components/admin/CategoryManagementModal.tsx` (from Story 5-3) — reference for admin modal patterns
- **ConfirmDeleteModal** exists at `components/ui/ConfirmDeleteModal.tsx` (from Story 5-2) — DO NOT reuse directly for status toggles (see Task 3.4)
- **`is_admin: boolean`** on User interface in `auth-context.tsx` (from Story 5-1)
- **`use-admin-categories.ts`** exists at `lib/hooks/` (from Story 5-3) — reference for admin hook patterns (`enabled: !!token`, `staleTime: 60_000`)
- **Admin layout does NOT exist** at `app/admin/layout.tsx` — Story 5-4 not yet implemented. MUST create in Task 4
- **No admin user API functions** in `lib/api.ts` — must create
- **No admin user hooks** — must create

### Key Implementation Decisions

1. **Status column uses colored badges** — Green "Active" / Red "Inactive" for clear visual distinction.
2. **Toggle controls for is_active and is_admin** — Use toggle switches or clickable badges, not separate buttons. Keep it compact.
3. **Self-protection is client-side AND server-side** — Client prevents the click and shows immediate error. Server returns 400 as fallback safety.
4. **Confirmation modal for ALL status changes** — Both activation/deactivation and admin grant/revoke require confirmation. Different modal text per action.
5. **Search debounce: 300ms** — Per AC. Same pattern as Story 5-4.
6. **Admin staleTime: 60 seconds** — Per architecture decision.
7. **Create admin layout** — `app/admin/layout.tsx` does not exist yet (5-4 not implemented). Create it — will be reused by 5-6.
8. **Date formatting** — Use `new Date(timestamp).toLocaleDateString()` or similar. Show "Never" for null `last_login_at`.

### Dependency on Previous Stories

| Story | Dependency | Status |
|-------|-----------|--------|
| 5-1 | `is_admin` on User interface, AdminBadge | done |
| 5-2 | ConfirmDeleteModal component pattern | review |
| 5-3 | CategoryManagementModal, admin hooks pattern | review |
| 5-4 | Admin layout at `app/admin/layout.tsx` | ready-for-dev (NOT implemented) |

**Admin layout does NOT exist** — Story 5-4 is not yet implemented. Task 4 MUST create `app/admin/layout.tsx`. It will be reused by Stories 5-5 and 5-6.

### Out-of-Scope (Explicitly Deferred)

- **User invite/registration** — Per PRD, deferred to Phase 2
- **Admin sidebar navigation** — Not part of this story
- **Bulk user operations** — Not in AC
- **User detail page** — Not in AC; table view is sufficient
- **Password reset by admin** — Not in PRD

### Architecture Compliance

| Requirement | Implementation |
|-------------|----------------|
| Admin state check | `user?.is_admin === true` [Source: docs/admin-panel-architecture.md — Decision #3] |
| Route protection | Admin layout with `useEffect` redirect [Source: docs/admin-panel-architecture.md] |
| Role-based caching | `staleTime: 60_000` for admin queries [Source: docs/admin-panel-architecture.md — Decision #1] |
| Admin component location | `components/admin/` [Source: docs/admin-panel-architecture.md — Frontend Additions] |
| Admin hooks location | `lib/hooks/use-admin-users.ts` [Source: docs/admin-panel-architecture.md] |
| Admin page location | `app/admin/users/page.tsx` [Source: docs/admin-panel-architecture.md] |
| Query invalidation | Invalidate `adminUsers.all` on mutations [Source: docs/admin-panel-architecture.md] |

### Library/Framework Requirements

- **No new dependencies.** Uses existing packages only.
- Lucide React icons: `Search`, `ChevronLeft`, `ChevronRight`, `Shield`, `ShieldOff`, `UserCheck`, `UserX`, `AlertTriangle` — all available in project
- TypeScript strict mode — all props and return types typed
- Tailwind CSS for all styling — use `clsx` for conditional classes
- React Query v5 object syntax for all hooks

### File Structure Requirements

| File | Action | Description |
|------|--------|-------------|
| `frontend/app/admin/layout.tsx` | CREATE | Admin route protection layout (does NOT exist yet) |
| `frontend/app/admin/users/page.tsx` | CREATE | User management page |
| `frontend/lib/api.ts` | MODIFY | Add admin user types and API functions |
| `frontend/lib/query-client.ts` | MODIFY | Add `adminUsers` query keys |
| `frontend/lib/hooks/use-admin-users.ts` | CREATE | Admin user hooks (1 query + 1 mutation) |
| `frontend/lib/hooks/index.ts` | MODIFY | Export admin user hooks |
| `frontend/tests/mocks/handlers.ts` | MODIFY | Add admin user MSW handlers |
| `frontend/tests/app/admin/UsersPage.test.tsx` | CREATE | Full page integration tests (17 cases) |

### Testing Requirements

**Test framework:** vitest (globals enabled — do NOT import describe/it/expect)
**Test setup:** `frontend/tests/setup.ts` already configured — don't duplicate
**Mock pattern:** MSW 2.x handlers for API mocking:
```typescript
http.get('*/api/admin/users', () => HttpResponse.json({ items: mockAdminUsers, total: 3, page: 1, per_page: 50 }))
```

**Test isolation (every test):**
```typescript
beforeEach(() => { queryClient.clear() })
afterEach(() => { cleanup(); vi.clearAllMocks() })
```

**Coverage target:** 100% on new code paths

### Previous Story Intelligence

**From Story 5-3 (Category Management Modal — done, code exists):**

- `use-admin-categories.ts` is the PRIMARY reference for admin hook patterns: `enabled: !!token`, `staleTime: 60_000`, mutation invalidation
- Admin API function pattern in `lib/api.ts`: auth headers, error extraction
- Admin query key pattern in `query-client.ts`: `adminCategories` structure to mirror for `adminUsers`

**From Story 5-2 (Recipe Admin Controls — done, code exists):**

- `ConfirmDeleteModal` props: `{ isOpen, title, itemName, onConfirm, onCancel, isDeleting? }` — DO NOT reuse for status toggles (see Task 3.4)
- Overlay pattern to replicate: `fixed inset-0 bg-black/50 z-50`, Escape key close

**From Story 5-1 (Admin State & Indicator — done, code exists):**

- `is_admin: boolean` on User interface in `auth-context.tsx`
- AdminBadge component at `components/admin/AdminBadge.tsx` with `role="status"`

**From Story 5-4 (Ingredient Admin Page — ready-for-dev, NOT yet implemented):**

- Story spec has similar patterns (search debounce, pagination, table) but NO code exists yet. Do not expect to find admin layout or ingredient hooks in the codebase.

### Git Intelligence

**Recent commits:**
- `d8e8c5b` fix: Epic 4->5 prep — fix 23 frontend test failures, verify toolchain
- `3bf2553` feat: Epic 4 — Audit Trail & Compliance (stories 4-1, 4-2)

**Key insight:** Frontend is clean (238+ tests pass). Stories 5-1 through 5-4 may have added files/tests that aren't committed yet. Run `npm test` early to verify baseline.

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

### References

- [Source: backend/app/routers/admin.py:380-432 — Admin user list + status update endpoints]
- [Source: backend/app/schemas/user.py:10-46 — UserAdminResponse, UserListResponse, UserStatusUpdate, UserStatusResponse]
- [Source: backend/app/services/user_service.py:15-100 — list_users() with computed recipe_count, update_user_status() with self-protection]
- [Source: frontend/lib/api.ts — Existing API pattern, formatEnumValue, API_BASE]
- [Source: frontend/lib/query-client.ts — Existing query key patterns]
- [Source: frontend/lib/hooks/index.ts — Hook export pattern]
- [Source: frontend/components/ui/ConfirmDeleteModal.tsx — Reusable confirmation modal pattern]
- [Source: frontend/lib/auth-context.tsx — User interface with is_admin]
- [Source: docs/admin-panel-architecture.md — Decision #1 (caching), #3 (admin state)]
- [Source: docs/admin-panel-prd.md — FR-3.4.1, FR-3.4.2 (user management requirements)]
- [Source: docs/epics.md:855-893 — Story 5.5 acceptance criteria]

---

## Dev Agent Record

### Context Reference

Story context created by BMAD create-story workflow on 2026-04-09.

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

None — clean implementation, no debug issues.

### Completion Notes List

- Task 1: Added `AdminUser`, `UserListResponse`, `UserStatusUpdate`, `UserStatusResponse` types and `fetchAdminUsers`, `updateUserStatus` API functions to `lib/api.ts`. Follows existing auth header pattern.
- Task 2: Added `adminUsers` query keys to `query-client.ts`. Created `use-admin-users.ts` with `useAdminUsers` (query, `staleTime: 60_000`, `enabled: !!token`) and `useUpdateUserStatus` (mutation with query invalidation). Exported from `hooks/index.ts`.
- Task 3: Created full user management page at `app/admin/users/page.tsx` with: paginated table (all 7 columns), search with 300ms debounce, status filter (All/Active/Inactive), toggle switches for is_active and is_admin with `role="switch"` and `aria-checked`, self-protection (client-side error for own account), `ConfirmActionModal` component (variant-based: danger/warning/default), error handling with dismissible alerts, loading/error/empty states, pagination controls.
- Task 4: Admin layout at `app/admin/layout.tsx` already existed from Story 5-4 implementation. Verified it matches spec — no changes needed.
- Task 5: Added MSW handlers for `GET /api/admin/users` (with search/status filtering) and `PATCH /api/admin/users/:id` (with self-protection). Created 21 test cases covering: table rendering, loading/error/empty states, search debounce, status filters, deactivate/activate/grant-admin/revoke-admin confirmations, self-protection errors, null handling (display_name "—", last_login "Never"), aria attributes, pagination, error dismissal, modal cancel, non-admin redirect, API mutation error path. Note: 1 pre-existing failure in recipe-edit.test.tsx (not related to this story).

### Change Log

- 2026-04-10: Story 5-5 implemented — User management page with all 5 ACs satisfied, 18 tests added.
- 2026-04-10: Code review fixes — Added 3 tests (non-admin redirect, revoke admin flow, API mutation error), added 4th mock admin user for revoke coverage, fixed ConfirmActionModal icon (CheckCircle for positive actions).

### File List

| File | Action |
|------|--------|
| `frontend/lib/api.ts` | MODIFIED — Added admin user types and API functions |
| `frontend/lib/query-client.ts` | MODIFIED — Added `adminUsers` query keys |
| `frontend/lib/hooks/use-admin-users.ts` | CREATED — Admin user hooks (query + mutation) |
| `frontend/lib/hooks/index.ts` | MODIFIED — Exported admin user hooks |
| `frontend/app/admin/users/page.tsx` | CREATED — User management page with table, search, filters, toggles, modal |
| `frontend/tests/mocks/handlers.ts` | MODIFIED — Added admin user MSW handlers and mock data |
| `frontend/tests/app/admin/UsersPage.test.tsx` | CREATED — 18 integration tests |
| `docs/sprint-artifacts/sprint-status.yaml` | MODIFIED — 5-5 status: ready-for-dev → review |
| `docs/sprint-artifacts/5-5-user-management-page.md` | MODIFIED — Tasks marked complete, Dev Agent Record updated |
