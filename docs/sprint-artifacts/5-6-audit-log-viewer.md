# Story 5.6: Audit Log Viewer

Status: done

## Story

As an **admin**,
I want **to view a log of all administrative actions with filtering and details**,
So that **I can track changes and troubleshoot issues**.

## Acceptance Criteria

### AC-1: Paginated Audit Log Table

**Given** I am logged in as an admin
**When** I navigate to `/admin/audit-log`
**Then** I see a paginated table of audit entries
**And** columns include: Timestamp, Admin, Action, Entity Type, Entity ID, Details
**And** entries are ordered by timestamp descending (newest first)

**Given** I am not logged in or not an admin
**When** I navigate to `/admin/audit-log`
**Then** I am redirected to the home page

### AC-2: Filter by Action Type

**Given** I am on the audit log page
**When** I select an action type filter
**Then** the table shows only entries for that action type

### AC-3: Filter by Entity Type

**Given** I am on the audit log page
**When** I select an entity type filter
**Then** the table shows only entries for that entity type

### AC-4: Filter by Date Range

**Given** I am on the audit log page
**When** I select a date range (from/to)
**Then** the table shows only entries within that range

### AC-5: Expandable Details Row

**Given** I click on an audit entry row
**When** the details panel expands
**Then** I see the full JSON details including old/new values for changes

### AC-6: Pagination

**Given** the audit log has many entries
**When** I view the table
**Then** pagination allows navigating through historical entries (Previous/Next, page indicator)

---

## Tasks / Subtasks

### Task 1: Add Audit Log API Types and Function (AC: #1, #2, #3, #4, #6)

- [x] **1.1** In `frontend/lib/api.ts`, add audit log types:
  ```typescript
  export interface AuditLogEntry {
    id: string;
    admin_user_id: string;
    admin_email: string | null;
    action: string;
    entity_type: string;
    entity_id: string | null;
    details: Record<string, unknown> | null;
    created_at: string;
  }

  export interface AuditLogListResponse {
    items: AuditLogEntry[];
    total: number;
    page: number;
    per_page: number;
  }
  ```

- [x] **1.2** Add API function following existing auth header pattern:
  ```typescript
  export async function fetchAuditLogs(
    params: {
      action?: string;
      entity_type?: string;
      from?: string;   // ISO date string
      to?: string;     // ISO date string
      page?: number;
      per_page?: number;
    },
    token: string | null
  ): Promise<AuditLogListResponse> {
    const headers: Record<string, string> = {};
    if (token) { headers['Authorization'] = `Bearer ${token}`; }
    const query = new URLSearchParams();
    if (params.action) query.set('action', params.action);
    if (params.entity_type) query.set('entity_type', params.entity_type);
    if (params.from) query.set('from', params.from);
    if (params.to) query.set('to', params.to);
    if (params.page) query.set('page', String(params.page));
    if (params.per_page) query.set('per_page', String(params.per_page));
    const res = await fetch(`${API_BASE}/admin/audit-log?${query}`, { headers });
    if (!res.ok) throw new Error('Failed to fetch audit logs');
    return res.json();
  }
  ```

### Task 2: Add Audit Log Query Keys and Hook (AC: #1, #2, #3, #4, #6)

- [x] **2.1** In `frontend/lib/query-client.ts`, add audit log query keys (named `auditLogs` not `adminAuditLogs` — audit logs are inherently admin-only, no public equivalent exists):
  ```typescript
  auditLogs: {
    all: ['audit-logs'] as const,
    lists: () => ['audit-logs', 'list'] as const,
    list: (filters: Record<string, unknown>) => ['audit-logs', 'list', filters] as const,
  },
  ```

- [x] **2.2** Create `frontend/lib/hooks/use-audit-logs.ts`:
  ```typescript
  'use client';

  import { useQuery } from '@tanstack/react-query';
  import { fetchAuditLogs } from '@/lib/api';
  import { queryKeys } from '@/lib/query-client';

  export function useAuditLogs(
    params: {
      action?: string;
      entity_type?: string;
      from?: string;
      to?: string;
      page?: number;
      per_page?: number;
    },
    token: string | null
  ) {
    return useQuery({
      queryKey: queryKeys.auditLogs.list(params),
      queryFn: () => fetchAuditLogs(params, token),
      staleTime: 60_000,  // Admin: 1 minute
    });
  }
  ```

- [x] **2.3** Export from `frontend/lib/hooks/index.ts`:
  ```typescript
  export { useAuditLogs } from './use-audit-logs';
  ```

