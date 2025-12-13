'use client';

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';

// Storage interface - designed for easy swapping to different storage backends
// In the future, this could be replaced with IndexedDB, a backend API, or sync service
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
      console.error('Failed to save favourites:', error);
    }
  },
};

interface FavouritesContextType {
  favourites: Set<string>;
  isLoading: boolean;
  isFavourite: (id: string) => boolean;
  toggleFavourite: (id: string) => void;
  addFavourite: (id: string) => void;
  removeFavourite: (id: string) => void;
  favouriteCount: number;
}

const FavouritesContext = createContext<FavouritesContextType | undefined>(undefined);

// Use the localStorage adapter by default
// To switch storage backends in the future, replace this with a different adapter
const storage = localStorageAdapter;

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

  // Save favourites whenever they change (skip initial load)
  useEffect(() => {
    if (isLoading) return;
    storage.save(Array.from(favourites));
  }, [favourites, isLoading]);

  const isFavourite = useCallback((id: string) => {
    return favourites.has(id);
  }, [favourites]);

  const addFavourite = useCallback((id: string) => {
    setFavourites((prev) => {
      const next = new Set(prev);
      next.add(id);
      return next;
    });
  }, []);

  const removeFavourite = useCallback((id: string) => {
    setFavourites((prev) => {
      const next = new Set(prev);
      next.delete(id);
      return next;
    });
  }, []);

  const toggleFavourite = useCallback((id: string) => {
    setFavourites((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }, []);

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
