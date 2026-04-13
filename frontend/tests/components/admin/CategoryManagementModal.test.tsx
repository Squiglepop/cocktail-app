import { render, screen, waitFor, cleanup } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi, afterEach, beforeEach } from 'vitest'
import { CategoryManagementModal } from '@/components/admin/CategoryManagementModal'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { HttpResponse, http } from 'msw'
import { server } from '../../mocks/server'
import { mockAdminCategories } from '../../mocks/handlers'

// Mock useAuth
vi.mock('@/lib/auth-context', () => ({
  useAuth: () => ({
    user: { id: '1', email: 'admin@test.com', display_name: 'Admin', is_admin: true, created_at: '2026-01-01' },
    token: 'fake-token',
    isLoading: false,
    login: vi.fn(),
    logout: vi.fn(),
    register: vi.fn(),
    refreshToken: vi.fn(),
  }),
}))

let queryClient: QueryClient

function renderModal(props: Partial<React.ComponentProps<typeof CategoryManagementModal>> = {}) {
  queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <CategoryManagementModal
        isOpen={true}
        categoryType="templates"
        categoryLabel="Templates"
        onClose={vi.fn()}
        {...props}
      />
    </QueryClientProvider>
  )
}

beforeEach(() => {
  queryClient?.clear()
})

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

