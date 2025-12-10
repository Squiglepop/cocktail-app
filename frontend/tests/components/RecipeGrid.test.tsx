import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { RecipeGrid } from '@/components/recipes/RecipeGrid'
import { RecipeListItem } from '@/lib/api'

const mockRecipes: RecipeListItem[] = [
  {
    id: '1',
    name: 'Margarita',
    template: 'sour',
    main_spirit: 'tequila',
    glassware: 'coupe',
    serving_style: 'up',
    source_image_path: null,
    user_id: '1',
    created_at: '2024-01-01T00:00:00Z',
  },
  {
    id: '2',
    name: 'Old Fashioned',
    template: 'old_fashioned',
    main_spirit: 'bourbon',
    glassware: 'rocks',
    serving_style: 'rocks',
    source_image_path: null,
    user_id: null,
    created_at: '2024-01-02T00:00:00Z',
  },
  {
    id: '3',
    name: 'Martini',
    template: 'martini',
    main_spirit: 'gin',
    glassware: 'martini',
    serving_style: 'up',
    source_image_path: null,
    user_id: '1',
    created_at: '2024-01-03T00:00:00Z',
  },
]

describe('RecipeGrid', () => {
  describe('Rendering Recipes', () => {
    it('renders recipe cards for each recipe', () => {
      render(<RecipeGrid recipes={mockRecipes} />)

      // Recipe names may appear multiple times due to template badges (e.g., "Old Fashioned", "Martini")
      expect(screen.getAllByText('Margarita').length).toBeGreaterThanOrEqual(1)
      expect(screen.getAllByText('Old Fashioned').length).toBeGreaterThanOrEqual(1)
      expect(screen.getAllByText('Martini').length).toBeGreaterThanOrEqual(1)
    })

    it('renders correct number of cards', () => {
      render(<RecipeGrid recipes={mockRecipes} />)

      const links = screen.getAllByRole('link')
      expect(links).toHaveLength(3)
    })
  })

  describe('Loading State', () => {
    it('shows loading skeleton when loading', () => {
      render(<RecipeGrid recipes={[]} loading={true} />)

      // Should show skeleton cards with animate-pulse
      const skeletons = document.querySelectorAll('.animate-pulse')
      expect(skeletons.length).toBeGreaterThan(0)
    })

    it('shows 6 skeleton cards', () => {
      render(<RecipeGrid recipes={[]} loading={true} />)

      const skeletons = document.querySelectorAll('.animate-pulse')
      expect(skeletons).toHaveLength(6)
    })

    it('does not show recipes when loading', () => {
      render(<RecipeGrid recipes={mockRecipes} loading={true} />)

      expect(screen.queryByText('Margarita')).not.toBeInTheDocument()
    })
  })

  describe('Empty State', () => {
    it('shows empty message when no recipes', () => {
      render(<RecipeGrid recipes={[]} />)

      expect(screen.getByText('No recipes found')).toBeInTheDocument()
    })

    it('shows helpful message in empty state', () => {
      render(<RecipeGrid recipes={[]} />)

      expect(
        screen.getByText(/try adjusting your filters or upload a new recipe/i)
      ).toBeInTheDocument()
    })

    it('does not show empty state when loading', () => {
      render(<RecipeGrid recipes={[]} loading={true} />)

      expect(screen.queryByText('No recipes found')).not.toBeInTheDocument()
    })
  })

  describe('Grid Layout', () => {
    it('renders grid container', () => {
      render(<RecipeGrid recipes={mockRecipes} />)

      const grid = document.querySelector('.grid')
      expect(grid).toBeInTheDocument()
    })
  })
})
