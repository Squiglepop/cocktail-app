import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import UploadPage from '@/app/upload/page'
import { AuthProvider } from '@/lib/auth-context'
import { mockRecipeDetail } from '../mocks/handlers'

// Mock useRouter
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
  usePathname: () => '/upload',
  useSearchParams: () => new URLSearchParams(),
}))

// Mock UploadDropzone component to control when recipe is extracted
let mockOnRecipeExtracted: ((recipe: typeof mockRecipeDetail) => void) | null = null

vi.mock('@/components/upload/UploadDropzone', () => ({
  UploadDropzone: ({ onRecipeExtracted }: { onRecipeExtracted: (recipe: typeof mockRecipeDetail) => void }) => {
    mockOnRecipeExtracted = onRecipeExtracted
    return <div data-testid="upload-dropzone">UploadDropzone Component</div>
  },
}))

function renderUploadPage() {
  return render(
    <AuthProvider>
      <UploadPage />
    </AuthProvider>
  )
}

describe('UploadPage', () => {
  beforeEach(() => {
    mockPush.mockClear()
    mockOnRecipeExtracted = null
    vi.mocked(localStorage.getItem).mockReturnValue(null)
  })

  describe('Rendering', () => {
    it('renders page title and description', () => {
      renderUploadPage()

      expect(screen.getByRole('heading', { name: /upload recipe/i })).toBeInTheDocument()
      // Text appears multiple times (in description and tips), check for at least one
      expect(screen.getAllByText(/upload a screenshot/i).length).toBeGreaterThanOrEqual(1)
    })

    it('renders UploadDropzone component', () => {
      renderUploadPage()

      expect(screen.getByTestId('upload-dropzone')).toBeInTheDocument()
    })

    it('shows empty state placeholder before extraction', () => {
      renderUploadPage()

      // "Extracted Recipe" appears as heading, check for at least one
      expect(screen.getAllByText(/extracted recipe/i).length).toBeGreaterThanOrEqual(1)
      expect(screen.getByText(/upload a screenshot to see the extracted recipe here/i)).toBeInTheDocument()
    })

    it('renders "Ways to add recipes" section', () => {
      renderUploadPage()

      expect(screen.getByRole('heading', { name: /ways to add recipes/i })).toBeInTheDocument()
      // Use getAllByText for elements that may appear multiple times
      expect(screen.getAllByText(/paste/i).length).toBeGreaterThanOrEqual(1)
      expect(screen.getAllByText(/drop/i).length).toBeGreaterThanOrEqual(1)
      expect(screen.getAllByText(/url/i).length).toBeGreaterThanOrEqual(1)
      expect(screen.getAllByText(/browse/i).length).toBeGreaterThanOrEqual(1)
    })

    it('renders "Tips for best results" section', () => {
      renderUploadPage()

      expect(screen.getByRole('heading', { name: /tips for best results/i })).toBeInTheDocument()
      expect(screen.getByText(/clear text/i)).toBeInTheDocument()
      expect(screen.getByText(/full recipe/i)).toBeInTheDocument()
      expect(screen.getByText(/good quality/i)).toBeInTheDocument()
    })
  })

  describe('Extracted Recipe Preview', () => {
    it('displays recipe preview after extraction', async () => {
      renderUploadPage()

      // Simulate recipe extraction
      mockOnRecipeExtracted?.(mockRecipeDetail)

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: mockRecipeDetail.name })).toBeInTheDocument()
      })
    })

    it('shows recipe name and description', async () => {
      renderUploadPage()

      mockOnRecipeExtracted?.(mockRecipeDetail)

      await waitFor(() => {
        expect(screen.getByText(mockRecipeDetail.name)).toBeInTheDocument()
      })

      expect(screen.getByText(mockRecipeDetail.description!)).toBeInTheDocument()
    })

    it('shows template and spirit badges', async () => {
      renderUploadPage()

      mockOnRecipeExtracted?.(mockRecipeDetail)

      await waitFor(() => {
        expect(screen.getByText(/sour/i)).toBeInTheDocument()
      })

      // Tequila appears both as spirit badge and in ingredients
      expect(screen.getAllByText(/tequila/i).length).toBeGreaterThanOrEqual(1)
    })

    it('renders ingredients list', async () => {
      renderUploadPage()

      mockOnRecipeExtracted?.(mockRecipeDetail)

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /ingredients/i })).toBeInTheDocument()
      })

      // Check that ingredients are displayed - Tequila appears multiple times
      expect(screen.getAllByText(/tequila/i).length).toBeGreaterThanOrEqual(1)
      expect(screen.getByText(/lime juice/i)).toBeInTheDocument()
    })

    it('shows "No ingredients extracted" when empty', async () => {
      renderUploadPage()

      mockOnRecipeExtracted?.({
        ...mockRecipeDetail,
        ingredients: [],
      })

      await waitFor(() => {
        expect(screen.getByText(/no ingredients extracted/i)).toBeInTheDocument()
      })
    })

    it('shows garnish when present', async () => {
      renderUploadPage()

      mockOnRecipeExtracted?.(mockRecipeDetail)

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /garnish/i })).toBeInTheDocument()
      })

      expect(screen.getByText(mockRecipeDetail.garnish!)).toBeInTheDocument()
    })

    it('View Full Recipe link has correct href', async () => {
      renderUploadPage()

      mockOnRecipeExtracted?.(mockRecipeDetail)

      await waitFor(() => {
        expect(screen.getByRole('link', { name: /view full recipe/i })).toBeInTheDocument()
      })

      const viewLink = screen.getByRole('link', { name: /view full recipe/i })
      expect(viewLink).toHaveAttribute('href', `/recipes/${mockRecipeDetail.id}`)
    })
  })
})
