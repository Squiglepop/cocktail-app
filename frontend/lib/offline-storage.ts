/**
 * Offline storage module using IndexedDB via the idb library.
 * Stores full recipe data for offline access when recipes are favourited.
 */

import { openDB, DBSchema, IDBPDatabase } from 'idb';
import { Recipe, RecipeListItem, getRecipeImageUrl } from './api';

// Database schema
interface CocktailOfflineDB extends DBSchema {
  recipes: {
    key: string;
    value: Recipe;
    indexes: { 'by-name': string };
  };
}

const DB_NAME = 'cocktail-offline-db';
const DB_VERSION = 1;

// Singleton database instance
let dbPromise: Promise<IDBPDatabase<CocktailOfflineDB>> | null = null;

/**
 * Get or create the database connection
 */
function getDB(): Promise<IDBPDatabase<CocktailOfflineDB>> {
  if (typeof window === 'undefined') {
    return Promise.reject(new Error('IndexedDB not available on server'));
  }

  if (!dbPromise) {
    dbPromise = openDB<CocktailOfflineDB>(DB_NAME, DB_VERSION, {
      upgrade(db) {
        // Create recipes store if it doesn't exist
        if (!db.objectStoreNames.contains('recipes')) {
          const store = db.createObjectStore('recipes', { keyPath: 'id' });
          store.createIndex('by-name', 'name');
        }
      },
    });
  }

  return dbPromise;
}

/**
 * Save a recipe to IndexedDB for offline access
 */
export async function saveRecipeOffline(recipe: Recipe): Promise<void> {
  const db = await getDB();
  await db.put('recipes', recipe);
}

/**
 * Remove a recipe from IndexedDB
 */
export async function removeRecipeOffline(recipeId: string): Promise<void> {
  const db = await getDB();
  await db.delete('recipes', recipeId);
}

/**
 * Get a recipe from IndexedDB by ID
 */
export async function getRecipeOffline(recipeId: string): Promise<Recipe | undefined> {
  const db = await getDB();
  return db.get('recipes', recipeId);
}

/**
 * Get all cached recipes from IndexedDB
 */
export async function getAllCachedRecipes(): Promise<Recipe[]> {
  const db = await getDB();
  return db.getAll('recipes');
}

/**
 * Get cached recipes as RecipeListItems (for gallery display)
 */
export async function getCachedRecipeListItems(): Promise<RecipeListItem[]> {
  const recipes = await getAllCachedRecipes();
  return recipes.map(recipeToListItem);
}

/**
 * Check if a recipe is cached offline
 */
export async function isRecipeCached(recipeId: string): Promise<boolean> {
  const recipe = await getRecipeOffline(recipeId);
  return recipe !== undefined;
}

/**
 * Get count of cached recipes
 */
export async function getCachedRecipeCount(): Promise<number> {
  const db = await getDB();
  return db.count('recipes');
}

/**
 * Clear all cached recipes (for debugging/testing)
 */
export async function clearAllCachedRecipes(): Promise<void> {
  const db = await getDB();
  await db.clear('recipes');
}

/**
 * Debug function to list all cached recipe IDs
 */
export async function listCachedRecipeIds(): Promise<string[]> {
  const db = await getDB();
  return db.getAllKeys('recipes');
}

/**
 * Convert a full Recipe to RecipeListItem for gallery display
 */
function recipeToListItem(recipe: Recipe): RecipeListItem {
  return {
    id: recipe.id,
    name: recipe.name,
    template: recipe.template,
    main_spirit: recipe.main_spirit,
    glassware: recipe.glassware,
    serving_style: recipe.serving_style,
    has_image: recipe.has_image,
    user_id: recipe.user_id,
    visibility: recipe.visibility,
    my_rating: recipe.my_rating,
    created_at: recipe.created_at,
  };
}

// ============================================================================
// Image Caching via Cache API (works with service worker)
// ============================================================================

const IMAGE_CACHE_NAME = 'cocktail-recipe-images-v1';

/**
 * Cache a recipe's image for offline access
 */
export async function cacheRecipeImage(recipeId: string): Promise<void> {
  if (typeof window === 'undefined' || !('caches' in window)) {
    return;
  }

  const imageUrl = getRecipeImageUrl(recipeId);

  try {
    const cache = await caches.open(IMAGE_CACHE_NAME);
    // Fetch and cache the image
    const response = await fetch(imageUrl);
    if (response.ok) {
      await cache.put(imageUrl, response);
    }
  } catch (error) {
    console.warn('Failed to cache recipe image:', error);
  }
}

/**
 * Remove a recipe's image from cache
 */
export async function removeCachedImage(recipeId: string): Promise<void> {
  if (typeof window === 'undefined' || !('caches' in window)) {
    return;
  }

  const imageUrl = getRecipeImageUrl(recipeId);

  try {
    const cache = await caches.open(IMAGE_CACHE_NAME);
    await cache.delete(imageUrl);
  } catch (error) {
    console.warn('Failed to remove cached image:', error);
  }
}

/**
 * Check if a recipe's image is cached
 */
export async function isImageCached(recipeId: string): Promise<boolean> {
  if (typeof window === 'undefined' || !('caches' in window)) {
    return false;
  }

  const imageUrl = getRecipeImageUrl(recipeId);

  try {
    const cache = await caches.open(IMAGE_CACHE_NAME);
    const response = await cache.match(imageUrl);
    return response !== undefined;
  } catch (error) {
    return false;
  }
}
