import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render } from '@testing-library/react'
import { ServiceWorkerRegistration } from '@/components/ServiceWorkerRegistration'

describe('ServiceWorkerRegistration', () => {
  let originalServiceWorker: ServiceWorkerContainer | undefined
  let consoleSpy: ReturnType<typeof vi.spyOn>
  let consoleErrorSpy: ReturnType<typeof vi.spyOn>

  beforeEach(() => {
    originalServiceWorker = navigator.serviceWorker
    consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {})
    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
  })

  afterEach(() => {
    // Restore original serviceWorker
    if (originalServiceWorker) {
      Object.defineProperty(navigator, 'serviceWorker', {
        value: originalServiceWorker,
        writable: true,
        configurable: true,
      })
    }
    consoleSpy.mockRestore()
    consoleErrorSpy.mockRestore()
  })

  it('renders nothing (returns null)', () => {
    const mockRegister = vi.fn().mockResolvedValue({ scope: '/' })
    Object.defineProperty(navigator, 'serviceWorker', {
      value: { register: mockRegister },
      writable: true,
      configurable: true,
    })

    const { container } = render(<ServiceWorkerRegistration />)

    expect(container.firstChild).toBeNull()
  })

  it('registers service worker when available', async () => {
    const mockRegister = vi.fn().mockResolvedValue({ scope: '/' })
    Object.defineProperty(navigator, 'serviceWorker', {
      value: { register: mockRegister },
      writable: true,
      configurable: true,
    })

    render(<ServiceWorkerRegistration />)

    // Wait for useEffect to run
    await vi.waitFor(() => {
      expect(mockRegister).toHaveBeenCalledWith('/sw.js')
    })
  })

  it('handles missing serviceWorker gracefully', () => {
    // Save original and delete serviceWorker from navigator - simulating browser that doesn't support it
    const originalDescriptor = Object.getOwnPropertyDescriptor(navigator, 'serviceWorker')

    // Delete the property entirely so 'serviceWorker' in navigator returns false
    delete (navigator as any).serviceWorker

    // Should not throw
    const { container } = render(<ServiceWorkerRegistration />)
    expect(container.firstChild).toBeNull()
    // Verify register was not called since serviceWorker doesn't exist
    expect(consoleSpy).not.toHaveBeenCalled()

    // Restore original
    if (originalDescriptor) {
      Object.defineProperty(navigator, 'serviceWorker', originalDescriptor)
    }
  })

  it('logs success on registration', async () => {
    const mockScope = '/test-scope/'
    const mockRegister = vi.fn().mockResolvedValue({ scope: mockScope })
    Object.defineProperty(navigator, 'serviceWorker', {
      value: { register: mockRegister },
      writable: true,
      configurable: true,
    })

    render(<ServiceWorkerRegistration />)

    await vi.waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith('Service Worker registered:', mockScope)
    })
  })

  it('logs error on registration failure', async () => {
    const mockError = new Error('Registration failed')
    const mockRegister = vi.fn().mockRejectedValue(mockError)
    Object.defineProperty(navigator, 'serviceWorker', {
      value: { register: mockRegister },
      writable: true,
      configurable: true,
    })

    render(<ServiceWorkerRegistration />)

    await vi.waitFor(() => {
      expect(consoleErrorSpy).toHaveBeenCalledWith('Service Worker registration failed:', mockError)
    })
  })
})
