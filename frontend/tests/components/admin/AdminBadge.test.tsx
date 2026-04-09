import { render, screen, cleanup } from '@testing-library/react'
import { AdminBadge } from '@/components/admin/AdminBadge'

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

describe('AdminBadge', () => {
  it('renders admin badge text', () => {
    render(<AdminBadge />)
    expect(screen.getByText('Admin')).toBeInTheDocument()
  })

  it('renders with correct styling classes', () => {
    render(<AdminBadge />)
    const badge = screen.getByText('Admin')
    expect(badge).toHaveClass('bg-amber-100')
    expect(badge).toHaveClass('text-amber-800')
    expect(badge).toHaveClass('border-amber-300')
    expect(badge).toHaveClass('text-xs')
    expect(badge).toHaveClass('font-medium')
  })

  it('has correct accessibility attributes', () => {
    render(<AdminBadge />)
    const badge = screen.getByRole('status')
    expect(badge).toHaveAttribute('aria-label', 'Administrator account')
    expect(badge).toHaveTextContent('Admin')
  })
})
