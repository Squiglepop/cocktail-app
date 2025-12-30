'use client';

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { fetchRecipe, Recipe } from './api';
import {
  saveRecipeOffline,
  removeRecipeOffline,
  cacheRecipeImage,
  removeCachedImage,
  isRecipeCached,
  listCachedRecipeIds,
} from './offline-storage';
import { favouritesDebug as debug } from './debug';

// Storage interface - designed for easy swapping to different storage backends
interface FavouritesStorage {
  load(): Promise<string[]>;
  save(ids: string[]): Promise<void>;
}

// Current implementation: localStorage
const localStorageAdapter: FavouritesStorage = {
  async load(): Promise<string[]> {
    if (typeof window === 'undefined') return [];
    try {
      const stored = localStorage.getItem('cocktail_favourites');
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  },
  async save(ids: string[]): Promise<void> {
    if (typeof window === 'undefined') return;
    try {
      localStorage.setItem('cocktail_favourites', JSON.stringify(ids));
    } catch (error) {
      debug.error('Failed to save favourites:', error);
    }
  },
};

interface FavouritesContextType {
  favourites: Set<string>;
  isLoading: boolean;
  isFavourite: (id: string) => boolean;
  toggleFavourite: (id: string, recipe?: Recipe) => void;
  addFavourite: (id: string, recipe?: Recipe) => void;
  removeFavourite: (id: string) => void;
  favouriteCount: number;
}

const FavouritesContext = createContext<FavouritesContextType | undefined>(undefined);

const storage = localStorageAdapter;

/**
 * Get auth token from localStorage (for background operations)
 */
function getStoredToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('cocktail_auth_token');
}

/**
 * Cache a recipe for offline access (runs in background)
 * Dispatches 'recipe-cached' event on success so offline-context can refresh
 */
async function cacheRecipeForOffline(recipeId: string, recipe?: Recipe, token?: string | null): Promise<void> {
  try {
    // If recipe data was provided, use it; otherwise fetch it
    let recipeData = recipe;
    if (!recipeData) {
      // Use provided token or get from localStorage
      const authToken = token ?? getStoredToken();
      debug.log(`Fetching recipe ${recipeId} from API...`);
      recipeData = await fetchRecipe(recipeId, authToken);
    }

    // Save recipe data to IndexedDB
    await saveRecipeOffline(recipeData);
    debug.log(`Saved recipe ${recipeId} to IndexedDB`);

    // Cache the image if it has one
    if (recipeData.has_image) {
      await cacheRecipeImage(recipeId);
      debug.log(`Cached image for ${recipeId}`);
    }

    debug.log(`Cached recipe ${recipeId} for offline`);

    // Notify offline-context to refresh its cached recipes list
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('recipe-cached', { detail: { recipeId } }));
    }
  } catch (error) {
    // Don't break the favourite operation if caching fails
    debug.error(`Failed to cache recipe ${recipeId}:`, error);
    throw error; // Re-throw so caller knows it failed
  }
}

/**
 * Remove a recipe from offline cache (runs in background)
 * Dispatches 'recipe-uncached' event so offline-context can refresh
 */
async function uncacheRecipe(recipeId: string): Promise<void> {
  try {
    await removeRecipeOffline(recipeId);
    await removeCachedImage(recipeId);
    debug.log(`Removed recipe ${recipeId} from offline cache`);

    // Notify offline-context to refresh its cached recipes list
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('recipe-uncached', { detail: { recipeId } }));
    }
  } catch (error) {
    debug.warn('Failed to remove recipe from offline cache:', error);
  }
}

