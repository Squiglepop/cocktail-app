import { render, screen, cleanup, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi, afterEach, beforeEach } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import UsersPage from '@/app/admin/users/page'
import AdminLayout from '@/app/admin/layout'
import { http, HttpResponse } from 'msw'
import { server } from '../../mocks/server'

// Mock next/navigation
const mockReplace = vi.fn()
vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn(), replace: mockReplace }),
  usePathname: () => '/admin/users',
}))

// Mock auth as admin
vi.mock('@/lib/auth-context', () => ({
  useAuth: vi.fn(),
}))

import { useAuth } from '@/lib/auth-context'

const mockUseAuth = vi.mocked(useAuth)

const adminAuth = {
  user: { id: '1', email: 'admin@test.com', display_name: 'Admin User', is_admin: true, created_at: '2026-01-01' },
  token: 'fake-token',
  isLoading: false,
  login: vi.fn(),
  logout: vi.fn(),
  register: vi.fn(),
  refreshToken: vi.fn(),
}

let queryClient: QueryClient

beforeEach(() => {
  queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 }, mutations: { retry: false } },
  })
  mockUseAuth.mockReturnValue(adminAuth)
})

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
  queryClient.clear()
})

function renderPage() {
  return render(
    <QueryClientProvider client={queryClient}>
      <UsersPage />
    </QueryClientProvider>
  )
}

