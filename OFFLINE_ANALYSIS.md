# Offline Feature Analysis Report

## Executive Summary

The offline functionality has become a **Rube Goldberg machine** of competing systems, redundant pages, and race conditions. The core problem isn't any single bug - it's architectural complexity that makes bugs inevitable.

---

## Storage Layers (5 Different Places)

| Storage | Contents | Purpose |
|---------|----------|---------|
| **localStorage** | `cocktail_favourites` - array of recipe IDs | Source of truth for "what is favourited" |
| **IndexedDB** | Full `Recipe` objects with ingredients, instructions, etc. | Offline recipe viewing |
| **SW Cache (v7)** | HTML pages: `/`, `/upload`, `/recipes`, `/offline/recipe` + all JS/CSS assets | Offline page navigation |
| **SW Image Cache** | Recipe images at `/api/recipes/[id]/image` | Offline image viewing |
| **React Query** | API responses (in-memory only) | Online data fetching |

**Problem**: 5 storage layers with no clear synchronization guarantees.

---

## The Navigation Clusterfuck

There are **TWO different recipe detail pages** that both claim to handle offline:

### Page 1: `/recipes/[id]` (Regular Detail Page)
- Lines 53-71: Loads from IndexedDB in parallel with API
- Line 74: Uses online recipe if available, falls back to offline
- **Already handles offline mode correctly**

### Page 2: `/offline/recipe` (Dedicated Offline Page)
- Only loads from IndexedDB
- Requires query param `?id=X`
- Pre-cached by service worker

### The Hack (RecipeCard.tsx lines 38-46):
```typescript
const handleCardClick = (e: React.MouseEvent) => {
  if (!isOnline) {
    e.preventDefault();
    window.location.href = `/offline/recipe?id=${recipe.id}`;  // Full page reload!
  }
};
```

**This is insane.** The regular detail page already works offline. This hack:
1. Breaks SPA navigation (full page reload)
2. Requires the `/offline/recipe` page to be cached with all its JS chunks
3. Created a whole second page that duplicates 90% of the regular detail page

---

## Race Condition Hell

### The Timing Dependencies:
1. Health check runs immediately + every 5 seconds
2. Browser online/offline events trigger health check
3. IndexedDB loads on mount (async)
4. React Query fetches on mount (async, only if `isOnline`)
5. `cachedRecipesLoading` state tracks IndexedDB completion

### The `displayedRecipes` Logic (page.tsx lines 65-90):
```typescript
// Offline: show cached
if (!isOnline) return cachedRecipes;

// Online but no API data yet: show cached (WHY?!)
if (recipes.length === 0 && cachedRecipes.length > 0) return cachedRecipes;

// Online with favourites filter: filter API results
if (favourites_only) return recipes.filter(...);

// Online: show API results
return recipes;
```

**Problems:**
1. Online users briefly see cached data while API loads (confusing if different)
2. Race between health check and IndexedDB load → wrong data shown
3. No invalidation when coming back online → stale data persists

---

## Silent Failures

### Favouriting from Gallery (RecipeCard.tsx line 35):
```typescript
toggleFavourite(recipe.id);  // No recipe object passed!
```

The card has `RecipeListItem`, not full `Recipe`. So `cacheRecipeForOffline` must fetch from API:

```typescript
// favourites-context.tsx line 70-73
if (!recipeData) {
  const authToken = token ?? getStoredToken();
  recipeData = await fetchRecipe(recipeId, authToken);  // Could fail!
}
```

**If this fetch fails:**
- User sees heart turn red (favourited)
- localStorage updated (favourited)
- IndexedDB NOT updated (not cached for offline)
- No error shown to user
- Offline mode will show "Recipe not found"

---

## Service Worker Caching Problems

### What's Pre-Cached (sw.js line 15):
```javascript
const urlsToCache = ['/', '/upload', '/recipes', '/offline/recipe'];
```

### What's NOT Pre-Cached:
- The JS chunks that `/offline/recipe` needs to run
- Next.js dynamically code-splits, so page shell ≠ runnable page

### The Hidden Iframe Hack (offline-context.tsx lines 111-122):
```typescript
const iframe = document.createElement('iframe');
iframe.src = '/offline/recipe?warmup=true';
document.body.appendChild(iframe);
```

This tries to force-load the page so SW caches everything. **Fragile as fuck.**

---

## Root Cause

**Layered complexity without clear ownership:**

1. Multiple storage layers that can get out of sync
2. Multiple pages for the same function
3. Multiple offline detection methods
4. Multiple fallback chains
5. Fire-and-forget async operations with no confirmation

Every "fix" has added another layer instead of simplifying.

---

## Recommendations

### Option A: Delete The Redundant Page (Recommended)

1. **Delete `/offline/recipe` entirely**
2. **Remove `handleCardClick` hack from RecipeCard** - let Link work normally
3. **Keep `/recipes/[id]` as-is** - it already handles offline via IndexedDB fallback
4. **Ensure SW serves app shell** for any navigation when offline
5. **Add React Query invalidation** when coming back online

**Effort: Low | Risk: Low | Simplification: High**

### Option B: Proper Offline-First Architecture

1. Use **Workbox** for SW management (handles precaching properly)
2. Use **React Query's `persistQueryClient`** to persist cache to IndexedDB
3. Add **retry logic** for failed IndexedDB saves
4. Show **explicit "Saved for offline" toast** to confirm caching
5. Add **background sync** for favourites

**Effort: High | Risk: Medium | Simplification: Medium**

### Option C: Reduce Scope

1. Accept offline as "best effort"
2. Only support offline gallery (list of favourites)
3. Remove offline recipe viewing entirely
4. Clear messaging: "Go online to view full recipe"

**Effort: Medium | Risk: Low | Simplification: Very High**

---

## Immediate Action Items (Option A)

1. [ ] Delete `/app/offline/recipe/` directory
2. [ ] Remove `handleCardClick` from RecipeCard - just use normal Link
3. [ ] Remove hidden iframe hack from offline-context
4. [ ] Remove `/offline/recipe` from SW's urlsToCache
5. [ ] Add React Query cache invalidation on offline→online transition
6. [ ] Test: Favourite → go offline → click recipe → should load from IndexedDB
7. [ ] Bump SW cache version to clear old shit

---

## The Philosophical Issue

This codebase has been treating symptoms instead of diseases. Every bug fix added complexity:

- "Offline detection is unreliable" → Added health check polling
- "Page doesn't work offline" → Added dedicated offline page
- "Dedicated page doesn't cache" → Added hidden iframe hack
- "Data shows wrong" → Added `cachedRecipesLoading` state
- "Still flickers" → Made browser events trigger health check

**The actual solution was always: make the existing page work offline, not create parallel systems.**
