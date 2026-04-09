import { render, screen, cleanup, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi, afterEach } from 'vitest'
import { ConfirmDeleteModal } from '@/components/ui/ConfirmDeleteModal'

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

describe('ConfirmDeleteModal', () => {
  const defaultProps = {
    isOpen: true,
    title: 'Delete this recipe?',
    itemName: 'Whiskey Sour',
    onConfirm: vi.fn(),
    onCancel: vi.fn(),
  }

  it('renders modal when isOpen is true', () => {
    render(<ConfirmDeleteModal {...defaultProps} />)

    expect(screen.getByText('Delete this recipe?')).toBeInTheDocument()
    expect(screen.getByText(/Whiskey Sour/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /delete/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument()
  })

  it('does not render when isOpen is false', () => {
    render(<ConfirmDeleteModal {...defaultProps} isOpen={false} />)

    expect(screen.queryByText('Delete this recipe?')).not.toBeInTheDocument()
  })

  it('calls onConfirm when Delete button clicked', async () => {
    const user = userEvent.setup()
    render(<ConfirmDeleteModal {...defaultProps} />)

    await user.click(screen.getByRole('button', { name: /delete/i }))

    expect(defaultProps.onConfirm).toHaveBeenCalledTimes(1)
  })

  it('calls onCancel when Cancel button clicked', async () => {
    const user = userEvent.setup()
    render(<ConfirmDeleteModal {...defaultProps} />)

    await user.click(screen.getByRole('button', { name: /cancel/i }))

    expect(defaultProps.onCancel).toHaveBeenCalledTimes(1)
  })

  it('calls onCancel when Escape key pressed', () => {
    render(<ConfirmDeleteModal {...defaultProps} />)

    fireEvent.keyDown(document, { key: 'Escape' })

    expect(defaultProps.onCancel).toHaveBeenCalledTimes(1)
  })

  it('shows deleting state when isDeleting is true', () => {
    render(<ConfirmDeleteModal {...defaultProps} isDeleting={true} />)

    const deleteButton = screen.getByRole('button', { name: /deleting/i })
    expect(deleteButton).toBeDisabled()
    expect(screen.getByText(/Deleting.../)).toBeInTheDocument()

    // Cancel button should remain enabled so user can bail out of a hanging delete
    const cancelButton = screen.getByRole('button', { name: /cancel/i })
    expect(cancelButton).not.toBeDisabled()
  })

  it('displays item name in confirmation message', () => {
    render(<ConfirmDeleteModal {...defaultProps} itemName="Negroni" />)

    expect(screen.getByText(/Negroni/)).toBeInTheDocument()
    expect(screen.getByText(/This cannot be undone/)).toBeInTheDocument()
  })

  it('calls onCancel when overlay is clicked', async () => {
    const user = userEvent.setup()
    render(<ConfirmDeleteModal {...defaultProps} />)

    // Click the overlay (the outermost fixed div)
    const overlay = screen.getByText('Delete this recipe?').closest('.fixed')!
    await user.click(overlay)

    expect(defaultProps.onCancel).toHaveBeenCalledTimes(1)
  })
})
