import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { RecipeCard } from '@/components/recipes/RecipeCard'
import { RecipeListItem } from '@/lib/api'
import { AuthProvider } from '@/lib/auth-context'
import { FavouritesProvider } from '@/lib/favourites-context'
import { OfflineProvider } from '@/lib/offline-context'
import { ListStateProvider } from '@/lib/list-state-context'
import { QueryClientProvider, QueryClient } from '@tanstack/react-query'
import { server } from '../mocks/server'
import { http, HttpResponse } from 'msw'

const API_BASE = '*/api'

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
    prefetch: vi.fn(),
  }),
  usePathname: () => '/',
  useSearchParams: () => new URLSearchParams(),
}))

function renderRecipeCard(recipe: RecipeListItem) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <FavouritesProvider>
          <OfflineProvider>
            <ListStateProvider>
              <RecipeCard recipe={recipe} />
            </ListStateProvider>
          </OfflineProvider>
        </FavouritesProvider>
      </AuthProvider>
    </QueryClientProvider>
  )
}

const mockRecipe: RecipeListItem = {
  id: '1',
  name: 'Margarita',
  template: 'sour',
  main_spirit: 'tequila',
  glassware: 'coupe',
  serving_style: 'up',
  has_image: false,
  user_id: '1',
  visibility: 'public',
  created_at: '2024-01-01T00:00:00Z',
}

const mockRecipeWithImage: RecipeListItem = {
  ...mockRecipe,
  id: '2',
  name: 'Old Fashioned',
  has_image: true,
}

const mockMinimalRecipe: RecipeListItem = {
  id: '3',
  name: 'Simple Cocktail',
  has_image: false,
  visibility: 'public',
  created_at: '2024-01-01T00:00:00Z',
}

describe('RecipeCard', () => {
  beforeEach(() => {
    // Default: no stored session (refresh returns 401)
    server.use(
      http.post(`${API_BASE}/auth/refresh`, () => {
        return HttpResponse.json(
          { detail: 'No refresh token provided' },
          { status: 401 }
        )
      })
    )
  })

  describe('Recipe Name', () => {
    it('renders recipe name', () => {
      renderRecipeCard(mockRecipe)

      expect(screen.getByText('Margarita')).toBeInTheDocument()
    })
  })

  describe('Image', () => {
    it('renders placeholder when no image', () => {
      renderRecipeCard(mockRecipe)

      // Check for the placeholder icon (GlassWater)
      const card = screen.getByRole('link')
      expect(card).toBeInTheDocument()
      // No img element should exist
      expect(screen.queryByRole('img')).not.toBeInTheDocument()
    })

    it('renders image when has_image is true', () => {
      renderRecipeCard(mockRecipeWithImage)

      const image = screen.getByRole('img')
      // Image URL is wrapped by Next.js Image component with URL encoding
      // Check for URL-encoded version of /recipes/2/image
      expect(image.getAttribute('src')).toContain('recipes%2F2%2Fimage')
      expect(image).toHaveAttribute('alt', 'Old Fashioned')
    })
  })

  describe('Badges', () => {
    it('renders template badge', () => {
      renderRecipeCard(mockRecipe)

      expect(screen.getByText('Sour')).toBeInTheDocument()
    })

    it('renders main spirit badge', () => {
      renderRecipeCard(mockRecipe)

      expect(screen.getByText('Tequila')).toBeInTheDocument()
    })

    it('does not render badges when template/spirit are missing', () => {
      renderRecipeCard(mockMinimalRecipe)

      expect(screen.queryByText('Sour')).not.toBeInTheDocument()
      expect(screen.queryByText('Tequila')).not.toBeInTheDocument()
    })
  })

  describe('Glassware and Serving Style', () => {
    it('renders glassware icon with title', () => {
      renderRecipeCard(mockRecipe)

      expect(screen.getByTitle('Coupe')).toBeInTheDocument()
    })

    it('does not render glassware when missing', () => {
      renderRecipeCard(mockMinimalRecipe)

      expect(screen.queryByTitle('Coupe')).not.toBeInTheDocument()
    })
  })

  describe('Navigation', () => {
    it('links to recipe detail page', () => {
      renderRecipeCard(mockRecipe)

      const link = screen.getByRole('link')
      expect(link).toHaveAttribute('href', '/recipes/1')
    })
  })

  describe('Enum Formatting', () => {
    it('formats snake_case template to Title Case', () => {
      const recipe: RecipeListItem = {
        ...mockRecipe,
        template: 'old_fashioned',
      }
      renderRecipeCard(recipe)

      expect(screen.getByText('Old Fashioned')).toBeInTheDocument()
    })

    it('formats snake_case spirit to Title Case', () => {
      const recipe: RecipeListItem = {
        ...mockRecipe,
        main_spirit: 'white_rum',
      }
      renderRecipeCard(recipe)

      expect(screen.getByText('White Rum')).toBeInTheDocument()
    })
  })
})
