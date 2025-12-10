'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  Recipe,
  fetchRecipe,
  deleteRecipe,
  formatEnumValue,
  formatUnit,
  getImageUrl,
} from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import {
  ArrowLeft,
  GlassWater,
  Wine,
  Clock,
  Trash2,
  Pencil,
} from 'lucide-react';

export default function RecipeDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { user, token } = useAuth();
  const [recipe, setRecipe] = useState<Recipe | null>(null);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);

  // Check if current user is the owner of this recipe
  const isOwner = user && recipe && recipe.user_id === user.id;
  // Allow editing for recipes without an owner (backwards compatibility) or if user is owner
  const canEdit = recipe && (recipe.user_id === null || recipe.user_id === undefined || isOwner);

  useEffect(() => {
    if (params.id) {
      fetchRecipe(params.id as string)
        .then(setRecipe)
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [params.id]);

  const handleDelete = async () => {
    if (!recipe) return;
    if (!confirm('Are you sure you want to delete this recipe?')) return;

    setDeleting(true);
    try {
      await deleteRecipe(recipe.id, token);
      router.push('/');
    } catch (error) {
      console.error('Failed to delete:', error);
      alert(error instanceof Error ? error.message : 'Failed to delete recipe');
      setDeleting(false);
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
            Recipe not found
          </h2>
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

      <div className="grid md:grid-cols-2 gap-8">
        {/* Image */}
        <div>
          <div className="aspect-square bg-gradient-to-br from-amber-100 to-amber-50 rounded-lg flex items-center justify-center overflow-hidden">
            {recipe.source_image_path ? (
              <img
                src={getImageUrl(recipe.source_image_path)}
                alt={recipe.name}
                className="w-full h-full object-contain"
              />
            ) : (
              <GlassWater className="h-24 w-24 text-amber-300" />
            )}
          </div>
        </div>

        {/* Details */}
        <div className="space-y-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              {recipe.name}
            </h1>
            {recipe.description && (
              <p className="text-gray-600">{recipe.description}</p>
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
        </div>
      </div>

      {/* Instructions */}
      {recipe.instructions && (
        <div className="mt-8">
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
        <div className="mt-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">Notes</h2>
          <p className="text-gray-600">{recipe.notes}</p>
        </div>
      )}

      {/* Actions */}
      <div className="mt-8 pt-6 border-t border-gray-200 flex items-center justify-between">
        <div className="text-sm text-gray-500">
          Added {new Date(recipe.created_at).toLocaleDateString()}
          {recipe.source_type && ` via ${recipe.source_type}`}
        </div>
        {canEdit && (
          <div className="flex items-center gap-2">
            <Link
              href={`/recipes/${recipe.id}/edit`}
              className="btn btn-secondary"
            >
              <Pencil className="h-4 w-4 mr-2" />
              Edit
            </Link>
            <button
              onClick={handleDelete}
              disabled={deleting}
              className="btn btn-ghost text-red-600 hover:text-red-700 hover:bg-red-50"
            >
              <Trash2 className="h-4 w-4 mr-2" />
              {deleting ? 'Deleting...' : 'Delete'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
