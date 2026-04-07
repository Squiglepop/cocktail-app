# Frontend Architecture

**Stack:** Next.js 14 (App Router) | React 18 | TypeScript | Tailwind CSS | React Query

---

## Architecture Overview

```
┌────────────────────────────────────────────────────────────────────┐
│                        App Router (pages)                          │
│   app/page.tsx │ app/upload/page.tsx │ app/recipes/[id]/page.tsx  │
└────────────────────────────────┬───────────────────────────────────┘
                                 │
┌────────────────────────────────▼───────────────────────────────────┐
│                    Context Providers                               │
│   QueryProvider │ AuthProvider │ FavouritesProvider │ Offline     │
└────────────────────────────────┬───────────────────────────────────┘
                                 │
┌────────────────────────────────▼───────────────────────────────────┐
│                      Components                                    │
│   RecipeGrid │ RecipeCard │ FilterSidebar │ Header │ etc.         │
└────────────────────────────────┬───────────────────────────────────┘
                                 │
┌────────────────────────────────▼───────────────────────────────────┐
│                    Hooks & API Client                              │
│   useRecipes │ useCategories │ api.ts (fetch wrappers)            │
└────────────────────────────────┬───────────────────────────────────┘
                                 │
                          HTTP requests
                                 │
                                 ▼
                         Backend API
```

---

## Next.js App Router

The frontend uses Next.js 14's App Router, where the folder structure defines routes:

```
app/
├── layout.tsx          # Root layout (wraps everything)
├── page.tsx            # Home page (/)
├── upload/
│   └── page.tsx        # Upload page (/upload)
├── recipes/
│   ├── new/
│   │   └── page.tsx    # New recipe (/recipes/new)
│   └── [id]/           # Dynamic route
│       ├── page.tsx    # View recipe (/recipes/abc123)
│       └── edit/
│           └── page.tsx # Edit recipe (/recipes/abc123/edit)
```

### Client vs Server Components

By default, Next.js components are **server components**. For client-side interactivity, add `'use client'` at the top:

```tsx
'use client';  // This makes it a client component

import { useState } from 'react';

export default function HomePage() {
  const [filters, setFilters] = useState({});  // useState requires client
  // ...
}
```

---

## Provider Pattern

The app uses React Context for global state. All providers are composed in `layout.tsx`:

```tsx
// app/layout.tsx
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html>
      <body>
        <QueryProvider>           {/* React Query for server state */}
          <AuthProvider>          {/* User authentication */}
            <FavouritesProvider>  {/* Favorite recipes */}
              <OfflineProvider>   {/* Online/offline status */}
                <Header />
                {children}
              </OfflineProvider>
            </FavouritesProvider>
          </AuthProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
```

### AuthContext (`lib/auth-context.tsx`)

Manages user authentication state:

```tsx
interface AuthContextValue {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
}

// Usage in components
const { user, token, login, logout } = useAuth();
```

### FavouritesContext (`lib/favourites-context.tsx`)

Manages favorite recipe IDs (stored in localStorage):

```tsx
interface FavouritesContextValue {
  favourites: Set<string>;           // Set of recipe IDs
  addFavourite: (id: string) => void;
  removeFavourite: (id: string) => void;
  isFavourite: (id: string) => boolean;
}

// Usage
const { favourites, addFavourite, isFavourite } = useFavourites();
```

### OfflineContext (`lib/offline-context.tsx`)

Detects online/offline status and manages cached recipes:

```tsx
interface OfflineContextValue {
  isOnline: boolean;                    // Navigator.onLine
  cachedRecipes: RecipeListItem[];      // From IndexedDB
  cachedRecipesLoading: boolean;
  refreshCachedRecipes: () => void;
}
```

---

## React Query for Data Fetching

React Query (`@tanstack/react-query`) handles server state with caching, refetching, and loading states.

### Setup (`lib/query-provider.tsx`)

```tsx
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,  // 5 minutes before refetch
      gcTime: 30 * 60 * 1000,    // 30 minutes in cache
    },
  },
});

export function QueryProvider({ children }) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}
```

### Custom Hooks (`lib/hooks/use-recipes.ts`)

```tsx
// Fetch paginated recipes with infinite scroll
export function useInfiniteRecipes(
  filters: RecipeFilters,
  pageSize: number,
  token?: string | null,
  options?: { enabled?: boolean }
) {
  return useInfiniteQuery({
    queryKey: ['recipes', filters],  // Cache key
    queryFn: ({ pageParam = 0 }) =>
      fetchRecipes(filters, { skip: pageParam, limit: pageSize }, token),
    getNextPageParam: (lastPage, allPages) =>
      lastPage.length === pageSize ? allPages.length * pageSize : undefined,
    enabled: options?.enabled ?? true,
  });
}

// Usage in page
const { data, fetchNextPage, hasNextPage, isLoading } = useInfiniteRecipes(filters, 20);
```

