import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '@/lib/auth-context';
import { OfflineProvider } from '@/lib/offline-context';
import { FavouritesProvider } from '@/lib/favourites-context';
import { ReactNode } from 'react';

// Create a new QueryClient for each test to avoid shared state
export function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
        staleTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  });
}

interface TestProviderProps {
  children: ReactNode;
  queryClient?: QueryClient;
}

export function TestProviders({ children, queryClient }: TestProviderProps) {
  const client = queryClient || createTestQueryClient();

  return (
    <QueryClientProvider client={client}>
      <AuthProvider>
        <OfflineProvider>
          <FavouritesProvider>
            {children}
          </FavouritesProvider>
        </OfflineProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}

// Wrapper factory for @testing-library/react render function
export function createTestWrapper(queryClient?: QueryClient) {
  const client = queryClient || createTestQueryClient();

  return function TestWrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={client}>
        <AuthProvider>
          <OfflineProvider>
            <FavouritesProvider>
              {children}
            </FavouritesProvider>
          </OfflineProvider>
        </AuthProvider>
      </QueryClientProvider>
    );
  };
}
