'use client';

import { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { RecipeListItem, RecipeFilters, fetchRecipes } from '@/lib/api';
import { FilterSidebar } from '@/components/recipes/FilterSidebar';
import { RecipeGrid } from '@/components/recipes/RecipeGrid';
import { Plus, Upload } from 'lucide-react';

export default function HomePage() {
  const [recipes, setRecipes] = useState<RecipeListItem[]>([]);
  const [filters, setFilters] = useState<RecipeFilters>({});
  const [loading, setLoading] = useState(true);

  const loadRecipes = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchRecipes(filters);
      setRecipes(data);
    } catch (error) {
      console.error('Failed to load recipes:', error);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    loadRecipes();
  }, [loadRecipes]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex gap-8">
        <FilterSidebar filters={filters} onFilterChange={setFilters} />
        <div className="flex-1">
          <div className="mb-6 flex items-start justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Cocktail Recipes</h1>
              <p className="text-gray-500 mt-1">
                {loading
                  ? 'Loading recipes...'
                  : `${recipes.length} recipe${recipes.length !== 1 ? 's' : ''} found`}
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
          <RecipeGrid recipes={recipes} loading={loading} />
        </div>
      </div>
    </div>
  );
}
