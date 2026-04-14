import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { UploadDropzone } from '@/components/upload/UploadDropzone'
import { AuthProvider } from '@/lib/auth-context'
import { server } from '../mocks/server'
import { http, HttpResponse } from 'msw'

const API_BASE = '*/api'

// Wrapper with auth provider
function renderUploadDropzone(
  onRecipeExtracted = vi.fn(),
  enhanceRecipeId?: string,
  onEnhanceComplete = vi.fn()
) {
  return render(
    <AuthProvider>
      <UploadDropzone
        onRecipeExtracted={onRecipeExtracted}
        enhanceRecipeId={enhanceRecipeId}
        onEnhanceComplete={onEnhanceComplete}
      />
    </AuthProvider>
  )
}

describe('UploadDropzone', () => {
  const mockOnRecipeExtracted = vi.fn()

  beforeEach(() => {
    mockOnRecipeExtracted.mockClear()
    vi.mocked(localStorage.getItem).mockReturnValue(null)
  })

  describe('Initial Rendering', () => {
    it('renders dropzone area', async () => {
      renderUploadDropzone(mockOnRecipeExtracted)

      await waitFor(() => {
        expect(
          screen.getByText(/upload a cocktail recipe screenshot/i)
        ).toBeInTheDocument()
      })
    })

    it('renders input mode toggle buttons', async () => {
      renderUploadDropzone(mockOnRecipeExtracted)

      await waitFor(() => {
        expect(screen.getByText(/drop \/ paste/i)).toBeInTheDocument()
        expect(screen.getByText(/from url/i)).toBeInTheDocument()
      })
    })

    it('shows supported formats', async () => {
      renderUploadDropzone(mockOnRecipeExtracted)

      await waitFor(() => {
        expect(screen.getByText(/supports jpg, png, gif, webp/i)).toBeInTheDocument()
      })
    })

    it('shows paste instruction', async () => {
      renderUploadDropzone(mockOnRecipeExtracted)

      await waitFor(() => {
        expect(screen.getByText(/paste from clipboard/i)).toBeInTheDocument()
      })
    })
  })

  describe('Drop Mode', () => {
    it('starts in drop mode by default', async () => {
      renderUploadDropzone(mockOnRecipeExtracted)

      await waitFor(() => {
        expect(
          screen.getByText(/upload a cocktail recipe screenshot/i)
        ).toBeInTheDocument()
      })
    })

    it('shows dropzone file input', async () => {
      renderUploadDropzone(mockOnRecipeExtracted)

      await waitFor(() => {
        const input = document.querySelector('input[type="file"]')
        expect(input).toBeInTheDocument()
      })
    })
  })

  describe('URL Mode', () => {
    it('switches to URL mode when clicking button', async () => {
      const user = userEvent.setup()
      renderUploadDropzone(mockOnRecipeExtracted)

      await waitFor(() => {
        expect(screen.getByText(/from url/i)).toBeInTheDocument()
      })

      await user.click(screen.getByText(/from url/i))

      expect(screen.getByPlaceholderText(/https:\/\/example.com/i)).toBeInTheDocument()
    })

    it('renders URL input and submit button', async () => {
      const user = userEvent.setup()
      renderUploadDropzone(mockOnRecipeExtracted)

      await waitFor(() => {
        expect(screen.getByText(/from url/i)).toBeInTheDocument()
      })

      await user.click(screen.getByText(/from url/i))

      expect(screen.getByRole('button', { name: /extract/i })).toBeInTheDocument()
    })

    it('disables Extract button when URL is empty', async () => {
      const user = userEvent.setup()
      renderUploadDropzone(mockOnRecipeExtracted)

      await waitFor(() => {
        expect(screen.getByText(/from url/i)).toBeInTheDocument()
      })

      await user.click(screen.getByText(/from url/i))

      const extractButton = screen.getByRole('button', { name: /extract/i })
      expect(extractButton).toBeDisabled()
    })
  })

  describe('Upload States', () => {
    it('shows loading state during upload', async () => {
      // Add a delay to the mock response to see loading state
      server.use(
        http.post(`${API_BASE}/upload/extract-immediate`, async () => {
          await new Promise((resolve) => setTimeout(resolve, 100))
          return HttpResponse.json({
            id: '5',
            name: 'Extracted Recipe',
            ingredients: [],
            source_type: 'screenshot',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          })
        })
      )

      renderUploadDropzone(mockOnRecipeExtracted)

      // Simulate file drop
      const file = new File(['test'], 'test.png', { type: 'image/png' })
      const input = document.querySelector('input[type="file"]') as HTMLInputElement

      await waitFor(() => {
        expect(input).toBeInTheDocument()
      })

      Object.defineProperty(input, 'files', {
        value: [file],
      })

      fireEvent.change(input)

      // Check for loading state
      await waitFor(() => {
        expect(screen.getByText(/extracting recipe with ai/i)).toBeInTheDocument()
      })
    })

    it('shows success state after successful upload', async () => {
      renderUploadDropzone(mockOnRecipeExtracted)

      const file = new File(['test'], 'test.png', { type: 'image/png' })
      const input = document.querySelector('input[type="file"]') as HTMLInputElement

      await waitFor(() => {
        expect(input).toBeInTheDocument()
      })

      Object.defineProperty(input, 'files', {
        value: [file],
      })

      fireEvent.change(input)

      await waitFor(() => {
        expect(screen.getByText(/recipe extracted successfully/i)).toBeInTheDocument()
      })
    })

    it('calls onRecipeExtracted on success', async () => {
      renderUploadDropzone(mockOnRecipeExtracted)

      const file = new File(['test'], 'test.png', { type: 'image/png' })
      const input = document.querySelector('input[type="file"]') as HTMLInputElement

      await waitFor(() => {
        expect(input).toBeInTheDocument()
      })

      Object.defineProperty(input, 'files', {
        value: [file],
      })

      fireEvent.change(input)

      await waitFor(() => {
        expect(mockOnRecipeExtracted).toHaveBeenCalled()
      })
    })

    it('shows error state on failure', async () => {
      server.use(
        http.post(`${API_BASE}/upload/extract-immediate`, () => {
          return HttpResponse.json({ detail: 'Extraction failed' }, { status: 500 })
        })
      )

      renderUploadDropzone(mockOnRecipeExtracted)

      const file = new File(['test'], 'test.png', { type: 'image/png' })
      const input = document.querySelector('input[type="file"]') as HTMLInputElement

      await waitFor(() => {
        expect(input).toBeInTheDocument()
      })

      Object.defineProperty(input, 'files', {
        value: [file],
      })

      fireEvent.change(input)

      await waitFor(() => {
        expect(screen.getByText(/failed to extract recipe/i)).toBeInTheDocument()
      })
    })

    it('shows error message on failure', async () => {
      server.use(
        http.post(`${API_BASE}/upload/extract-immediate`, () => {
          return HttpResponse.json({ detail: 'No recipe found in image' }, { status: 500 })
        })
      )

      renderUploadDropzone(mockOnRecipeExtracted)

      const file = new File(['test'], 'test.png', { type: 'image/png' })
      const input = document.querySelector('input[type="file"]') as HTMLInputElement

      await waitFor(() => {
        expect(input).toBeInTheDocument()
      })

      Object.defineProperty(input, 'files', {
        value: [file],
      })

      fireEvent.change(input)

      await waitFor(() => {
        expect(screen.getByText(/no recipe found in image/i)).toBeInTheDocument()
      })
    })
  })

  describe('Back-Navigation Regression (Story 8.2)', () => {
    it('stays in success state when enhanceRecipeId changes to undefined after success', async () => {
      // Set up enhance endpoint
      server.use(
        http.post(`${API_BASE}/upload/enhance/*`, () => {
          return HttpResponse.json({
            id: '5',
            name: 'Enhanced Recipe',
            ingredients: [],
            source_type: 'screenshot',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          })
        })
      )

      const onEnhanceComplete = vi.fn()
      const { rerender } = renderUploadDropzone(vi.fn(), 'some-uuid', onEnhanceComplete)

      // Trigger file upload to reach success state
      const file = new File(['test'], 'test.png', { type: 'image/png' })
      const input = document.querySelector('input[type="file"]') as HTMLInputElement

      await waitFor(() => {
        expect(input).toBeInTheDocument()
      })

      Object.defineProperty(input, 'files', { value: [file] })
      fireEvent.change(input)

      await waitFor(() => {
        expect(screen.getByText(/recipe enhanced successfully/i)).toBeInTheDocument()
      })

      // Simulate back-navigation: enhanceRecipeId goes to undefined
      rerender(
        <AuthProvider>
          <UploadDropzone
            onRecipeExtracted={vi.fn()}
            enhanceRecipeId={undefined}
            onEnhanceComplete={onEnhanceComplete}
          />
        </AuthProvider>
      )

      // Should still show success, NOT error
      expect(screen.getByText(/recipe enhanced successfully/i)).toBeInTheDocument()
      expect(screen.queryByText(/failed/i)).not.toBeInTheDocument()
    })

    it('processFiles is a no-op when state is success', async () => {
      renderUploadDropzone(vi.fn())

      // Trigger file upload to reach success state
      const file = new File(['test'], 'test.png', { type: 'image/png' })
      const input = document.querySelector('input[type="file"]') as HTMLInputElement

      await waitFor(() => {
        expect(input).toBeInTheDocument()
      })

      Object.defineProperty(input, 'files', { value: [file] })
      fireEvent.change(input)

      await waitFor(() => {
        expect(screen.getByText(/recipe extracted successfully/i)).toBeInTheDocument()
      })

      // Try to paste another image while in success state — should be a no-op
      const pasteFile = new File(['test2'], 'test2.png', { type: 'image/png' })
      const dataTransfer = {
        items: [{
          type: 'image/png',
          getAsFile: () => pasteFile,
        }],
      }

      const pasteEvent = new Event('paste', { bubbles: true })
      Object.defineProperty(pasteEvent, 'clipboardData', { value: dataTransfer })
      document.dispatchEvent(pasteEvent)

      // Should still show success — no state change
      await waitFor(() => {
        expect(screen.getByText(/recipe extracted successfully/i)).toBeInTheDocument()
      })
      expect(screen.queryByText(/failed/i)).not.toBeInTheDocument()
    })

    it('processFiles is a no-op when state is error', async () => {
      server.use(
        http.post(`${API_BASE}/upload/extract-immediate`, () => {
          return HttpResponse.json({ detail: 'Extraction failed' }, { status: 500 })
        })
      )

      renderUploadDropzone(vi.fn())

      const file = new File(['test'], 'test.png', { type: 'image/png' })
      const input = document.querySelector('input[type="file"]') as HTMLInputElement

      await waitFor(() => {
        expect(input).toBeInTheDocument()
      })

      Object.defineProperty(input, 'files', { value: [file] })
      fireEvent.change(input)

      await waitFor(() => {
        expect(screen.getByText(/failed to extract recipe/i)).toBeInTheDocument()
      })

      // Try to paste another image while in error state — should be a no-op
      const pasteFile = new File(['test2'], 'test2.png', { type: 'image/png' })
      const dataTransfer = {
        items: [{
          type: 'image/png',
          getAsFile: () => pasteFile,
        }],
      }

      const pasteEvent = new Event('paste', { bubbles: true })
      Object.defineProperty(pasteEvent, 'clipboardData', { value: dataTransfer })
      document.dispatchEvent(pasteEvent)

      // Should still show error — no state change to uploading
      await waitFor(() => {
        expect(screen.getByText(/failed to extract recipe/i)).toBeInTheDocument()
      })
    })

    it('rerender with enhanceRecipeId=undefined after success does not show error', async () => {
      // This tests the full back-navigation scenario with normal upload (not enhance)
      const onRecipeExtracted = vi.fn()
      const { rerender } = renderUploadDropzone(onRecipeExtracted)

      const file = new File(['test'], 'test.png', { type: 'image/png' })
      const input = document.querySelector('input[type="file"]') as HTMLInputElement

      await waitFor(() => {
        expect(input).toBeInTheDocument()
      })

      Object.defineProperty(input, 'files', { value: [file] })
      fireEvent.change(input)

      await waitFor(() => {
        expect(screen.getByText(/recipe extracted successfully/i)).toBeInTheDocument()
      })

      // Simulate the component being rerendered with explicit undefined enhanceRecipeId
      // (as would happen during back-navigation)
      rerender(
        <AuthProvider>
          <UploadDropzone
            onRecipeExtracted={onRecipeExtracted}
            enhanceRecipeId={undefined}
            onEnhanceComplete={vi.fn()}
          />
        </AuthProvider>
      )

      // Should still show success, NOT error
      expect(screen.getByText(/recipe extracted successfully/i)).toBeInTheDocument()
      expect(screen.queryByText(/failed/i)).not.toBeInTheDocument()
    })
  })

  describe('Reset Functionality', () => {
    it('shows Upload Another button after success', async () => {
      renderUploadDropzone(mockOnRecipeExtracted)

      const file = new File(['test'], 'test.png', { type: 'image/png' })
      const input = document.querySelector('input[type="file"]') as HTMLInputElement

      await waitFor(() => {
        expect(input).toBeInTheDocument()
      })

      Object.defineProperty(input, 'files', {
        value: [file],
      })

      fireEvent.change(input)

      await waitFor(() => {
        expect(screen.getByText(/upload another/i)).toBeInTheDocument()
      })
    })

    it('shows Upload Another button after error', async () => {
      server.use(
        http.post(`${API_BASE}/upload/extract-immediate`, () => {
          return HttpResponse.json({ detail: 'Error' }, { status: 500 })
        })
      )

      renderUploadDropzone(mockOnRecipeExtracted)

      const file = new File(['test'], 'test.png', { type: 'image/png' })
      const input = document.querySelector('input[type="file"]') as HTMLInputElement

      await waitFor(() => {
        expect(input).toBeInTheDocument()
      })

      Object.defineProperty(input, 'files', {
        value: [file],
      })

      fireEvent.change(input)

      await waitFor(() => {
        expect(screen.getByText(/upload another/i)).toBeInTheDocument()
      })
    })

    it('resets state when clicking Upload Another', async () => {
      const user = userEvent.setup()
      renderUploadDropzone(mockOnRecipeExtracted)

      const file = new File(['test'], 'test.png', { type: 'image/png' })
      const input = document.querySelector('input[type="file"]') as HTMLInputElement

      await waitFor(() => {
        expect(input).toBeInTheDocument()
      })

      Object.defineProperty(input, 'files', {
        value: [file],
      })

      fireEvent.change(input)

      await waitFor(() => {
        expect(screen.getByText(/upload another/i)).toBeInTheDocument()
      })

      await user.click(screen.getByText(/upload another/i))

      await waitFor(() => {
        expect(
          screen.getByText(/upload a cocktail recipe screenshot/i)
        ).toBeInTheDocument()
      })
    })
  })
})
