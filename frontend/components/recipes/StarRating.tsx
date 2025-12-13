'use client';

import { Star } from 'lucide-react';
import { RATING_CAPTIONS } from '@/lib/api';

interface StarRatingProps {
  rating?: number | null;
  onRate?: (rating: number) => void;
  size?: 'sm' | 'md' | 'lg';
  showCaption?: boolean;
  interactive?: boolean;
}

export function StarRating({
  rating,
  onRate,
  size = 'md',
  showCaption = false,
  interactive = false
}: StarRatingProps) {
  const sizeClasses = {
    sm: 'h-3 w-3',
    md: 'h-4 w-4',
    lg: 'h-5 w-5',
  };

  const gapClasses = {
    sm: 'gap-0.5',
    md: 'gap-1',
    lg: 'gap-1',
  };

  const handleClick = (starValue: number) => {
    if (interactive && onRate) {
      // If clicking the same rating, clear it
      if (rating === starValue) {
        onRate(0);
      } else {
        onRate(starValue);
      }
    }
  };

  if (!rating && !interactive) {
    return null;
  }

  return (
    <div className="flex flex-col">
      <div className={`flex items-center ${gapClasses[size]}`}>
        {[1, 2, 3, 4, 5].map((starValue) => (
          <button
            key={starValue}
            type="button"
            onClick={() => handleClick(starValue)}
            disabled={!interactive}
            className={`${interactive ? 'cursor-pointer hover:scale-110 transition-transform' : 'cursor-default'} disabled:cursor-default`}
            title={interactive ? RATING_CAPTIONS[starValue] : undefined}
          >
            <Star
              className={`${sizeClasses[size]} ${
                rating && starValue <= rating
                  ? 'fill-amber-400 text-amber-400'
                  : 'fill-none text-gray-300'
              }`}
            />
          </button>
        ))}
      </div>
      {showCaption && rating && RATING_CAPTIONS[rating] && (
        <span className="text-xs text-gray-500 mt-0.5 italic">
          {RATING_CAPTIONS[rating]}
        </span>
      )}
    </div>
  );
}
