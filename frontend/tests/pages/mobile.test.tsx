import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import MobilePage from '@/app/mobile/page'

// Mock next/navigation
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
    prefetch: vi.fn(),
  }),
  usePathname: () => '/mobile',
  useSearchParams: () => new URLSearchParams(),
}))

function renderMobilePage() {
  return render(<MobilePage />)
}

describe('MobilePage', () => {
  it('renders page title', () => {
    renderMobilePage()

    expect(screen.getByRole('heading', { name: /use on your phone/i })).toBeInTheDocument()
  })

  it('shows Option 1: Direct Access section', () => {
    renderMobilePage()

    expect(screen.getByRole('heading', { name: /option 1: open in phone browser/i })).toBeInTheDocument()
    expect(screen.getByText(/the easiest way/i)).toBeInTheDocument()
    expect(screen.getByText(/your_computer_ip:3000/i)).toBeInTheDocument()
  })

  it('shows Option 2: PWA installation section', () => {
    renderMobilePage()

    expect(screen.getByRole('heading', { name: /option 2: add to home screen/i })).toBeInTheDocument()
    expect(screen.getByText(/install as an app/i)).toBeInTheDocument()
  })

  it('shows iOS and Android instructions', () => {
    renderMobilePage()

    // Check for iOS instructions
    expect(screen.getByText(/ios \(safari\)/i)).toBeInTheDocument()
    // "Add to Home Screen" appears multiple times (iOS and Android)
    expect(screen.getAllByText(/add to home screen/i).length).toBeGreaterThanOrEqual(1)

    // Check for Android instructions
    expect(screen.getByText(/android \(chrome\)/i)).toBeInTheDocument()
    // "Install app" appears in text
    expect(screen.getAllByText(/install app/i).length).toBeGreaterThanOrEqual(1)
  })

  it('shows Option 3: iOS Shortcut section', () => {
    renderMobilePage()

    expect(screen.getByRole('heading', { name: /option 3: ios shortcut/i })).toBeInTheDocument()
    expect(screen.getByText(/create a shortcut/i)).toBeInTheDocument()
    expect(screen.getByText(/shortcuts app/i)).toBeInTheDocument()
  })

  it('Go to Upload Page link has correct href', () => {
    renderMobilePage()

    const uploadLink = screen.getByRole('link', { name: /go to upload page/i })
    expect(uploadLink).toHaveAttribute('href', '/upload')
  })
})