### Task 3: Create Audit Log Viewer Page (AC: #1, #2, #3, #4, #5, #6)

- [x] **3.1** Create `frontend/app/admin/audit-log/page.tsx`:
  - `'use client'` directive
  - Use `useAuth()` for token
  - State: `page` (number, default 1), `actionFilter` (string, empty = all), `entityTypeFilter` (string, empty = all), `fromDate` (string, empty), `toDate` (string, empty), `expandedRowId` (string | null)
  - Use `useAuditLogs({ action: actionFilter || undefined, entity_type: entityTypeFilter || undefined, from: fromDate || undefined, to: toDate || undefined, page, per_page: 20 }, token)`

  **Layout:**
  - Page title: "Audit Log"
  - Filter bar row with:
    - Action type dropdown: "All Actions", then known action values (see list below)
    - Entity type dropdown: "All Entities", then known entity types
    - From date: `<input type="date" />`
    - To date: `<input type="date" />`
    - "Clear Filters" button (resets all filters and goes to page 1)
  - Table columns:
    | Column | Field | Notes |
    |--------|-------|-------|
    | Timestamp | `created_at` | Format as locale date+time string |
    | Admin | `admin_email` | Show admin_user_id if email is null |
    | Action | `action` | Format with `formatEnumValue()` from api.ts |
    | Entity Type | `entity_type` | Format with `formatEnumValue()` |
    | Entity ID | `entity_id` | Show "—" if null, truncate if long UUID |
    | Details | expand chevron | Clickable row or chevron icon to toggle expansion |
  - Pagination: Previous/Next buttons, "Page X of Y" indicator, total count

- [x] **3.2** Expandable details row:
  ```typescript
  // When a row is clicked, toggle expandedRowId
  function toggleRow(id: string) {
    setExpandedRowId(prev => prev === id ? null : id);
  }

  // Render expanded details as formatted JSON
  {expandedRowId === entry.id && entry.details && (
    <tr>
      <td colSpan={6} className="bg-gray-50 px-6 py-4">
        <pre className="text-sm text-gray-700 whitespace-pre-wrap overflow-x-auto">
          {JSON.stringify(entry.details, null, 2)}
        </pre>
      </td>
    </tr>
  )}
  ```

- [x] **3.3** Known filter values (hardcoded dropdown options — backend accepts any string but these are the known actions):
  ```typescript
  const ACTION_OPTIONS = [
    'category_create', 'category_update', 'category_delete',
    'ingredient_create', 'ingredient_update', 'ingredient_delete', 'ingredient_merge',
    'recipe_admin_update', 'recipe_admin_delete',
    'user_activate', 'user_deactivate', 'user_grant_admin', 'user_revoke_admin',
  ];

  const ENTITY_TYPE_OPTIONS = [
    'category', 'ingredient', 'recipe', 'user',
  ];
  ```

- [x] **3.4** Filter change resets page to 1:
  ```typescript
  // On any filter change, reset to page 1
  function handleFilterChange(setter: Function, value: string) {
    setter(value);
    setPage(1);
  }
  ```

### Task 4: Admin Route Protection (AC: #1)

- [x] **4.1** Create `frontend/app/admin/layout.tsx` (admin directory does not exist yet — Stories 5-4/5-5 are not yet implemented):
  ```typescript
  'use client';

  import { useEffect } from 'react';
  import { useRouter } from 'next/navigation';
  import { useAuth } from '@/lib/auth-context';

  export default function AdminLayout({ children }: { children: React.ReactNode }) {
    const { user, isLoading } = useAuth();
    const router = useRouter();

    useEffect(() => {
      if (!isLoading && (!user || !user.is_admin)) {
        router.replace('/');
      }
    }, [user, isLoading, router]);

    if (isLoading) return <div className="p-8 text-center">Loading...</div>;
    if (!user?.is_admin) return null;

    return <>{children}</>;
  }
  ```

  - **Note:** If a later story (5-4 or 5-5) runs first and creates this file, skip this task. Check with `ls frontend/app/admin/layout.tsx` before creating.

### Task 5: Write Tests (AC: #1, #2, #3, #4, #5, #6)

