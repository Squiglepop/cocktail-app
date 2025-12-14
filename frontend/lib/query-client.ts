import { QueryClient } from '@tanstack/react-query';

// Stale times for different data types
export const STALE_TIMES = {
  // Categories are static enums - cache for 24 hours
  categories: 24 * 60 * 60 * 1000,
  // Recipe list - cache for 5 minutes
  recipes: 5 * 60 * 1000,
  // Individual recipe - cache for 5 minutes
  recipe: 5 * 60 * 1000,
  // Recipe count - cache for 5 minutes
  recipeCount: 5 * 60 * 1000,
};

// Query keys for consistent cache management
export const queryKeys = {
  recipes: {
    all: ['recipes'] as const,
    lists: () => [...queryKeys.recipes.all, 'list'] as const,
    list: (filters: Record<string, unknown>) => [...queryKeys.recipes.lists(), filters] as const,
    details: () => [...queryKeys.recipes.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.recipes.details(), id] as const,
    count: (filters: Record<string, unknown>) => [...queryKeys.recipes.all, 'count', filters] as const,
  },
  categories: {
    all: ['categories'] as const,
  },
};

// Create a new QueryClient with default options
export function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        // Default stale time
        staleTime: STALE_TIMES.recipes,
        // Retry once on failure
        retry: 1,
        // Don't refetch on window focus by default (can override per query)
        refetchOnWindowFocus: false,
      },
    },
  });
}

// Singleton for client-side
let browserQueryClient: QueryClient | undefined = undefined;

export function getQueryClient() {
  if (typeof window === 'undefined') {
    // Server: always make a new query client
    return makeQueryClient();
  } else {
    // Browser: make a new query client if we don't already have one
    if (!browserQueryClient) {
      browserQueryClient = makeQueryClient();
    }
    return browserQueryClient;
  }
}
