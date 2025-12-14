'use client';

import { useQuery, useMutation, useQueryClient, useInfiniteQuery } from '@tanstack/react-query';
import {
  Recipe,
  RecipeListItem,
  RecipeFilters,
  RecipeCount,
  RecipeInput,
  Categories,
  fetchRecipes,
  fetchRecipe,
  fetchRecipeCount,
  fetchCategories,
  createRecipe,
  updateRecipe,
  deleteRecipe,
} from '@/lib/api';
import { queryKeys, STALE_TIMES } from '@/lib/query-client';

// Hook for fetching categories (static data - long cache)
export function useCategories() {
  return useQuery({
    queryKey: queryKeys.categories.all,
    queryFn: fetchCategories,
    staleTime: STALE_TIMES.categories,
    gcTime: STALE_TIMES.categories,
  });
}

// Hook for fetching recipe list with filters and pagination
export function useRecipes(
  filters: RecipeFilters = {},
  pagination: { skip?: number; limit?: number } = {},
  token?: string | null
) {
  return useQuery({
    queryKey: queryKeys.recipes.list({ ...filters, ...pagination, token }),
    queryFn: () => fetchRecipes(filters, pagination, token),
    staleTime: STALE_TIMES.recipes,
  });
}

// Hook for infinite scrolling recipes
export function useInfiniteRecipes(
  filters: RecipeFilters = {},
  pageSize: number = 20,
  token?: string | null
) {
  return useInfiniteQuery({
    queryKey: queryKeys.recipes.list({ ...filters, infinite: true, token }),
    queryFn: ({ pageParam = 0 }) =>
      fetchRecipes(filters, { skip: pageParam, limit: pageSize }, token),
    initialPageParam: 0,
    getNextPageParam: (lastPage, allPages) => {
      if (lastPage.length < pageSize) {
        return undefined; // No more pages
      }
      return allPages.reduce((acc, page) => acc + page.length, 0);
    },
    staleTime: STALE_TIMES.recipes,
  });
}

// Hook for fetching recipe count
export function useRecipeCount(filters: RecipeFilters = {}) {
  return useQuery({
    queryKey: queryKeys.recipes.count(filters),
    queryFn: () => fetchRecipeCount(filters),
    staleTime: STALE_TIMES.recipeCount,
  });
}

// Hook for fetching a single recipe
export function useRecipe(id: string | null | undefined, token?: string | null) {
  return useQuery({
    queryKey: queryKeys.recipes.detail(id || ''),
    queryFn: () => fetchRecipe(id!, token),
    enabled: !!id,
    staleTime: STALE_TIMES.recipe,
  });
}

// Hook for creating a recipe
export function useCreateRecipe() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ data, token }: { data: RecipeInput; token?: string | null }) =>
      createRecipe(data, token),
    onSuccess: (newRecipe) => {
      // Invalidate recipe list queries to refetch with new recipe
      queryClient.invalidateQueries({ queryKey: queryKeys.recipes.lists() });
      queryClient.invalidateQueries({ queryKey: queryKeys.recipes.counts() });

      // Add the new recipe to the cache
      queryClient.setQueryData(queryKeys.recipes.detail(newRecipe.id), newRecipe);
    },
  });
}

// Hook for updating a recipe with optimistic updates
export function useUpdateRecipe() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      id,
      data,
      token,
    }: {
      id: string;
      data: Partial<RecipeInput>;
      token?: string | null;
    }) => updateRecipe(id, data, token),
    onMutate: async ({ id, data }) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: queryKeys.recipes.detail(id) });

      // Snapshot the previous value
      const previousRecipe = queryClient.getQueryData<Recipe>(
        queryKeys.recipes.detail(id)
      );

      // Optimistically update the cache
      if (previousRecipe) {
        queryClient.setQueryData(queryKeys.recipes.detail(id), {
          ...previousRecipe,
          ...data,
          updated_at: new Date().toISOString(),
        });
      }

      return { previousRecipe };
    },
    onError: (_err, { id }, context) => {
      // Rollback on error
      if (context?.previousRecipe) {
        queryClient.setQueryData(queryKeys.recipes.detail(id), context.previousRecipe);
      }
    },
    onSettled: (_data, _error, { id }) => {
      // Refetch to ensure cache is in sync
      queryClient.invalidateQueries({ queryKey: queryKeys.recipes.detail(id) });
      queryClient.invalidateQueries({ queryKey: queryKeys.recipes.lists() });
    },
  });
}

// Type for infinite query data structure
interface InfiniteRecipeData {
  pages: RecipeListItem[][];
  pageParams: number[];
}

// Hook for deleting a recipe with optimistic updates
export function useDeleteRecipe() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, token }: { id: string; token?: string | null }) =>
      deleteRecipe(id, token),
    onMutate: async ({ id }) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: queryKeys.recipes.lists() });

      // Snapshot previous list data for potential rollback
      // Use unknown type since data could be flat array or infinite query structure
      const previousLists = queryClient.getQueriesData<unknown>({
        queryKey: queryKeys.recipes.lists(),
      });

      // Optimistically remove from all list caches
      // Handle both flat arrays (useRecipes) and infinite query structure (useInfiniteRecipes)
      queryClient.setQueriesData<unknown>(
        { queryKey: queryKeys.recipes.lists() },
        (old: unknown) => {
          if (!old) return old;

          // Check if it's an infinite query structure (has pages array)
          if (typeof old === 'object' && old !== null && 'pages' in old) {
            const infiniteData = old as InfiniteRecipeData;
            return {
              ...infiniteData,
              pages: infiniteData.pages.map((page) =>
                page.filter((recipe) => recipe.id !== id)
              ),
            };
          }

          // It's a flat array
          if (Array.isArray(old)) {
            return old.filter((recipe: RecipeListItem) => recipe.id !== id);
          }

          return old;
        }
      );

      return { previousLists };
    },
    onError: (_err, _variables, context) => {
      // Rollback on error
      context?.previousLists?.forEach(([queryKey, data]) => {
        queryClient.setQueryData(queryKey, data);
      });
    },
    onSettled: () => {
      // Refetch lists to ensure cache is in sync
      queryClient.invalidateQueries({ queryKey: queryKeys.recipes.lists() });
      queryClient.invalidateQueries({ queryKey: queryKeys.recipes.counts() });
    },
  });
}

// Utility hook to invalidate all recipe-related caches
export function useInvalidateRecipes() {
  const queryClient = useQueryClient();

  return {
    invalidateAll: () => queryClient.invalidateQueries({ queryKey: queryKeys.recipes.all }),
    invalidateLists: () => queryClient.invalidateQueries({ queryKey: queryKeys.recipes.lists() }),
    invalidateDetail: (id: string) =>
      queryClient.invalidateQueries({ queryKey: queryKeys.recipes.detail(id) }),
  };
}
