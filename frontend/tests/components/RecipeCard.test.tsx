import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { RecipeCard } from '@/components/recipes/RecipeCard'
import { RecipeListItem } from '@/lib/api'

const mockRecipe: RecipeListItem = {
  id: '1',
  name: 'Margarita',
  template: 'sour',
  main_spirit: 'tequila',
  glassware: 'coupe',
  serving_style: 'up',
  source_image_path: null,
  user_id: '1',
  created_at: '2024-01-01T00:00:00Z',
}

const mockRecipeWithImage: RecipeListItem = {
  ...mockRecipe,
  id: '2',
  name: 'Old Fashioned',
  source_image_path: '/uploads/old-fashioned.jpg',
}

const mockMinimalRecipe: RecipeListItem = {
  id: '3',
  name: 'Simple Cocktail',
  created_at: '2024-01-01T00:00:00Z',
}

describe('RecipeCard', () => {
  describe('Recipe Name', () => {
    it('renders recipe name', () => {
      render(<RecipeCard recipe={mockRecipe} />)

      expect(screen.getByText('Margarita')).toBeInTheDocument()
    })
  })

  describe('Image', () => {
    it('renders placeholder when no image', () => {
      render(<RecipeCard recipe={mockRecipe} />)

      // Check for the placeholder icon (GlassWater)
      const card = screen.getByRole('link')
      expect(card).toBeInTheDocument()
      // No img element should exist
      expect(screen.queryByRole('img')).not.toBeInTheDocument()
    })

    it('renders image when source_image_path exists', () => {
      render(<RecipeCard recipe={mockRecipeWithImage} />)

      const image = screen.getByRole('img')
      expect(image).toHaveAttribute('src', '/uploads/old-fashioned.jpg')
      expect(image).toHaveAttribute('alt', 'Old Fashioned')
    })
  })

  describe('Badges', () => {
    it('renders template badge', () => {
      render(<RecipeCard recipe={mockRecipe} />)

      expect(screen.getByText('Sour')).toBeInTheDocument()
    })

    it('renders main spirit badge', () => {
      render(<RecipeCard recipe={mockRecipe} />)

      expect(screen.getByText('Tequila')).toBeInTheDocument()
    })

    it('does not render badges when template/spirit are missing', () => {
      render(<RecipeCard recipe={mockMinimalRecipe} />)

      expect(screen.queryByText('Sour')).not.toBeInTheDocument()
      expect(screen.queryByText('Tequila')).not.toBeInTheDocument()
    })
  })

  describe('Glassware and Serving Style', () => {
    it('renders glassware', () => {
      render(<RecipeCard recipe={mockRecipe} />)

      expect(screen.getByText('Coupe')).toBeInTheDocument()
    })

    it('renders serving style', () => {
      render(<RecipeCard recipe={mockRecipe} />)

      expect(screen.getByText('Up')).toBeInTheDocument()
    })

    it('does not render when missing', () => {
      render(<RecipeCard recipe={mockMinimalRecipe} />)

      expect(screen.queryByText('Coupe')).not.toBeInTheDocument()
      expect(screen.queryByText('Up')).not.toBeInTheDocument()
    })
  })

  describe('Navigation', () => {
    it('links to recipe detail page', () => {
      render(<RecipeCard recipe={mockRecipe} />)

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
      render(<RecipeCard recipe={recipe} />)

      expect(screen.getByText('Old Fashioned')).toBeInTheDocument()
    })

    it('formats snake_case spirit to Title Case', () => {
      const recipe: RecipeListItem = {
        ...mockRecipe,
        main_spirit: 'white_rum',
      }
      render(<RecipeCard recipe={recipe} />)

      expect(screen.getByText('White Rum')).toBeInTheDocument()
    })
  })
})
