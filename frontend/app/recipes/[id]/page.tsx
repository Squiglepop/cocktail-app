'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import Image from 'next/image';
import {
  Recipe,
  updateRecipeRating,
  formatEnumValue,
  formatUnit,
  getRecipeImageUrl,
} from '@/lib/api';
import { StarRating } from '@/components/recipes/StarRating';
import { useAuth } from '@/lib/auth-context';
import { useFavourites } from '@/lib/favourites-context';
import { useOffline } from '@/lib/offline-context';
import { useRecipe, useDeleteRecipe } from '@/lib/hooks';
import { getRecipeOffline } from '@/lib/offline-storage';
import { AddToPlaylistButton } from '@/components/playlists/AddToPlaylistButton';
import {
  ArrowLeft,
  GlassWater,
  Wine,
  Clock,
  Trash2,
  Pencil,
  ImagePlus,
  Share2,
  Heart,
  WifiOff,
} from 'lucide-react';
import { shareRecipe } from '@/lib/share';

export default function RecipeDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { user, token } = useAuth();
  const { favourites, toggleFavourite } = useFavourites();
  const { isOnline } = useOffline();
  const [updatingRating, setUpdatingRating] = useState(false);
  const [offlineRecipe, setOfflineRecipe] = useState<Recipe | null>(null);
  const [offlineLoading, setOfflineLoading] = useState(false);

  const recipeId = params.id as string;

  // Always try to fetch from API (will fail gracefully if offline)
  const { data: onlineRecipe, isLoading: onlineLoading, isError: onlineError, refetch } = useRecipe(
    recipeId,
    token
  );

  // Always load from IndexedDB as fallback (don't rely on isOnline - it's unreliable)
  useEffect(() => {
    if (recipeId) {
      setOfflineLoading(true);
      console.log(`[RecipeDetail] Trying to load recipe ${recipeId} from IndexedDB...`);
      getRecipeOffline(recipeId)
        .then((cached) => {
          console.log(`[RecipeDetail] IndexedDB result for ${recipeId}:`, cached ? 'FOUND' : 'NOT FOUND');
          setOfflineRecipe(cached || null);
        })
        .catch((err) => {
          console.error(`[RecipeDetail] IndexedDB error for ${recipeId}:`, err);
          setOfflineRecipe(null);
        })
        .finally(() => {
          setOfflineLoading(false);
        });
    }
  }, [recipeId]);

  // Use online recipe if fetch succeeded, otherwise fall back to IndexedDB cache
  const recipe = (!onlineError && onlineRecipe) ? onlineRecipe : offlineRecipe;
  const loading = onlineLoading && !offlineRecipe; // Show loading only if we don't have cached data

  // Delete mutation
  const deleteRecipeMutation = useDeleteRecipe();
  const deleting = deleteRecipeMutation.isPending;

  // Check if current user is the owner of this recipe
  const isOwner = user && recipe && recipe.user_id === user.id;
  // Allow editing for recipes without an owner (backwards compatibility) or if user is owner
  const canEdit = isOnline && recipe && (recipe.user_id === null || recipe.user_id === undefined || isOwner);

  const handleDelete = async () => {
    if (!recipe || !isOnline) return;
    if (!confirm('Are you sure you want to delete this recipe?')) return;

    try {
      await deleteRecipeMutation.mutateAsync({ id: recipe.id, token });
      router.push('/');
    } catch (error) {
      console.error('Failed to delete:', error);
      alert(error instanceof Error ? error.message : 'Failed to delete recipe');
    }
  };

  const handleShare = async () => {
    if (!recipe) return;
    await shareRecipe({
      id: recipe.id,
      name: recipe.name,
      hasImage: recipe.has_image,
    });
  };

  const handleRatingChange = async (newRating: number) => {
    if (!recipe || !user || !isOnline) return;

    setUpdatingRating(true);
    try {
      await updateRecipeRating(
        recipe.id,
        newRating === 0 ? null : newRating,
        token
      );
      // Refetch to update the cache
      refetch();
    } catch (error) {
      console.error('Failed to update rating:', error);
      alert(error instanceof Error ? error.message : 'Failed to update rating');
    } finally {
      setUpdatingRating(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="animate-pulse space-y-8">
          <div className="h-8 bg-gray-200 rounded w-1/4"></div>
          <div className="grid md:grid-cols-2 gap-8">
            <div className="aspect-square bg-gray-200 rounded-lg"></div>
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
      </div>
    );
  }

  if (!recipe) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center py-12">
          <GlassWater className="h-16 w-16 text-gray-300 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            {isOnline ? 'Recipe not found' : 'Recipe not cached offline'}
          </h2>
          {!isOnline && (
            <p className="text-gray-500 mb-4">
              This recipe hasn&apos;t been favourited and cached for offline viewing.
            </p>
          )}
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
      {!isOnline && (
        <div className="mb-6 flex items-center gap-2 text-amber-700 bg-amber-50 px-4 py-2 rounded-lg">
          <WifiOff className="h-4 w-4" />
          <span className="text-sm">Viewing cached version (offline)</span>
        </div>
      )}

      {/* Recipe Details */}
      <div className="space-y-6">
        <div>
          <div className="flex items-start justify-between gap-2">
            <h1 className="text-3xl font-bold text-gray-900">
              {recipe.name}
            </h1>
            <div className="flex items-center gap-1 flex-shrink-0 mt-1">
              <button
                onClick={() => toggleFavourite(recipe.id, recipe)}
                className="p-2 hover:bg-gray-100 rounded-full transition-colors"
                title={favourites.has(recipe.id) ? 'Remove from favourites' : 'Add to favourites'}
              >
                <Heart
                  className={`h-5 w-5 transition-colors ${
                    favourites.has(recipe.id)
                      ? 'fill-red-500 text-red-500'
                      : 'text-gray-600'
                  }`}
                />
              </button>
              <button
                onClick={handleShare}
                className="p-2 hover:bg-gray-100 rounded-full transition-colors"
                title="Share recipe"
              >
                <Share2 className="h-5 w-5 text-gray-600" />
              </button>
              {user && isOnline && (
                <AddToPlaylistButton recipeId={recipe.id} variant="icon" />
              )}
            </div>
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

        {/* Rating - shown for any authenticated user when online */}
        {user && isOnline && (
          <div className="flex items-center gap-3">
            <span className="text-sm font-medium text-gray-700">Your Rating:</span>
            <StarRating
              rating={recipe.my_rating}
              onRate={handleRatingChange}
              size="lg"
              showCaption
              interactive={!updatingRating}
            />
            {updatingRating && (
              <span className="text-sm text-gray-400">Saving...</span>
            )}
          </div>
        )}

        {/* Show rating (read-only) when offline */}
        {recipe.my_rating && !isOnline && (
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
                      <span className="text-sm text-gray-500">
                        ({ri.notes})
                      </span>
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
            <h2 className="text-lg font-semibold text-gray-900 mb-1">
              Garnish
            </h2>
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

      {/* Actions */}
      <div className="mt-8 pt-6 border-t border-gray-200 space-y-4">
        {/* Action buttons - only shown when online and user can edit */}
        {canEdit && (
          <div className="grid grid-cols-3 gap-2">
            <Link
              href={`/upload?enhance=${recipe.id}`}
              className="btn btn-secondary w-full justify-center"
            >
              <ImagePlus className="h-4 w-4 mr-1" />
              <span className="hidden sm:inline">Add </span>Images
            </Link>
            <Link
              href={`/recipes/${recipe.id}/edit`}
              className="btn btn-secondary w-full justify-center"
            >
              <Pencil className="h-4 w-4 mr-1" />
              Edit
            </Link>
            <button
              onClick={handleDelete}
              disabled={deleting}
              className="btn btn-ghost text-red-600 hover:text-red-700 hover:bg-red-50 w-full justify-center"
            >
              <Trash2 className="h-4 w-4 mr-1" />
              {deleting ? 'Deleting...' : 'Delete'}
            </button>
          </div>
        )}

        {/* Offline notice for actions */}
        {!isOnline && (
          <div className="text-center text-sm text-gray-500">
            <WifiOff className="h-4 w-4 inline mr-1" />
            Editing disabled while offline
          </div>
        )}

        {/* Date added */}
        <div className="text-sm text-gray-500 text-center">
          Added {new Date(recipe.created_at).toLocaleDateString()}
          {recipe.source_type && ` via ${recipe.source_type}`}
        </div>
      </div>
    </div>
  );
}
