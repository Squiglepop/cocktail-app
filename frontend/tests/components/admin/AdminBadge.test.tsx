import { render, screen, cleanup } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AdminBadge } from '@/components/admin/AdminBadge'

vi.mock('next/navigation', () => ({
  usePathname: () => '/',
}))

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
    const badge = screen.getByText('Admin').closest('button')!
    expect(badge).toHaveClass('bg-amber-100')
    expect(badge).toHaveClass('text-amber-800')
    expect(badge).toHaveClass('border-amber-300')
    expect(badge).toHaveClass('text-xs')
    expect(badge).toHaveClass('font-medium')
  })

  it('has correct accessibility attributes', () => {
    render(<AdminBadge />)
    const badge = screen.getByRole('status')
    expect(badge).toHaveAttribute('aria-label', 'Administrator menu')
    expect(badge).toHaveTextContent('Admin')
  })

  it('opens dropdown with admin links on click', async () => {
    const user = userEvent.setup()
    render(<AdminBadge />)

    expect(screen.queryByText('Users')).not.toBeInTheDocument()

    await user.click(screen.getByText('Admin'))

    expect(screen.getByText('Users')).toBeInTheDocument()
    expect(screen.getByText('Ingredients')).toBeInTheDocument()
    expect(screen.getByText('Audit Log')).toBeInTheDocument()
  })

  it('links point to correct admin pages', async () => {
    const user = userEvent.setup()
    render(<AdminBadge />)

    await user.click(screen.getByText('Admin'))

    expect(screen.getByText('Users').closest('a')).toHaveAttribute('href', '/admin/users')
    expect(screen.getByText('Ingredients').closest('a')).toHaveAttribute('href', '/admin/ingredients')
    expect(screen.getByText('Audit Log').closest('a')).toHaveAttribute('href', '/admin/audit-log')
  })

  it('closes dropdown on second click', async () => {
    const user = userEvent.setup()
    render(<AdminBadge />)

    await user.click(screen.getByText('Admin'))
    expect(screen.getByText('Users')).toBeInTheDocument()

    await user.click(screen.getByText('Admin'))
    expect(screen.queryByText('Users')).not.toBeInTheDocument()
  })
})
