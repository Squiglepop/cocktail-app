import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest'
import { server } from '../mocks/server'
import { http, HttpResponse } from 'msw'
import {
  API_BASE,
  fetchCategories,
  fetchRecipes,
  fetchRecipe,
  createRecipe,
  updateRecipe,
  deleteRecipe,
  uploadAndExtract,
  formatEnumValue,
  formatUnit,
} from '@/lib/api'

const API_BASE_PATTERN = '*/api'

describe('API_BASE Configuration', () => {
  it('defaults to localhost:8000/api when NEXT_PUBLIC_API_URL is not set', () => {
    // When NEXT_PUBLIC_API_URL is not set, API_BASE should default to localhost
    // This ensures safe development behavior - never accidentally hitting production
    const expectedDefault = 'http://localhost:8000/api'
    const envValue = process.env.NEXT_PUBLIC_API_URL

    if (!envValue) {
      expect(API_BASE).toBe(expectedDefault)
    } else {
      // If env var is set, API_BASE should equal the env value
      expect(API_BASE).toBe(envValue)
    }
  })

  it('API_BASE is a valid URL', () => {
    // Verify the URL is parseable - this catches malformed URLs
    expect(() => new URL(API_BASE)).not.toThrow()
  })
})

describe('API Client', () => {
  describe('fetchCategories', () => {
    it('returns categories successfully', async () => {
      const categories = await fetchCategories()

      expect(categories).toBeDefined()
      expect(categories.templates).toBeDefined()
      expect(categories.spirits).toBeDefined()
      expect(categories.glassware).toBeDefined()
      expect(categories.serving_styles).toBeDefined()
      expect(categories.methods).toBeDefined()
    })

    it('throws error on failure', async () => {
      server.use(
        http.get(`${API_BASE_PATTERN}/categories`, () => {
          return HttpResponse.json({ detail: 'Server error' }, { status: 500 })
        })
      )

      await expect(fetchCategories()).rejects.toThrow('Failed to fetch categories')
    })
  })

  describe('fetchRecipes', () => {
    it('returns all recipes without filters', async () => {
      const recipes = await fetchRecipes()

      expect(recipes).toBeDefined()
      expect(Array.isArray(recipes)).toBe(true)
      expect(recipes.length).toBeGreaterThan(0)
    })

    it('filters recipes by template', async () => {
      const recipes = await fetchRecipes({ template: 'sour' })

      expect(recipes).toBeDefined()
      recipes.forEach((recipe) => {
        expect(recipe.template).toBe('sour')
      })
    })

    it('filters recipes by main_spirit', async () => {
      const recipes = await fetchRecipes({ main_spirit: 'bourbon' })

      expect(recipes).toBeDefined()
      recipes.forEach((recipe) => {
        expect(recipe.main_spirit).toBe('bourbon')
      })
    })

    it('filters recipes by search term', async () => {
      const recipes = await fetchRecipes({ search: 'Margarita' })

      expect(recipes).toBeDefined()
      expect(recipes.length).toBe(1)
      expect(recipes[0].name).toBe('Margarita')
    })

    it('throws error on failure', async () => {
      server.use(
        http.get(`${API_BASE_PATTERN}/recipes`, () => {
          return HttpResponse.json({ detail: 'Server error' }, { status: 500 })
        })
      )

      await expect(fetchRecipes()).rejects.toThrow('Failed to fetch recipes')
    })
  })

  describe('fetchRecipe', () => {
    it('returns single recipe with ingredients', async () => {
      const recipe = await fetchRecipe('1')

      expect(recipe).toBeDefined()
      expect(recipe.id).toBe('1')
      expect(recipe.name).toBe('Margarita')
      expect(recipe.ingredients).toBeDefined()
      expect(Array.isArray(recipe.ingredients)).toBe(true)
    })

    it('throws error for non-existent recipe', async () => {
      await expect(fetchRecipe('non-existent')).rejects.toThrow('Recipe not found')
    })
  })

  describe('createRecipe', () => {
    it('creates recipe without token', async () => {
      const recipe = await createRecipe({ name: 'New Cocktail' })

      expect(recipe).toBeDefined()
      expect(recipe.name).toBe('New Cocktail')
      expect(recipe.user_id).toBeNull()
    })

    it('creates recipe with token', async () => {
      const recipe = await createRecipe({ name: 'Auth Cocktail' }, 'mock-jwt-token')

      expect(recipe).toBeDefined()
      expect(recipe.name).toBe('Auth Cocktail')
      expect(recipe.user_id).toBe('1')
    })

    it('creates recipe with all fields', async () => {
      const recipe = await createRecipe({
        name: 'Full Cocktail',
        description: 'Full description',
        instructions: 'Step by step',
        template: 'sour',
        main_spirit: 'vodka',
        glassware: 'coupe',
        serving_style: 'up',
        method: 'shaken',
        garnish: 'Lime',
        notes: 'Notes here',
        ingredients: [
          { ingredient_name: 'Vodka', amount: 2, unit: 'oz' },
        ],
      })

      expect(recipe).toBeDefined()
      expect(recipe.name).toBe('Full Cocktail')
    })

    it('throws error on failure', async () => {
      server.use(
        http.post(`${API_BASE_PATTERN}/recipes`, () => {
          return HttpResponse.json({ detail: 'Validation error' }, { status: 422 })
        })
      )

      await expect(createRecipe({ name: '' })).rejects.toThrow('Validation error')
    })
  })

  describe('updateRecipe', () => {
    it('updates recipe successfully', async () => {
      const recipe = await updateRecipe('1', { name: 'Updated Name' }, 'mock-jwt-token')

      expect(recipe).toBeDefined()
      expect(recipe.name).toBe('Updated Name')
    })

    it('throws error without auth for owned recipe', async () => {
      await expect(updateRecipe('1', { name: 'Hacked' })).rejects.toThrow()
    })

    it('throws error for non-existent recipe', async () => {
      await expect(
        updateRecipe('non-existent', { name: 'Test' }, 'mock-jwt-token')
      ).rejects.toThrow('Recipe not found')
    })
  })

  describe('deleteRecipe', () => {
    it('deletes recipe successfully', async () => {
      await expect(deleteRecipe('1', 'mock-jwt-token')).resolves.toBeUndefined()
    })

    it('throws error without auth for owned recipe', async () => {
      await expect(deleteRecipe('1')).rejects.toThrow()
    })

    it('throws error for non-existent recipe', async () => {
      await expect(deleteRecipe('non-existent', 'mock-jwt-token')).rejects.toThrow(
        'Recipe not found'
      )
    })
  })

  describe('uploadAndExtract', () => {
    it('uploads and extracts recipe', async () => {
      const file = new File(['test'], 'test.png', { type: 'image/png' })
      const recipe = await uploadAndExtract(file)

      expect(recipe).toBeDefined()
      expect(recipe.name).toBe('Immediate Extraction')
      expect(recipe.source_type).toBe('screenshot')
    })

    it('uploads with token', async () => {
      const file = new File(['test'], 'test.png', { type: 'image/png' })
      const recipe = await uploadAndExtract(file, 'mock-jwt-token')

      expect(recipe).toBeDefined()
    })

    it('throws error on failure', async () => {
      server.use(
        http.post(`${API_BASE_PATTERN}/upload/extract-immediate`, () => {
          return HttpResponse.json({ detail: 'Extraction failed' }, { status: 500 })
        })
      )

      const file = new File(['test'], 'test.png', { type: 'image/png' })
      await expect(uploadAndExtract(file)).rejects.toThrow('Extraction failed')
    })
  })
})

