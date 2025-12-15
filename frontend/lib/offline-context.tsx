'use client';

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { getCachedRecipeListItems } from './offline-storage';
import { RecipeListItem, API_BASE } from './api';

interface OfflineContextType {
  isOnline: boolean;
  cachedRecipes: RecipeListItem[];
  refreshCachedRecipes: () => Promise<void>;
}

const OfflineContext = createContext<OfflineContextType | undefined>(undefined);

export function OfflineProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  // Start with true to avoid flash of offline state during SSR hydration
  const [isOnline, setIsOnline] = useState(true);
  const [cachedRecipes, setCachedRecipes] = useState<RecipeListItem[]>([]);

  // Browser online/offline events are UNRELIABLE in PWAs
  // They fire erratically and often claim "online" when we're actually offline
  // We ONLY use them to trigger an immediate health check, NOT to set state directly
  // The health check is the single source of truth for isOnline state

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

    // Also check when browser fires online/offline events
    // (use them as triggers for immediate check, not as truth)
    const handleNetworkChange = () => {
      console.log('[OfflineContext] Browser network event - triggering immediate health check');
      checkRealConnectivity();
    };

    window.addEventListener('online', handleNetworkChange);
    window.addEventListener('offline', handleNetworkChange);

    return () => {
      clearInterval(interval);
      window.removeEventListener('online', handleNetworkChange);
      window.removeEventListener('offline', handleNetworkChange);
    };
  }, [checkRealConnectivity]);

  // Load cached recipes on mount AND when going offline
  // Loading on mount ensures cachedRecipes is populated for fallback even if isOnline is wrong
  useEffect(() => {
    refreshCachedRecipes();
  }, [refreshCachedRecipes]);

  // Pre-cache the offline recipe page (and its JS chunks) when online
  // This ensures the page works when user goes offline later
  // We use both Next.js prefetch AND a hidden iframe to ensure full caching
  useEffect(() => {
    if (isOnline && typeof window !== 'undefined') {
      // 1. Use Next.js router prefetch for client-side routing cache
      router.prefetch('/offline/recipe');
      console.log('[OfflineContext] Prefetched /offline/recipe via Next.js router');

      // 2. Also load the page in a hidden iframe to ensure SW caches ALL resources
      // This is a belt-and-suspenders approach since prefetch alone may not cache JS chunks
      const iframe = document.createElement('iframe');
      iframe.style.display = 'none';
      iframe.src = '/offline/recipe?warmup=true';
      iframe.onload = () => {
        console.log('[OfflineContext] Offline recipe page fully loaded in hidden iframe (cached by SW)');
        // Remove iframe after it loads to free resources
        setTimeout(() => iframe.remove(), 1000);
      };
      document.body.appendChild(iframe);
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
