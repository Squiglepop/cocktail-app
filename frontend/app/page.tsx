'use client';

import { useEffect, useState, useCallback, useRef, useMemo } from 'react';
import Link from 'next/link';
import { RecipeListItem, RecipeFilters, RecipeCount, fetchRecipes, fetchRecipeCount } from '@/lib/api';
import { FilterSidebar } from '@/components/recipes/FilterSidebar';
import { RecipeGrid } from '@/components/recipes/RecipeGrid';
import { useAuth } from '@/lib/auth-context';
import { useFavourites } from '@/lib/favourites-context';
import { Plus, Upload, GlassWater } from 'lucide-react';

const INITIAL_LIMIT = 20;
const LOAD_MORE_LIMIT = 20;

// Extended filters type to include favourites_only (client-side filter)
interface ExtendedFilters extends RecipeFilters {
  favourites_only?: string;
}

export default function HomePage() {
  const { token } = useAuth();
  const { favourites } = useFavourites();
  const [recipes, setRecipes] = useState<RecipeListItem[]>([]);
  const [filters, setFilters] = useState<ExtendedFilters>({});
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [recipeCount, setRecipeCount] = useState<RecipeCount | null>(null);
  const loadMoreRef = useRef<HTMLDivElement>(null);

  // Use ref to track current skip value to avoid stale closures
  const skipRef = useRef(0);

  // Extract favourites_only for client-side filtering (won't trigger API reload)
  const favourites_only = filters.favourites_only;

  // Memoize API filters to prevent unnecessary re-renders
  // Only include filters that actually go to the API
  const apiFiltersKey = useMemo(() => {
    return JSON.stringify({
      template: filters.template,
      main_spirit: filters.main_spirit,
      glassware: filters.glassware,
      serving_style: filters.serving_style,
      search: filters.search,
      min_rating: filters.min_rating,
    });
  }, [filters.template, filters.main_spirit, filters.glassware, filters.serving_style, filters.search, filters.min_rating]);

  const apiFilters: RecipeFilters = useMemo(() => JSON.parse(apiFiltersKey), [apiFiltersKey]);

  // Check if any filters are active
  const hasActiveFilters = Object.values(filters).some((v) => v);

  // Filter recipes by favourites on the client side
  const displayedRecipes = useMemo(() => {
    if (!favourites_only) return recipes;
    return recipes.filter((recipe) => favourites.has(recipe.id));
  }, [recipes, favourites_only, favourites]);

  // Load initial recipes and count
  const loadRecipes = useCallback(async () => {
    setLoading(true);
    setHasMore(true);
    skipRef.current = 0;
    try {
      const [data, count] = await Promise.all([
        fetchRecipes(apiFilters, { skip: 0, limit: INITIAL_LIMIT }, token),
        fetchRecipeCount(apiFilters),
      ]);
      setRecipes(data);
      setRecipeCount(count);
      skipRef.current = data.length;
      setHasMore(data.length === INITIAL_LIMIT);
    } catch (error) {
      console.error('Failed to load recipes:', error);
    } finally {
      setLoading(false);
    }
  }, [apiFilters, token]);

  // Load more recipes
  const loadMore = useCallback(async () => {
    if (loadingMore || !hasMore) return;

    setLoadingMore(true);
    try {
      const data = await fetchRecipes(apiFilters, { skip: skipRef.current, limit: LOAD_MORE_LIMIT }, token);
      if (data.length > 0) {
        setRecipes((prev) => [...prev, ...data]);
        skipRef.current += data.length;
      }
      setHasMore(data.length === LOAD_MORE_LIMIT);
    } catch (error) {
      console.error('Failed to load more recipes:', error);
    } finally {
      setLoadingMore(false);
    }
  }, [apiFilters, loadingMore, hasMore, token]);

  // Initial load and filter changes
  useEffect(() => {
    loadRecipes();
  }, [loadRecipes]);

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
            {loading
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
        <RecipeGrid recipes={displayedRecipes} loading={loading} loadingMore={loadingMore} onLoadMore={loadMore} />
      </div>

      {/* Desktop layout */}
      <div className="hidden md:flex gap-8">
        <FilterSidebar filters={filters} onFilterChange={setFilters} className="w-64 shrink-0" />
        <div className="flex-1">
          <div className="mb-6 flex items-start justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Cocktail Recipes</h1>
              <p className="text-gray-500 mt-1">
                {loading
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
          <RecipeGrid recipes={displayedRecipes} loading={loading} loadingMore={loadingMore} onLoadMore={loadMore} />
        </div>
      </div>

      {/* Scroll sentinel for infinite scroll - fallback for non-virtualized views */}
      <div ref={loadMoreRef} className="h-4" />
    </div>
  );
}