describe('Format Helpers', () => {
  describe('formatEnumValue', () => {
    it('converts snake_case to Title Case', () => {
      expect(formatEnumValue('old_fashioned')).toBe('Old Fashioned')
      expect(formatEnumValue('white_rum')).toBe('White Rum')
    })

    it('handles single word', () => {
      expect(formatEnumValue('sour')).toBe('Sour')
      expect(formatEnumValue('vodka')).toBe('Vodka')
    })

    it('returns empty string for undefined/null', () => {
      expect(formatEnumValue(undefined)).toBe('')
      expect(formatEnumValue('')).toBe('')
    })
  })

  describe('formatUnit', () => {
    it('returns standard units as-is', () => {
      expect(formatUnit('oz')).toBe('oz')
      expect(formatUnit('ml')).toBe('ml')
      expect(formatUnit('tsp')).toBe('tsp')
    })

    it('handles singular/plural for dashes', () => {
      expect(formatUnit('dash', 1)).toBe('dash')
      expect(formatUnit('dash', 2)).toBe('dashes')
    })

    it('handles singular/plural for drops', () => {
      expect(formatUnit('drop', 1)).toBe('drop')
      expect(formatUnit('drop', 3)).toBe('drops')
    })

    it('handles singular/plural for barspoons', () => {
      expect(formatUnit('barspoon', 1)).toBe('barspoon')
      expect(formatUnit('barspoon', 2)).toBe('barspoons')
    })

    it('handles singular/plural for wedges', () => {
      expect(formatUnit('wedge', 1)).toBe('wedge')
      expect(formatUnit('wedge', 2)).toBe('wedges')
    })

    it('handles singular/plural for slices', () => {
      expect(formatUnit('slice', 1)).toBe('slice')
      expect(formatUnit('slice', 4)).toBe('slices')
    })

    it('handles singular/plural for sprigs', () => {
      expect(formatUnit('sprig', 1)).toBe('sprig')
      expect(formatUnit('sprig', 2)).toBe('sprigs')
    })

    it('handles singular/plural for leaves', () => {
      expect(formatUnit('leaf', 1)).toBe('leaf')
      expect(formatUnit('leaf', 6)).toBe('leaves')
    })

    it('returns empty string for undefined/null', () => {
      expect(formatUnit(undefined)).toBe('')
    })

    it('returns unknown units as-is', () => {
      expect(formatUnit('custom_unit')).toBe('custom_unit')
    })
  })
})
