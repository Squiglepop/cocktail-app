import { render, screen, waitFor, cleanup } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi, afterEach } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// Always-admin mock (default)
let mockAuthUser: Record<string, unknown> | null = {
  id: '1', email: 'admin@test.com', display_name: 'Admin', is_admin: true, created_at: '2026-01-01',
}
let mockAuthToken: string | null = 'fake-token'

vi.mock('@/lib/auth-context', () => ({
  useAuth: () => ({
    user: mockAuthUser,
    token: mockAuthToken,
    isLoading: false,
    login: vi.fn(), logout: vi.fn(), register: vi.fn(), refreshToken: vi.fn(),
  }),
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

vi.mock('@/lib/favourites-context', () => ({
  useFavourites: () => ({ favourites: new Set(), favouriteCount: 0, toggleFavourite: vi.fn(), isFavourite: () => false }),
  FavouritesProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

import { FilterSidebar } from '@/components/recipes/FilterSidebar'

let queryClient: QueryClient

function renderFilterSidebar(props?: Partial<React.ComponentProps<typeof FilterSidebar>>) {
  queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <FilterSidebar filters={{}} onFilterChange={vi.fn()} {...props} />
    </QueryClientProvider>
  )
}

afterEach(() => {
  cleanup()
  // Reset to admin default
  mockAuthUser = { id: '1', email: 'admin@test.com', display_name: 'Admin', is_admin: true, created_at: '2026-01-01' }
  mockAuthToken = 'fake-token'
})

describe('FilterSidebar - Admin Manage Links', () => {
  it('shows Manage links when user is admin', async () => {
    renderFilterSidebar()

    await waitFor(() => {
      expect(screen.getByText('Template')).toBeInTheDocument()
    })

    const manageButtons = screen.getAllByText(/Manage/)
    expect(manageButtons.length).toBe(5)
  })

  it('does not show Manage links when user is not admin', async () => {
    mockAuthUser = { id: '2', email: 'user@test.com', display_name: 'User', is_admin: false, created_at: '2026-01-01' }

    renderFilterSidebar()

    await waitFor(() => {
      expect(screen.getByText('Template')).toBeInTheDocument()
    })

    expect(screen.queryByText(/Manage/)).not.toBeInTheDocument()
  })

  it('does not show Manage links when user is null', async () => {
    mockAuthUser = null
    mockAuthToken = null

    renderFilterSidebar()

    await waitFor(() => {
      expect(screen.getByText('Template')).toBeInTheDocument()
    })

    expect(screen.queryByText(/Manage/)).not.toBeInTheDocument()
  })

  it('clicking Manage opens CategoryManagementModal', async () => {
    const user = userEvent.setup()

    renderFilterSidebar()

    await waitFor(() => {
      expect(screen.getByText('Template')).toBeInTheDocument()
    })

    const manageButtons = screen.getAllByText(/Manage/)
    await user.click(manageButtons[0])

    await waitFor(() => {
      expect(screen.getByText('Manage Templates')).toBeInTheDocument()
    })
  })
})
