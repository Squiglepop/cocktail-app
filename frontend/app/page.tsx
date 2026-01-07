'use client';

import { useState, useMemo, useRef, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { RecipeFilters } from '@/lib/api';
import { FilterSidebar } from '@/components/recipes/FilterSidebar';
import { RecipeGrid } from '@/components/recipes/RecipeGrid';
import { useAuth } from '@/lib/auth-context';
import { useFavourites } from '@/lib/favourites-context';
import { useOffline } from '@/lib/offline-context';
import { useInfiniteRecipes, useRecipeCount } from '@/lib/hooks';
import { Plus, Upload, WifiOff } from 'lucide-react';

const PAGE_SIZE = 20;

// Extended filters type to include favourites_only (client-side filter)
interface ExtendedFilters extends RecipeFilters {
  favourites_only?: string;
}

export default function HomePage() {
  const { token } = useAuth();
  const { favourites } = useFavourites();
  const { isOnline, cachedRecipes, cachedRecipesLoading, refreshCachedRecipes } = useOffline();
  const [filters, setFilters] = useState<ExtendedFilters>({});

  // Extract favourites_only for client-side filtering (won't trigger API reload)
  const favourites_only = filters.favourites_only;

  // API filters (excluding client-side only filters)
  const apiFilters: RecipeFilters = useMemo(() => {
    const { favourites_only: _, ...rest } = filters;
    return rest;
  }, [filters]);

  // Check if any filters are active
  const hasActiveFilters = Object.values(filters).some((v) => v);

  // Fetch recipes with infinite scroll (only when online)
  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading,
  } = useInfiniteRecipes(apiFilters, PAGE_SIZE, token, { enabled: isOnline });

  // Fetch recipe count (only when online)
  const { data: recipeCount } = useRecipeCount(apiFilters, token, { enabled: isOnline });

  // Refresh cached recipes when going offline
  useEffect(() => {
    if (!isOnline) {
      refreshCachedRecipes();
    }
  }, [isOnline, refreshCachedRecipes]);

  // Flatten pages into a single array
  const recipes = useMemo(
    () => data?.pages.flatMap((page) => page) ?? [],
    [data]
  );

  // Determine which recipes to display
  const displayedRecipes = useMemo(() => {
    console.log(`[HomePage] Computing displayedRecipes - isOnline: ${isOnline}, cachedRecipes: ${cachedRecipes.length}, recipes: ${recipes.length}, favourites_only: ${favourites_only}, isLoading: ${isLoading}`);

    // When explicitly offline, show cached recipes
    if (!isOnline) {
      console.log(`[HomePage] OFFLINE - showing ${cachedRecipes.length} cached recipes from IndexedDB`);
      return cachedRecipes;
    }

    // PRIORITY: If we have cached recipes and API has nothing (loading OR failed), show cached IMMEDIATELY
    // This prevents the empty screen flash while waiting for API
    if (recipes.length === 0 && cachedRecipes.length > 0) {
      console.log(`[HomePage] No API data yet, showing ${cachedRecipes.length} cached recipes`);
      return cachedRecipes;
    }

    // When online with favourites filter, filter from API results
    if (favourites_only) {
      const filtered = recipes.filter((recipe) => favourites.has(recipe.id));
      console.log(`[HomePage] ONLINE with favourites filter - showing ${filtered.length} of ${recipes.length}`);
      return filtered;
    }

    console.log(`[HomePage] ONLINE - showing ${recipes.length} recipes from API`);
    return recipes;
  }, [isOnline, cachedRecipes, recipes, favourites_only, favourites, isLoading]);

  // Load more handler (only works when online)
  const loadMore = useCallback(() => {
    if (isOnline && hasNextPage && !isFetchingNextPage) {
      fetchNextPage();
    }
  }, [isOnline, hasNextPage, isFetchingNextPage, fetchNextPage]);

  // Scroll sentinel ref for infinite scroll
  const loadMoreRef = useRef<HTMLDivElement>(null);

  // Infinite scroll observer
  useEffect(() => {
    const currentRef = loadMoreRef.current;
    if (!currentRef) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          loadMore();
        }
      },
      { threshold: 0, rootMargin: '200px' }
    );

    observer.observe(currentRef);

    return () => {
      observer.disconnect();
    };
  }, [loadMore]);

  // Recipe count text
  const getRecipeCountText = () => {
    if (!isOnline) {
      return `${cachedRecipes.length} cached favourite${cachedRecipes.length !== 1 ? 's' : ''}`;
    }
    if (isLoading) {
      return 'Loading recipes...';
    }
    if (favourites_only) {
      return `${displayedRecipes.length} favourite${displayedRecipes.length !== 1 ? 's' : ''}`;
    }
    if (recipeCount) {
      return hasActiveFilters
        ? `${recipeCount.filtered} of ${recipeCount.total} recipes`
        : `${recipeCount.total} recipes`;
    }
    return `${recipes.length} recipes`;
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Mobile layout */}
      <div className="md:hidden space-y-4">
        {/* Action tiles - 3 in a row */}
        <div className="grid grid-cols-3 gap-2">
          {isOnline ? (
            <>
              <Link
                href="/upload"
                className="card p-3 flex flex-col items-center justify-center text-center hover:shadow-md transition-shadow bg-amber-700 border-amber-800"
              >
                <Upload className="h-6 w-6 text-amber-100 mb-1" />
                <span className="text-xs font-medium text-white">Upload</span>
              </Link>
              <Link
                href="/recipes/new"
                className="card p-3 flex flex-col items-center justify-center text-center hover:shadow-md transition-shadow bg-amber-100 border-amber-300"
              >
                <Plus className="h-6 w-6 text-amber-800 mb-1" />
                <span className="text-xs font-medium text-amber-900">Add</span>
              </Link>
            </>
          ) : (
            <>
              <div className="card p-3 flex flex-col items-center justify-center text-center bg-gray-200 border-gray-300 opacity-50 cursor-not-allowed">
                <WifiOff className="h-6 w-6 text-gray-500 mb-1" />
                <span className="text-xs font-medium text-gray-600">Offline</span>
              </div>
              <div className="card p-3 flex flex-col items-center justify-center text-center bg-gray-200 border-gray-300 opacity-50 cursor-not-allowed">
                <Plus className="h-6 w-6 text-gray-500 mb-1" />
                <span className="text-xs font-medium text-gray-600">Add</span>
              </div>
            </>
          )}
          <FilterSidebar
            filters={filters}
            onFilterChange={setFilters}
            variant="tile"
            disabled={!isOnline}
          />
        </div>

        {/* Recipe count */}
        <p className="text-sm text-gray-500">{getRecipeCountText()}</p>

        {/* Recipe grid */}
        <RecipeGrid
          recipes={displayedRecipes}
          loading={(isOnline && isLoading) || (!isOnline && cachedRecipesLoading)}
          loadingMore={isOnline && isFetchingNextPage}
          onLoadMore={loadMore}
        />
      </div>

      {/* Desktop layout */}
      <div className="hidden md:flex gap-8">
        <FilterSidebar
          filters={filters}
          onFilterChange={setFilters}
          className="w-64 shrink-0"
          disabled={!isOnline}
        />
        <div className="flex-1">
          <div className="mb-4">
            {isOnline ? (
              <div className="flex gap-2 justify-end">
                <Link href="/recipes/new" className="btn btn-secondary">
                  <Plus className="h-4 w-4 mr-1" />
                  Add Recipe
                </Link>
                <Link href="/upload" className="btn btn-primary">
                  <Upload className="h-4 w-4 mr-1" />
                  Extract from Image
                </Link>
              </div>
            ) : (
              <div className="flex items-center gap-2 text-gray-500 text-sm justify-end">
                <WifiOff className="h-4 w-4" />
                <span>Upload disabled offline</span>
              </div>
            )}
            <p className="text-sm text-gray-500 mt-2">{getRecipeCountText()}</p>
          </div>
          <RecipeGrid
            recipes={displayedRecipes}
            loading={(isOnline && isLoading) || (!isOnline && cachedRecipesLoading)}
            loadingMore={isOnline && isFetchingNextPage}
            onLoadMore={loadMore}
          />
        </div>
      </div>

      {/* Scroll sentinel for infinite scroll - fallback for non-virtualized views */}
      {isOnline && <div ref={loadMoreRef} className="h-4" />}
    </div>
  );
}
