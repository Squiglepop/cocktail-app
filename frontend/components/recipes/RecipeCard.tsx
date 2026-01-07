'use client';

import Link from 'next/link';
import Image from 'next/image';
import { RecipeListItem, formatEnumValue, getRecipeImageUrl } from '@/lib/api';
import { GlassWater, Wine, Share2, Heart, User } from 'lucide-react';
import { StarRating } from './StarRating';
import { AddToPlaylistButton } from '../playlists/AddToPlaylistButton';
import { shareRecipe } from '@/lib/share';
import { useFavourites } from '@/lib/favourites-context';
import { useOffline } from '@/lib/offline-context';
import { debug } from '@/lib/debug';

interface RecipeCardProps {
  recipe: RecipeListItem;
}

export function RecipeCard({ recipe }: RecipeCardProps) {
  const { isFavourite, toggleFavourite } = useFavourites();
  const { isOnline } = useOffline();
  const favourited = isFavourite(recipe.id);

  const handleShare = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    await shareRecipe({
      id: recipe.id,
      name: recipe.name,
      hasImage: recipe.has_image,
    });
  };

  const handleFavourite = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    toggleFavourite(recipe.id);
  };

  // When offline, navigate to the offline recipe viewer
  // Uses window.location for clean page navigation that service worker can intercept
  // (router.push triggers RSC prefetch which fails offline)
  const handleCardClick = (e: React.MouseEvent) => {
    if (!isOnline) {
      e.preventDefault();
      debug.log(`Offline navigation to /offline/recipe?id=${recipe.id}`);
      window.location.assign(`/offline/recipe?id=${recipe.id}`);
    }
    // When online, let the Link handle navigation normally
  };

  return (
    <div className="relative h-full group">
      {/* Action buttons - positioned outside Link to prevent stacking context issues */}
      <div className="absolute top-2 right-2 opacity-100 md:opacity-0 md:group-hover:opacity-100 transition-opacity flex gap-1 z-50">
        <button
          onClick={handleFavourite}
          className={`p-2 rounded-full shadow-sm transition-colors ${
            favourited
              ? 'bg-red-500 hover:bg-red-600'
              : 'bg-white/90 hover:bg-white'
          }`}
          title={favourited ? 'Remove from favourites' : 'Add to favourites'}
        >
          <Heart
            className={`h-4 w-4 ${
              favourited ? 'text-white fill-white' : 'text-gray-600'
            }`}
          />
        </button>
        <button
          onClick={handleShare}
          className="p-2 bg-white/90 hover:bg-white rounded-full shadow-sm transition-colors"
          title="Share recipe"
        >
          <Share2 className="h-4 w-4 text-gray-600" />
        </button>
        <AddToPlaylistButton recipeId={recipe.id} variant="icon" />
      </div>

      <Link href={`/recipes/${recipe.id}`} className="block h-full" onClick={handleCardClick}>
        <div className="card hover:shadow-md transition-shadow cursor-pointer h-full">
          {/* Image placeholder or actual image */}
          <div className="aspect-[4/3] bg-gradient-to-br from-amber-100 to-amber-50 rounded-t-lg flex items-center justify-center overflow-hidden relative">
            {recipe.has_image ? (
              <Image
                src={getRecipeImageUrl(recipe.id)}
                alt={recipe.name}
                fill
                sizes="(max-width: 768px) 50vw, 33vw"
                className="object-cover object-top"
                loading="lazy"
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

            {recipe.uploader_name && (
              <div className="flex items-center gap-1 text-xs text-gray-400">
                <User className="h-3 w-3" />
                <span>{recipe.uploader_name}</span>
              </div>
            )}
          </div>
        </div>
      </Link>
    </div>
  );
}
