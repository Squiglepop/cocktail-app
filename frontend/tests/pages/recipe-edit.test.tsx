import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import EditRecipePage from '@/app/recipes/[id]/edit/page'
import { TestProviders, createTestQueryClient } from '../utils/test-utils'
import { server } from '../mocks/server'
import { http, HttpResponse } from 'msw'
import { mockRecipeDetail, mockCategories } from '../mocks/handlers'
import { QueryClient } from '@tanstack/react-query'

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
  usePathname: () => `/recipes/${mockParamsId}/edit`,
  useSearchParams: () => new URLSearchParams(),
}))

let queryClient: QueryClient

function renderEditRecipePage() {
  queryClient = createTestQueryClient()
  return render(
    <TestProviders queryClient={queryClient}>
      <EditRecipePage />
    </TestProviders>
  )
}

describe('EditRecipePage', () => {
  beforeEach(() => {
    mockParamsId = '1'
    mockPush.mockClear()
    mockBack.mockClear()
    vi.mocked(localStorage.getItem).mockReturnValue('mock-jwt-token')
    vi.mocked(localStorage.setItem).mockClear()
  })

  describe('Loading and Authorization', () => {
    it('shows loading spinner while fetching', () => {
      renderEditRecipePage()

      // Check for loading spinner with animate-spin class
      const spinner = document.querySelector('.animate-spin')
      expect(spinner).toBeInTheDocument()
    })

    it('shows "Access Denied" for unauthorized user', async () => {
      server.use(
        http.get(`${API_BASE}/recipes/:id`, () => {
          return HttpResponse.json({
            ...mockRecipeDetail,
            user_id: 'different-user-id',
          })
        })
      )

      renderEditRecipePage()

      await waitFor(() => {
        expect(screen.getByText(/access denied/i)).toBeInTheDocument()
      })

      expect(screen.getByText(/don't have permission/i)).toBeInTheDocument()
    })
  })

  describe('Form Population', () => {
    it('populates form with existing recipe data', async () => {
      renderEditRecipePage()

      await waitFor(() => {
        expect(screen.getByLabelText(/name/i)).toHaveValue(mockRecipeDetail.name)
      })

      expect(screen.getByLabelText(/description/i)).toHaveValue(mockRecipeDetail.description)
      expect(screen.getByLabelText(/garnish/i)).toHaveValue(mockRecipeDetail.garnish)
      expect(screen.getByLabelText(/instructions/i)).toHaveValue(mockRecipeDetail.instructions)
      expect(screen.getByLabelText(/notes/i)).toHaveValue(mockRecipeDetail.notes)
    })

    it('loads category dropdown options', async () => {
      renderEditRecipePage()

      await waitFor(() => {
        expect(screen.getByLabelText(/template/i)).toBeInTheDocument()
      })

      // Check template options
      const templateSelect = screen.getByLabelText(/template/i)
      expect(templateSelect).toHaveValue(mockRecipeDetail.template)

      // Check spirit options
      const spiritSelect = screen.getByLabelText(/main spirit/i)
      expect(spiritSelect).toHaveValue(mockRecipeDetail.main_spirit)
    })

    it('renders existing ingredients in order', async () => {
      renderEditRecipePage()

      await waitFor(() => {
        // Wait for ingredients to load
        const ingredientInputs = screen.getAllByPlaceholderText(/ingredient name/i)
        expect(ingredientInputs.length).toBeGreaterThanOrEqual(2)
      })

      // Check first ingredient
      const ingredientInputs = screen.getAllByPlaceholderText(/ingredient name/i)
      expect(ingredientInputs[0]).toHaveValue('Tequila')
      expect(ingredientInputs[1]).toHaveValue('Lime Juice')
    })
  })

  describe('Ingredient Management', () => {
    it('adds new ingredient row when clicking Add', async () => {
      const user = userEvent.setup()
      renderEditRecipePage()

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /add ingredient/i })).toBeInTheDocument()
      })

      const initialIngredients = screen.getAllByPlaceholderText(/ingredient name/i)
      const initialCount = initialIngredients.length

      await user.click(screen.getByRole('button', { name: /add ingredient/i }))

      const updatedIngredients = screen.getAllByPlaceholderText(/ingredient name/i)
      expect(updatedIngredients.length).toBe(initialCount + 1)
    })

    it('removes ingredient when clicking Remove', async () => {
      const user = userEvent.setup()
      renderEditRecipePage()

      await waitFor(() => {
        expect(screen.getAllByPlaceholderText(/ingredient name/i).length).toBeGreaterThanOrEqual(2)
      })

      const initialIngredients = screen.getAllByPlaceholderText(/ingredient name/i)
      const initialCount = initialIngredients.length

      // Find and click the first remove button (they have Trash2 icon)
      const removeButtons = document.querySelectorAll('button.text-gray-400')
      await user.click(removeButtons[0] as HTMLElement)

      const updatedIngredients = screen.getAllByPlaceholderText(/ingredient name/i)
      expect(updatedIngredients.length).toBe(initialCount - 1)
    })

    it('updates ingredient fields correctly', async () => {
      const user = userEvent.setup()
      renderEditRecipePage()

      await waitFor(() => {
        expect(screen.getAllByPlaceholderText(/ingredient name/i).length).toBeGreaterThanOrEqual(1)
      })

      const ingredientInput = screen.getAllByPlaceholderText(/ingredient name/i)[0]
      await user.clear(ingredientInput)
      await user.type(ingredientInput, 'Mezcal')

      expect(ingredientInput).toHaveValue('Mezcal')
    })
  })

  describe('Form Submission', () => {
    it('requires name field', async () => {
      renderEditRecipePage()

      await waitFor(() => {
        expect(screen.getByLabelText(/name/i)).toBeInTheDocument()
      })

      const nameInput = screen.getByLabelText(/name/i)
      expect(nameInput).toHaveAttribute('required')
    })

    it('disables submit when name is empty', async () => {
      const user = userEvent.setup()
      renderEditRecipePage()

      await waitFor(() => {
        expect(screen.getByLabelText(/name/i)).toBeInTheDocument()
      })

      const nameInput = screen.getByLabelText(/name/i)
      await user.clear(nameInput)

      const submitButton = screen.getByRole('button', { name: /save changes/i })
      expect(submitButton).toBeDisabled()
    })

    it('shows "Saving..." while submitting', async () => {
      const user = userEvent.setup()

      server.use(
        http.put(`${API_BASE}/recipes/:id`, async () => {
          await new Promise((resolve) => setTimeout(resolve, 200))
          return HttpResponse.json({
            ...mockRecipeDetail,
            updated_at: new Date().toISOString(),
          })
        })
      )

      renderEditRecipePage()

      await waitFor(() => {
        expect(screen.getByLabelText(/name/i)).toBeInTheDocument()
      })

      await user.click(screen.getByRole('button', { name: /save changes/i }))

      await waitFor(() => {
        expect(screen.getByText(/saving/i)).toBeInTheDocument()
      })
    })

    it('redirects to recipe detail on success', async () => {
      const user = userEvent.setup()
      renderEditRecipePage()

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /save changes/i })).not.toBeDisabled()
      })

      await user.click(screen.getByRole('button', { name: /save changes/i }))

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/recipes/1')
      })
    })

    it('shows error message on failure', async () => {
      const user = userEvent.setup()

      server.use(
        http.put(`${API_BASE}/recipes/:id`, () => {
          return HttpResponse.json({ detail: 'Failed to update' }, { status: 500 })
        })
      )

      renderEditRecipePage()

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /save changes/i })).not.toBeDisabled()
      })

      await user.click(screen.getByRole('button', { name: /save changes/i }))

      await waitFor(() => {
        expect(screen.getByText(/failed to update/i)).toBeInTheDocument()
      })
    })
  })

  describe('Navigation', () => {
    it('cancel returns to recipe detail', async () => {
      renderEditRecipePage()

      await waitFor(() => {
        expect(screen.getByRole('link', { name: /cancel/i })).toBeInTheDocument()
      })

      const cancelLink = screen.getByRole('link', { name: /cancel/i })
      expect(cancelLink).toHaveAttribute('href', '/recipes/1')
    })

    it('back link navigates to recipe detail', async () => {
      renderEditRecipePage()

      await waitFor(() => {
        expect(screen.getByRole('link', { name: /back to recipe/i })).toBeInTheDocument()
      })

      const backLink = screen.getByRole('link', { name: /back to recipe/i })
      expect(backLink).toHaveAttribute('href', '/recipes/1')
    })
  })
})
