'use client';

import Link from 'next/link';
import Image from 'next/image';
import { RecipeListItem, formatEnumValue, getRecipeImageUrl } from '@/lib/api';
import { GlassWater, Share2, Heart, User } from 'lucide-react';
import { GlasswareIcon } from '@/components/icons/GlasswareIcon';
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
        <div className="card hover:shadow-md transition-shadow cursor-pointer h-full flex flex-col overflow-hidden">
          {/* Hero image section with title overlay */}
          <div
            className="aspect-[3/4] relative flex-shrink-0"
            style={{
              isolation: 'isolate',
              contain: 'paint',
              backfaceVisibility: 'hidden',
              WebkitBackfaceVisibility: 'hidden',
            }}
          >
            {/* Background: image or buff fallback */}
            {recipe.has_image ? (
              <Image
                src={getRecipeImageUrl(recipe.id)}
                alt={recipe.name}
                fill
                sizes="(max-width: 768px) 50vw, 33vw"
                className="object-cover object-top"
                loading="lazy"
                style={{ backfaceVisibility: 'hidden' }}
              />
            ) : (
              <div className="absolute inset-0 bg-[#F5F0E6] flex items-center justify-center">
                <GlassWater className="h-20 w-20 text-amber-300/60" />
              </div>
            )}

            {/* Top gradient overlay - simplified 2-stop gradient for Android GPU stability */}
            <div
              className="absolute inset-x-0 top-0 h-24"
              style={{
                background: 'linear-gradient(to bottom, rgba(0,0,0,0.6) 0%, rgba(0,0,0,0) 100%)',
                backfaceVisibility: 'hidden',
                WebkitBackfaceVisibility: 'hidden',
              }}
            />

            {/* Title positioned at top */}
            <div className="absolute inset-x-0 top-0 p-3 pt-10">
              <h3 className="font-semibold text-white text-sm leading-tight line-clamp-2 drop-shadow-md">
                {recipe.name}
              </h3>
            </div>
          </div>

          {/* Info strip at bottom - badges stacked left, glassware right */}
          <div className="p-2 bg-white flex-shrink-0">
            <div className="flex justify-between items-start gap-2">
              {/* Left: badges stacked + uploader */}
              <div className="flex flex-col gap-1 min-w-0">
                {recipe.template && (
                  <span className="badge badge-amber text-xs px-1.5 py-0.5 w-fit">
                    {formatEnumValue(recipe.template)}
                  </span>
                )}
                {recipe.main_spirit && (
                  <span className="badge badge-gray text-xs px-1.5 py-0.5 w-fit">
                    {formatEnumValue(recipe.main_spirit)}
                  </span>
                )}
                {recipe.uploader_name && (
                  <div className="flex items-center gap-1 text-xs text-gray-400">
                    <User className="h-3 w-3 flex-shrink-0" />
                    <span className="truncate">{recipe.uploader_name}</span>
                  </div>
                )}
              </div>
              {/* Right: large glassware icon */}
              {recipe.glassware && (
                <div className="flex-shrink-0" title={formatEnumValue(recipe.glassware)}>
                  <GlasswareIcon glassware={recipe.glassware} className="h-14 w-14 text-gray-400" />
                </div>
              )}
            </div>
          </div>
        </div>
      </Link>
    </div>
  );
}
