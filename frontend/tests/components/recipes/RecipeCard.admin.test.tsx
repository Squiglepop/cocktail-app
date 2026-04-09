import { render, screen, cleanup, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi, afterEach, beforeEach } from 'vitest'
import { RecipeCard } from '@/components/recipes/RecipeCard'
import { RecipeListItem } from '@/lib/api'
import { FavouritesProvider } from '@/lib/favourites-context'
import { OfflineProvider } from '@/lib/offline-context'
import { ListStateProvider } from '@/lib/list-state-context'
import { QueryClientProvider, QueryClient } from '@tanstack/react-query'
import { server } from '../../mocks/server'
import { http, HttpResponse } from 'msw'

const API_BASE = '*/api'

// Mock useAuth to control admin state
vi.mock('@/lib/auth-context', () => ({
  useAuth: vi.fn(),
  AuthProvider: ({ children }: { children: React.ReactNode }) => children,
}))

import { useAuth } from '@/lib/auth-context'

const mockUseAuth = vi.mocked(useAuth)

const mockPush = vi.fn()
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
    prefetch: vi.fn(),
  }),
  usePathname: () => '/',
  useSearchParams: () => new URLSearchParams(),
}))

const mockRecipe: RecipeListItem = {
  id: '1',
  name: 'Margarita',
  template: 'sour',
  main_spirit: 'tequila',
  glassware: 'coupe',
  serving_style: 'up',
  has_image: false,
  user_id: '2',
  visibility: 'public',
  created_at: '2024-01-01T00:00:00Z',
}

const adminAuth = {
  user: { id: '1', email: 'admin@test.com', display_name: 'Admin', is_admin: true, created_at: '2026-01-01T00:00:00Z' },
  token: 'fake-token',
  isLoading: false,
  login: vi.fn(),
  register: vi.fn(),
  logout: vi.fn(),
  refreshToken: vi.fn(),
}

const regularAuth = {
  ...adminAuth,
  user: { ...adminAuth.user, is_admin: false },
}

const nullAuth = {
  ...adminAuth,
  user: null,
  token: null,
}

let queryClient: QueryClient

function renderRecipeCard(recipe: RecipeListItem = mockRecipe) {
  queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <FavouritesProvider>
        <OfflineProvider>
          <ListStateProvider>
            <RecipeCard recipe={recipe} />
          </ListStateProvider>
        </OfflineProvider>
      </FavouritesProvider>
    </QueryClientProvider>
  )
}

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

beforeEach(() => {
  server.use(
    http.post(`${API_BASE}/auth/refresh`, () => {
      return HttpResponse.json({ detail: 'No refresh token' }, { status: 401 })
    })
  )
})

describe('RecipeCard - Admin Controls', () => {
  it('shows edit and delete icons when user is admin', () => {
    mockUseAuth.mockReturnValue(adminAuth)
    renderRecipeCard()

    expect(screen.getByTitle('Edit recipe')).toBeInTheDocument()
    expect(screen.getByTitle('Delete recipe')).toBeInTheDocument()
  })

  it('does not show admin icons when user is not admin', () => {
    mockUseAuth.mockReturnValue(regularAuth)
    renderRecipeCard()

    expect(screen.queryByTitle('Edit recipe')).not.toBeInTheDocument()
    expect(screen.queryByTitle('Delete recipe')).not.toBeInTheDocument()
  })

  it('does not show admin icons when user is null', () => {
    mockUseAuth.mockReturnValue(nullAuth)
    renderRecipeCard()

    expect(screen.queryByTitle('Edit recipe')).not.toBeInTheDocument()
    expect(screen.queryByTitle('Delete recipe')).not.toBeInTheDocument()
  })

  it('edit icon navigates to edit page', async () => {
    mockUseAuth.mockReturnValue(adminAuth)
    const user = userEvent.setup()
    renderRecipeCard()

    await user.click(screen.getByTitle('Edit recipe'))

    expect(mockPush).toHaveBeenCalledWith('/recipes/1/edit')
  })

  it('delete icon opens confirmation modal', async () => {
    mockUseAuth.mockReturnValue(adminAuth)
    const user = userEvent.setup()
    renderRecipeCard()

    await user.click(screen.getByTitle('Delete recipe'))

    expect(screen.getByText('Delete this recipe?')).toBeInTheDocument()
    expect(screen.getByText(/Are you sure you want to delete/)).toBeInTheDocument()
  })

  it('confirming delete calls delete mutation with correct recipe id and auth', async () => {
    mockUseAuth.mockReturnValue(adminAuth)
    const user = userEvent.setup()

    let capturedId: string | undefined
    let capturedAuth: string | null = null

    server.use(
      http.delete(`${API_BASE}/recipes/:id`, ({ params, request }) => {
        capturedId = params.id as string
        capturedAuth = request.headers.get('Authorization')
        return HttpResponse.json({ message: 'Deleted' })
      })
    )

    renderRecipeCard()

    // Open modal
    await user.click(screen.getByTitle('Delete recipe'))

    // Confirm delete
    await user.click(screen.getByRole('button', { name: /^delete$/i }))

    // Modal should close after successful delete
    await waitFor(() => {
      expect(screen.queryByText('Delete this recipe?')).not.toBeInTheDocument()
    })

    // Verify correct recipe ID and auth token were sent
    expect(capturedId).toBe('1')
    expect(capturedAuth).toBe('Bearer fake-token')
  })
})
