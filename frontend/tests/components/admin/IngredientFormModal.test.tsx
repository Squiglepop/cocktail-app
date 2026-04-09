import { render, screen, cleanup, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi, afterEach } from 'vitest'
import { IngredientFormModal } from '@/components/admin/IngredientFormModal'
import { AdminIngredient } from '@/lib/api'

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

const mockIngredient: AdminIngredient = {
  id: '3',
  name: 'London Dry Gin',
  type: 'spirit',
  spirit_category: 'gin',
  description: 'Classic gin style',
  common_brands: 'Beefeater, Tanqueray',
}

const defaultProps = {
  isOpen: true,
  ingredient: null as AdminIngredient | null,
  onClose: vi.fn(),
  onSave: vi.fn(),
  isSaving: false,
  error: null as string | null,
}

describe('IngredientFormModal', () => {
  it('renders create form when ingredient is null', () => {
    render(<IngredientFormModal {...defaultProps} />)

    expect(screen.getByText('Add Ingredient')).toBeInTheDocument()
    expect(screen.getByLabelText(/name/i)).toHaveValue('')
  })

  it('renders edit form when ingredient is provided', () => {
    render(<IngredientFormModal {...defaultProps} ingredient={mockIngredient} />)

    expect(screen.getByText('Edit Ingredient')).toBeInTheDocument()
    expect(screen.getByLabelText(/name/i)).toHaveValue('London Dry Gin')
  })

  it('shows spirit_category dropdown only when type is spirit', () => {
    render(<IngredientFormModal {...defaultProps} ingredient={mockIngredient} />)

    expect(screen.getByLabelText(/spirit category/i)).toBeInTheDocument()
  })

  it('hides spirit_category dropdown when type is not spirit', () => {
    const juiceIngredient = { ...mockIngredient, type: 'juice', spirit_category: null }
    render(<IngredientFormModal {...defaultProps} ingredient={juiceIngredient} />)

    expect(screen.queryByLabelText(/spirit category/i)).not.toBeInTheDocument()
  })

  it('calls onSave with form data on submit', async () => {
    const user = userEvent.setup()
    render(<IngredientFormModal {...defaultProps} />)

    await user.clear(screen.getByLabelText(/name/i))
    await user.type(screen.getByLabelText(/name/i), 'New Ingredient')

    // Change type to juice
    await user.selectOptions(screen.getByLabelText(/^type/i), 'juice')

    await user.click(screen.getByRole('button', { name: /create/i }))

    expect(defaultProps.onSave).toHaveBeenCalledWith(
      expect.objectContaining({ name: 'New Ingredient', type: 'juice' })
    )
  })

  it('shows error message when error prop is set', () => {
    render(<IngredientFormModal {...defaultProps} error="Ingredient name already exists" />)

    expect(screen.getByText('Ingredient name already exists')).toBeInTheDocument()
  })

  it('disables save button when isSaving', () => {
    render(<IngredientFormModal {...defaultProps} isSaving={true} />)

    expect(screen.getByRole('button', { name: /saving/i })).toBeDisabled()
  })

  it('closes on Escape key', () => {
    render(<IngredientFormModal {...defaultProps} />)

    fireEvent.keyDown(document, { key: 'Escape' })

    expect(defaultProps.onClose).toHaveBeenCalledTimes(1)
  })

  it('closes on overlay click', async () => {
    const user = userEvent.setup()
    render(<IngredientFormModal {...defaultProps} />)

    const overlay = screen.getByText('Add Ingredient').closest('.fixed')!
    await user.click(overlay)

    expect(defaultProps.onClose).toHaveBeenCalledTimes(1)
  })
})
