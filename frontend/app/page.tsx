'use client';

import { useState, useMemo, useRef, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { RecipeFilters } from '@/lib/api';
import { FilterSidebar } from '@/components/recipes/FilterSidebar';
import { RecipeGrid } from '@/components/recipes/RecipeGrid';
import { useAuth } from '@/lib/auth-context';
import { useFavourites } from '@/lib/favourites-context';
import { useInfiniteRecipes, useRecipeCount } from '@/lib/hooks';
import { Plus, Upload } from 'lucide-react';

const PAGE_SIZE = 20;

// Extended filters type to include favourites_only (client-side filter)
interface ExtendedFilters extends RecipeFilters {
  favourites_only?: string;
}

export default function HomePage() {
  const { token } = useAuth();
  const { favourites } = useFavourites();
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

  // Fetch recipes with infinite scroll
  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading,
  } = useInfiniteRecipes(apiFilters, PAGE_SIZE, token);

  // Fetch recipe count
  const { data: recipeCount } = useRecipeCount(apiFilters);

  // Flatten pages into a single array
  const recipes = useMemo(
    () => data?.pages.flatMap((page) => page) ?? [],
    [data]
  );

  // Filter recipes by favourites on the client side
  const displayedRecipes = useMemo(() => {
    if (!favourites_only) return recipes;
    return recipes.filter((recipe) => favourites.has(recipe.id));
  }, [recipes, favourites_only, favourites]);

  // Load more handler
  const loadMore = useCallback(() => {
    if (hasNextPage && !isFetchingNextPage) {
      fetchNextPage();
    }
  }, [hasNextPage, isFetchingNextPage, fetchNextPage]);

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

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Mobile layout */}
      <div className="md:hidden space-y-4">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Cocktail Recipes</h1>
          <p className="text-gray-500 mt-1">
            {isLoading
              ? 'Loading recipes...'
              : favourites_only
                ? `${displayedRecipes.length} favourite${displayedRecipes.length !== 1 ? 's' : ''}`
                : recipeCount
                  ? hasActiveFilters
                    ? `${recipeCount.filtered} of ${recipeCount.total} recipes`
                    : `${recipeCount.total} recipes`
                  : `${recipes.length} recipes`}
          </p>
        </div>

        {/* Action tiles - 3 in a row */}
        <div className="grid grid-cols-3 gap-2">
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
          <FilterSidebar
            filters={filters}
            onFilterChange={setFilters}
            variant="tile"
          />
        </div>

        {/* Recipe grid */}
        <RecipeGrid
          recipes={displayedRecipes}
          loading={isLoading}
          loadingMore={isFetchingNextPage}
          onLoadMore={loadMore}
        />
      </div>

      {/* Desktop layout */}
      <div className="hidden md:flex gap-8">
        <FilterSidebar
          filters={filters}
          onFilterChange={setFilters}
          className="w-64 shrink-0"
        />
        <div className="flex-1">
          <div className="mb-6 flex items-start justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Cocktail Recipes</h1>
              <p className="text-gray-500 mt-1">
                {isLoading
                  ? 'Loading recipes...'
                  : favourites_only
                    ? `${displayedRecipes.length} favourite${displayedRecipes.length !== 1 ? 's' : ''}`
                    : recipeCount
                      ? hasActiveFilters
                        ? `${recipeCount.filtered} of ${recipeCount.total} recipes`
                        : `${recipeCount.total} recipes`
                      : `${recipes.length} recipes`}
              </p>
            </div>
            <div className="flex gap-2">
              <Link href="/recipes/new" className="btn btn-secondary">
                <Plus className="h-4 w-4 mr-1" />
                Add Recipe
              </Link>
              <Link href="/upload" className="btn btn-primary">
                <Upload className="h-4 w-4 mr-1" />
                Extract from Image
              </Link>
            </div>
          </div>
          <RecipeGrid
            recipes={displayedRecipes}
            loading={isLoading}
            loadingMore={isFetchingNextPage}
            onLoadMore={loadMore}
          />
        </div>
      </div>

      {/* Scroll sentinel for infinite scroll - fallback for non-virtualized views */}
      <div ref={loadMoreRef} className="h-4" />
    </div>
  );
}
