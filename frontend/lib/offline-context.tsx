'use client';

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { getCachedRecipeListItems } from './offline-storage';
import { RecipeListItem, API_BASE } from './api';

interface OfflineContextType {
  isOnline: boolean;
  cachedRecipes: RecipeListItem[];
  refreshCachedRecipes: () => Promise<void>;
}

const OfflineContext = createContext<OfflineContextType | undefined>(undefined);

export function OfflineProvider({ children }: { children: ReactNode }) {
  // Start with true to avoid flash of offline state during SSR hydration
  const [isOnline, setIsOnline] = useState(true);
  const [cachedRecipes, setCachedRecipes] = useState<RecipeListItem[]>([]);

  // Initialize online state and set up listeners
  // Note: navigator.onLine is unreliable in PWAs - service worker may serve cached
  // responses even when wifi is off, making browser think it's still "online"
  useEffect(() => {
    // Set initial state from navigator
    if (typeof navigator !== 'undefined') {
      console.log(`[OfflineContext] Initial navigator.onLine: ${navigator.onLine}`);
      setIsOnline(navigator.onLine);
    }

    const handleOnline = () => {
      console.log('[OfflineContext] Browser online event fired');
      setIsOnline(true);
    };

    const handleOffline = () => {
      console.log('[OfflineContext] Browser offline event fired');
      setIsOnline(false);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // Actually TEST connectivity by making a real request (navigator.onLine lies)
  // This is the ONLY reliable way to detect offline in PWAs where service workers
  // serve cached content even when wifi is off
  const checkRealConnectivity = useCallback(async () => {
    try {
      // Construct health URL from API_BASE (remove /api suffix, add /health)
      // Add cache-busting param to prevent ANY caching (browser, CDN, etc)
      const healthUrl = API_BASE.replace(/\/api\/?$/, '') + '/health?_=' + Date.now();
      console.log(`[OfflineContext] Checking connectivity: ${healthUrl}`);

      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 3000);

      const response = await fetch(healthUrl, {
        method: 'GET',
        cache: 'no-store',
        signal: controller.signal,
      });
      clearTimeout(timeout);

      if (!response.ok) throw new Error('Health check failed');

      console.log('[OfflineContext] Health check passed - ONLINE');
      setIsOnline(true);
    } catch (error) {
      // Network request failed = actually offline
      console.log('[OfflineContext] Health check failed - OFFLINE', error);
      setIsOnline(false);
    }
  }, []);

  // Refresh the list of cached recipes from IndexedDB
  const refreshCachedRecipes = useCallback(async () => {
    try {
      const recipes = await getCachedRecipeListItems();
      console.log(`[OfflineContext] Loaded ${recipes.length} recipes from IndexedDB:`, recipes.map(r => r.name));
      setCachedRecipes(recipes);
    } catch (error) {
      console.error('Failed to load cached recipes:', error);
      setCachedRecipes([]);
    }
  }, []);

  useEffect(() => {
    // Check immediately and periodically
    checkRealConnectivity();
    const interval = setInterval(checkRealConnectivity, 5000);

    return () => clearInterval(interval);
  }, [checkRealConnectivity]);

  // Load cached recipes on mount AND when going offline
  // Loading on mount ensures cachedRecipes is populated for fallback even if isOnline is wrong
  useEffect(() => {
    refreshCachedRecipes();
  }, [refreshCachedRecipes]);

  // Pre-cache the offline recipe page (and its JS chunks) when online
  // This ensures the page works when user goes offline later
  useEffect(() => {
    if (isOnline && typeof window !== 'undefined') {
      // Prefetch the offline recipe page to cache its JS chunks
      const link = document.createElement('link');
      link.rel = 'prefetch';
      link.href = '/offline/recipe';
      link.as = 'document';
      document.head.appendChild(link);
      console.log('[OfflineContext] Prefetched /offline/recipe for offline use');
    }
  }, [isOnline]);

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