- [x] **5.1** Add MSW handlers for audit log endpoint in `frontend/tests/mocks/handlers.ts`:
  ```typescript
  export const mockAuditLogs: AuditLogEntry[] = [
    {
      id: 'audit-1', admin_user_id: '1', admin_email: 'admin@test.com',
      action: 'category_create', entity_type: 'category', entity_id: 'cat-1',
      details: { type: 'templates', value: 'tiki', label: 'Tiki' },
      created_at: '2026-04-09T14:00:00Z',
    },
    {
      id: 'audit-2', admin_user_id: '1', admin_email: 'admin@test.com',
      action: 'recipe_admin_delete', entity_type: 'recipe', entity_id: 'rec-1',
      details: { recipe_name: 'Old Fashioned', owner_id: '2' },
      created_at: '2026-04-09T13:00:00Z',
    },
    {
      id: 'audit-3', admin_user_id: '1', admin_email: 'admin@test.com',
      action: 'user_deactivate', entity_type: 'user', entity_id: 'user-3',
      details: { email: 'banned@test.com' },
      created_at: '2026-04-08T10:00:00Z',
    },
    {
      id: 'audit-4', admin_user_id: '1', admin_email: null,
      action: 'ingredient_merge', entity_type: 'ingredient', entity_id: null,
      details: { source_ids: ['ing-1', 'ing-2'], target_id: 'ing-3', recipes_updated: 5 },
      created_at: '2026-04-07T09:00:00Z',
    },
    {
      id: 'audit-5', admin_user_id: '1', admin_email: 'admin@test.com',
      action: 'category_delete', entity_type: 'category', entity_id: 'cat-99',
      details: null,
      created_at: '2026-04-06T08:00:00Z',
    },
  ];

  // Handler:
  http.get('*/api/admin/audit-log', ({ request }) => {
    const authHeader = request.headers.get('Authorization');
    if (!authHeader) return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 });
    const url = new URL(request.url);
    const action = url.searchParams.get('action');
    const entityType = url.searchParams.get('entity_type');
    let items = mockAuditLogs;
    if (action) items = items.filter(e => e.action === action);
    if (entityType) items = items.filter(e => e.entity_type === entityType);
    return HttpResponse.json({ items, total: items.length, page: 1, per_page: 20 });
  }),
  ```

- [x] **5.2** Create `frontend/tests/app/admin/AuditLogPage.test.tsx` (create `tests/app/admin/` directory — it does not exist yet):
  - `test renders audit log table with entries` — verify 5 mock entries shown with all columns
  - `test redirects non-admin users` — mock non-admin auth, verify redirect
  - `test filter by action type` — select action filter, verify filtered results
  - `test filter by entity type` — select entity type filter, verify filtered results
  - `test date range filter` — set from/to dates, verify query params
  - `test clear filters resets all` — set filters, click clear, verify reset
  - `test expand row shows details JSON` — click row, verify details rendered
  - `test collapse row hides details` — click expanded row again, verify hidden
  - `test shows dash for null entity_id` — verify null handling
  - `test shows admin_user_id when email is null` — verify fallback display
  - `test formats action with formatEnumValue` — verify "category_create" → "Category Create"
  - `test does not render details panel for null details` — click row with `details: null`, verify no JSON rendered
  - `test pagination controls work` — verify Previous/Next/page display
  - `test filter change resets page to 1` — change filter on page 2, verify page resets

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

  **Mock next/navigation:**
  ```typescript
  const mockReplace = vi.fn();
  vi.mock('next/navigation', () => ({
    useRouter: () => ({ push: vi.fn(), replace: mockReplace }),
    usePathname: () => '/admin/audit-log',
  }))
  ```

- [x] **5.3** Run full frontend test suite: `cd frontend && npm test` — no regressions

---

## Dev Notes

### CRITICAL: This is a Frontend-Only Story

**Zero backend changes required.** The backend endpoint is fully implemented and tested (22 tests):

| Endpoint | Router Location | Description |
|----------|----------------|-------------|
| `GET /api/admin/audit-log` | `admin.py:438-477` | Paginated list with action/entity_type/date filters |

Protected by `require_admin`. Rate limited 30/min.

### Backend API Contract Details

**GET `/api/admin/audit-log`** query params:
- `action` (optional string) — exact match on action name
- `entity_type` (optional string) — exact match on entity type
- `from` (optional datetime) — ISO format, start of date range (inclusive)
- `to` (optional datetime) — ISO format, end of date range (inclusive)
- `page` (int, default=1, min=1)
- `per_page` (int, default=20, min=1, max=100)

**Response `AuditLogListResponse`** fields:
- `items`: array of `AuditLogResponse`
- `total`: int (total count across all pages)
- `page`: int
- `per_page`: int

