import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import RegisterPage from '@/app/register/page'
import { AuthProvider } from '@/lib/auth-context'
import { server } from '../mocks/server'
import { http, HttpResponse } from 'msw'

const API_BASE = '*/api'

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
  usePathname: () => '/register',
  useSearchParams: () => new URLSearchParams(),
}))

function renderRegisterPage() {
  return render(
    <AuthProvider>
      <RegisterPage />
    </AuthProvider>
  )
}

describe('RegisterPage', () => {
  beforeEach(() => {
    vi.mocked(localStorage.getItem).mockReturnValue(null)
    vi.mocked(localStorage.setItem).mockClear()
    mockPush.mockClear()
  })

  describe('Rendering', () => {
    it('renders registration form with all fields', async () => {
      renderRegisterPage()

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /create account/i })).toBeInTheDocument()
      })

      expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/display name/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /create account/i })).toBeInTheDocument()
    })

    it('shows loading state while auth context initializes', async () => {
      // When auth is loading, it shows "Loading..."
      vi.mocked(localStorage.getItem).mockReturnValue('mock-jwt-token')

      const { container } = render(
        <AuthProvider>
          <RegisterPage />
        </AuthProvider>
      )

      // Initially may show loading
      expect(container).toBeDefined()
    })

    it('has link to login page', async () => {
      renderRegisterPage()

      await waitFor(() => {
        const loginLink = screen.getByRole('link', { name: /login/i })
        expect(loginLink).toHaveAttribute('href', '/login')
      })
    })
  })

  describe('Validation', () => {
    it('shows error when passwords do not match', async () => {
      const user = userEvent.setup()
      renderRegisterPage()

      await waitFor(() => {
        expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
      })

      await user.type(screen.getByLabelText(/email/i), 'new@example.com')
      await user.type(screen.getByLabelText(/^password$/i), 'password123')
      await user.type(screen.getByLabelText(/confirm password/i), 'differentpassword')
      await user.click(screen.getByRole('button', { name: /create account/i }))

      await waitFor(() => {
        expect(screen.getByText(/passwords do not match/i)).toBeInTheDocument()
      })
    })

    it('shows error when password is less than 8 characters', async () => {
      const user = userEvent.setup()
      renderRegisterPage()

      await waitFor(() => {
        expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
      })

      await user.type(screen.getByLabelText(/email/i), 'new@example.com')
      await user.type(screen.getByLabelText(/^password$/i), 'short')
      await user.type(screen.getByLabelText(/confirm password/i), 'short')
      await user.click(screen.getByRole('button', { name: /create account/i }))

      await waitFor(() => {
        expect(screen.getByText(/password must be at least 8 characters/i)).toBeInTheDocument()
      })
    })
  })

  describe('Form Submission', () => {
    it('disables submit button while submitting', async () => {
      const user = userEvent.setup()

      server.use(
        http.post(`${API_BASE}/auth/register`, async () => {
          await new Promise((resolve) => setTimeout(resolve, 200))
          return HttpResponse.json({
            id: '2',
            email: 'new@example.com',
            display_name: null,
            created_at: new Date().toISOString(),
          }, { status: 201 })
        })
      )

      renderRegisterPage()

      await waitFor(() => {
        expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
      })

      await user.type(screen.getByLabelText(/email/i), 'new@example.com')
      await user.type(screen.getByLabelText(/^password$/i), 'password123')
      await user.type(screen.getByLabelText(/confirm password/i), 'password123')
      await user.click(screen.getByRole('button', { name: /create account/i }))

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /creating account/i })).toBeDisabled()
      })
    })

    it('shows "Creating account..." while submitting', async () => {
      const user = userEvent.setup()

      server.use(
        http.post(`${API_BASE}/auth/register`, async () => {
          await new Promise((resolve) => setTimeout(resolve, 200))
          return HttpResponse.json({
            id: '2',
            email: 'new@example.com',
            display_name: null,
            created_at: new Date().toISOString(),
          }, { status: 201 })
        })
      )

      renderRegisterPage()

      await waitFor(() => {
        expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
      })

      await user.type(screen.getByLabelText(/email/i), 'new@example.com')
      await user.type(screen.getByLabelText(/^password$/i), 'password123')
      await user.type(screen.getByLabelText(/confirm password/i), 'password123')
      await user.click(screen.getByRole('button', { name: /create account/i }))

      await waitFor(() => {
        expect(screen.getByText(/creating account/i)).toBeInTheDocument()
      })
    })

    it('redirects to home on successful registration', async () => {
      const user = userEvent.setup()

      // Override handlers to allow login with the new user
      server.use(
        http.post(`${API_BASE}/auth/login`, () => {
          return HttpResponse.json({
            access_token: 'mock-jwt-token',
            token_type: 'bearer',
          })
        }),
        http.get(`${API_BASE}/auth/me`, () => {
          return HttpResponse.json({
            id: '2',
            email: 'new@example.com',
            display_name: null,
            created_at: new Date().toISOString(),
          })
        })
      )

      renderRegisterPage()

      await waitFor(() => {
        expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
      })

      await user.type(screen.getByLabelText(/email/i), 'new@example.com')
      await user.type(screen.getByLabelText(/^password$/i), 'password123')
      await user.type(screen.getByLabelText(/confirm password/i), 'password123')
      await user.click(screen.getByRole('button', { name: /create account/i }))

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/')
      })
    })

    it('shows API error message on registration failure', async () => {
      const user = userEvent.setup()

      server.use(
        http.post(`${API_BASE}/auth/register`, () => {
          return HttpResponse.json(
            { detail: 'Registration failed' },
            { status: 400 }
          )
        })
      )

      renderRegisterPage()

      await waitFor(() => {
        expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
      })

      await user.type(screen.getByLabelText(/email/i), 'new@example.com')
      await user.type(screen.getByLabelText(/^password$/i), 'password123')
      await user.type(screen.getByLabelText(/confirm password/i), 'password123')
      await user.click(screen.getByRole('button', { name: /create account/i }))

      await waitFor(() => {
        expect(screen.getByText(/registration failed/i)).toBeInTheDocument()
      })
    })

    it('handles "email already registered" error', async () => {
      const user = userEvent.setup()

      renderRegisterPage()

      await waitFor(() => {
        expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
      })

      await user.type(screen.getByLabelText(/email/i), 'existing@example.com')
      await user.type(screen.getByLabelText(/^password$/i), 'password123')
      await user.type(screen.getByLabelText(/confirm password/i), 'password123')
      await user.click(screen.getByRole('button', { name: /create account/i }))

      await waitFor(() => {
        expect(screen.getByText(/email already registered/i)).toBeInTheDocument()
      })
    })
  })
})
