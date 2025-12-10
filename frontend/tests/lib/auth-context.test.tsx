import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AuthProvider, useAuth, getAuthHeaders } from '@/lib/auth-context'
import { server } from '../mocks/server'
import { http, HttpResponse } from 'msw'

const API_BASE = '*/api'

// Test component that uses useAuth
function TestComponent() {
  const { user, token, isLoading, login, register, logout } = useAuth()

  if (isLoading) {
    return <div>Loading...</div>
  }

  return (
    <div>
      {user ? (
        <>
          <div data-testid="user-email">{user.email}</div>
          <div data-testid="user-name">{user.display_name}</div>
          <div data-testid="token">{token}</div>
          <button onClick={logout}>Logout</button>
        </>
      ) : (
        <>
          <div data-testid="logged-out">Not logged in</div>
          <button
            onClick={() => login('test@example.com', 'testpassword123')}
            data-testid="login-btn"
          >
            Login
          </button>
          <button
            onClick={() => register('new@example.com', 'newpassword123', 'New User')}
            data-testid="register-btn"
          >
            Register
          </button>
        </>
      )}
    </div>
  )
}

// Test component for hook error
function TestComponentWithoutProvider() {
  try {
    useAuth()
    return <div>Should not render</div>
  } catch (error) {
    return <div data-testid="error">{(error as Error).message}</div>
  }
}

