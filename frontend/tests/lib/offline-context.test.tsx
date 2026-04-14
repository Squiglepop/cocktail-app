// Unmock the offline-context module — the global test setup mocks it,
// but we need the real implementation here.
vi.unmock('@/lib/offline-context');

import React from 'react';
import { render, screen, act, cleanup } from '@testing-library/react';
import { vi, beforeEach, afterEach } from 'vitest';
import { OfflineProvider, useOffline } from '@/lib/offline-context';
import { offlineDebug } from '@/lib/debug';

// Mock offline-storage to avoid real IndexedDB in these tests
vi.mock('@/lib/offline-storage', () => ({
  getCachedRecipeListItems: vi.fn().mockResolvedValue([]),
}));

function TestConsumer() {
  const { isOnline } = useOffline();
  return <div data-testid="status">{isOnline ? 'online' : 'offline'}</div>;
}

function renderWithProvider() {
  return render(
    <OfflineProvider>
      <TestConsumer />
    </OfflineProvider>
  );
}

describe('OfflineProvider health check', () => {
  let fetchSpy: ReturnType<typeof vi.spyOn>;
  let debugLogSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    vi.useFakeTimers();
    fetchSpy = vi.spyOn(globalThis, 'fetch');
    debugLogSpy = vi.spyOn(offlineDebug, 'log');
  });

  afterEach(() => {
    cleanup();
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  it('starts online (no flash of offline during hydration)', () => {
    fetchSpy.mockResolvedValue(new Response('ok', { status: 200 }));
    renderWithProvider();
    expect(screen.getByTestId('status')).toHaveTextContent('online');
  });

  it('uses an 8000ms timeout on the AbortController (AC-3)', async () => {
    // Track setTimeout calls to find the abort timeout
    const setTimeoutSpy = vi.spyOn(globalThis, 'setTimeout');

    fetchSpy.mockResolvedValue(new Response('ok', { status: 200 }));
    renderWithProvider();

    // Trigger the initial health check (2s delay)
    await act(async () => {
      vi.advanceTimersByTime(2000);
    });

    // Find the setTimeout call with 8000ms — that's the abort timeout
    const abortCall = setTimeoutSpy.mock.calls.find(
      (call) => call[1] === 8000
    );
    expect(abortCall).toBeDefined();

    setTimeoutSpy.mockRestore();
  });

  it('single health check failure does NOT flip isOnline to false (AC-2)', async () => {
    // First: succeed to establish online
    fetchSpy.mockResolvedValueOnce(new Response('ok', { status: 200 }));
    renderWithProvider();

    await act(async () => {
      vi.advanceTimersByTime(2000);
    });
    expect(screen.getByTestId('status')).toHaveTextContent('online');

    // Second: one failure — should stay online
    fetchSpy.mockRejectedValueOnce(new Error('Network error'));
    await act(async () => {
      vi.advanceTimersByTime(15000);
    });

    expect(screen.getByTestId('status')).toHaveTextContent('online');
  });

  it('two consecutive health check failures DO flip isOnline to false (AC-2)', async () => {
    // First: succeed to establish online
    fetchSpy.mockResolvedValueOnce(new Response('ok', { status: 200 }));
    renderWithProvider();

    await act(async () => {
      vi.advanceTimersByTime(2000);
    });
    expect(screen.getByTestId('status')).toHaveTextContent('online');

    // Second: first failure — stays online
    fetchSpy.mockRejectedValueOnce(new Error('Network error'));
    await act(async () => {
      vi.advanceTimersByTime(15000);
    });
    expect(screen.getByTestId('status')).toHaveTextContent('online');

    // Third: second consecutive failure — now offline
    fetchSpy.mockRejectedValueOnce(new Error('Network error'));
    await act(async () => {
      vi.advanceTimersByTime(15000);
    });
    expect(screen.getByTestId('status')).toHaveTextContent('offline');
  });

  it('a success after one failure resets the counter — subsequent single failure stays online (AC-2)', async () => {
    // Establish online
    fetchSpy.mockResolvedValueOnce(new Response('ok', { status: 200 }));
    renderWithProvider();

    await act(async () => {
      vi.advanceTimersByTime(2000);
    });

    // One failure
    fetchSpy.mockRejectedValueOnce(new Error('Network error'));
    await act(async () => {
      vi.advanceTimersByTime(15000);
    });
    expect(screen.getByTestId('status')).toHaveTextContent('online');

    // Success — resets counter
    fetchSpy.mockResolvedValueOnce(new Response('ok', { status: 200 }));
    await act(async () => {
      vi.advanceTimersByTime(15000);
    });
    expect(screen.getByTestId('status')).toHaveTextContent('online');

    // Another single failure — counter was reset, so stays online
    fetchSpy.mockRejectedValueOnce(new Error('Network error'));
    await act(async () => {
      vi.advanceTimersByTime(15000);
    });
    expect(screen.getByTestId('status')).toHaveTextContent('online');
  });

  it('after going offline (2 failures), a single success brings back online (AC-1)', async () => {
    // Establish online
    fetchSpy.mockResolvedValueOnce(new Response('ok', { status: 200 }));
    renderWithProvider();

    await act(async () => {
      vi.advanceTimersByTime(2000);
    });

    // Two failures → offline
    fetchSpy.mockRejectedValueOnce(new Error('Network error'));
    await act(async () => {
      vi.advanceTimersByTime(15000);
    });
    fetchSpy.mockRejectedValueOnce(new Error('Network error'));
    await act(async () => {
      vi.advanceTimersByTime(15000);
    });
    expect(screen.getByTestId('status')).toHaveTextContent('offline');

    // One success → back online
    fetchSpy.mockResolvedValueOnce(new Response('ok', { status: 200 }));
    await act(async () => {
      vi.advanceTimersByTime(15000);
    });
    expect(screen.getByTestId('status')).toHaveTextContent('online');
  });

  it('logs state transitions with failure count (AC-4)', async () => {
    // Establish online
    fetchSpy.mockResolvedValueOnce(new Response('ok', { status: 200 }));
    renderWithProvider();

    await act(async () => {
      vi.advanceTimersByTime(2000);
    });

    debugLogSpy.mockClear();

    // First failure — logs single failure, no transition
    fetchSpy.mockRejectedValueOnce(new Error('Network error'));
    await act(async () => {
      vi.advanceTimersByTime(15000);
    });
    expect(debugLogSpy).toHaveBeenCalledWith(
      expect.stringContaining('1 consecutive'),
      expect.anything()
    );
    expect(debugLogSpy).toHaveBeenCalledWith('Single failure — not transitioning to offline yet');

    debugLogSpy.mockClear();

    // Second failure — logs OFFLINE transition with failure count
    fetchSpy.mockRejectedValueOnce(new Error('Network error'));
    await act(async () => {
      vi.advanceTimersByTime(15000);
    });
    expect(debugLogSpy).toHaveBeenCalledWith(
      expect.stringContaining('OFFLINE transition')
    );

    debugLogSpy.mockClear();

    // Recovery — logs ONLINE transition
    fetchSpy.mockResolvedValueOnce(new Response('ok', { status: 200 }));
    await act(async () => {
      vi.advanceTimersByTime(15000);
    });
    expect(debugLogSpy).toHaveBeenCalledWith(
      'ONLINE transition: health check passed, failureCount reset'
    );
  });
});
