'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { getCachedRecipeListItems } from './offline-storage';
import { RecipeListItem } from './api';

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
  useEffect(() => {
    // Set initial state from navigator
    if (typeof navigator !== 'undefined') {
      setIsOnline(navigator.onLine);
    }

    const handleOnline = () => {
      setIsOnline(true);
    };

    const handleOffline = () => {
      setIsOnline(false);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // Load cached recipes when going offline (or on mount if offline)
  useEffect(() => {
    if (!isOnline) {
      refreshCachedRecipes();
    }
  }, [isOnline]);

  // Refresh the list of cached recipes from IndexedDB
  const refreshCachedRecipes = async () => {
    try {
      const recipes = await getCachedRecipeListItems();
      setCachedRecipes(recipes);
    } catch (error) {
      console.error('Failed to load cached recipes:', error);
      setCachedRecipes([]);
    }
  };

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
