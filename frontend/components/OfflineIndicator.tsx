'use client';

import { WifiOff } from 'lucide-react';
import { useOffline } from '@/lib/offline-context';

export function OfflineIndicator() {
  const { isOnline, cachedRecipes } = useOffline();

  if (isOnline) {
    return null;
  }

  return (
    <div className="bg-amber-600 text-white px-4 py-2">
      <div className="max-w-7xl mx-auto flex items-center justify-center gap-2 text-sm">
        <WifiOff className="h-4 w-4" />
        <span>
          Offline mode - Showing {cachedRecipes.length} cached favourite{cachedRecipes.length !== 1 ? 's' : ''}
        </span>
      </div>
    </div>
  );
}
