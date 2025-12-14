import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import NewRecipePage from '@/app/recipes/new/page'
import { TestProviders, createTestQueryClient } from '../utils/test-utils'
import { server } from '../mocks/server'
import { http, HttpResponse } from 'msw'
import { mockCategories } from '../mocks/handlers'
import { QueryClient } from '@tanstack/react-query'

const API_BASE = '*/api'

// Mock useRouter
const mockPush = vi.fn()
const mockBack = vi.fn()

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: vi.fn(),
    back: mockBack,
    forward: vi.fn(),
    refresh: vi.fn(),
    prefetch: vi.fn(),
  }),
  usePathname: () => '/recipes/new',
  useSearchParams: () => new URLSearchParams(),
}))

let queryClient: QueryClient

function renderNewRecipePage() {
  queryClient = createTestQueryClient()
  return render(
    <TestProviders queryClient={queryClient}>
      <NewRecipePage />
    </TestProviders>
  )
}

describe('NewRecipePage', () => {
  beforeEach(() => {
    mockPush.mockClear()
    mockBack.mockClear()
    vi.mocked(localStorage.getItem).mockReturnValue('mock-jwt-token')
    vi.mocked(localStorage.setItem).mockClear()
  })

  describe('Loading', () => {
    it('shows loading spinner while fetching categories', () => {
      renderNewRecipePage()

      // Check for loading spinner with animate-spin class
      const spinner = document.querySelector('.animate-spin')
      expect(spinner).toBeInTheDocument()
    })

    it('shows error if categories fail to load', async () => {
      server.use(
        http.get(`${API_BASE}/categories`, () => {
          return HttpResponse.json({ detail: 'Failed to load' }, { status: 500 })
        })
      )

      renderNewRecipePage()

      await waitFor(() => {
        expect(screen.getByText(/failed to load/i)).toBeInTheDocument()
      })
    })
  })

  describe('Form Rendering', () => {
    it('renders all form sections', async () => {
      renderNewRecipePage()

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /add new recipe/i })).toBeInTheDocument()
      })

      expect(screen.getByRole('heading', { name: /basic info/i })).toBeInTheDocument()
      expect(screen.getByRole('heading', { name: /classification/i })).toBeInTheDocument()
      expect(screen.getByRole('heading', { name: /ingredients/i })).toBeInTheDocument()
      expect(screen.getByRole('heading', { name: /preparation/i })).toBeInTheDocument()
    })

    it('populates category dropdowns', async () => {
      renderNewRecipePage()

      await waitFor(() => {
        expect(screen.getByLabelText(/template/i)).toBeInTheDocument()
      })

      // Verify template options are present
      const templateSelect = screen.getByLabelText(/template/i) as HTMLSelectElement
      expect(templateSelect.options.length).toBeGreaterThan(1) // More than just the placeholder

      // Verify spirit options are present
      const spiritSelect = screen.getByLabelText(/main spirit/i) as HTMLSelectElement
      expect(spiritSelect.options.length).toBeGreaterThan(1)
    })

    it('has initial ingredient row', async () => {
      renderNewRecipePage()

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/ingredient name/i)).toBeInTheDocument()
      })

      // Should start with exactly one ingredient row
      const ingredientInputs = screen.getAllByPlaceholderText(/ingredient name/i)
      expect(ingredientInputs.length).toBe(1)
    })
  })

  describe('Ingredient Management', () => {
    it('adds ingredient row', async () => {
      const user = userEvent.setup()
      renderNewRecipePage()

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /add ingredient/i })).toBeInTheDocument()
      })

      const initialCount = screen.getAllByPlaceholderText(/ingredient name/i).length
      await user.click(screen.getByRole('button', { name: /add ingredient/i }))

      const updatedCount = screen.getAllByPlaceholderText(/ingredient name/i).length
      expect(updatedCount).toBe(initialCount + 1)
    })

    it('cannot remove last ingredient', async () => {
      renderNewRecipePage()

      await waitFor(() => {
        expect(screen.getAllByPlaceholderText(/ingredient name/i).length).toBe(1)
      })

      // The remove button for the last ingredient should be disabled
      const removeButtons = document.querySelectorAll('button[disabled].text-gray-400')
      expect(removeButtons.length).toBeGreaterThanOrEqual(1)
    })
  })

  describe('Form Submission', () => {
    it('disables submit when name is empty', async () => {
      renderNewRecipePage()

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /create recipe/i })).toBeInTheDocument()
      })

      const submitButton = screen.getByRole('button', { name: /create recipe/i })
      expect(submitButton).toBeDisabled()
    })

    it('shows "Creating..." while submitting', async () => {
      const user = userEvent.setup()

      server.use(
        http.post(`${API_BASE}/recipes`, async () => {
          await new Promise((resolve) => setTimeout(resolve, 200))
          return HttpResponse.json({
            id: '3',
            name: 'Test Cocktail',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          })
        })
      )

      renderNewRecipePage()

      await waitFor(() => {
        expect(screen.getByLabelText(/name/i)).toBeInTheDocument()
      })

      await user.type(screen.getByLabelText(/name/i), 'Test Cocktail')
      await user.click(screen.getByRole('button', { name: /create recipe/i }))

      await waitFor(() => {
        expect(screen.getByText(/creating/i)).toBeInTheDocument()
      })
    })

    it('redirects to new recipe on success', async () => {
      const user = userEvent.setup()
      renderNewRecipePage()

      await waitFor(() => {
        expect(screen.getByLabelText(/name/i)).toBeInTheDocument()
      })

      await user.type(screen.getByLabelText(/name/i), 'Test Cocktail')
      await user.click(screen.getByRole('button', { name: /create recipe/i }))

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/recipes/3')
      })
    })

    it('shows error message on failure', async () => {
      const user = userEvent.setup()

      server.use(
        http.post(`${API_BASE}/recipes`, () => {
          return HttpResponse.json({ detail: 'Failed to create' }, { status: 500 })
        })
      )

      renderNewRecipePage()

      await waitFor(() => {
        expect(screen.getByLabelText(/name/i)).toBeInTheDocument()
      })

      await user.type(screen.getByLabelText(/name/i), 'Test Cocktail')
      await user.click(screen.getByRole('button', { name: /create recipe/i }))

      await waitFor(() => {
        expect(screen.getByText(/failed to create/i)).toBeInTheDocument()
      })
    })
  })

  describe('Navigation', () => {
    it('cancel returns to home', async () => {
      renderNewRecipePage()

      await waitFor(() => {
        expect(screen.getByRole('link', { name: /cancel/i })).toBeInTheDocument()
      })

      const cancelLink = screen.getByRole('link', { name: /cancel/i })
      expect(cancelLink).toHaveAttribute('href', '/')
    })

    it('back link navigates to home', async () => {
      renderNewRecipePage()

      await waitFor(() => {
        expect(screen.getByRole('link', { name: /back to recipes/i })).toBeInTheDocument()
      })

      const backLink = screen.getByRole('link', { name: /back to recipes/i })
      expect(backLink).toHaveAttribute('href', '/')
    })
  })
})
