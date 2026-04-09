import { render, screen, cleanup, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi, afterEach, beforeEach } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import AuditLogPage from '@/app/admin/audit-log/page'
import { http, HttpResponse } from 'msw'
import { server } from '../../mocks/server'
import { mockAuditLogs } from '../../mocks/handlers'

// Mock auth as admin
vi.mock('@/lib/auth-context', () => ({
  useAuth: vi.fn(),
}))

import { useAuth } from '@/lib/auth-context'

const mockUseAuth = vi.mocked(useAuth)

const adminAuth = {
  user: { id: '1', email: 'admin@test.com', display_name: 'Admin', is_admin: true, created_at: '2026-01-01' },
  token: 'fake-token',
  isLoading: false,
  login: vi.fn(),
  logout: vi.fn(),
  register: vi.fn(),
  refreshToken: vi.fn(),
}

// Mock next/navigation
const mockReplace = vi.fn()
vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn(), replace: mockReplace }),
  usePathname: () => '/admin/audit-log',
}))

let queryClient: QueryClient

function auditLogHandler() {
  return http.get('*/api/admin/audit-log', ({ request }) => {
    const authHeader = request.headers.get('Authorization')
    if (!authHeader) return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 })
    const url = new URL(request.url)
    const action = url.searchParams.get('action')
    const entityType = url.searchParams.get('entity_type')
    const from = url.searchParams.get('from')
    const to = url.searchParams.get('to')
    let items = [...mockAuditLogs]
    if (action) items = items.filter(e => e.action === action)
    if (entityType) items = items.filter(e => e.entity_type === entityType)
    if (from) items = items.filter(e => e.created_at >= new Date(from).toISOString())
    if (to) {
      const toEnd = new Date(to)
      toEnd.setDate(toEnd.getDate() + 1)
      items = items.filter(e => e.created_at < toEnd.toISOString())
    }
    return HttpResponse.json({ items, total: items.length, page: 1, per_page: 20 })
  })
}

beforeEach(() => {
  queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
  mockUseAuth.mockReturnValue(adminAuth)
  server.use(auditLogHandler())
})

afterEach(() => {
  queryClient.cancelQueries()
  queryClient.clear()
  cleanup()
  vi.clearAllMocks()
})

function renderPage() {
  return render(
    <QueryClientProvider client={queryClient}>
      <AuditLogPage />
    </QueryClientProvider>
  )
}

/** Wait for table data to fully load (text only in table, not dropdown) */
async function waitForData() {
  await waitFor(() => {
    expect(screen.getByText(/total entries/)).toBeInTheDocument()
  })
}

