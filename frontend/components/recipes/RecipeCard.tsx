'use client';

import Link from 'next/link';
import { RecipeListItem, formatEnumValue, getRecipeImageUrl } from '@/lib/api';
import { GlassWater, Wine, Share2 } from 'lucide-react';
import { StarRating } from './StarRating';
import { AddToPlaylistButton } from '../playlists/AddToPlaylistButton';
import { shareRecipe } from '@/lib/share';

interface RecipeCardProps {
  recipe: RecipeListItem;
}

export function RecipeCard({ recipe }: RecipeCardProps) {
  const handleShare = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    await shareRecipe({
      id: recipe.id,
      name: recipe.name,
      hasImage: recipe.has_image,
    });
  };

  return (
    <div className="relative h-full group">
      {/* Action buttons - positioned outside Link to prevent stacking context issues */}
      <div className="absolute top-2 right-2 opacity-100 md:opacity-0 md:group-hover:opacity-100 transition-opacity flex gap-1 z-50">
        <button
          onClick={handleShare}
          className="p-2 bg-white/90 hover:bg-white rounded-full shadow-sm transition-colors"
          title="Share recipe"
        >
          <Share2 className="h-4 w-4 text-gray-600" />
        </button>
        <AddToPlaylistButton recipeId={recipe.id} variant="icon" />
      </div>

      <Link href={`/recipes/${recipe.id}`} className="block h-full">
        <div className="card hover:shadow-md transition-shadow cursor-pointer h-full">
          {/* Image placeholder or actual image */}
          <div className="aspect-[4/3] bg-gradient-to-br from-amber-100 to-amber-50 rounded-t-lg flex items-center justify-center overflow-hidden">
            {recipe.has_image ? (
              <img
                src={getRecipeImageUrl(recipe.id)}
                alt={recipe.name}
                className="w-full h-full object-cover object-top"
              />
            ) : (
              <GlassWater className="h-16 w-16 text-amber-300" />
            )}
          </div>

          <div className="p-4 space-y-2">
            <h3 className="font-semibold text-gray-900 line-clamp-1">
              {recipe.name}
            </h3>

            {recipe.my_rating && (
              <StarRating rating={recipe.my_rating} size="sm" showCaption />
            )}

            <div className="flex flex-wrap gap-1">
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
            </div>

            <div className="flex items-center gap-3 text-sm text-gray-500">
              {recipe.glassware && (
                <span className="flex items-center gap-1">
                  <Wine className="h-3 w-3" />
                  {formatEnumValue(recipe.glassware)}
                </span>
              )}
              {recipe.serving_style && (
                <span>{formatEnumValue(recipe.serving_style)}</span>
              )}
            </div>
          </div>
        </div>
      </Link>
    </div>
  );
}
