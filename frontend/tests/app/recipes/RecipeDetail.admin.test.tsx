import { render, screen, waitFor, cleanup } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi, afterEach, beforeEach } from 'vitest'
import RecipeDetailPage from '@/app/recipes/[id]/page'
import { TestProviders, createTestQueryClient } from '../../utils/test-utils'
import { server } from '../../mocks/server'
import { http, HttpResponse } from 'msw'
import { mockRecipeDetail } from '../../mocks/handlers'
import { QueryClient } from '@tanstack/react-query'

// Mock IndexedDB offline storage to prevent async state updates after unmount
vi.mock('@/lib/offline-storage', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/lib/offline-storage')>()
  return {
    ...actual,
    getRecipeOffline: vi.fn().mockResolvedValue(null),
    getCachedRecipeListItems: vi.fn().mockResolvedValue([]),
  }
})

const API_BASE = '*/api'

const mockPush = vi.fn()
let mockParamsId = '1'

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
    prefetch: vi.fn(),
  }),
  useParams: () => ({ id: mockParamsId }),
  usePathname: () => `/recipes/${mockParamsId}`,
  useSearchParams: () => new URLSearchParams(),
}))

const adminUser = {
  id: 'admin-1',
  email: 'admin@test.com',
  display_name: 'Admin User',
  is_admin: true,
  created_at: '2026-01-01T00:00:00Z',
}

const regularUser = {
  id: 'regular-1',
  email: 'user@test.com',
  display_name: 'Regular User',
  is_admin: false,
  created_at: '2026-01-01T00:00:00Z',
}

let queryClient: QueryClient

function renderWithAuth(userOverride?: typeof adminUser) {
  const user = userOverride || adminUser
  queryClient = createTestQueryClient()

  server.use(
    http.post(`${API_BASE}/auth/refresh`, () => {
      return HttpResponse.json({
        access_token: 'mock-jwt-token',
        token_type: 'bearer',
      })
    }),
    http.get(`${API_BASE}/auth/me`, () => {
      return HttpResponse.json(user)
    })
  )

  return render(
    <TestProviders queryClient={queryClient}>
      <RecipeDetailPage />
    </TestProviders>
  )
}

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

beforeEach(() => {
  mockParamsId = '1'
  mockPush.mockClear()
})

describe('RecipeDetailPage - Admin Controls', () => {
  it('shows edit/delete buttons when user is admin but not owner', async () => {
    // Recipe owned by user_id '1', admin is 'admin-1' — not owner
    server.use(
      http.get(`${API_BASE}/recipes/:id`, () => {
        return HttpResponse.json({
          ...mockRecipeDetail,
          user_id: 'other-user-id',
        })
      })
    )

    renderWithAuth(adminUser)

    await waitFor(() => {
      expect(screen.getByRole('link', { name: /edit/i })).toBeInTheDocument()
    })

    expect(screen.getByRole('button', { name: /delete/i })).toBeInTheDocument()
  })

  it('does not show edit/delete when regular user and not owner', async () => {
    server.use(
      http.get(`${API_BASE}/recipes/:id`, () => {
        return HttpResponse.json({
          ...mockRecipeDetail,
          user_id: 'other-user-id',
        })
      })
    )

    renderWithAuth(regularUser)

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: mockRecipeDetail.name })).toBeInTheDocument()
    })

    expect(screen.queryByRole('link', { name: /edit/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /delete/i })).not.toBeInTheDocument()
  })

  it('delete button opens confirmation modal instead of browser confirm', async () => {
    const confirmSpy = vi.spyOn(window, 'confirm')
    const user = userEvent.setup()

    renderWithAuth(adminUser)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /delete/i })).toBeInTheDocument()
    })

    await user.click(screen.getByRole('button', { name: /delete/i }))

    // Should show modal, NOT browser confirm
    await waitFor(() => {
      expect(screen.getByText('Delete this recipe?')).toBeInTheDocument()
    })
    expect(confirmSpy).not.toHaveBeenCalled()
    expect(screen.getByText(/Are you sure you want to delete/)).toBeInTheDocument()

    confirmSpy.mockRestore()
  })
})
