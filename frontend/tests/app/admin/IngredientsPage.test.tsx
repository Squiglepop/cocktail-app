import { render, screen, cleanup, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi, afterEach, beforeEach } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import IngredientsPage from '@/app/admin/ingredients/page'
import AdminLayout from '@/app/admin/layout'
import { http, HttpResponse } from 'msw'
import { server } from '../../mocks/server'

// Mock auth as admin
vi.mock('@/lib/auth-context', () => ({
  useAuth: vi.fn(),
}))

const mockReplace = vi.fn()
vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn(), replace: mockReplace }),
  usePathname: () => '/admin/ingredients',
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

const nonAdminAuth = {
  ...adminAuth,
  user: { ...adminAuth.user, is_admin: false },
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
      <IngredientsPage />
    </QueryClientProvider>
  )
}

describe('IngredientsPage', () => {
  it('renders ingredient table with data', async () => {
    renderPage()

    await waitFor(() => {
      expect(screen.getByText('Lime Juice')).toBeInTheDocument()
    })
    expect(screen.getByText('Simple Syrup')).toBeInTheDocument()
    expect(screen.getByText('London Dry Gin')).toBeInTheDocument()
  })

  it('search filters ingredients with debounce', async () => {
    const user = userEvent.setup()
    renderPage()

    await waitFor(() => {
      expect(screen.getByText('Lime Juice')).toBeInTheDocument()
    })

    await user.type(screen.getByPlaceholderText(/search/i), 'Gin')

    // Wait for debounce + refetch
    await waitFor(() => {
      expect(screen.getByText('London Dry Gin')).toBeInTheDocument()
      expect(screen.queryByText('Lime Juice')).not.toBeInTheDocument()
    })
  })

  it('type filter shows filtered results', async () => {
    const user = userEvent.setup()
    renderPage()

    await waitFor(() => {
      expect(screen.getByText('Lime Juice')).toBeInTheDocument()
    })

    await user.selectOptions(screen.getByDisplayValue('All Types'), 'juice')

    await waitFor(() => {
      expect(screen.getByText('Lime Juice')).toBeInTheDocument()
      expect(screen.queryByText('Simple Syrup')).not.toBeInTheDocument()
    })
  })

  it('clicking Add opens create modal', async () => {
    const user = userEvent.setup()
    renderPage()

    await waitFor(() => {
      expect(screen.getByText('Lime Juice')).toBeInTheDocument()
    })

    await user.click(screen.getByRole('button', { name: /add ingredient/i }))

    // Modal should open with empty name field
    expect(screen.getByLabelText(/name/i)).toHaveValue('')
    expect(screen.getByLabelText(/^type/i)).toBeInTheDocument()
  })

  it('clicking edit icon opens edit modal', async () => {
    const user = userEvent.setup()
    renderPage()

    await waitFor(() => {
      expect(screen.getByText('Lime Juice')).toBeInTheDocument()
    })

    const editButtons = screen.getAllByLabelText(/edit/i)
    await user.click(editButtons[0])

    expect(screen.getByText('Edit Ingredient')).toBeInTheDocument()
    expect(screen.getByDisplayValue('Lime Juice')).toBeInTheDocument()
  })

  it('successful create refreshes list', async () => {
    const user = userEvent.setup()
    renderPage()

    await waitFor(() => {
      expect(screen.getByText('Lime Juice')).toBeInTheDocument()
    })

    await user.click(screen.getByRole('button', { name: /add ingredient/i }))

    await user.type(screen.getByLabelText(/name/i), 'Angostura Bitters')
    await user.selectOptions(screen.getByLabelText(/^type/i), 'bitter')
    await user.click(screen.getByRole('button', { name: /create/i }))

    // Modal should close on success — the name input should be gone
    await waitFor(() => {
      expect(screen.queryByLabelText(/name/i)).not.toBeInTheDocument()
    })
  })

  it('409 on create shows error', async () => {
    const user = userEvent.setup()
    renderPage()

    await waitFor(() => {
      expect(screen.getByText('Lime Juice')).toBeInTheDocument()
    })

    await user.click(screen.getByRole('button', { name: /add ingredient/i }))

    await user.type(screen.getByLabelText(/name/i), 'Lime Juice')
    await user.selectOptions(screen.getByLabelText(/^type/i), 'juice')
    await user.click(screen.getByRole('button', { name: /create/i }))

    await waitFor(() => {
      expect(screen.getByText(/already exists/i)).toBeInTheDocument()
    })
  })

  it('delete shows confirmation then removes', async () => {
    const user = userEvent.setup()
    renderPage()

    await waitFor(() => {
      expect(screen.getByText('Simple Syrup')).toBeInTheDocument()
    })

    // Click delete on Simple Syrup (id: 2, not in-use)
    const deleteButtons = screen.getAllByLabelText(/delete/i)
    await user.click(deleteButtons[1]) // Second row

    expect(screen.getByText(/are you sure/i)).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /^delete$/i }))

    // Confirmation modal should close
    await waitFor(() => {
      expect(screen.queryByText(/are you sure/i)).not.toBeInTheDocument()
    })
  })

  it('delete of in-use ingredient shows error', async () => {
    const user = userEvent.setup()
    renderPage()

    await waitFor(() => {
      expect(screen.getByText('Lime Juice')).toBeInTheDocument()
    })

    // Click delete on Lime Juice (id: 1, in-use — returns 409)
    const deleteButtons = screen.getAllByLabelText(/delete/i)
    await user.click(deleteButtons[0])

    await user.click(screen.getByRole('button', { name: /^delete$/i }))

    await waitFor(() => {
      expect(screen.getByText(/cannot delete: used in 15 recipes/i)).toBeInTheDocument()
    })
  })

  it('pagination controls work', async () => {
    // Override with lots of items to get multiple pages
    server.use(
      http.get('*/api/admin/ingredients', ({ request }) => {
        const url = new URL(request.url)
        const page = parseInt(url.searchParams.get('page') || '1')
        return HttpResponse.json({
          items: [{ id: String(page), name: `Ingredient Page ${page}`, type: 'other', spirit_category: null, description: null, common_brands: null }],
          total: 100,
          page,
          per_page: 50,
        })
      })
    )
    const user = userEvent.setup()
    renderPage()

    await waitFor(() => {
      expect(screen.getByText('Page 1 of 2')).toBeInTheDocument()
    })

    await user.click(screen.getByRole('button', { name: /next/i }))

    await waitFor(() => {
      expect(screen.getByText('Page 2 of 2')).toBeInTheDocument()
    })
  })

  it('shows error message when API returns 500', async () => {
    server.use(
      http.get('*/api/admin/ingredients', () => new HttpResponse(null, { status: 500 }))
    )
    renderPage()

    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument()
    })
  })

  it('handles 401 API response gracefully', async () => {
    server.use(
      http.get('*/api/admin/ingredients', () =>
        HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 })
      )
    )
    renderPage()

    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument()
    })
  })

  it('redirects non-admin users via AdminLayout', async () => {
    mockUseAuth.mockReturnValue(nonAdminAuth)

    render(
      <QueryClientProvider client={queryClient}>
        <AdminLayout>
          <IngredientsPage />
        </AdminLayout>
      </QueryClientProvider>
    )

    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith('/')
    })

    // Layout renders nothing for non-admin (prevents flash)
    expect(screen.queryByText('Ingredient Management')).not.toBeInTheDocument()
  })
})
