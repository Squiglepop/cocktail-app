'use client';

import Link from 'next/link';
import { RecipeListItem, formatEnumValue, getRecipeImageUrl } from '@/lib/api';
import { GlassWater, Wine } from 'lucide-react';
import { StarRating } from './StarRating';

interface RecipeCardProps {
  recipe: RecipeListItem;
}

export function RecipeCard({ recipe }: RecipeCardProps) {
  return (
    <Link href={`/recipes/${recipe.id}`}>
      <div className="card hover:shadow-md transition-shadow cursor-pointer h-full">
        {/* Image placeholder or actual image */}
        <div className="aspect-[4/3] bg-gradient-to-br from-amber-100 to-amber-50 rounded-t-lg flex items-center justify-center relative overflow-hidden">
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

          {recipe.rating && (
            <StarRating rating={recipe.rating} size="sm" showCaption />
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
  );
}
