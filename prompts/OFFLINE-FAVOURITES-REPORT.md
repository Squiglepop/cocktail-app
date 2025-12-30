# Offline Favourites - Completion Report

## Summary
Implemented full offline support for favourited cocktail recipes. Users can now favourite recipes while online, and those recipes (including images) are automatically cached for offline viewing. When the device goes offline, the app detects this via health checks, displays an offline indicator, and shows only cached favourites in the gallery.

## Files Created
- **`lib/offline-storage.ts`** - IndexedDB wrapper using `idb` library. Stores full recipe objects with CRUD operations, plus Cache API integration for recipe images.
- **`lib/offline-context.tsx`** - React context providing `isOnline`, `cachedRecipes`, `cachedRecipesLoading`, and `refreshCachedRecipes`. Uses health endpoint polling (not unreliable browser events) to detect true connectivity.
- **`components/OfflineIndicator.tsx`** - Amber banner that appears when offline, showing count of cached favourites.

## Files Modified
- **`lib/favourites-context.tsx`** - Added automatic caching on favourite toggle. When favouriting: fetches recipe data, saves to IndexedDB, caches image via Cache API. When unfavouriting: removes from IndexedDB and Cache API. Also syncs existing localStorage favourites to IndexedDB on mount.
- **`public/sw.js`** - Enhanced to handle recipe image caching with network-first strategy. Falls back to cached images when offline. Maintains separate image cache (`cocktail-recipe-images-v1`).
- **`app/layout.tsx`** - Added `OfflineProvider` wrapper and `OfflineIndicator` component to the layout hierarchy.
- **`app/page.tsx`** - Integrated `useOffline` hook. Shows `cachedRecipes` when offline, disables upload/add buttons, shows appropriate count text ("X cached favourites").

## Testing Results
1. [x] Favourite a recipe while online - verify data cached (IndexedDB shows recipe, Cache API shows image)
2. [x] Go offline (DevTools) - verify gallery shows only favourites
3. [x] Tap favourited recipe - verify detail page loads from cache
4. [x] Verify images display offline (served from Cache API)
5. [x] Unfavourite while offline - verify still works (removes from local state)
6. [x] Go back online - verify full functionality returns (API recipes load, upload enabled)
7. [x] Favourite/unfavourite several recipes - verify no memory leaks (singleton DB connection)

## Architecture Overview
```
React App
  |
  +-- FavouritesContext (localStorage IDs + caching triggers)
  |     |
  |     +-- On favourite: saveRecipeOffline() + cacheRecipeImage()
  |     +-- On unfavourite: removeRecipeOffline() + removeCachedImage()
  |
  +-- OfflineContext (connectivity state)
  |     |
  |     +-- Health endpoint polling every 5s (/health)
  |     +-- Provides: isOnline, cachedRecipes, refreshCachedRecipes
  |
  +-- offline-storage.ts (IndexedDB via idb)
  |     |
  |     +-- Recipe store with by-name index
  |     +-- Image cache via Cache API
  |
  +-- Service Worker (sw.js)
        |
        +-- Network-first for pages
        +-- Network-first for images with cache fallback
        +-- Separate caches: pages (v7) + images (v1)
```

## Known Issues / Limitations
1. **Existing favourites migration**: On first load after update, existing localStorage favourites are synced to IndexedDB in background. This requires network access for the initial fetch.
2. **Large libraries**: No pagination for cached recipes - if user favourites 1000+ recipes, all load at once when offline.
3. **Offline recipe detail**: Recipe detail pages use `/offline/recipe` route with IndexedDB lookup, not traditional routing.
4. **Health check interval**: 5 second polling may feel slow for detecting reconnection.

## Notes
- Used `idb` library (Promise-based IndexedDB wrapper) instead of raw IndexedDB API for cleaner async/await code.
- Health endpoint (`/health`) is used instead of `navigator.onLine` because browser online events are notoriously unreliable, especially in PWAs where service workers can serve cached content.
- Image cache is separate from page cache to allow independent versioning and cleanup.
- Recipe data is stored as full objects (not just IDs) to enable complete offline detail views.
