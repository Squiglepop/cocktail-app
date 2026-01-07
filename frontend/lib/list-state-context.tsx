'use client';

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode, useRef } from 'react';
import { RecipeFilters } from './api';

const STORAGE_KEY = 'recipe-list-state';
const SCROLL_DEBOUNCE_MS = 100;

// Extended filters type matching page.tsx
export interface ExtendedFilters extends RecipeFilters {
  favourites_only?: string;
}

interface ListState {
  filters: ExtendedFilters;
  scrollTop: number;
}

interface ListStateContextType {
  filters: ExtendedFilters;
  setFilters: (filters: ExtendedFilters | ((prev: ExtendedFilters) => ExtendedFilters)) => void;
  scrollTop: number;
  saveScrollPosition: (scrollTop: number) => void;
  getScrollPosition: () => number;
  clearState: () => void;
}

const ListStateContext = createContext<ListStateContextType | undefined>(undefined);

// Storage helpers
function loadState(): ListState {
  if (typeof window === 'undefined') {
    return { filters: {}, scrollTop: 0 };
  }
  try {
    const stored = sessionStorage.getItem(STORAGE_KEY);
    if (stored) {
      const parsed = JSON.parse(stored);
      return {
        filters: parsed.filters || {},
        scrollTop: parsed.scrollTop || 0,
      };
    }
  } catch {
    // Ignore parse errors
  }
  return { filters: {}, scrollTop: 0 };
}

function saveState(state: ListState): void {
  if (typeof window === 'undefined') return;
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch {
    // Ignore storage errors
  }
}

export function ListStateProvider({ children }: { children: ReactNode }) {
  // Initialize from session storage
  const [filters, setFiltersState] = useState<ExtendedFilters>(() => loadState().filters);
  const [scrollTop, setScrollTop] = useState<number>(() => loadState().scrollTop);
  const [isHydrated, setIsHydrated] = useState(false);

  // Debounce timer ref
  const scrollDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Hydrate from session storage on mount (client-side only)
  useEffect(() => {
    const state = loadState();
    setFiltersState(state.filters);
    setScrollTop(state.scrollTop);
    setIsHydrated(true);
  }, []);

  // Persist filters to session storage when they change
  useEffect(() => {
    if (!isHydrated) return;
    saveState({ filters, scrollTop });
  }, [filters, scrollTop, isHydrated]);

  // Wrapped setFilters that supports functional updates
  const setFilters = useCallback((
    newFilters: ExtendedFilters | ((prev: ExtendedFilters) => ExtendedFilters)
  ) => {
    setFiltersState((prev) => {
      const next = typeof newFilters === 'function' ? newFilters(prev) : newFilters;
      return next;
    });
  }, []);

  // Debounced scroll position save
  const saveScrollPosition = useCallback((newScrollTop: number) => {
    // Clear existing debounce timer
    if (scrollDebounceRef.current) {
      clearTimeout(scrollDebounceRef.current);
    }

    // Debounce the state update and persist
    scrollDebounceRef.current = setTimeout(() => {
      setScrollTop(newScrollTop);
    }, SCROLL_DEBOUNCE_MS);
  }, []);

  // Get current scroll position (for restoring on mount)
  const getScrollPosition = useCallback(() => {
    return scrollTop;
  }, [scrollTop]);

  // Clear all state (useful for "clear filters" button)
  const clearState = useCallback(() => {
    setFiltersState({});
    setScrollTop(0);
    if (typeof window !== 'undefined') {
      sessionStorage.removeItem(STORAGE_KEY);
    }
  }, []);

  // Cleanup debounce timer on unmount
  useEffect(() => {
    return () => {
      if (scrollDebounceRef.current) {
        clearTimeout(scrollDebounceRef.current);
      }
    };
  }, []);

  return (
    <ListStateContext.Provider
      value={{
        filters,
        setFilters,
        scrollTop,
        saveScrollPosition,
        getScrollPosition,
        clearState,
      }}
    >
      {children}
    </ListStateContext.Provider>
  );
}

export function useListState() {
  const context = useContext(ListStateContext);
  if (context === undefined) {
    throw new Error('useListState must be used within a ListStateProvider');
  }
  return context;
}