export function FavouritesProvider({ children }: { children: ReactNode }) {
  const [favourites, setFavourites] = useState<Set<string>>(new Set());
  const [isLoading, setIsLoading] = useState(true);

  // Load favourites on mount
  useEffect(() => {
    const loadFavourites = async () => {
      const ids = await storage.load();
      setFavourites(new Set(ids));
      setIsLoading(false);
    };
    loadFavourites();
  }, []);

  // Sync existing favourites to IndexedDB (for favourites added before offline feature)
  // Runs once after favourites are loaded
  useEffect(() => {
    if (isLoading || favourites.size === 0) return;

    const syncFavouritesToIndexedDB = async () => {
      const ids = Array.from(favourites);
      const token = getStoredToken();

      // Debug: Show what's actually in IndexedDB vs localStorage
      const cachedIds = await listCachedRecipeIds();
      debug.log(`Favourites in localStorage: ${ids.length}`, ids);
      debug.log(`Recipes in IndexedDB: ${cachedIds.length}`, cachedIds);
      debug.log(`Auth token available: ${!!token}`);

      // First, check which ones need syncing
      const needsSync: string[] = [];
      for (const id of ids) {
        try {
          const cached = await isRecipeCached(id);
          debug.log(`Recipe ${id} cached: ${cached}`);
          if (!cached) {
            needsSync.push(id);
          }
        } catch (err) {
          debug.log(`Recipe ${id} check failed:`, err);
          needsSync.push(id);
        }
      }

      if (needsSync.length === 0) {
        debug.log('All favourites already cached for offline');
        return;
      }

      debug.log(`Syncing ${needsSync.length} favourites to IndexedDB...`);

      // Sync all in parallel for speed
      const results = await Promise.allSettled(
        needsSync.map(id => cacheRecipeForOffline(id, undefined, token))
      );

      const succeeded = results.filter(r => r.status === 'fulfilled').length;
      const failed = results.filter(r => r.status === 'rejected').length;

      debug.log(`Sync complete: ${succeeded} succeeded, ${failed} failed`);
    };

    // Run sync in background
    syncFavouritesToIndexedDB();
  }, [isLoading, favourites.size]); // Only re-run when loading completes or count changes

  // Save favourites whenever they change (skip initial load)
  useEffect(() => {
    if (isLoading) return;
    storage.save(Array.from(favourites));
  }, [favourites, isLoading]);

  const isFavourite = useCallback((id: string) => {
    return favourites.has(id);
  }, [favourites]);

  const addFavourite = useCallback((id: string, recipe?: Recipe) => {
    setFavourites((prev) => {
      const next = new Set(prev);
      next.add(id);
      return next;
    });
    // Cache for offline in background (don't await)
    cacheRecipeForOffline(id, recipe).catch((err) => {
      debug.error(`Failed to cache recipe ${id}:`, err);
    });
  }, []);

  const removeFavourite = useCallback((id: string) => {
    setFavourites((prev) => {
      const next = new Set(prev);
      next.delete(id);
      return next;
    });
    // Remove from offline cache in background (don't await)
    uncacheRecipe(id);
  }, []);

  const toggleFavourite = useCallback((id: string, recipe?: Recipe) => {
    // Track state inside setState callback to avoid dependency on favourites
    let wasFavourite = false;

    setFavourites((prev) => {
      wasFavourite = prev.has(id);
      const next = new Set(prev);
      if (wasFavourite) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });

    // Defer async operations to after state update using queueMicrotask
    queueMicrotask(() => {
      if (wasFavourite) {
        debug.log(`Removing recipe ${id} from cache`);
        uncacheRecipe(id);
      } else {
        debug.log(`Caching recipe ${id} for offline`);
        cacheRecipeForOffline(id, recipe).catch((err) => {
          debug.error(`Failed to cache recipe ${id}:`, err);
        });
      }
    });
  }, []); // Empty deps - no re-creation on state changes!

  return (
    <FavouritesContext.Provider
      value={{
        favourites,
        isLoading,
        isFavourite,
        toggleFavourite,
        addFavourite,
        removeFavourite,
        favouriteCount: favourites.size,
      }}
    >
      {children}
    </FavouritesContext.Provider>
  );
}

export function useFavourites() {
  const context = useContext(FavouritesContext);
  if (context === undefined) {
    throw new Error('useFavourites must be used within a FavouritesProvider');
  }
  return context;
}
