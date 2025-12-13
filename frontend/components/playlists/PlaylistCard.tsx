'use client';

import Link from 'next/link';
import { CollectionListItem } from '@/lib/api';
import { ListMusic, Lock, Globe } from 'lucide-react';

interface PlaylistCardProps {
  playlist: CollectionListItem;
}

export function PlaylistCard({ playlist }: PlaylistCardProps) {
  return (
    <Link href={`/playlists/${playlist.id}`}>
      <div className="card hover:shadow-md transition-shadow cursor-pointer h-full">
        {/* Visual header */}
        <div className="aspect-[4/3] bg-gradient-to-br from-amber-100 to-amber-50 rounded-t-lg flex items-center justify-center relative overflow-hidden">
          <ListMusic className="h-16 w-16 text-amber-300" />
          {/* Privacy indicator */}
          <div className="absolute top-2 right-2" title={playlist.is_public ? "Public playlist" : "Private playlist"}>
            {playlist.is_public ? (
              <Globe className="h-4 w-4 text-amber-600" />
            ) : (
              <Lock className="h-4 w-4 text-gray-400" />
            )}
          </div>
        </div>

        <div className="p-4 space-y-2">
          <h3 className="font-semibold text-gray-900 line-clamp-1">
            {playlist.name}
          </h3>

          {playlist.description && (
            <p className="text-sm text-gray-500 line-clamp-2">
              {playlist.description}
            </p>
          )}

          <div className="flex items-center gap-2 text-sm text-gray-500">
            <span>
              {playlist.recipe_count} {playlist.recipe_count === 1 ? 'recipe' : 'recipes'}
            </span>
          </div>
        </div>
      </div>
    </Link>
  );
}