**`AuditLogResponse`** fields:
- `id`: string (UUID)
- `admin_user_id`: string (UUID)
- `admin_email`: string | null (joined from users table)
- `action`: string (e.g. `"category_create"`, `"recipe_admin_delete"`)
- `entity_type`: string (e.g. `"category"`, `"recipe"`, `"user"`, `"ingredient"`)
- `entity_id`: string | null (UUID of affected entity)
- `details`: object | null (JSON — varies by action, contains old/new values)
- `created_at`: string (ISO datetime)

Results ordered by `created_at DESC` (newest first).

### Known Audit Actions and Their Details Shape

| Action | Entity Type | Details Fields |
|--------|------------|----------------|
| `category_create` | category | `{ type, value, label }` |
| `category_update` | category | `{ type, changes: { field: [old, new] } }` |
| `category_delete` | category | `{ type, value }` |
| `ingredient_create` | ingredient | `{ name, type }` |
| `ingredient_update` | ingredient | `{ changes: { field: [old, new] } }` |
| `ingredient_delete` | ingredient | `{ name, type }` |
| `ingredient_merge` | ingredient | `{ source_ids, source_names, target_id, target_name, recipes_updated }` |
| `recipe_admin_update` | recipe | `{ recipe_name, owner_id, changes: { field: [old, new] } }` |
| `recipe_admin_delete` | recipe | `{ recipe_name, owner_id }` |
| `user_activate` | user | `{ email }` |
| `user_deactivate` | user | `{ email }` |
| `user_grant_admin` | user | `{ email }` |
| `user_revoke_admin` | user | `{ email }` |

### Current Frontend State

- **AdminBadge** exists at `components/admin/AdminBadge.tsx` (from Story 5-1)
- **ConfirmDeleteModal** exists at `components/ui/ConfirmDeleteModal.tsx` (from Story 5-2)
- **`is_admin: boolean`** on User interface in `auth-context.tsx` (from Story 5-1)
- **Admin layout** does NOT exist yet — `app/admin/` directory is absent. Stories 5-4/5-5 are still `ready-for-dev`. Task 4 handles creation.
- **`formatEnumValue()`** exists in `lib/api.ts` — use for displaying action/entity_type values
- **No audit log API functions** in `lib/api.ts` — must create
- **No audit log hooks** — must create
- **No audit query keys** in `lib/query-client.ts` — must add

### Key Implementation Decisions

1. **Read-only page** — No mutations, no confirmation modals. Simpler than 5-4 and 5-5.
2. **Dropdowns for action and entity type filters** — Hardcoded known values. Backend accepts any string but these are the only values that exist (wired in Story 4-2).
3. **Native date inputs for date range** — `<input type="date" />` for from/to. Convert to ISO string for API call.
4. **Expandable row for details** — Click a row to toggle a details panel below it showing formatted JSON. No separate detail page.
5. **Admin staleTime: 60 seconds** — Per architecture decision.
6. **`formatEnumValue()`** for action/entity_type display — converts `"category_create"` → `"Category Create"`. Already exists in api.ts.
7. **Fallback for null admin_email** — Show `admin_user_id` (truncated UUID) when email is null. Edge case: admin user deleted but FK is RESTRICT so shouldn't happen in practice.
8. **No search box** — Unlike 5-4 and 5-5, audit log uses dropdown filters not free-text search. No debounce needed.
9. **per_page: 20** — Backend default. Audit entries are more detailed than user/ingredient rows.

### Dependency on Previous Stories

| Story | Dependency | Status |
|-------|-----------|--------|
| 4-1 | Backend audit log endpoint (GET /api/admin/audit-log) | done |
| 4-2 | Backend audit log integration (all actions wired) | done |
| 5-1 | `is_admin` on User interface, AdminBadge | review |
| 5-4 | Admin layout at `app/admin/layout.tsx` | ready-for-dev |

**If admin layout doesn't exist yet:** Create it in Task 4. See Story 5-5 Task 4 for exact code.

### Out-of-Scope (Explicitly Deferred)

- **Audit log export** — Not in AC; no CSV/JSON download
- **Audit log search** — Not in AC; use filters only
- **Audit log deletion/archival** — Not in AC
- **Real-time streaming** — Not in AC; polling via staleTime is sufficient
- **Admin sidebar navigation** — Not part of this story

### Architecture Compliance