---

## API Client (`lib/api.ts`)

Centralized fetch functions for all backend endpoints:

```tsx
export const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

// Fetch recipes with filters
export async function fetchRecipes(
  filters: RecipeFilters = {},
  pagination: PaginationParams = {},
  token?: string | null
): Promise<RecipeListItem[]> {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value) params.append(key, value);
  });

  const headers: Record<string, string> = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}/recipes?${params}`, { headers });
  if (!res.ok) throw new Error('Failed to fetch recipes');
  return res.json();
}

// Upload and extract recipe
export async function uploadAndExtract(files: File | File[]): Promise<Recipe> {
  const formData = new FormData();
  // ... append files
  const res = await fetch(`${API_BASE}/upload/extract-immediate`, {
    method: 'POST',
    body: formData,
  });
  return res.json();
}
```

---

## Component Patterns

### RecipeGrid (`components/recipes/RecipeGrid.tsx`)

Displays a grid of recipe cards:

```tsx
interface RecipeGridProps {
  recipes: RecipeListItem[];
  loading: boolean;
  loadingMore: boolean;
  onLoadMore: () => void;
}

export function RecipeGrid({ recipes, loading, loadingMore, onLoadMore }: RecipeGridProps) {
  if (loading) return <Skeleton />;

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
      {recipes.map((recipe) => (
        <RecipeCard key={recipe.id} recipe={recipe} />
      ))}
      {loadingMore && <LoadingSpinner />}
    </div>
  );
}
```

### RecipeCard (`components/recipes/RecipeCard.tsx`)

Single recipe card with image and metadata:

```tsx
export function RecipeCard({ recipe }: { recipe: RecipeListItem }) {
  const { isFavourite, toggleFavourite } = useFavourites();

  return (
    <Link href={`/recipes/${recipe.id}`}>
      <div className="card hover:shadow-lg transition-shadow">
        {recipe.has_image && (
          <img src={getRecipeImageUrl(recipe.id)} alt={recipe.name} />
        )}
        <h3>{recipe.name}</h3>
        <p>{formatEnumValue(recipe.template)}</p>
        <button onClick={(e) => { e.preventDefault(); toggleFavourite(recipe.id); }}>
          {isFavourite(recipe.id) ? '★' : '☆'}
        </button>
      </div>
    </Link>
  );
}
```

---

## Offline Support (PWA)

The app works offline using:

1. **Service Worker** (`public/sw.js`) - Caches static assets
2. **IndexedDB** (`lib/offline-storage.ts`) - Caches favorite recipes
3. **OfflineContext** - Detects online/offline status

```tsx
// Detecting offline status
useEffect(() => {
  const handleOnline = () => setIsOnline(true);
  const handleOffline = () => setIsOnline(false);

  window.addEventListener('online', handleOnline);
  window.addEventListener('offline', handleOffline);

  return () => {
    window.removeEventListener('online', handleOnline);
    window.removeEventListener('offline', handleOffline);
  };
}, []);
```

---

## Styling with Tailwind CSS

The app uses utility-first CSS with Tailwind:

```tsx
// Example component with Tailwind classes
<button className="
  px-4 py-2              /* padding */
  bg-amber-600           /* background color */
  hover:bg-amber-700     /* hover state */
  text-white             /* text color */
  rounded-lg             /* border radius */
  font-medium            /* font weight */
  transition-colors      /* smooth transitions */
">
  Upload Recipe
</button>
```

Custom styles are in `app/globals.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

/* Custom component classes */
.btn {
  @apply px-4 py-2 rounded-lg font-medium transition-colors;
}
.btn-primary {
  @apply bg-amber-600 hover:bg-amber-700 text-white;
}
.card {
  @apply bg-white rounded-lg shadow border border-gray-200 p-4;
}
```

---

## Testing with Vitest

Tests use Vitest with React Testing Library:

```tsx
// tests/components/RecipeCard.test.tsx
import { render, screen } from '@testing-library/react';
import { RecipeCard } from '@/components/recipes/RecipeCard';

describe('RecipeCard', () => {
  it('renders recipe name', () => {
    const recipe = { id: '1', name: 'Margarita', ... };
    render(<RecipeCard recipe={recipe} />);
    expect(screen.getByText('Margarita')).toBeInTheDocument();
  });
});
```
