import { render, screen, waitFor, cleanup } from '@testing-library/react'
import { vi, afterEach, beforeEach } from 'vitest'
import EditRecipePage from '@/app/recipes/[id]/edit/page'
import { TestProviders, createTestQueryClient } from '../../utils/test-utils'
import { server } from '../../mocks/server'
import { http, HttpResponse } from 'msw'
import { mockRecipeDetail } from '../../mocks/handlers'
import { QueryClient } from '@tanstack/react-query'

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
  usePathname: () => `/recipes/${mockParamsId}/edit`,
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
    }),
    http.get(`${API_BASE}/recipes/:id`, () => {
      return HttpResponse.json({
        ...mockRecipeDetail,
        user_id: 'other-user-id',
      })
    })
  )

  return render(
    <TestProviders queryClient={queryClient}>
      <EditRecipePage />
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

describe('EditRecipePage - Admin Access', () => {
  it('admin can access edit page for other user recipe', async () => {
    renderWithAuth(adminUser)

    // Should show the edit form, NOT "Access Denied"
    await waitFor(() => {
      expect(screen.getByLabelText(/name/i)).toBeInTheDocument()
    })

    expect(screen.queryByText(/access denied/i)).not.toBeInTheDocument()
    expect(screen.getByLabelText(/name/i)).toHaveValue(mockRecipeDetail.name)
  })

  it('regular user sees Access Denied for other user recipe', async () => {
    renderWithAuth(regularUser)

    await waitFor(() => {
      expect(screen.getByText(/access denied/i)).toBeInTheDocument()
    })

    expect(screen.getByText(/don't have permission/i)).toBeInTheDocument()
  })
})
