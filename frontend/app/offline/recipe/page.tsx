'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import Image from 'next/image';
import {
  Recipe,
  formatEnumValue,
  formatUnit,
  getRecipeImageUrl,
} from '@/lib/api';
import { getRecipeOffline } from '@/lib/offline-storage';
import { useFavourites } from '@/lib/favourites-context';
import {
  ArrowLeft,
  GlassWater,
  Wine,
  Clock,
  Heart,
  WifiOff,
} from 'lucide-react';
import { StarRating } from '@/components/recipes/StarRating';

/**
 * Static offline recipe viewer page.
 * This page is pre-cached by the service worker because it's a static route.
 * It reads the recipe ID from query params and loads from IndexedDB.
 */
export default function OfflineRecipePage() {
  return (
    <Suspense fallback={<OfflineRecipeLoading />}>
      <OfflineRecipeContent />
    </Suspense>
  );
}

function OfflineRecipeLoading() {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="animate-pulse space-y-8">
        <div className="h-8 bg-gray-200 rounded w-1/4"></div>
        <div className="space-y-4">
          <div className="h-8 bg-gray-200 rounded w-3/4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    </div>
  );
}

function OfflineRecipeContent() {
  const searchParams = useSearchParams();
  const recipeId = searchParams.get('id');
  const { favourites, toggleFavourite } = useFavourites();

  const [recipe, setRecipe] = useState<Recipe | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!recipeId) {
      setError('No recipe ID provided');
      setLoading(false);
      return;
    }

    console.log(`[OfflineRecipe] Loading recipe ${recipeId} from IndexedDB...`);
    getRecipeOffline(recipeId)
      .then((cached) => {
        console.log(`[OfflineRecipe] Result:`, cached ? 'FOUND' : 'NOT FOUND');
        if (cached) {
          setRecipe(cached);
        } else {
          setError('Recipe not found in offline cache');
        }
      })
      .catch((err) => {
        console.error(`[OfflineRecipe] Error:`, err);
        setError('Failed to load recipe from offline cache');
      })
      .finally(() => {
        setLoading(false);
      });
  }, [recipeId]);

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="animate-pulse space-y-8">
          <div className="h-8 bg-gray-200 rounded w-1/4"></div>
          <div className="space-y-4">
            <div className="h-8 bg-gray-200 rounded w-3/4"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
            <div className="space-y-2">
              <div className="h-4 bg-gray-200 rounded"></div>
              <div className="h-4 bg-gray-200 rounded"></div>
              <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !recipe) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center py-12">
          <GlassWater className="h-16 w-16 text-gray-300 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            {error || 'Recipe not available offline'}
          </h2>
          <p className="text-gray-500 mb-4">
            This recipe hasn&apos;t been favourited and cached for offline viewing.
          </p>
          <Link href="/" className="text-amber-600 hover:text-amber-700">
            Back to recipes
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Back button */}
      <Link
        href="/"
        className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-6"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to recipes
      </Link>

      {/* Offline indicator */}
      <div className="mb-6 flex items-center gap-2 text-amber-700 bg-amber-50 px-4 py-2 rounded-lg">
        <WifiOff className="h-4 w-4" />
        <span className="text-sm">Viewing cached version (offline)</span>
      </div>

      {/* Recipe Details */}
      <div className="space-y-6">
        <div>
          <div className="flex items-start justify-between gap-2">
            <h1 className="text-3xl font-bold text-gray-900">{recipe.name}</h1>
            <button
              onClick={() => toggleFavourite(recipe.id, recipe)}
              className="p-2 hover:bg-gray-100 rounded-full transition-colors flex-shrink-0 mt-1"
              title={
                favourites.has(recipe.id)
                  ? 'Remove from favourites'
                  : 'Add to favourites'
              }
            >
              <Heart
                className={`h-5 w-5 transition-colors ${
                  favourites.has(recipe.id)
                    ? 'fill-red-500 text-red-500'
                    : 'text-gray-600'
                }`}
              />
            </button>
          </div>
          {recipe.description && (
            <p className="text-gray-600 mt-2">{recipe.description}</p>
          )}
        </div>

        {/* Metadata badges */}
        <div className="flex flex-wrap gap-2">
          {recipe.template && (
            <span className="badge badge-amber">
              {formatEnumValue(recipe.template)}
            </span>
          )}
          {recipe.main_spirit && (
            <span className="badge badge-gray">
              {formatEnumValue(recipe.main_spirit)}
            </span>
          )}
          {recipe.method && (
            <span className="badge badge-gray">
              {formatEnumValue(recipe.method)}
            </span>
          )}
        </div>

        {/* Rating (read-only when offline) */}
        {recipe.my_rating && (
          <div className="flex items-center gap-3">
            <span className="text-sm font-medium text-gray-700">Your Rating:</span>
            <StarRating
              rating={recipe.my_rating}
              size="lg"
              showCaption
              interactive={false}
            />
          </div>
        )}

        {/* Glass and serving style */}
        <div className="flex flex-wrap gap-4 text-sm text-gray-600">
          {recipe.glassware && (
            <div className="flex items-center gap-1">
              <Wine className="h-4 w-4" />
              {formatEnumValue(recipe.glassware)}
            </div>
          )}
          {recipe.serving_style && (
            <div className="flex items-center gap-1">
              <Clock className="h-4 w-4" />
              Served {formatEnumValue(recipe.serving_style)}
            </div>
          )}
        </div>

        {/* Ingredients */}
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-3">
            Ingredients
          </h2>
          {recipe.ingredients.length > 0 ? (
            <ul className="space-y-2">
              {recipe.ingredients
                .sort((a, b) => a.order - b.order)
                .map((ri) => (
                  <li key={ri.id} className="flex items-baseline gap-2">
                    <span className="font-medium text-gray-900">
                      {ri.amount && (
                        <>
                          {ri.amount} {formatUnit(ri.unit, ri.amount)}{' '}
                        </>
                      )}
                      {ri.ingredient.name}
                    </span>
                    {ri.notes && (
                      <span className="text-sm text-gray-500">({ri.notes})</span>
                    )}
                    {ri.optional && (
                      <span className="text-xs text-gray-400">optional</span>
                    )}
                  </li>
                ))}
            </ul>
          ) : (
            <p className="text-gray-500 text-sm">No ingredients listed</p>
          )}
        </div>

        {/* Garnish */}
        {recipe.garnish && (
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-1">Garnish</h2>
            <p className="text-gray-600">{recipe.garnish}</p>
          </div>
        )}

        {/* Instructions */}
        {recipe.instructions && (
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-3">
              Instructions
            </h2>
            <div className="prose prose-amber max-w-none">
              <p className="text-gray-600 whitespace-pre-wrap">
                {recipe.instructions}
              </p>
            </div>
          </div>
        )}

        {/* Notes */}
        {recipe.notes && (
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-3">Notes</h2>
            <p className="text-gray-600">{recipe.notes}</p>
          </div>
        )}
      </div>

      {/* Screenshot */}
      {recipe.has_image && (
        <div className="mt-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">
            Original Screenshot
          </h2>
          <div className="bg-gradient-to-br from-amber-100 to-amber-50 rounded-lg overflow-hidden relative aspect-[4/3]">
            <Image
              src={getRecipeImageUrl(recipe.id)}
              alt={recipe.name}
              fill
              sizes="(max-width: 768px) 100vw, 800px"
              className="object-contain"
              loading="lazy"
            />
          </div>
        </div>
      )}

      {/* Date added */}
      <div className="mt-8 pt-6 border-t border-gray-200">
        <div className="text-sm text-gray-500 text-center">
          Added {new Date(recipe.created_at).toLocaleDateString()}
          {recipe.source_type && ` via ${recipe.source_type}`}
        </div>
      </div>
    </div>
  );
}
