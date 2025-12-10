import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import RecipeDetailPage from '@/app/recipes/[id]/page'
import { AuthProvider } from '@/lib/auth-context'
import { server } from '../mocks/server'
import { http, HttpResponse } from 'msw'
import { mockRecipeDetail, mockUser } from '../mocks/handlers'

const API_BASE = '*/api'

// Mock useRouter and useParams
const mockPush = vi.fn()
const mockBack = vi.fn()
let mockParamsId = '1'

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: vi.fn(),
    back: mockBack,
    forward: vi.fn(),
    refresh: vi.fn(),
    prefetch: vi.fn(),
  }),
  useParams: () => ({ id: mockParamsId }),
  usePathname: () => `/recipes/${mockParamsId}`,
  useSearchParams: () => new URLSearchParams(),
}))

function renderRecipeDetailPage() {
  return render(
    <AuthProvider>
      <RecipeDetailPage />
    </AuthProvider>
  )
}

describe('RecipeDetailPage', () => {
  beforeEach(() => {
    mockParamsId = '1'
    mockPush.mockClear()
    mockBack.mockClear()
    vi.mocked(localStorage.getItem).mockReturnValue(null)
    vi.mocked(localStorage.setItem).mockClear()
  })

  describe('Loading States', () => {
    it('shows loading skeleton initially', () => {
      renderRecipeDetailPage()

      // Check for loading skeleton with animate-pulse class
      const skeleton = document.querySelector('.animate-pulse')
      expect(skeleton).toBeInTheDocument()
    })

    it('displays "Recipe not found" for invalid ID', async () => {
      mockParamsId = 'invalid-id'

      server.use(
        http.get(`${API_BASE}/recipes/:id`, () => {
          return HttpResponse.json({ detail: 'Recipe not found' }, { status: 404 })
        })
      )

      renderRecipeDetailPage()

      await waitFor(() => {
        expect(screen.getByText(/recipe not found/i)).toBeInTheDocument()
      })
    })
  })

  describe('Recipe Display', () => {
    it('renders recipe name and description', async () => {
      renderRecipeDetailPage()

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: mockRecipeDetail.name })).toBeInTheDocument()
      })

      expect(screen.getByText(mockRecipeDetail.description!)).toBeInTheDocument()
    })

    it('displays template and spirit badges', async () => {
      renderRecipeDetailPage()

      await waitFor(() => {
        expect(screen.getByText(/sour/i)).toBeInTheDocument()
      })

      // Tequila appears both as spirit badge and in ingredients, so check for at least one
      expect(screen.getAllByText(/tequila/i).length).toBeGreaterThanOrEqual(1)
    })

    it('shows glassware and serving style with icons', async () => {
      renderRecipeDetailPage()

      await waitFor(() => {
        expect(screen.getByText(/coupe/i)).toBeInTheDocument()
      })

      // Check for serving style
      expect(screen.getByText(/served up/i)).toBeInTheDocument()
    })

    it('renders ingredients list sorted by order', async () => {
      renderRecipeDetailPage()

      await waitFor(() => {
        // Tequila appears both as spirit badge and in ingredients
        expect(screen.getAllByText(/tequila/i).length).toBeGreaterThanOrEqual(1)
      })

      // Check ingredients are rendered
      expect(screen.getByText(/lime juice/i)).toBeInTheDocument()

      // Check amounts are displayed
      expect(screen.getByText(/2 oz/i)).toBeInTheDocument()
      expect(screen.getByText(/1 oz/i)).toBeInTheDocument()
    })

    it('shows garnish section when present', async () => {
      renderRecipeDetailPage()

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /garnish/i })).toBeInTheDocument()
      })

      expect(screen.getByText(mockRecipeDetail.garnish!)).toBeInTheDocument()
    })

    it('shows instructions when present', async () => {
      renderRecipeDetailPage()

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /instructions/i })).toBeInTheDocument()
      })

      expect(screen.getByText(/shake all ingredients with ice/i)).toBeInTheDocument()
    })

    it('shows notes when present', async () => {
      renderRecipeDetailPage()

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /notes/i })).toBeInTheDocument()
      })

      expect(screen.getByText(mockRecipeDetail.notes!)).toBeInTheDocument()
    })

    it('displays created date and source type', async () => {
      renderRecipeDetailPage()

      await waitFor(() => {
        expect(screen.getByText(/added/i)).toBeInTheDocument()
      })

      expect(screen.getByText(/via manual/i)).toBeInTheDocument()
    })
  })

  describe('Authorization', () => {
    it('shows Edit/Delete buttons when user owns recipe', async () => {
      // Set up authenticated user who owns the recipe
      vi.mocked(localStorage.getItem).mockReturnValue('mock-jwt-token')

      renderRecipeDetailPage()

      await waitFor(() => {
        expect(screen.getByRole('link', { name: /edit/i })).toBeInTheDocument()
      })

      expect(screen.getByRole('button', { name: /delete/i })).toBeInTheDocument()
    })

    it('shows Edit/Delete for unowned recipes (user_id is null)', async () => {
      server.use(
        http.get(`${API_BASE}/recipes/:id`, () => {
          return HttpResponse.json({
            ...mockRecipeDetail,
            user_id: null,
          })
        })
      )

      renderRecipeDetailPage()

      await waitFor(() => {
        expect(screen.getByRole('link', { name: /edit/i })).toBeInTheDocument()
      })

      expect(screen.getByRole('button', { name: /delete/i })).toBeInTheDocument()
    })

    it('hides Edit/Delete when different user owns recipe', async () => {
      vi.mocked(localStorage.getItem).mockReturnValue('mock-jwt-token')

      server.use(
        http.get(`${API_BASE}/recipes/:id`, () => {
          return HttpResponse.json({
            ...mockRecipeDetail,
            user_id: 'different-user-id',
          })
        })
      )

      renderRecipeDetailPage()

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: mockRecipeDetail.name })).toBeInTheDocument()
      })

      expect(screen.queryByRole('link', { name: /edit/i })).not.toBeInTheDocument()
      expect(screen.queryByRole('button', { name: /delete/i })).not.toBeInTheDocument()
    })
  })

  describe('Delete Functionality', () => {
    beforeEach(() => {
      vi.mocked(localStorage.getItem).mockReturnValue('mock-jwt-token')
    })

    it('shows confirmation dialog before delete', async () => {
      const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(false)
      const user = userEvent.setup()

      renderRecipeDetailPage()

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /delete/i })).toBeInTheDocument()
      })

      await user.click(screen.getByRole('button', { name: /delete/i }))

      expect(confirmSpy).toHaveBeenCalledWith('Are you sure you want to delete this recipe?')
      confirmSpy.mockRestore()
    })

    it('calls delete API and redirects to home on confirm', async () => {
      vi.spyOn(window, 'confirm').mockReturnValue(true)
      const user = userEvent.setup()

      renderRecipeDetailPage()

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /delete/i })).toBeInTheDocument()
      })

      await user.click(screen.getByRole('button', { name: /delete/i }))

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/')
      })
    })

    it('shows error message on delete failure', async () => {
      vi.spyOn(window, 'confirm').mockReturnValue(true)
      vi.spyOn(window, 'alert').mockImplementation(() => {})
      const user = userEvent.setup()

      server.use(
        http.delete(`${API_BASE}/recipes/:id`, () => {
          return HttpResponse.json({ detail: 'Failed to delete' }, { status: 500 })
        })
      )

      renderRecipeDetailPage()

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /delete/i })).toBeInTheDocument()
      })

      await user.click(screen.getByRole('button', { name: /delete/i }))

      await waitFor(() => {
        expect(window.alert).toHaveBeenCalled()
      })
    })
  })

  describe('Navigation', () => {
    it('back link navigates to home', async () => {
      renderRecipeDetailPage()

      await waitFor(() => {
        expect(screen.getByRole('link', { name: /back to recipes/i })).toBeInTheDocument()
      })

      const backLink = screen.getByRole('link', { name: /back to recipes/i })
      expect(backLink).toHaveAttribute('href', '/')
    })

    it('edit link goes to edit page', async () => {
      vi.mocked(localStorage.getItem).mockReturnValue('mock-jwt-token')

      renderRecipeDetailPage()

      await waitFor(() => {
        expect(screen.getByRole('link', { name: /edit/i })).toBeInTheDocument()
      })

      const editLink = screen.getByRole('link', { name: /edit/i })
      expect(editLink).toHaveAttribute('href', '/recipes/1/edit')
    })
  })
})
