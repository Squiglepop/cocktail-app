import { render, screen, waitFor, cleanup } from '@testing-library/react'
import { Header } from '@/components/Header'

// Mock useAuth to control admin state directly
vi.mock('@/lib/auth-context', () => ({
  useAuth: vi.fn(),
}))

import { useAuth } from '@/lib/auth-context'

const mockUseAuth = vi.mocked(useAuth)

const baseUser = {
  id: '1',
  email: 'admin@test.com',
  display_name: 'Admin User',
  is_admin: false,
  created_at: '2026-01-01T00:00:00Z',
}

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

describe('Header - Admin Badge', () => {
  it('shows admin badge when user is admin', async () => {
    mockUseAuth.mockReturnValue({
      user: { ...baseUser, is_admin: true },
      token: 'fake-token',
      isLoading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      refreshToken: vi.fn(),
    })

    render(<Header />)

    await waitFor(() => {
      expect(screen.getByText('Admin')).toBeInTheDocument()
    })
  })

  it('does not show admin badge when user is not admin', async () => {
    mockUseAuth.mockReturnValue({
      user: { ...baseUser, is_admin: false },
      token: 'fake-token',
      isLoading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      refreshToken: vi.fn(),
    })

    render(<Header />)

    await waitFor(() => {
      expect(screen.getByText('Admin User')).toBeInTheDocument()
    })

    expect(screen.queryByText('Admin')).not.toBeInTheDocument()
  })

  it('does not show admin badge when user is null', async () => {
    mockUseAuth.mockReturnValue({
      user: null,
      token: null,
      isLoading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      refreshToken: vi.fn(),
    })

    render(<Header />)

    await waitFor(() => {
      expect(screen.getByText('Login')).toBeInTheDocument()
    })

    expect(screen.queryByText('Admin')).not.toBeInTheDocument()
  })

  it('does not flash admin badge during loading state', async () => {
    mockUseAuth.mockReturnValue({
      user: null,
      token: null,
      isLoading: true,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      refreshToken: vi.fn(),
    })

    render(<Header />)

    // Loading state should show pulse placeholder, not admin badge
    expect(screen.queryByText('Admin')).not.toBeInTheDocument()
    expect(document.querySelector('.animate-pulse')).toBeInTheDocument()
  })
})
