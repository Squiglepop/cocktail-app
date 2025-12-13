'use client';

import { RecipeListItem } from '@/lib/api';
import { RecipeCard } from './RecipeCard';
import { GlassWater, Loader2 } from 'lucide-react';

interface RecipeGridProps {
  recipes: RecipeListItem[];
  loading?: boolean;
  loadingMore?: boolean;
}

export function RecipeGrid({ recipes, loading, loadingMore }: RecipeGridProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4 lg:gap-6">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="card animate-pulse">
            <div className="aspect-[4/3] bg-gray-200 rounded-t-lg"></div>
            <div className="p-4 space-y-3">
              <div className="h-5 bg-gray-200 rounded w-3/4"></div>
              <div className="h-4 bg-gray-200 rounded w-1/2"></div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (recipes.length === 0) {
    return (
      <div className="text-center py-12">
        <GlassWater className="h-16 w-16 text-gray-300 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          No recipes found
        </h3>
        <p className="text-gray-500">
          Try adjusting your filters or upload a new recipe screenshot.
        </p>
      </div>
    );
  }

  return (
    <>
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4 lg:gap-6">
        {recipes.map((recipe) => (
          <RecipeCard key={recipe.id} recipe={recipe} />
        ))}
      </div>
      {loadingMore && (
        <div className="flex justify-center py-6">
          <Loader2 className="h-6 w-6 animate-spin text-amber-600" />
        </div>
      )}
    </>
  );
}
