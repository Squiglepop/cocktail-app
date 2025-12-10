import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import LoginPage from '@/app/login/page'
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
  usePathname: () => '/login',
  useSearchParams: () => new URLSearchParams(),
}))

function renderLoginPage() {
  return render(
    <AuthProvider>
      <LoginPage />
    </AuthProvider>
  )
}

describe('Login Page', () => {
  beforeEach(() => {
    vi.mocked(localStorage.getItem).mockReturnValue(null)
    vi.mocked(localStorage.setItem).mockClear()
    mockPush.mockClear()
  })

  describe('Form Rendering', () => {
    it('renders login title', async () => {
      renderLoginPage()

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /login/i })).toBeInTheDocument()
      })
    })

    it('renders email input', async () => {
      renderLoginPage()

      await waitFor(() => {
        expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
      })
    })

    it('renders password input', async () => {
      renderLoginPage()

      await waitFor(() => {
        expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
      })
    })

    it('renders submit button', async () => {
      renderLoginPage()

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument()
      })
    })

    it('renders link to register page', async () => {
      renderLoginPage()

      await waitFor(() => {
        const registerLink = screen.getByRole('link', { name: /register/i })
        expect(registerLink).toHaveAttribute('href', '/register')
      })
    })
  })

  describe('Form Submission', () => {
    it('submits form with valid credentials', async () => {
      const user = userEvent.setup()
      renderLoginPage()

      await waitFor(() => {
        expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
      })

      await user.type(screen.getByLabelText(/email/i), 'test@example.com')
      await user.type(screen.getByLabelText(/password/i), 'testpassword123')
      await user.click(screen.getByRole('button', { name: /login/i }))

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/')
      })
    })

    it('stores token in localStorage on success', async () => {
      const user = userEvent.setup()
      renderLoginPage()

      await waitFor(() => {
        expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
      })

      await user.type(screen.getByLabelText(/email/i), 'test@example.com')
      await user.type(screen.getByLabelText(/password/i), 'testpassword123')
      await user.click(screen.getByRole('button', { name: /login/i }))

      await waitFor(() => {
        expect(localStorage.setItem).toHaveBeenCalledWith(
          'cocktail_auth_token',
          'mock-jwt-token'
        )
      })
    })

    it('shows error for invalid credentials', async () => {
      const user = userEvent.setup()

      server.use(
        http.post(`${API_BASE}/auth/login`, () => {
          return HttpResponse.json(
            { detail: 'Incorrect email or password' },
            { status: 401 }
          )
        })
      )

      renderLoginPage()

      await waitFor(() => {
        expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
      })

      await user.type(screen.getByLabelText(/email/i), 'wrong@example.com')
      await user.type(screen.getByLabelText(/password/i), 'wrongpassword')
      await user.click(screen.getByRole('button', { name: /login/i }))

      await waitFor(() => {
        expect(screen.getByText(/incorrect email or password/i)).toBeInTheDocument()
      })
    })

    it('shows loading state during submission', async () => {
      const user = userEvent.setup()

      // Add delay to see loading state
      server.use(
        http.post(`${API_BASE}/auth/login`, async () => {
          await new Promise((resolve) => setTimeout(resolve, 100))
          return HttpResponse.json({
            access_token: 'mock-jwt-token',
            token_type: 'bearer',
          })
        })
      )

      renderLoginPage()

      await waitFor(() => {
        expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
      })

      await user.type(screen.getByLabelText(/email/i), 'test@example.com')
      await user.type(screen.getByLabelText(/password/i), 'testpassword123')
      await user.click(screen.getByRole('button', { name: /login/i }))

      // Check for loading state
      await waitFor(() => {
        expect(screen.getByText(/logging in/i)).toBeInTheDocument()
      })
    })

    it('disables submit button during submission', async () => {
      const user = userEvent.setup()

      server.use(
        http.post(`${API_BASE}/auth/login`, async () => {
          await new Promise((resolve) => setTimeout(resolve, 200))
          return HttpResponse.json({
            access_token: 'mock-jwt-token',
            token_type: 'bearer',
          })
        })
      )

      renderLoginPage()

      await waitFor(() => {
        expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
      })

      await user.type(screen.getByLabelText(/email/i), 'test@example.com')
      await user.type(screen.getByLabelText(/password/i), 'testpassword123')
      await user.click(screen.getByRole('button', { name: /login/i }))

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /logging in/i })).toBeDisabled()
      })
    })
  })

  describe('Form Validation', () => {
    it('requires email input', async () => {
      renderLoginPage()

      await waitFor(() => {
        const emailInput = screen.getByLabelText(/email/i)
        expect(emailInput).toHaveAttribute('required')
      })
    })

    it('requires password input', async () => {
      renderLoginPage()

      await waitFor(() => {
        const passwordInput = screen.getByLabelText(/password/i)
        expect(passwordInput).toHaveAttribute('required')
      })
    })

    it('requires minimum password length', async () => {
      renderLoginPage()

      await waitFor(() => {
        const passwordInput = screen.getByLabelText(/password/i)
        expect(passwordInput).toHaveAttribute('minLength', '8')
      })
    })

    it('email input has correct type', async () => {
      renderLoginPage()

      await waitFor(() => {
        const emailInput = screen.getByLabelText(/email/i)
        expect(emailInput).toHaveAttribute('type', 'email')
      })
    })

    it('password input has correct type', async () => {
      renderLoginPage()

      await waitFor(() => {
        const passwordInput = screen.getByLabelText(/password/i)
        expect(passwordInput).toHaveAttribute('type', 'password')
      })
    })
  })
})
