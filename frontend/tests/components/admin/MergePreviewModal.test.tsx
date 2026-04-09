import { render, screen, cleanup, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi, afterEach } from 'vitest'
import { MergePreviewModal } from '@/components/admin/MergePreviewModal'
import { IngredientDuplicateGroup } from '@/lib/api'

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

const mockGroup: IngredientDuplicateGroup = {
  target: { ingredient_id: '1', name: 'Lime Juice', type: 'juice', similarity_score: 1.0, detection_reason: 'exact_match_case_insensitive', usage_count: 15 },
  duplicates: [
    { ingredient_id: '10', name: 'lime juice', type: 'juice', similarity_score: 1.0, detection_reason: 'exact_match_case_insensitive', usage_count: 3 },
  ],
  group_reason: 'exact_match_case_insensitive',
}

const defaultProps = {
  isOpen: true,
  group: mockGroup,
  onConfirm: vi.fn(),
  onCancel: vi.fn(),
  isMerging: false,
}

describe('MergePreviewModal', () => {
  it('renders target and source ingredients', () => {
    render(<MergePreviewModal {...defaultProps} />)

    expect(screen.getByText('Lime Juice')).toBeInTheDocument()
    expect(screen.getByText('lime juice')).toBeInTheDocument()
    expect(screen.getByText(/keep \(target\)/i)).toBeInTheDocument()
    expect(screen.getByText(/merge and remove/i)).toBeInTheDocument()
  })

  it('shows affected recipe count', () => {
    render(<MergePreviewModal {...defaultProps} />)

    // The warning box shows affected recipe count and source info shows usage count
    // Source duplicate shows "3 recipes" in its info line
    expect(screen.getByText(/source ingredients will be deleted/i)).toBeInTheDocument()
    expect(screen.getByText('3 recipes')).toBeInTheDocument()
  })

  it('calls onConfirm when Merge button clicked', async () => {
    const user = userEvent.setup()
    render(<MergePreviewModal {...defaultProps} />)

    await user.click(screen.getByRole('button', { name: /confirm merge/i }))

    expect(defaultProps.onConfirm).toHaveBeenCalledTimes(1)
  })

  it('disables buttons when isMerging', () => {
    render(<MergePreviewModal {...defaultProps} isMerging={true} />)

    expect(screen.getByRole('button', { name: /merging/i })).toBeDisabled()
    expect(screen.getByRole('button', { name: /cancel/i })).toBeDisabled()
  })

  it('closes on Cancel', async () => {
    const user = userEvent.setup()
    render(<MergePreviewModal {...defaultProps} />)

    await user.click(screen.getByRole('button', { name: /cancel/i }))

    expect(defaultProps.onCancel).toHaveBeenCalledTimes(1)
  })
})
