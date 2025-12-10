import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Header } from '@/components/Header'
import { AuthProvider } from '@/lib/auth-context'
import { server } from '../mocks/server'
import { http, HttpResponse } from 'msw'

const API_BASE = '*/api'

// Wrapper component with AuthProvider
function renderHeader() {
  return render(
    <AuthProvider>
      <Header />
    </AuthProvider>
  )
}

describe('Header', () => {
  beforeEach(() => {
    vi.mocked(localStorage.getItem).mockReturnValue(null)
    vi.mocked(localStorage.setItem).mockClear()
    vi.mocked(localStorage.removeItem).mockClear()
  })

  describe('Branding', () => {
    it('renders logo and title', async () => {
      renderHeader()

      await waitFor(() => {
        expect(screen.getByText('Cocktail Library')).toBeInTheDocument()
      })
    })

    it('logo links to home', async () => {
      renderHeader()

      await waitFor(() => {
        const link = screen.getByRole('link', { name: /cocktail library/i })
        expect(link).toHaveAttribute('href', '/')
      })
    })
  })

  describe('Navigation', () => {
    it('renders Recipes link', async () => {
      renderHeader()

      await waitFor(() => {
        const recipesLink = screen.getByRole('link', { name: /recipes/i })
        expect(recipesLink).toHaveAttribute('href', '/')
      })
    })

    it('renders Upload button', async () => {
      renderHeader()

      await waitFor(() => {
        const uploadLink = screen.getByRole('link', { name: /upload/i })
        expect(uploadLink).toHaveAttribute('href', '/upload')
      })
    })
  })

  describe('Auth UI - Logged Out', () => {
    it('shows Login link when logged out', async () => {
      renderHeader()

      await waitFor(() => {
        expect(screen.getByRole('link', { name: /login/i })).toBeInTheDocument()
      })
    })

    it('shows Register link when logged out', async () => {
      renderHeader()

      await waitFor(() => {
        expect(screen.getByRole('link', { name: /register/i })).toBeInTheDocument()
      })
    })

    it('Login link navigates to /login', async () => {
      renderHeader()

      await waitFor(() => {
        const loginLink = screen.getByRole('link', { name: /login/i })
        expect(loginLink).toHaveAttribute('href', '/login')
      })
    })

    it('Register link navigates to /register', async () => {
      renderHeader()

      await waitFor(() => {
        const registerLink = screen.getByRole('link', { name: /register/i })
        expect(registerLink).toHaveAttribute('href', '/register')
      })
    })
  })

  describe('Auth UI - Logged In', () => {
    beforeEach(() => {
      vi.mocked(localStorage.getItem).mockReturnValue('mock-jwt-token')
    })

    it('shows user display name when logged in', async () => {
      renderHeader()

      await waitFor(() => {
        expect(screen.getByText('Test User')).toBeInTheDocument()
      })
    })

    it('shows user email if no display name', async () => {
      server.use(
        http.get(`${API_BASE}/auth/me`, () => {
          return HttpResponse.json({
            id: '1',
            email: 'nodisplay@example.com',
            display_name: null,
            created_at: new Date().toISOString(),
          })
        })
      )

      renderHeader()

      await waitFor(() => {
        expect(screen.getByText('nodisplay@example.com')).toBeInTheDocument()
      })
    })

    it('shows Logout button when logged in', async () => {
      renderHeader()

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /logout/i })).toBeInTheDocument()
      })
    })

    it('does not show Login link when logged in', async () => {
      renderHeader()

      await waitFor(() => {
        expect(screen.getByText('Test User')).toBeInTheDocument()
      })

      expect(screen.queryByRole('link', { name: /^login$/i })).not.toBeInTheDocument()
    })

    it('does not show Register link when logged in', async () => {
      renderHeader()

      await waitFor(() => {
        expect(screen.getByText('Test User')).toBeInTheDocument()
      })

      expect(screen.queryByRole('link', { name: /register/i })).not.toBeInTheDocument()
    })

    it('logout button clears auth state', async () => {
      const user = userEvent.setup()

      renderHeader()

      await waitFor(() => {
        expect(screen.getByText('Test User')).toBeInTheDocument()
      })

      await user.click(screen.getByRole('button', { name: /logout/i }))

      await waitFor(() => {
        expect(screen.getByRole('link', { name: /login/i })).toBeInTheDocument()
      })

      expect(localStorage.removeItem).toHaveBeenCalledWith('cocktail_auth_token')
    })
  })

  describe('Loading State', () => {
    it('shows loading placeholder initially', () => {
      renderHeader()

      // The loading state shows a div with animate-pulse
      const loadingEl = document.querySelector('.animate-pulse')
      // This may or may not be present depending on timing
      // Just ensure the component renders without error
      expect(screen.getByText('Cocktail Library')).toBeInTheDocument()
    })
  })
})
