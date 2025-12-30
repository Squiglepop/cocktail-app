import '@testing-library/jest-dom'
import 'fake-indexeddb/auto'  // Polyfill IndexedDB for jsdom environment
import { cleanup } from '@testing-library/react'
import { afterEach, beforeAll, afterAll, vi } from 'vitest'
import { server } from './mocks/server'

// Establish API mocking before all tests
beforeAll(() => {
  server.listen({ onUnhandledRequest: 'warn' })
})

// Reset any request handlers that are declared as a part of tests
afterEach(() => {
  cleanup()
  server.resetHandlers()
})

// Clean up after tests are finished
afterAll(() => {
  server.close()
})

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
})

// Mock IntersectionObserver
class MockIntersectionObserver {
  readonly root: Element | null = null;
  readonly rootMargin: string = '';
  readonly thresholds: ReadonlyArray<number> = [];

  constructor(private callback: IntersectionObserverCallback) {}

  observe() {}
  unobserve() {}
  disconnect() {}
  takeRecords(): IntersectionObserverEntry[] { return []; }
}

Object.defineProperty(window, 'IntersectionObserver', {
  writable: true,
  value: MockIntersectionObserver,
})

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
  usePathname: () => '/',
  useSearchParams: () => new URLSearchParams(),
}))

// Mock URL.createObjectURL and URL.revokeObjectURL
// Used by UploadDropzone for file previews
Object.defineProperty(URL, 'createObjectURL', {
  writable: true,
  value: vi.fn((blob: Blob) => `blob:mock-url-${Math.random()}`),
})

Object.defineProperty(URL, 'revokeObjectURL', {
  writable: true,
  value: vi.fn(),
})

// Mock the offline context to always be online in tests
// The real health check can fail in jsdom environment
vi.mock('@/lib/offline-context', async () => {
  const actual = await vi.importActual<typeof import('@/lib/offline-context')>('@/lib/offline-context')
  return {
    ...actual,
    useOffline: () => ({
      isOnline: true,
      cachedRecipes: [],
      cachedRecipesLoading: false,
      refreshCachedRecipes: vi.fn(),
    }),
  }
})

