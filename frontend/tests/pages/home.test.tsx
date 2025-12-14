import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import HomePage from '@/app/page'
import { AuthProvider } from '@/lib/auth-context'
import { FavouritesProvider } from '@/lib/favourites-context'
import { server } from '../mocks/server'
import { http, HttpResponse } from 'msw'

const API_BASE = '*/api'

function renderHomePage() {
  return render(
    <AuthProvider>
      <FavouritesProvider>
        <HomePage />
      </FavouritesProvider>
    </AuthProvider>
  )
}

// Helper to get select by its preceding label text
const getSelectByLabel = (labelText: RegExp) => {
  const label = screen.getByText(labelText)
  const container = label.closest('div')
  return container?.querySelector('select') as HTMLSelectElement
}

describe('Home Page', () => {
  beforeEach(() => {
    vi.mocked(localStorage.getItem).mockReturnValue(null)
  })

  describe('Title and Header', () => {
    it('renders page title', async () => {
      renderHomePage()

      await waitFor(() => {
        // Page has both mobile and desktop layouts - get all and check at least one
        const headings = screen.getAllByRole('heading', { name: /cocktail recipes/i })
        expect(headings.length).toBeGreaterThanOrEqual(1)
      })
    })

    it('shows recipe count after loading', async () => {
      renderHomePage()

      await waitFor(() => {
        // Page has both mobile and desktop layouts
        const counts = screen.getAllByText(/2 recipes/i)
        expect(counts.length).toBeGreaterThanOrEqual(1)
      })
    })

    it('shows loading message while fetching', () => {
      renderHomePage()

      // Page has both mobile and desktop layouts
      const loadingMessages = screen.getAllByText(/loading recipes/i)
      expect(loadingMessages.length).toBeGreaterThanOrEqual(1)
    })
  })

  describe('Action Buttons', () => {
    it('renders Add Recipe link', async () => {
      renderHomePage()

      await waitFor(() => {
        const addLink = screen.getByRole('link', { name: /add recipe/i })
        expect(addLink).toHaveAttribute('href', '/recipes/new')
      })
    })

    it('renders Extract from Image link', async () => {
      renderHomePage()

      await waitFor(() => {
        const uploadLink = screen.getByRole('link', { name: /extract from image/i })
        expect(uploadLink).toHaveAttribute('href', '/upload')
      })
    })
  })

  describe('Recipe Loading', () => {
    it('loads recipes on mount', async () => {
      renderHomePage()

      await waitFor(() => {
        // Use getAllByText since recipe names may appear multiple times (name + template badge)
        expect(screen.getAllByText('Margarita').length).toBeGreaterThanOrEqual(1)
        expect(screen.getAllByText('Old Fashioned').length).toBeGreaterThanOrEqual(1)
      })
    })

    it('displays recipes in grid', async () => {
      renderHomePage()

      await waitFor(() => {
        const grid = document.querySelector('.grid')
        expect(grid).toBeInTheDocument()
      })
    })
  })

  describe('Filter Integration', () => {
    it('renders filter sidebar', async () => {
      renderHomePage()

      await waitFor(() => {
        expect(screen.getByText('Filters')).toBeInTheDocument()
      })
    })

    it('has search input that accepts text', async () => {
      const user = userEvent.setup()
      renderHomePage()

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/search recipes/i)).toBeInTheDocument()
      })

      const searchInput = screen.getByPlaceholderText(/search recipes/i)
      await user.type(searchInput, 'test')

      expect(searchInput).toHaveValue('test')
    })

    it('renders template filter dropdown', async () => {
      renderHomePage()

      await waitFor(() => {
        expect(screen.getByText('Template / Family')).toBeInTheDocument()
      })
    })
  })

  describe('Empty State', () => {
    it('shows empty message when no recipes match', async () => {
      const user = userEvent.setup()

      // Mock empty response for filtered search
      server.use(
        http.get(`${API_BASE}/recipes`, ({ request }) => {
          const url = new URL(request.url)
          const search = url.searchParams.get('search')
          if (search === 'nonexistent') {
            return HttpResponse.json([])
          }
          return HttpResponse.json([
            { id: '1', name: 'Margarita', template: 'sour', created_at: '2024-01-01' },
          ])
        }),
        http.get(`${API_BASE}/recipes/count`, ({ request }) => {
          const url = new URL(request.url)
          const search = url.searchParams.get('search')
          if (search === 'nonexistent') {
            return HttpResponse.json({ total: 1, filtered: 0 })
          }
          return HttpResponse.json({ total: 1, filtered: 1 })
        })
      )

      renderHomePage()

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/search recipes/i)).toBeInTheDocument()
      })

      const searchInput = screen.getByPlaceholderText(/search recipes/i)
      await user.clear(searchInput)
      await user.type(searchInput, 'nonexistent')

      await waitFor(() => {
        // Page has both mobile and desktop layouts
        const emptyMessages = screen.getAllByText(/no recipes found/i)
        expect(emptyMessages.length).toBeGreaterThanOrEqual(1)
      })
    })
  })

  describe('Singular/Plural Recipe Count', () => {
    it('shows singular when 1 recipe', async () => {
      server.use(
        http.get(`${API_BASE}/recipes`, () => {
          return HttpResponse.json([
            { id: '1', name: 'Margarita', created_at: '2024-01-01' },
          ])
        }),
        http.get(`${API_BASE}/recipes/count`, () => {
          return HttpResponse.json({ total: 1, filtered: 1 })
        })
      )

      renderHomePage()

      await waitFor(() => {
        // Page has both mobile and desktop layouts
        const counts = screen.getAllByText(/1 recipe/i)
        expect(counts.length).toBeGreaterThanOrEqual(1)
      })
    })

    it('shows plural when multiple recipes', async () => {
      renderHomePage()

      await waitFor(() => {
        // Page has both mobile and desktop layouts
        const counts = screen.getAllByText(/2 recipes/i)
        expect(counts.length).toBeGreaterThanOrEqual(1)
      })
    })
  })

  describe('Error Handling', () => {
    it('handles API error gracefully', async () => {
      // Suppress console.error for this test
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      server.use(
        http.get(`${API_BASE}/recipes`, () => {
          return HttpResponse.json({ detail: 'Server error' }, { status: 500 })
        }),
        http.get(`${API_BASE}/recipes/count`, () => {
          return HttpResponse.json({ detail: 'Server error' }, { status: 500 })
        })
      )

      renderHomePage()

      // Should not crash - the page should still render
      await waitFor(() => {
        // Page has both mobile and desktop layouts
        const headings = screen.getAllByRole('heading', { name: /cocktail recipes/i })
        expect(headings.length).toBeGreaterThanOrEqual(1)
      })

      consoleSpy.mockRestore()
    })
  })
})
