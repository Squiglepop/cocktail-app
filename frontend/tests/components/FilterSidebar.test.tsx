import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { FilterSidebar } from '@/components/recipes/FilterSidebar'
import { TestProviders, createTestQueryClient } from '../utils/test-utils'
import { QueryClient } from '@tanstack/react-query'

let queryClient: QueryClient

function renderFilterSidebar(props: Parameters<typeof FilterSidebar>[0]) {
  queryClient = createTestQueryClient()
  return render(
    <TestProviders queryClient={queryClient}>
      <FilterSidebar {...props} />
    </TestProviders>
  )
}

describe('FilterSidebar', () => {
  const mockOnFilterChange = vi.fn()

  const defaultFilters = {}

  beforeEach(() => {
    mockOnFilterChange.mockClear()
  })

  // Helper to get select by its preceding label text
  const getSelectByLabel = (labelText: string | RegExp) => {
    const label = screen.getByText(labelText)
    const container = label.closest('div')
    return container?.querySelector('select') as HTMLSelectElement
  }

  describe('Rendering', () => {
    it('renders all filter sections after loading', async () => {
      renderFilterSidebar({ filters: defaultFilters, onFilterChange: mockOnFilterChange })

      await waitFor(() => {
        expect(screen.getByText('Search')).toBeInTheDocument()
        expect(screen.getByText('Template / Family')).toBeInTheDocument()
        expect(screen.getByText('Main Spirit')).toBeInTheDocument()
        expect(screen.getByText('Glassware')).toBeInTheDocument()
        expect(screen.getByText('Serving Style')).toBeInTheDocument()
      })
    })

    it('shows loading skeleton initially', () => {
      renderFilterSidebar({ filters: defaultFilters, onFilterChange: mockOnFilterChange })

      // Should show loading skeleton
      const skeleton = document.querySelector('.animate-pulse')
      expect(skeleton).toBeInTheDocument()
    })

    it('renders Filters heading', async () => {
      renderFilterSidebar({ filters: defaultFilters, onFilterChange: mockOnFilterChange })

      await waitFor(() => {
        expect(screen.getByText('Filters')).toBeInTheDocument()
      })
    })
  })

  describe('Search Input', () => {
    it('renders search input', async () => {
      renderFilterSidebar({ filters: defaultFilters, onFilterChange: mockOnFilterChange })

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Search recipes...')).toBeInTheDocument()
      })
    })

    it('calls onFilterChange when typing in search', async () => {
      const user = userEvent.setup()

      renderFilterSidebar({ filters: defaultFilters, onFilterChange: mockOnFilterChange })

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Search recipes...')).toBeInTheDocument()
      })

      const searchInput = screen.getByPlaceholderText('Search recipes...')
      await user.type(searchInput, 'margarita')

      expect(mockOnFilterChange).toHaveBeenCalled()
      // Check last call contains search value
      const lastCall = mockOnFilterChange.mock.calls[mockOnFilterChange.mock.calls.length - 1][0]
      expect(lastCall.search).toContain('a') // At least partial match
    })

    it('displays current search value', async () => {
      renderFilterSidebar({
        filters: { search: 'mojito' },
        onFilterChange: mockOnFilterChange
      })

      await waitFor(() => {
        const searchInput = screen.getByPlaceholderText('Search recipes...')
        expect(searchInput).toHaveValue('mojito')
      })
    })
  })

  describe('Filter Selection', () => {
    it('calls onFilterChange when selecting template', async () => {
      const user = userEvent.setup()

      renderFilterSidebar({ filters: defaultFilters, onFilterChange: mockOnFilterChange })

      await waitFor(() => {
        expect(screen.getByText('Template / Family')).toBeInTheDocument()
      })

      const templateSelect = getSelectByLabel('Template / Family')
      await user.selectOptions(templateSelect, 'sour')

      expect(mockOnFilterChange).toHaveBeenCalledWith(
        expect.objectContaining({ template: 'sour' })
      )
    })

    it('calls onFilterChange when selecting spirit', async () => {
      const user = userEvent.setup()

      renderFilterSidebar({ filters: defaultFilters, onFilterChange: mockOnFilterChange })

      await waitFor(() => {
        expect(screen.getByText('Main Spirit')).toBeInTheDocument()
      })

      const spiritSelect = getSelectByLabel(/Main Spirit/i)
      await user.selectOptions(spiritSelect, 'vodka')

      expect(mockOnFilterChange).toHaveBeenCalledWith(
        expect.objectContaining({ main_spirit: 'vodka' })
      )
    })

    it('displays current filter values', async () => {
      renderFilterSidebar({
        filters: { template: 'sour', main_spirit: 'tequila' },
        onFilterChange: mockOnFilterChange
      })

      await waitFor(() => {
        const templateSelect = getSelectByLabel('Template / Family')
        expect(templateSelect).toHaveValue('sour')

        const spiritSelect = getSelectByLabel('Main Spirit')
        expect(spiritSelect).toHaveValue('tequila')
      })
    })
  })

  describe('Clear Filters', () => {
    it('shows clear button when filters are active', async () => {
      renderFilterSidebar({
        filters: { template: 'sour' },
        onFilterChange: mockOnFilterChange
      })

      await waitFor(() => {
        expect(screen.getByText('Clear all')).toBeInTheDocument()
      })
    })

    it('does not show clear button when no filters', async () => {
      renderFilterSidebar({ filters: defaultFilters, onFilterChange: mockOnFilterChange })

      await waitFor(() => {
        expect(screen.getByText('Filters')).toBeInTheDocument()
      })

      expect(screen.queryByText('Clear all')).not.toBeInTheDocument()
    })

    it('calls onFilterChange with empty object when clearing', async () => {
      const user = userEvent.setup()

      renderFilterSidebar({
        filters: { template: 'sour', main_spirit: 'vodka' },
        onFilterChange: mockOnFilterChange
      })

      await waitFor(() => {
        expect(screen.getByText('Clear all')).toBeInTheDocument()
      })

      await user.click(screen.getByText('Clear all'))

      expect(mockOnFilterChange).toHaveBeenCalledWith({})
    })
  })

  describe('Filter Dropdowns Options', () => {
    it('populates template options from categories', async () => {
      renderFilterSidebar({ filters: defaultFilters, onFilterChange: mockOnFilterChange })

      await waitFor(() => {
        expect(screen.getByText('Template / Family')).toBeInTheDocument()
      })

      // Check that options include values from mock categories
      expect(screen.getByText('All templates')).toBeInTheDocument()
      expect(screen.getByText('Sour')).toBeInTheDocument()
    })

    it('populates spirit options from categories', async () => {
      renderFilterSidebar({ filters: defaultFilters, onFilterChange: mockOnFilterChange })

      await waitFor(() => {
        expect(screen.getByText('All spirits')).toBeInTheDocument()
        expect(screen.getByText('Vodka')).toBeInTheDocument()
      })
    })

    it('populates glassware with grouped options', async () => {
      renderFilterSidebar({ filters: defaultFilters, onFilterChange: mockOnFilterChange })

      await waitFor(() => {
        expect(screen.getByText('All glassware')).toBeInTheDocument()
        expect(screen.getByText('Coupe')).toBeInTheDocument()
      })
    })

    it('populates serving styles from categories', async () => {
      renderFilterSidebar({ filters: defaultFilters, onFilterChange: mockOnFilterChange })

      await waitFor(() => {
        expect(screen.getByText('All styles')).toBeInTheDocument()
        expect(screen.getByText('Up')).toBeInTheDocument()
        expect(screen.getByText('Rocks')).toBeInTheDocument()
      })
    })
  })
})