| Requirement | Implementation |
|-------------|----------------|
| Admin state check | `user?.is_admin === true` [Source: docs/admin-panel-architecture.md — Decision #3] |
| Route protection | Admin layout with `useEffect` redirect [Source: docs/admin-panel-architecture.md] |
| Role-based caching | `staleTime: 60_000` for admin queries [Source: docs/admin-panel-architecture.md — Decision #1] |
| Admin page location | `app/admin/audit-log/page.tsx` [Source: docs/admin-panel-architecture.md] |
| Admin hooks location | `lib/hooks/use-audit-logs.ts` [Source: docs/admin-panel-architecture.md] |
| Query invalidation | Not needed — read-only page, no mutations |

### Library/Framework Requirements

- **No new dependencies.** Uses existing packages only.
- Lucide React icons (if used): `ChevronDown`, `ChevronRight`, `ChevronLeft`, `Filter`, `X` — all available
- TypeScript strict mode — all props and return types typed
- Tailwind CSS for all styling — use `clsx` for conditional classes
- React Query v5 object syntax for hooks

### File Structure Requirements

| File | Action | Description |
|------|--------|-------------|
| `frontend/app/admin/audit-log/page.tsx` | CREATE | Audit log viewer page |
| `frontend/lib/api.ts` | MODIFY | Add AuditLogEntry, AuditLogListResponse types and fetchAuditLogs function |
| `frontend/lib/query-client.ts` | MODIFY | Add `auditLogs` query keys |
| `frontend/lib/hooks/use-audit-logs.ts` | CREATE | Audit log query hook |
| `frontend/lib/hooks/index.ts` | MODIFY | Export audit log hook |
| `frontend/tests/mocks/handlers.ts` | MODIFY | Add audit log MSW handler |
| `frontend/tests/app/admin/AuditLogPage.test.tsx` | CREATE | Page integration tests (13 cases) |

### Testing Requirements

**Test framework:** vitest (globals enabled — do NOT import describe/it/expect)
**Test setup:** `frontend/tests/setup.ts` already configured — don't duplicate
**Mock pattern:** MSW 2.x handlers for API mocking:
```typescript
http.get('*/api/admin/audit-log', () => HttpResponse.json({ items: mockAuditLogs, total: 5, page: 1, per_page: 20 }))
```

**Test isolation (every test):**
```typescript
beforeEach(() => { queryClient.clear() })
afterEach(() => { cleanup(); vi.clearAllMocks() })
```

**Coverage target:** 100% on new code paths

### Previous Story Intelligence

**From Story 5-5 (User Management Page — ready-for-dev):**
- Admin page pattern: useAuth() + table + pagination + filters
- API function pattern: auth header via `Record<string, string>`, error extraction
- Query key pattern: `['admin-*', 'list', filters]`
- Test pattern: MSW handlers with auth check, mock auth context with `is_admin: true`
- Pagination: Previous/Next buttons, "Page X of Y"
- Filter change resets page to 1

**From Story 5-4 (Ingredient Admin Page — ready-for-dev):**
- Admin layout guard exists at `app/admin/layout.tsx`
- Search debounce pattern (300ms) — NOT needed here, using dropdowns instead
- Table layout with action column

**From Story 4-1 (Audit Log Infrastructure — done):**
- `from` param uses Query alias (`Query(None, alias="from")`) — frontend just passes `from` as query param name
- Response includes `admin_email` via User join
- `details` field is JSON object or null
- Rate limit: 30/minute (read-heavy)

### Git Intelligence

**Recent commits:**
- `d8e8c5b` fix: Epic 4→5 prep — fix 23 frontend test failures, verify toolchain
- `3bf2553` feat: Epic 4 — Audit Trail & Compliance (stories 4-1, 4-2)

**Key insight:** Frontend is clean (238+ tests pass). Stories 5-1 through 5-5 may have added uncommitted files/tests. Run `npm test` early to verify baseline.

### Anti-Patterns to Avoid

**DO NOT:**
- Create a backend endpoint or model — already done in Stories 4-1/4-2
- Import `describe`/`it`/`expect` in vitest tests — globals enabled
- Mock fetch directly — use MSW handlers
- Use `next/router` — use `next/navigation` (App Router)
- Use `useQuery('key', fn)` — use v5 object syntax `useQuery({ queryKey, queryFn })`
- Add debounce — this page uses dropdown filters, not free-text search
- Create a separate detail page — use expandable rows in the table
- Add mutation hooks — this is a read-only page

**DO:**
- Reuse `formatEnumValue()` from `lib/api.ts` for action/entity_type display
- Reuse admin layout from Story 5-4 (don't recreate)
- Use native `<input type="date" />` for date range (no date picker library)
- Use `clsx` for conditional classes (e.g., expanded row styling)
- Reset page to 1 on any filter change
- Handle null `admin_email` with fallback display
- Handle null `entity_id` and `details` gracefully

### Project Context Reference

See `docs/project_context.md` for:
- TypeScript strict mode rules (no implicit `any`)
- React Query v5 object syntax — `useQuery({ queryKey, queryFn })`
- MSW 2.x test handler pattern — `http.get('*/api/...', () => HttpResponse.json(...))`
- Component file naming: PascalCase.tsx
- `clsx` for conditional Tailwind classes
- Admin authorization pattern: `user?.is_admin`
- Admin staleTime: 60_000 (1 min)

### References

- [Source: backend/app/routers/admin.py:438-477 — GET /admin/audit-log endpoint]
- [Source: backend/app/schemas/audit.py — AuditLogResponse, AuditLogListResponse]
- [Source: docs/admin-panel-architecture.md — Decision #1 (caching), #3 (admin state)]
- [Source: docs/admin-panel-prd.md — FR-3.6.1, FR-3.6.2 (audit log requirements)]

---

## Dev Agent Record

### Context Reference

Story context created by BMAD create-story workflow on 2026-04-09.

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

- Default MSW handler in handlers.ts array didn't fire for audit-log endpoint during tests; resolved by using `server.use()` in test `beforeEach`. Root cause unclear — other admin handlers in the same array work. Functional workaround applied.

### Completion Notes List

- **Task 1** (AC #1,#2,#3,#4,#6): Added `AuditLogEntry`, `AuditLogListResponse` types and `fetchAuditLogs()` to api.ts following existing auth header pattern.
- **Task 2** (AC #1,#2,#3,#4,#6): Added `auditLogs` query keys to query-client.ts, created `useAuditLogs` hook with 60s staleTime, exported from hooks/index.ts.
- **Task 3** (AC #1,#2,#3,#4,#5,#6): Created audit log viewer page at `app/admin/audit-log/page.tsx` with paginated table, action/entity type dropdown filters, date range inputs, expandable JSON details rows, clear filters button, and Previous/Next pagination.
- **Task 4** (AC #1): SKIPPED — Admin layout already exists at `app/admin/layout.tsx` from Stories 5-4/5-5 with `useAuth()`/`useEffect` redirect pattern.
- **Task 5** (AC #1-#6): Added MSW handler for audit-log endpoint with auth check + action/entity_type filtering. Created 15 integration tests covering: table rendering, null handling (entity_id, admin_email, details), formatEnumValue display, action/entity type filtering, date range inputs, clear filters, expand/collapse details, pagination controls/disabled state, filter resets page, error state.
- **Full regression**: 31 test files, 357 tests, 0 failures.

### Change Log

- 2026-04-10: Story 5-6 implementation complete — Audit Log Viewer page with all 6 ACs satisfied, 15 new tests added.
- 2026-04-10: **Code Review (AI)** — 8 issues found (2 HIGH, 4 MEDIUM, 2 LOW), all HIGH/MEDIUM fixed:
  - H1: Date range filter test now verifies API params and filtered results; MSW handler supports from/to filtering
  - H2: Fixed `<pre>` JSX indentation bug causing extra whitespace in JSON details display
  - M1: Added `enabled: !!token` to `useAuditLogs` hook to prevent 401 calls before auth redirect
  - M2: Replaced raw `setTimeout` with `waitFor` in null-details test
  - M3: Reordered afterEach to cancel queries before cleanup (reduces act() warnings)
  - M4: Added test for entity ID truncation with long UUID
  - Post-fix regression: 31 test files, 358 tests, 0 failures

### File List

**New files:**
- `frontend/app/admin/audit-log/page.tsx` — Audit log viewer page component
- `frontend/lib/hooks/use-audit-logs.ts` — useAuditLogs query hook
- `frontend/tests/app/admin/AuditLogPage.test.tsx` — 16 integration tests

**Modified files:**
- `frontend/lib/api.ts` — Added AuditLogEntry, AuditLogListResponse types and fetchAuditLogs function
- `frontend/lib/query-client.ts` — Added auditLogs query keys
- `frontend/lib/hooks/index.ts` — Exported useAuditLogs
- `frontend/tests/mocks/handlers.ts` — Added mockAuditLogs data and audit-log MSW handler (with date filtering)
- `docs/sprint-artifacts/sprint-status.yaml` — Updated 5-6 status: ready-for-dev → review → done
- `docs/sprint-artifacts/5-6-audit-log-viewer.md` — This file: tasks marked complete, review record added
