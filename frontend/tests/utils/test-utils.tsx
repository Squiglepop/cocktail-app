import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '@/lib/auth-context';
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
        <FavouritesProvider>
          {children}
        </FavouritesProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}