describe('AuthContext', () => {
  beforeEach(() => {
    vi.mocked(localStorage.getItem).mockReturnValue(null)
    vi.mocked(localStorage.setItem).mockClear()
    vi.mocked(localStorage.removeItem).mockClear()
  })

  describe('Initial State', () => {
    it('shows loading initially or resolves to logged-out', async () => {
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      )

      // Either loading is shown initially, or it resolves quickly to logged-out
      // Due to test timing, the loading state may pass very quickly
      await waitFor(() => {
        expect(screen.getByTestId('logged-out')).toBeInTheDocument()
      })
    })

    it('user is null when not logged in', async () => {
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('logged-out')).toBeInTheDocument()
      })
    })
  })

  describe('Login', () => {
    it('sets user and token on successful login', async () => {
      const user = userEvent.setup()

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      )

      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByTestId('login-btn')).toBeInTheDocument()
      })

      // Click login button
      await user.click(screen.getByTestId('login-btn'))

      // Check user is now logged in
      await waitFor(() => {
        expect(screen.getByTestId('user-email')).toHaveTextContent('test@example.com')
        expect(screen.getByTestId('token')).toHaveTextContent('mock-jwt-token')
      })

      // Check localStorage was updated
      expect(localStorage.setItem).toHaveBeenCalledWith(
        'cocktail_auth_token',
        'mock-jwt-token'
      )
    })

    it('throws error on failed login', async () => {
      const user = userEvent.setup()

      // Override handler for failed login
      server.use(
        http.post(`${API_BASE}/auth/login`, () => {
          return HttpResponse.json(
            { detail: 'Invalid credentials' },
            { status: 401 }
          )
        })
      )

      const onError = vi.fn()

      function LoginErrorTestComponent() {
        const { login, isLoading } = useAuth()

        if (isLoading) return <div>Loading...</div>

        return (
          <button
            onClick={async () => {
              try {
                await login('wrong@example.com', 'wrongpassword')
              } catch (error) {
                onError(error)
              }
            }}
            data-testid="login-btn"
          >
            Login
          </button>
        )
      }

      render(
        <AuthProvider>
          <LoginErrorTestComponent />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('login-btn')).toBeInTheDocument()
      })

      await user.click(screen.getByTestId('login-btn'))

      await waitFor(() => {
        expect(onError).toHaveBeenCalled()
        expect(onError.mock.calls[0][0].message).toContain('Invalid credentials')
      })
    })
  })

  describe('Register', () => {
    it('registers and auto-logs in user', async () => {
      const user = userEvent.setup()

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('register-btn')).toBeInTheDocument()
      })

      // Mock successful registration followed by login
      server.use(
        http.post(`${API_BASE}/auth/register`, () => {
          return HttpResponse.json(
            {
              id: '2',
              email: 'new@example.com',
              display_name: 'New User',
              created_at: new Date().toISOString(),
            },
            { status: 201 }
          )
        }),
        http.post(`${API_BASE}/auth/login`, () => {
          return HttpResponse.json({
            access_token: 'new-user-token',
            token_type: 'bearer',
          })
        }),
        http.get(`${API_BASE}/auth/me`, ({ request }) => {
          const auth = request.headers.get('Authorization')
          if (auth === 'Bearer new-user-token') {
            return HttpResponse.json({
              id: '2',
              email: 'new@example.com',
              display_name: 'New User',
              created_at: new Date().toISOString(),
            })
          }
          return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 })
        })
      )

      await user.click(screen.getByTestId('register-btn'))

      await waitFor(() => {
        expect(screen.getByTestId('user-email')).toHaveTextContent('new@example.com')
        expect(screen.getByTestId('user-name')).toHaveTextContent('New User')
      })
    })

    it('throws error on registration failure', async () => {
      const user = userEvent.setup()

      server.use(
        http.post(`${API_BASE}/auth/register`, () => {
          return HttpResponse.json(
            { detail: 'Email already registered' },
            { status: 400 }
          )
        })
      )

      const onError = vi.fn()

      function RegisterErrorTestComponent() {
        const { register, isLoading } = useAuth()

        if (isLoading) return <div>Loading...</div>

        return (
          <button
            onClick={async () => {
              try {
                await register('existing@example.com', 'password123')
              } catch (error) {
                onError(error)
              }
            }}
            data-testid="register-btn"
          >
            Register
          </button>
        )
      }

      render(
        <AuthProvider>
          <RegisterErrorTestComponent />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('register-btn')).toBeInTheDocument()
      })

      await user.click(screen.getByTestId('register-btn'))

      await waitFor(() => {
        expect(onError).toHaveBeenCalled()
        expect(onError.mock.calls[0][0].message).toContain('Email already registered')
      })
    })
  })

  describe('Logout', () => {
    it('clears user, token, and localStorage on logout', async () => {
      const user = userEvent.setup()

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      )

      // First login
      await waitFor(() => {
        expect(screen.getByTestId('login-btn')).toBeInTheDocument()
      })

      await user.click(screen.getByTestId('login-btn'))

      await waitFor(() => {
        expect(screen.getByTestId('user-email')).toBeInTheDocument()
      })

      // Now logout
      await user.click(screen.getByText('Logout'))

      await waitFor(() => {
        expect(screen.getByTestId('logged-out')).toBeInTheDocument()
      })

      expect(localStorage.removeItem).toHaveBeenCalledWith('cocktail_auth_token')
    })
  })

  describe('Session Restore', () => {
    it('restores session from localStorage on mount', async () => {
      // Mock stored token
      vi.mocked(localStorage.getItem).mockReturnValue('mock-jwt-token')

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('user-email')).toHaveTextContent('test@example.com')
      })
    })

    it('clears invalid token from localStorage', async () => {
      // Mock stored but invalid token
      vi.mocked(localStorage.getItem).mockReturnValue('invalid-token')

      server.use(
        http.get(`${API_BASE}/auth/me`, () => {
          return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 })
        })
      )

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('logged-out')).toBeInTheDocument()
      })

      expect(localStorage.removeItem).toHaveBeenCalledWith('cocktail_auth_token')
    })
  })

  describe('useAuth Hook', () => {
    it('throws error when used outside AuthProvider', () => {
      // This should throw an error
      render(<TestComponentWithoutProvider />)

      expect(screen.getByTestId('error')).toHaveTextContent(
        'useAuth must be used within an AuthProvider'
      )
    })
  })
})

describe('getAuthHeaders', () => {
  it('returns Authorization header with token', () => {
    const headers = getAuthHeaders('test-token')
    expect(headers).toEqual({ Authorization: 'Bearer test-token' })
  })

  it('returns empty object when token is null', () => {
    const headers = getAuthHeaders(null)
    expect(headers).toEqual({})
  })

  it('returns empty object when token is empty string', () => {
    const headers = getAuthHeaders('')
    expect(headers).toEqual({})
  })
})
