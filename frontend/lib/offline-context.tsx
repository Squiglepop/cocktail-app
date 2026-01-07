'use client';

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { getCachedRecipeListItems } from './offline-storage';
import { RecipeListItem } from './api';
import { offlineDebug as debug } from './debug';

interface OfflineContextType {
  isOnline: boolean;
  cachedRecipes: RecipeListItem[];
  cachedRecipesLoading: boolean;  // True until first IndexedDB load completes
  refreshCachedRecipes: () => Promise<void>;
}

const OfflineContext = createContext<OfflineContextType | undefined>(undefined);

export function OfflineProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  // Start with true to avoid flash of offline state during SSR hydration
  const [isOnline, setIsOnline] = useState(true);
  const [cachedRecipes, setCachedRecipes] = useState<RecipeListItem[]>([]);
  const [cachedRecipesLoading, setCachedRecipesLoading] = useState(true);

  // Browser online/offline events are UNRELIABLE in PWAs
  // They fire erratically and often claim "online" when we're actually offline
  // We ONLY use them to trigger an immediate health check, NOT to set state directly
  // The health check is the single source of truth for isOnline state

  // Actually TEST connectivity by making a real request (navigator.onLine lies)
  // This is the ONLY reliable way to detect offline in PWAs where service workers
  // serve cached content even when wifi is off
  const checkRealConnectivity = useCallback(async () => {
    try {
      // Use relative /health URL - Next.js rewrites proxy it to the backend
      // Add cache-busting param to prevent ANY caching (browser, CDN, etc)
      const healthUrl = `/health?_=${Date.now()}`;
      debug.log(`Checking connectivity: ${healthUrl}`);

      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 3000);

      const response = await fetch(healthUrl, {
        method: 'GET',
        cache: 'no-store',
        signal: controller.signal,
      });
      clearTimeout(timeout);

      if (!response.ok) throw new Error('Health check failed');

      debug.log('Health check passed - ONLINE');
      setIsOnline(true);
    } catch (error) {
      // Network request failed = actually offline
      debug.log('Health check failed - OFFLINE', error);
      setIsOnline(false);
    }
  }, []);

  // Refresh the list of cached recipes from IndexedDB
  const refreshCachedRecipes = useCallback(async () => {
    try {
      const recipes = await getCachedRecipeListItems();
      debug.log(`Loaded ${recipes.length} recipes from IndexedDB:`, recipes.map(r => r.name));
      setCachedRecipes(recipes);
    } catch (error) {
      debug.error('Failed to load cached recipes:', error);
      setCachedRecipes([]);
    } finally {
      setCachedRecipesLoading(false);
    }
  }, []);

  useEffect(() => {
    // Delay initial check to avoid competing with page load (prevents Android crashes)
    // Then check periodically (15s is less battery-draining than 5s)
    const initialCheck = setTimeout(checkRealConnectivity, 2000);
    const interval = setInterval(checkRealConnectivity, 15000);

    // Also check when browser fires online/offline events
    // (use them as triggers for immediate check, not as truth)
    const handleNetworkChange = () => {
      debug.log('Browser network event - triggering immediate health check');
      checkRealConnectivity();
    };

    window.addEventListener('online', handleNetworkChange);
    window.addEventListener('offline', handleNetworkChange);

    return () => {
      clearTimeout(initialCheck);
      clearInterval(interval);
      window.removeEventListener('online', handleNetworkChange);
      window.removeEventListener('offline', handleNetworkChange);
    };
  }, [checkRealConnectivity]);

  // Listen for recipe-cached/uncached events from favourites-context
  // This ensures cachedRecipes stays in sync when recipes are cached/removed
  useEffect(() => {
    const handleRecipeCached = (event: Event) => {
      const customEvent = event as CustomEvent<{ recipeId: string }>;
      debug.log(`Recipe cached: ${customEvent.detail.recipeId} - refreshing list`);
      refreshCachedRecipes();
    };

    const handleRecipeUncached = (event: Event) => {
      const customEvent = event as CustomEvent<{ recipeId: string }>;
      debug.log(`Recipe uncached: ${customEvent.detail.recipeId} - refreshing list`);
      refreshCachedRecipes();
    };

    window.addEventListener('recipe-cached', handleRecipeCached);
    window.addEventListener('recipe-uncached', handleRecipeUncached);
    return () => {
      window.removeEventListener('recipe-cached', handleRecipeCached);
      window.removeEventListener('recipe-uncached', handleRecipeUncached);
    };
  }, [refreshCachedRecipes]);

  // Load cached recipes on mount AND when going offline
  // Loading on mount ensures cachedRecipes is populated for fallback even if isOnline is wrong
  useEffect(() => {
    refreshCachedRecipes();
  }, [refreshCachedRecipes]);

  // Pre-cache the offline recipe page when online
  // Next.js prefetch handles client-side routing cache
  // Note: Removed iframe warming - it was causing Android crashes on navigation
  useEffect(() => {
    if (isOnline && typeof window !== 'undefined') {
      router.prefetch('/offline/recipe');
      debug.log('Prefetched /offline/recipe via Next.js router');
    }
  }, [isOnline, router]);

  // Also refresh when explicitly going offline
  useEffect(() => {
    if (!isOnline) {
      refreshCachedRecipes();
    }
  }, [isOnline, refreshCachedRecipes]);

  return (
    <OfflineContext.Provider
      value={{
        isOnline,
        cachedRecipes,
        cachedRecipesLoading,
        refreshCachedRecipes,
      }}
    >
      {children}
    </OfflineContext.Provider>
  );
}

export function useOffline() {
  const context = useContext(OfflineContext);
  if (context === undefined) {
    throw new Error('useOffline must be used within an OfflineProvider');
  }
  return context;
}
