import { render, screen, cleanup, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi, afterEach, beforeEach } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { DuplicateDetectionPanel } from '@/components/admin/DuplicateDetectionPanel'
import { http, HttpResponse } from 'msw'
import { server } from '../../mocks/server'
import { mockDuplicateIngredientResponse } from '../../mocks/handlers'

let queryClient: QueryClient

beforeEach(() => {
  queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 }, mutations: { retry: false } },
  })
})

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
  queryClient.clear()
})

function renderPanel(token: string | null = 'fake-token') {
  return render(
    <QueryClientProvider client={queryClient}>
      <DuplicateDetectionPanel token={token} />
    </QueryClientProvider>
  )
}

describe('DuplicateDetectionPanel', () => {
  it('shows "Show Duplicates" button initially', () => {
    renderPanel()

    expect(screen.getByRole('button', { name: /show duplicates/i })).toBeInTheDocument()
    expect(screen.queryByText(/found/i)).not.toBeInTheDocument()
  })

  it('loads and displays duplicate groups', async () => {
    const user = userEvent.setup()
    renderPanel()

    await user.click(screen.getByRole('button', { name: /show duplicates/i }))

    await waitFor(() => {
      expect(screen.getByText(/1 group with 1 potential duplicate/)).toBeInTheDocument()
    })
    expect(screen.getByText('Lime Juice')).toBeInTheDocument()
    expect(screen.getByText('lime juice')).toBeInTheDocument()
  })

  it('shows detection reason badges', async () => {
    const user = userEvent.setup()
    renderPanel()

    await user.click(screen.getByRole('button', { name: /show duplicates/i }))

    await waitFor(() => {
      expect(screen.getByText('Exact Match')).toBeInTheDocument()
    })
  })

  it('shows empty state when no duplicates found', async () => {
    server.use(
      http.get('*/api/admin/ingredients/duplicates', () =>
        HttpResponse.json({ groups: [], total_groups: 0, total_duplicates: 0 })
      )
    )
    const user = userEvent.setup()
    renderPanel()

    await user.click(screen.getByRole('button', { name: /show duplicates/i }))

    await waitFor(() => {
      expect(screen.getByText(/no duplicates detected/i)).toBeInTheDocument()
    })
  })

  it('opens merge preview modal on Merge click', async () => {
    const user = userEvent.setup()
    renderPanel()

    await user.click(screen.getByRole('button', { name: /show duplicates/i }))

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /^merge$/i })).toBeInTheDocument()
    })

    await user.click(screen.getByRole('button', { name: /^merge$/i }))

    await waitFor(() => {
      expect(screen.getByText('Merge Ingredients')).toBeInTheDocument()
    })
  })
})