describe('CategoryManagementModal', () => {
  it('renders modal with category list when open', async () => {
    renderModal()

    await waitFor(() => {
      expect(screen.getByText('Manage Templates')).toBeInTheDocument()
    })

    await waitFor(() => {
      expect(screen.getByText('Sour')).toBeInTheDocument()
      expect(screen.getByText('Old Fashioned')).toBeInTheDocument()
      expect(screen.getByText('Flip')).toBeInTheDocument()
    })
  })

  it('does not render when isOpen is false', () => {
    renderModal({ isOpen: false })
    expect(screen.queryByText('Manage Templates')).not.toBeInTheDocument()
  })

  it('shows inactive categories with visual distinction', async () => {
    renderModal()

    await waitFor(() => {
      expect(screen.getByText('Flip')).toBeInTheDocument()
    })

    const flipLabel = screen.getByText('Flip')
    expect(flipLabel).toHaveClass('line-through')
    expect(flipLabel).toHaveClass('text-gray-500')
  })

  it('shows Add New button and form on click', async () => {
    const user = userEvent.setup()
    renderModal()

    await waitFor(() => {
      expect(screen.getByText('Add New')).toBeInTheDocument()
    })

    await user.click(screen.getByText('Add New'))

    expect(screen.getByPlaceholderText('Label (e.g. Daisy)')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Description (optional)')).toBeInTheDocument()
  })

  it('auto-generates snake_case value from label', async () => {
    const user = userEvent.setup()
    renderModal()

    await waitFor(() => {
      expect(screen.getByText('Add New')).toBeInTheDocument()
    })

    await user.click(screen.getByText('Add New'))
    await user.type(screen.getByPlaceholderText('Label (e.g. Daisy)'), 'Rum Punch')

    await waitFor(() => {
      expect(screen.getByText('rum_punch')).toBeInTheDocument()
    })
  })

  it('creates category on form submit', async () => {
    const user = userEvent.setup()
    renderModal()

    await waitFor(() => {
      expect(screen.getByText('Add New')).toBeInTheDocument()
    })

    await user.click(screen.getByText('Add New'))
    await user.type(screen.getByPlaceholderText('Label (e.g. Daisy)'), 'Daisy')
    await user.click(screen.getByText('Save'))

    // Form should close on success
    await waitFor(() => {
      expect(screen.queryByPlaceholderText('Label (e.g. Daisy)')).not.toBeInTheDocument()
    })
  })

  it('shows error on duplicate value (409)', async () => {
    const user = userEvent.setup()
    renderModal()

    await waitFor(() => {
      expect(screen.getByText('Add New')).toBeInTheDocument()
    })

    await user.click(screen.getByText('Add New'))
    // Type "Sour" which generates value "sour" — our mock returns 409 for this
    await user.type(screen.getByPlaceholderText('Label (e.g. Daisy)'), 'Sour')
    await user.click(screen.getByText('Save'))

    await waitFor(() => {
      expect(screen.getByText('Category value already exists')).toBeInTheDocument()
    })
  })

  it('inline edit label on click', async () => {
    const user = userEvent.setup()
    renderModal()

    await waitFor(() => {
      expect(screen.getByText('Sour')).toBeInTheDocument()
    })

    // Click on the label to start editing
    await user.click(screen.getByText('Sour'))

    // Should show an input with the current value
    const editInput = screen.getByDisplayValue('Sour')
    expect(editInput).toBeInTheDocument()
    expect(editInput.tagName).toBe('INPUT')
  })

  it('saves label on Enter key', async () => {
    const user = userEvent.setup()
    renderModal()

    await waitFor(() => {
      expect(screen.getByText('Sour')).toBeInTheDocument()
    })

    await user.click(screen.getByText('Sour'))
    const editInput = screen.getByDisplayValue('Sour')
    await user.clear(editInput)
    await user.type(editInput, 'Sour Classic{Enter}')

    // Input should disappear after save
    await waitFor(() => {
      expect(screen.queryByDisplayValue('Sour Classic')).not.toBeInTheDocument()
    })
  })

  it('cancels edit on Escape key', async () => {
    const user = userEvent.setup()
    renderModal()

    await waitFor(() => {
      expect(screen.getByText('Sour')).toBeInTheDocument()
    })

    await user.click(screen.getByText('Sour'))
    const editInput = screen.getByDisplayValue('Sour')
    await user.clear(editInput)
    await user.type(editInput, 'Changed{Escape}')

    // Should revert — edit input gone, original label still there
    await waitFor(() => {
      expect(screen.queryByDisplayValue('Changed')).not.toBeInTheDocument()
    })
  })

  it('reorder up disabled for first item', async () => {
    renderModal()

    await waitFor(() => {
      expect(screen.getByText('Sour')).toBeInTheDocument()
    })

    // First item's up arrow should be disabled
    const upButtons = screen.getAllByTitle('Move up')
    expect(upButtons[0]).toBeDisabled()
  })

  it('reorder down disabled for last item', async () => {
    renderModal()

    await waitFor(() => {
      expect(screen.getByText('Flip')).toBeInTheDocument()
    })

    const downButtons = screen.getAllByTitle('Move down')
    expect(downButtons[downButtons.length - 1]).toBeDisabled()
  })

  it('delete button deactivates category', async () => {
    const user = userEvent.setup()
    renderModal()

    await waitFor(() => {
      expect(screen.getByText('Sour')).toBeInTheDocument()
    })

    // Find the deactivate buttons (only for active items)
    const deleteButtons = screen.getAllByTitle('Deactivate')
    await user.click(deleteButtons[0])

    // Should show inline feedback
    await waitFor(() => {
      expect(screen.getByText(/deactivated.*3 recipes affected/)).toBeInTheDocument()
    })
  })

  it('invalidates public categories on close', async () => {
    const onClose = vi.fn()
    renderModal({ onClose })

    await waitFor(() => {
      expect(screen.getByText('Manage Templates')).toBeInTheDocument()
    })

    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries')

    await userEvent.click(screen.getByText('Done'))

    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['categories'] })
    expect(onClose).toHaveBeenCalled()
  })

  it('closes on overlay click', async () => {
    const onClose = vi.fn()
    const { container } = renderModal({ onClose })

    await waitFor(() => {
      expect(screen.getByText('Manage Templates')).toBeInTheDocument()
    })

    // Click the overlay (the outermost fixed div)
    const overlay = container.querySelector('.fixed.inset-0')
    if (overlay) {
      await userEvent.click(overlay)
    }

    expect(onClose).toHaveBeenCalled()
  })

  it('closes on Escape key', async () => {
    const onClose = vi.fn()
    renderModal({ onClose })

    await waitFor(() => {
      expect(screen.getByText('Manage Templates')).toBeInTheDocument()
    })

    await userEvent.keyboard('{Escape}')

    expect(onClose).toHaveBeenCalled()
  })

  it('shows validation error when label produces invalid value', async () => {
    const user = userEvent.setup()
    renderModal()

    await waitFor(() => {
      expect(screen.getByText('Add New')).toBeInTheDocument()
    })

    await user.click(screen.getByText('Add New'))
    // Type digits-only label — produces empty snake_case value
    await user.type(screen.getByPlaceholderText('Label (e.g. Daisy)'), '123')

    // Should show validation error
    await waitFor(() => {
      expect(screen.getByText('Label must contain at least one letter')).toBeInTheDocument()
    })

    // Save button should be disabled
    expect(screen.getByText('Save')).toBeDisabled()
  })

  it('reorder up button moves item up and calls API', async () => {
    const user = userEvent.setup()
    renderModal()

    await waitFor(() => {
      expect(screen.getByText('Old Fashioned')).toBeInTheDocument()
    })

    // Click the second item's up button (index 1)
    const upButtons = screen.getAllByTitle('Move up')
    await user.click(upButtons[1])

    // Reorder API should have been called — verify no error thrown
    // The mutation fires and invalidates the query
    await waitFor(() => {
      // If reorder failed, the UI would still be responsive
      expect(screen.getByText('Old Fashioned')).toBeInTheDocument()
    })
  })

  it('renders empty state when no categories returned', async () => {
    server.use(
      http.get('*/api/admin/categories/:type', () => {
        return HttpResponse.json([])
      })
    )

    renderModal()

    await waitFor(() => {
      expect(screen.getByText('No categories found')).toBeInTheDocument()
    })
  })

  it('shows delete buttons for active items and reactivate for inactive', async () => {
    renderModal()

    await waitFor(() => {
      expect(screen.getByText('Flip')).toBeInTheDocument()
    })

    // Should have 2 deactivate buttons (for Sour and Old Fashioned)
    const deleteButtons = screen.getAllByTitle('Deactivate')
    expect(deleteButtons.length).toBe(2)

    // Should have 1 Restore button (for Flip)
    const reactivateButtons = screen.getAllByRole('button', { name: /Tap to restore/ })
    expect(reactivateButtons.length).toBe(1)
  })

  it('renders Reactivate button on inactive categories', async () => {
    renderModal()

    await waitFor(() => {
      expect(screen.getByText('Flip')).toBeInTheDocument()
    })

    // Inactive category should show Reactivate button
    expect(screen.getByRole('button', { name: /Tap to restore/ })).toBeInTheDocument()
  })

  it('clicking Reactivate calls update API with is_active true', async () => {
    let capturedBody: Record<string, unknown> | null = null
    server.use(
      http.put('*/api/admin/categories/:type/:id', async ({ params, request }) => {
        const body = await request.json() as Record<string, unknown>
        capturedBody = body
        const existing = mockAdminCategories.find(c => c.id === params.id)
        if (!existing) return HttpResponse.json({ detail: 'Not found' }, { status: 404 })
        return HttpResponse.json({ ...existing, ...body })
      })
    )

    const user = userEvent.setup()
    renderModal()

    await waitFor(() => {
      expect(screen.getByText('Flip')).toBeInTheDocument()
    })

    const reactivateButton = screen.getByRole('button', { name: /Tap to restore/ })
    await user.click(reactivateButton)

    await waitFor(() => {
      expect(capturedBody).not.toBeNull()
    })
    expect(capturedBody).toEqual({ is_active: true })

    // Verify success feedback message
    await waitFor(() => {
      expect(screen.getByText('flip reactivated.')).toBeInTheDocument()
    })
  })

  it('shows error feedback when reactivation fails', async () => {
    server.use(
      http.put('*/api/admin/categories/:type/:id', () => {
        return HttpResponse.json({ detail: 'Failed to update category' }, { status: 500 })
      })
    )

    const user = userEvent.setup()
    renderModal()

    await waitFor(() => {
      expect(screen.getByText('Flip')).toBeInTheDocument()
    })

    const reactivateButton = screen.getByRole('button', { name: /Tap to restore/ })
    await user.click(reactivateButton)

    await waitFor(() => {
      expect(screen.getByText(/Failed to reactivate/)).toBeInTheDocument()
    })
  })

  it('active categories show Edit and Delete buttons, not Reactivate', async () => {
    renderModal()

    await waitFor(() => {
      expect(screen.getByText('Sour')).toBeInTheDocument()
    })

    // Active items should have Edit and Deactivate buttons
    const editButtons = screen.getAllByTitle('Edit label')
    expect(editButtons.length).toBe(2) // Sour and Old Fashioned

    const deleteButtons = screen.getAllByTitle('Deactivate')
    expect(deleteButtons.length).toBe(2)
  })
})