describe('AuditLogPage', () => {
  it('renders audit log table with entries', async () => {
    renderPage()
    await waitForData()

    // All 5 entries visible — check unique action column values in table cells
    const rows = screen.getAllByRole('row')
    // header + 5 data rows
    expect(rows.length).toBeGreaterThanOrEqual(6)
    // admin@test.com appears in 4 rows (audit-4 has null email)
    expect(screen.getAllByText('admin@test.com').length).toBe(4)
    // Column headers present
    expect(screen.getByText('Timestamp')).toBeInTheDocument()
    expect(screen.getByText('Admin')).toBeInTheDocument()
  })

  it('shows dash for null entity_id', async () => {
    renderPage()
    await waitForData()

    // audit-4 has null entity_id — should show em dash in entity column
    const dashes = screen.getAllByText('—')
    expect(dashes.length).toBeGreaterThanOrEqual(1)
  })

  it('truncates long entity IDs to 8 chars', async () => {
    const longId = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'
    server.use(
      http.get('*/api/admin/audit-log', () => {
        return HttpResponse.json({
          items: [{
            id: 'audit-long', admin_user_id: '1', admin_email: 'admin@test.com',
            action: 'category_create', entity_type: 'category', entity_id: longId,
            details: null, created_at: '2026-04-09T14:00:00Z',
          }],
          total: 1, page: 1, per_page: 20,
        })
      })
    )

    renderPage()
    await waitFor(() => {
      expect(screen.getByText(/1 total/)).toBeInTheDocument()
    })

    // Should show first 8 chars + "..."
    expect(screen.getByText('a1b2c3d4...')).toBeInTheDocument()
  })

  it('shows admin_user_id when email is null', async () => {
    renderPage()
    await waitForData()

    // audit-4 has null admin_email, admin_user_id is '1'
    const rows = screen.getAllByRole('row')
    const mergeRow = rows.find(row => row.textContent?.includes('Ingredient Merge'))
    expect(mergeRow).toBeDefined()
    const cells = mergeRow!.querySelectorAll('td')
    // Second cell (index 1) is Admin column — should show '1' not 'admin@test.com'
    expect(cells[1].textContent).toBe('1')
  })

  it('formats action with formatEnumValue', async () => {
    renderPage()
    await waitForData()

    // These appear in both dropdowns AND table — just verify presence
    expect(screen.getAllByText('Category Create').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('Recipe Admin Delete').length).toBeGreaterThanOrEqual(1)
  })

  it('filters by action type', async () => {
    const user = userEvent.setup()
    renderPage()
    await waitForData()

    const actionSelect = screen.getByLabelText('Action')
    await user.selectOptions(actionSelect, 'category_create')

    // After filtering, only category_create entries visible
    await waitFor(() => {
      // Recipe Admin Delete should no longer appear in the table
      // It still exists in dropdown, so check table row count
      const dataRows = screen.getAllByRole('row').filter(row => row.textContent?.includes('admin@test.com'))
      expect(dataRows.length).toBe(1)
    })
  })

  it('filters by entity type', async () => {
    const user = userEvent.setup()
    renderPage()
    await waitForData()

    const entitySelect = screen.getByLabelText('Entity Type')
    await user.selectOptions(entitySelect, 'recipe')

    await waitFor(() => {
      // Only 1 recipe entry (audit-2)
      const dataRows = screen.getAllByRole('row').filter(row => row.textContent?.includes('admin@test.com'))
      expect(dataRows.length).toBe(1)
    })
  })

  it('date range filter inputs work and filter results', async () => {
    const user = userEvent.setup()
    renderPage()
    await waitForData()

    const fromInput = screen.getByLabelText('From')
    const toInput = screen.getByLabelText('To')

    // Set from date to 2026-04-09 — should exclude audit-3 (Apr 8), audit-4 (Apr 7), audit-5 (Apr 6)
    await user.type(fromInput, '2026-04-09')

    expect(fromInput).toHaveValue('2026-04-09')

    // After filtering by from=2026-04-09, only audit-1 and audit-2 remain (both Apr 9)
    await waitFor(() => {
      expect(screen.getByText(/2 total entries/)).toBeInTheDocument()
    })

    // Now set to date to narrow further
    await user.type(toInput, '2026-04-09')
    expect(toInput).toHaveValue('2026-04-09')

    // Both entries are on Apr 9, so still 2
    await waitFor(() => {
      expect(screen.getByText(/2 total entries/)).toBeInTheDocument()
    })
  })

  it('clears all filters and resets page', async () => {
    const user = userEvent.setup()
    renderPage()
    await waitForData()

    // Set action filter
    const actionSelect = screen.getByLabelText('Action')
    await user.selectOptions(actionSelect, 'category_create')

    await waitFor(() => {
      expect(screen.getByText(/1 total/)).toBeInTheDocument()
    })

    // Click clear
    const clearButton = screen.getByText('Clear Filters')
    await user.click(clearButton)

    // All entries should reappear
    await waitFor(() => {
      expect(screen.getByText(/5 total entries/)).toBeInTheDocument()
    })
    expect((actionSelect as HTMLSelectElement).value).toBe('')
  })

  it('expands row to show details JSON', async () => {
    const user = userEvent.setup()
    renderPage()
    await waitForData()

    // Click the row containing Category Create (in the table, not dropdown)
    const rows = screen.getAllByRole('row')
    const categoryRow = rows.find(row => {
      const cells = row.querySelectorAll('td')
      return cells.length >= 3 && cells[2]?.textContent === 'Category Create'
    })
    expect(categoryRow).toBeDefined()
    await user.click(categoryRow!)

    // Details JSON should now be visible
    await waitFor(() => {
      expect(screen.getByText(/"tiki"/)).toBeInTheDocument()
    })
  })

  it('collapses expanded row on second click', async () => {
    const user = userEvent.setup()
    renderPage()
    await waitForData()

    // Click to expand
    const rows = screen.getAllByRole('row')
    const categoryRow = rows.find(row => {
      const cells = row.querySelectorAll('td')
      return cells.length >= 3 && cells[2]?.textContent === 'Category Create'
    })
    await user.click(categoryRow!)

    await waitFor(() => {
      expect(screen.getByText(/"tiki"/)).toBeInTheDocument()
    })

    // Click again to collapse — find the main row again (not the details row)
    const updatedRows = screen.getAllByRole('row')
    const mainRow = updatedRows.find(row => {
      const cells = row.querySelectorAll('td')
      return cells.length >= 3 && cells[2]?.textContent === 'Category Create'
    })
    await user.click(mainRow!)

    await waitFor(() => {
      expect(screen.queryByText(/"tiki"/)).not.toBeInTheDocument()
    })
  })

  it('does not render details panel for null details', async () => {
    const user = userEvent.setup()
    renderPage()
    await waitForData()

    // audit-5 has null details — click the Category Delete row
    const rows = screen.getAllByRole('row')
    const deleteRow = rows.find(row => {
      const cells = row.querySelectorAll('td')
      return cells.length >= 3 && cells[2]?.textContent === 'Category Delete'
    })
    await user.click(deleteRow!)

    // Row should be "expanded" (highlighted) but no <pre> element since details is null
    await waitFor(() => {
      expect(document.querySelectorAll('pre').length).toBe(0)
    })
  })

  it('shows pagination controls', async () => {
    renderPage()
    await waitForData()

    expect(screen.getByText('Previous')).toBeInTheDocument()
    expect(screen.getByText('Next')).toBeInTheDocument()
    expect(screen.getByText('Page 1 of 1')).toBeInTheDocument()
    expect(screen.getByText(/5 total entries/)).toBeInTheDocument()
  })

  it('pagination buttons disabled correctly', async () => {
    renderPage()
    await waitForData()

    // On page 1 of 1, both should be disabled
    expect(screen.getByText('Previous')).toBeDisabled()
    expect(screen.getByText('Next')).toBeDisabled()
  })

  it('filter change resets page to 1', async () => {
    const user = userEvent.setup()
    renderPage()
    await waitForData()

    // Change action filter
    const actionSelect = screen.getByLabelText('Action')
    await user.selectOptions(actionSelect, 'category_create')

    // Page should display 1
    await waitFor(() => {
      expect(screen.getByText(/Page 1 of/)).toBeInTheDocument()
    })
  })

  it('shows error state when API fails', async () => {
    server.use(
      http.get('*/api/admin/audit-log', () => {
        return new HttpResponse(null, { status: 500 })
      })
    )

    renderPage()

    await waitFor(() => {
      expect(screen.getByText(/Failed to load audit logs/)).toBeInTheDocument()
    })
  })
})
