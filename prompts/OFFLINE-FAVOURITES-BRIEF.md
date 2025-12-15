# Offline Favourites Feature - Implementation Brief

## Objective
Implement offline storage for favourited cocktail recipes so users can view their favourites when offline, including recipe details and images.

---

## Required Research (Do This First)

### 1. Study the Current Codebase:
- `frontend/lib/favourites-context.tsx` - Current favourites implementation (localStorage, IDs only)
- `frontend/public/sw.js` - Existing service worker (network-first, skips API calls)
- `frontend/lib/api.ts` - API client and recipe types
- `frontend/components/recipes/RecipeCard.tsx` - Gallery card component
- `frontend/app/recipes/[id]/page.tsx` - Recipe detail page
- `frontend/app/page.tsx` - Home page with recipe grid

### 2. Online Research Topics:
- IndexedDB best practices 2024/2025 (idb library vs raw API)
- Service Worker Cache API for images
- Detecting online/offline status in React (navigator.onLine + events)
- PWA offline patterns - specifically "cache on demand" vs "background sync"
- Next.js 14 App Router + Service Workers gotchas

---

## Feature Requirements

### When a recipe is favourited:
1. Save recipe ID to localStorage (already works)
2. Fetch full recipe data and store in IndexedDB
3. Cache the recipe image using Cache API via service worker

### When a recipe is unfavourited:
1. Remove ID from localStorage (already works)
2. Remove recipe data from IndexedDB
3. Remove cached image

### When offline:
1. Detect offline status and show indicator in header
2. Home page gallery shows ONLY cached favourites
3. Recipe detail pages load from IndexedDB cache
4. Images load from service worker cache
5. Disable upload/add functionality
6. Show toast/banner: "Offline - Showing favourites only"

### When back online:
1. Restore full gallery
2. Re-enable all functionality
3. Optional: sync any changes made offline

---

## Files to Create/Modify

### Already Created/Updated (DONE):
- ~~`lib/offline-storage.ts`~~ - IndexedDB wrapper for recipe data
- ~~`lib/offline-context.tsx`~~ - Online/offline state management
- ~~`public/sw.js`~~ - Handle offline API requests + image caching
- ~~`components/OfflineIndicator.tsx`~~ - UI component for offline status
- ~~`lib/favourites-context.tsx`~~ - Caching on toggle (calls saveRecipeOffline, cacheRecipeImage, etc.)
- ~~`app/layout.tsx`~~ - OfflineProvider + OfflineIndicator wired up

### Still Need to Modify:
- `app/page.tsx` - Filter to cachedRecipes when offline (use useOffline hook, show cachedRecipes instead of API data when !isOnline)

---

## Technical Constraints
- Keep localStorage for favourite IDs (simple, fast, already works)
- Use IndexedDB for full recipe objects (structured data)
- Use Cache API for images (service worker handles this)
- Must work with Next.js 14 App Router
- Must not break existing functionality
- Test with Chrome DevTools offline mode

---

## Testing Checklist
1. [ ] Favourite a recipe while online - verify data cached
2. [ ] Go offline (DevTools) - verify gallery shows only favourites
3. [ ] Tap favourited recipe - verify detail page loads
4. [ ] Verify images display offline
5. [ ] Unfavourite while offline - verify still works
6. [ ] Go back online - verify full functionality returns
7. [ ] Favourite/unfavourite several recipes - verify no memory leaks

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    React App                         │
├──────────────────┬──────────────────────────────────┤
│ FavouritesContext│ OfflineContext                   │
│ (IDs + caching)  │ (online/offline state)           │
├──────────────────┴──────────────────────────────────┤
│              offline-storage.ts                      │
│         (IndexedDB read/write wrapper)               │
├─────────────────────────────────────────────────────┤
│                 Service Worker                       │
│  - Intercepts /api/recipes/* when offline           │
│  - Serves images from Cache API                     │
│  - Posts messages to client for cache operations    │
└─────────────────────────────────────────────────────┘
```

---

## Implementation Order

1. ~~**Research phase** - Read all listed files, do online research~~ DONE
2. ~~**Create `offline-storage.ts`** - IndexedDB wrapper~~ DONE
3. ~~**Create `offline-context.tsx`** - Online/offline detection~~ DONE
4. ~~**Update `sw.js`** - Handle offline API + image requests~~ DONE
5. ~~**Modify `favourites-context.tsx`** - Add caching logic~~ DONE
6. ~~**Add `OfflineProvider` to `app/layout.tsx`** - Wire up the context~~ DONE
7. ~~**Create `OfflineIndicator.tsx`** - UI component for header~~ DONE
8. **Update `app/page.tsx`** - Filter to cachedRecipes when offline
9. **Test all scenarios** - Use the checklist above
10. **Complete the task** - Create completion report and update status

> **NOTE**: Almost there! Only step 8 remains - modify page.tsx to use `useOffline()` and display `cachedRecipes` when `!isOnline`.

---

## On Completion (REQUIRED)

When the implementation is complete, you MUST do both of the following:

### 1. Create Completion Report
Create `prompts/OFFLINE-FAVOURITES-REPORT.md` with:

```markdown
# Offline Favourites - Completion Report

## Summary
[Brief description of what was implemented]

## Files Created
- [list new files with brief descriptions]

## Files Modified
- [list modified files with what changed]

## Testing Results
[Copy the testing checklist with results filled in]

## Known Issues / Limitations
[Any caveats, edge cases, or future improvements]

## Notes
[Any additional context for future sessions]
```

### 2. Update Status File
Update `status/tasks.json`:
- Set `status` to `"completed"`
- Set `completed_at` to current date
- Add any relevant `notes`