describe('UsersPage', () => {
  it('renders user table with data', async () => {
    renderPage()

    await waitFor(() => {
      expect(screen.getByText('admin@test.com')).toBeInTheDocument()
    })
    expect(screen.getByText('user@test.com')).toBeInTheDocument()
    expect(screen.getByText('inactive@test.com')).toBeInTheDocument()
    expect(screen.getByText('Admin User')).toBeInTheDocument()
    expect(screen.getByText('Regular User')).toBeInTheDocument()
    // Check recipe counts
    expect(screen.getByText('10')).toBeInTheDocument()
    expect(screen.getByText('5')).toBeInTheDocument()
    expect(screen.getByText('0')).toBeInTheDocument()
  })

  it('shows loading state while fetching', () => {
    renderPage()
    // The loading spinner should appear before data loads
    expect(screen.getByText('User Management')).toBeInTheDocument()
    // Table should not be visible yet
    expect(screen.queryByText('admin@test.com')).not.toBeInTheDocument()
  })

  it('shows error state with retry on query failure', async () => {
    server.use(
      http.get('*/api/admin/users', () => {
        return new HttpResponse(null, { status: 500 })
      })
    )

    renderPage()

    await waitFor(() => {
      expect(screen.getByText('Failed to load users')).toBeInTheDocument()
    })
    expect(screen.getByText('Retry')).toBeInTheDocument()
  })

  it('shows empty state when no users match', async () => {
    server.use(
      http.get('*/api/admin/users', () => {
        return HttpResponse.json({ items: [], total: 0, page: 1, per_page: 50 })
      })
    )

    renderPage()

    await waitFor(() => {
      expect(screen.getByText('No users found')).toBeInTheDocument()
    })
    expect(screen.getByText('Try adjusting your search or filter')).toBeInTheDocument()
  })

  it('search filters users with debounce', async () => {
    const user = userEvent.setup()
    renderPage()

    await waitFor(() => {
      expect(screen.getByText('admin@test.com')).toBeInTheDocument()
    })

    await user.type(screen.getByPlaceholderText(/search/i), 'inactive')

    // Wait for debounce + refetch
    await waitFor(() => {
      expect(screen.getByText('inactive@test.com')).toBeInTheDocument()
      expect(screen.queryByText('admin@test.com')).not.toBeInTheDocument()
    })
  })

  it('status filter shows active users', async () => {
    const user = userEvent.setup()
    renderPage()

    await waitFor(() => {
      expect(screen.getByText('admin@test.com')).toBeInTheDocument()
    })

    await user.click(screen.getByRole('button', { name: 'Active' }))

    await waitFor(() => {
      expect(screen.queryByText('inactive@test.com')).not.toBeInTheDocument()
    })
    expect(screen.getByText('admin@test.com')).toBeInTheDocument()
    expect(screen.getByText('user@test.com')).toBeInTheDocument()
  })

  it('status filter shows inactive users', async () => {
    const user = userEvent.setup()
    renderPage()

    await waitFor(() => {
      expect(screen.getByText('admin@test.com')).toBeInTheDocument()
    })

    await user.click(screen.getByRole('button', { name: 'Inactive' }))

    await waitFor(() => {
      expect(screen.getByText('inactive@test.com')).toBeInTheDocument()
      expect(screen.queryByText('admin@test.com')).not.toBeInTheDocument()
    })
  })

  it('deactivate user shows confirmation and updates', async () => {
    const user = userEvent.setup()
    renderPage()

    await waitFor(() => {
      expect(screen.getByText('user@test.com')).toBeInTheDocument()
    })

    // Click the status toggle for user@test.com (user id=2, is_active=true)
    const activeToggles = screen.getAllByRole('switch', { name: /toggle active status/i })
    // Second toggle is for user@test.com
    await user.click(activeToggles[1])

    // Confirmation modal should appear
    await waitFor(() => {
      expect(screen.getByText('Deactivate this user?')).toBeInTheDocument()
    })
    expect(screen.getByText('Deactivate')).toBeInTheDocument()

    // Confirm
    await user.click(screen.getByText('Deactivate'))

    // Modal should close after success
    await waitFor(() => {
      expect(screen.queryByText('Deactivate this user?')).not.toBeInTheDocument()
    })
  })

  it('activate user shows confirmation and updates', async () => {
    const user = userEvent.setup()
    renderPage()

    await waitFor(() => {
      expect(screen.getByText('inactive@test.com')).toBeInTheDocument()
    })

    // Click the status toggle for inactive@test.com (user id=3, is_active=false)
    const activeToggles = screen.getAllByRole('switch', { name: /toggle active status/i })
    // Third toggle is for inactive user
    await user.click(activeToggles[2])

    await waitFor(() => {
      expect(screen.getByText('Activate this user?')).toBeInTheDocument()
    })
    expect(screen.getByText('Activate')).toBeInTheDocument()

    await user.click(screen.getByText('Activate'))

    await waitFor(() => {
      expect(screen.queryByText('Activate this user?')).not.toBeInTheDocument()
    })
  })

  it('grant admin shows confirmation and updates', async () => {
    const user = userEvent.setup()
    renderPage()

    await waitFor(() => {
      expect(screen.getByText('user@test.com')).toBeInTheDocument()
    })

    // Click the admin toggle for user@test.com
    const adminToggles = screen.getAllByRole('switch', { name: /toggle admin status/i })
    // Second toggle is for user@test.com
    await user.click(adminToggles[1])

    await waitFor(() => {
      expect(screen.getByText('Grant admin privileges to user@test.com?')).toBeInTheDocument()
    })
    expect(screen.getByText('Grant Admin')).toBeInTheDocument()

    await user.click(screen.getByText('Grant Admin'))

    await waitFor(() => {
      expect(screen.queryByText(/Grant admin privileges/)).not.toBeInTheDocument()
    })
  })

  it('self-deactivate shows error message', async () => {
    const user = userEvent.setup()
    renderPage()

    await waitFor(() => {
      expect(screen.getByText('admin@test.com')).toBeInTheDocument()
    })

    // Click the status toggle for admin@test.com (our own account, id=1)
    const activeToggles = screen.getAllByRole('switch', { name: /toggle active status/i })
    await user.click(activeToggles[0])

    // Should show error, NOT confirmation modal
    await waitFor(() => {
      expect(screen.getByText('Cannot deactivate your own account')).toBeInTheDocument()
    })
    expect(screen.queryByText('Deactivate this user?')).not.toBeInTheDocument()
  })

  it('self-admin-revoke shows error message', async () => {
    const user = userEvent.setup()
    renderPage()

    await waitFor(() => {
      expect(screen.getByText('admin@test.com')).toBeInTheDocument()
    })

    // Click the admin toggle for admin@test.com (our own account)
    const adminToggles = screen.getAllByRole('switch', { name: /toggle admin status/i })
    await user.click(adminToggles[0])

    await waitFor(() => {
      expect(screen.getByText('Cannot remove your own admin status')).toBeInTheDocument()
    })
    expect(screen.queryByText(/Revoke admin/)).not.toBeInTheDocument()
  })

  it('shows "Never" for null last_login_at', async () => {
    renderPage()

    await waitFor(() => {
      expect(screen.getByText('inactive@test.com')).toBeInTheDocument()
    })

    expect(screen.getByText('Never')).toBeInTheDocument()
  })

  it('shows dash for null display_name', async () => {
    renderPage()

    await waitFor(() => {
      expect(screen.getByText('inactive@test.com')).toBeInTheDocument()
    })

    // The third user has null display_name, should show "—"
    expect(screen.getByText('—')).toBeInTheDocument()
  })

  it('toggle controls have correct aria attributes', async () => {
    renderPage()

    await waitFor(() => {
      expect(screen.getByText('admin@test.com')).toBeInTheDocument()
    })

    const activeToggles = screen.getAllByRole('switch', { name: /toggle active status/i })
    const adminToggles = screen.getAllByRole('switch', { name: /toggle admin status/i })

    // Admin user (active=true, admin=true)
    expect(activeToggles[0]).toHaveAttribute('aria-checked', 'true')
    expect(adminToggles[0]).toHaveAttribute('aria-checked', 'true')

    // Regular user (active=true, admin=false)
    expect(activeToggles[1]).toHaveAttribute('aria-checked', 'true')
    expect(adminToggles[1]).toHaveAttribute('aria-checked', 'false')

    // Inactive user (active=false, admin=false)
    expect(activeToggles[2]).toHaveAttribute('aria-checked', 'false')
    expect(adminToggles[2]).toHaveAttribute('aria-checked', 'false')
  })

  it('pagination controls work', async () => {
    // Mock a response with pagination
    server.use(
      http.get('*/api/admin/users', ({ request }) => {
        const url = new URL(request.url)
        const page = parseInt(url.searchParams.get('page') || '1')
        return HttpResponse.json({
          items: [
            {
              id: String(page), email: `user-page${page}@test.com`, display_name: `Page ${page} User`,
              is_active: true, is_admin: false, recipe_count: 0,
              created_at: '2026-01-01T00:00:00Z', last_login_at: null,
            },
          ],
          total: 100,
          page,
          per_page: 50,
        })
      })
    )

    const user = userEvent.setup()
    renderPage()

    await waitFor(() => {
      expect(screen.getByText('user-page1@test.com')).toBeInTheDocument()
    })

    expect(screen.getByText('Page 1 of 2 (100 total)')).toBeInTheDocument()

    // Click Next
    await user.click(screen.getByText('Next'))

    await waitFor(() => {
      expect(screen.getByText('user-page2@test.com')).toBeInTheDocument()
    })

    // Click Previous
    await user.click(screen.getByText('Previous'))

    await waitFor(() => {
      expect(screen.getByText('user-page1@test.com')).toBeInTheDocument()
    })
  })

  it('dismisses error on new action', async () => {
    const user = userEvent.setup()
    renderPage()

    await waitFor(() => {
      expect(screen.getByText('admin@test.com')).toBeInTheDocument()
    })

    // Trigger self-deactivate error
    const activeToggles = screen.getAllByRole('switch', { name: /toggle active status/i })
    await user.click(activeToggles[0])

    await waitFor(() => {
      expect(screen.getByText('Cannot deactivate your own account')).toBeInTheDocument()
    })

    // Now click Dismiss
    await user.click(screen.getByText('Dismiss'))

    expect(screen.queryByText('Cannot deactivate your own account')).not.toBeInTheDocument()
  })

  it('closes confirmation modal on Cancel', async () => {
    const user = userEvent.setup()
    renderPage()

    await waitFor(() => {
      expect(screen.getByText('user@test.com')).toBeInTheDocument()
    })

    const activeToggles = screen.getAllByRole('switch', { name: /toggle active status/i })
    await user.click(activeToggles[1])

    await waitFor(() => {
      expect(screen.getByText('Deactivate this user?')).toBeInTheDocument()
    })

    await user.click(screen.getByText('Cancel'))

    expect(screen.queryByText('Deactivate this user?')).not.toBeInTheDocument()
  })

  it('redirects non-admin users to home page', async () => {
    mockUseAuth.mockReturnValue({
      ...adminAuth,
      user: { id: '2', email: 'user@test.com', display_name: 'Regular User', is_admin: false, created_at: '2026-02-01' },
      token: 'fake-token',
      isLoading: false,
    })

    render(
      <QueryClientProvider client={queryClient}>
        <AdminLayout>
          <UsersPage />
        </AdminLayout>
      </QueryClientProvider>
    )

    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith('/')
    })
  })

  it('revoke admin shows confirmation and updates', async () => {
    const user = userEvent.setup()
    renderPage()

    await waitFor(() => {
      expect(screen.getByText('otheradmin@test.com')).toBeInTheDocument()
    })

    // Click the admin toggle for otheradmin@test.com (user id=4, is_admin=true)
    const adminToggles = screen.getAllByRole('switch', { name: /toggle admin status/i })
    // Fourth toggle is for otheradmin@test.com
    await user.click(adminToggles[3])

    await waitFor(() => {
      expect(screen.getByText('Revoke admin privileges from otheradmin@test.com?')).toBeInTheDocument()
    })
    expect(screen.getByText('Revoke Admin')).toBeInTheDocument()

    await user.click(screen.getByText('Revoke Admin'))

    await waitFor(() => {
      expect(screen.queryByText(/Revoke admin privileges/)).not.toBeInTheDocument()
    })
  })

  it('shows API error when mutation fails', async () => {
    server.use(
      http.patch('*/api/admin/users/:id', () => {
        return HttpResponse.json(
          { detail: 'Server rejected the update' },
          { status: 400 }
        )
      })
    )

    const user = userEvent.setup()
    renderPage()

    await waitFor(() => {
      expect(screen.getByText('user@test.com')).toBeInTheDocument()
    })

    // Toggle active status for user@test.com
    const activeToggles = screen.getAllByRole('switch', { name: /toggle active status/i })
    await user.click(activeToggles[1])

    await waitFor(() => {
      expect(screen.getByText('Deactivate this user?')).toBeInTheDocument()
    })

    // Confirm the action — API will return 400
    await user.click(screen.getByText('Deactivate'))

    await waitFor(() => {
      expect(screen.getByText('Server rejected the update')).toBeInTheDocument()
    })
  })
})
