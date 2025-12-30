// Service Worker for Cocktail Recipe Library PWA
// Handles offline caching for pages and recipe images

const CACHE_NAME = 'cocktail-recipes-v9';
const IMAGE_CACHE_NAME = 'cocktail-recipe-images-v1';

// Store for shared images (temporary, in-memory)
let pendingSharedImage = null;

// Install event - cache essential files
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      // Cache files individually to avoid failing if one request fails
      const urlsToCache = ['/', '/upload', '/recipes', '/offline/recipe'];
      return Promise.allSettled(
        urlsToCache.map((url) =>
          fetch(url).then((response) => {
            if (response.ok) {
              return cache.put(url, response);
            }
          }).catch(() => {
            // Silently ignore cache failures
          })
        )
      );
    })
  );
  self.skipWaiting();
});

// Activate event - clean up old caches (keep image cache)
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME && name !== IMAGE_CACHE_NAME)
          .map((name) => caches.delete(name))
      );
    })
  );
  self.clients.claim();
});

// Fetch event - handle different request types
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Handle share target POST
  if (url.pathname === '/share' && event.request.method === 'POST') {
    event.respondWith(handleShareTarget(event.request));
    return;
  }

  // Skip non-GET requests
  if (event.request.method !== 'GET') {
    return;
  }

  // Handle recipe images from API
  if (url.pathname.match(/^\/api\/recipes\/[^/]+\/image$/)) {
    event.respondWith(handleRecipeImage(event.request));
    return;
  }

  // Skip other API calls - let them fail naturally (React will handle offline state)
  if (url.pathname.startsWith('/api/')) {
    return;
  }

  // Handle regular page/asset requests - network first, cache fallback
  event.respondWith(
    fetch(event.request)
      .then((response) => {
        // Clone the response before caching
        const responseClone = response.clone();
        caches.open(CACHE_NAME).then((cache) => {
          cache.put(event.request, responseClone);
        });
        return response;
      })
      .catch(async () => {
        // Try to get from cache (exact match)
        const cachedResponse = await caches.match(event.request);
        if (cachedResponse) {
          return cachedResponse;
        }

        // Check if this is a NAVIGATION request (not RSC/prefetch)
        const isNavigation = event.request.mode === 'navigate' ||
                             (event.request.headers.get('accept') || '').includes('text/html');

        // RSC requests have ?_rsc= param or specific headers - DON'T serve HTML for these
        const isRscRequest = url.searchParams.has('_rsc') ||
                             event.request.headers.get('RSC') === '1' ||
                             event.request.headers.get('Next-Router-Prefetch') === '1';

        // For NAVIGATION to /offline/recipe (full page load), serve the cached page
        // This happens when user clicks a recipe card while offline and we use window.location.assign()
        if (isNavigation && !isRscRequest && url.pathname.startsWith('/offline/recipe')) {
          const offlinePage = await caches.match('/offline/recipe');
          if (offlinePage) {
            console.log('[SW] Serving cached /offline/recipe for navigation:', event.request.url);
            return offlinePage;
          }
        }

        // For other navigation requests, serve the home page as fallback
        // This allows the app to at least load when offline
        if (isNavigation && !isRscRequest) {
          const appShell = await caches.match('/');
          if (appShell) {
            console.log('[SW] Serving home page fallback for:', event.request.url);
            return appShell;
          }
        }

        // RSC requests and other non-navigation requests - let them fail
        // This is intentional: Next.js handles RSC failures gracefully
        console.log('[SW] Offline - no cache for:', event.request.url);
        return new Response('Offline', { status: 503 });
      })
  );
});

/**
 * Handle recipe image requests
 * Network first, fallback to image cache when offline
 */
async function handleRecipeImage(request) {
  try {
    // Try network first
    const response = await fetch(request);
    if (response.ok) {
      // Cache successful responses
      const cache = await caches.open(IMAGE_CACHE_NAME);
      cache.put(request, response.clone());
      return response;
    }
    throw new Error('Network response not ok');
  } catch (error) {
    // Network failed, try cache
    const cachedResponse = await caches.match(request, { cacheName: IMAGE_CACHE_NAME });
    if (cachedResponse) {
      return cachedResponse;
    }

    // Also check the general cache
    const generalCachedResponse = await caches.match(request);
    if (generalCachedResponse) {
      return generalCachedResponse;
    }

    // Return a placeholder or 404
    return new Response('Image not available offline', {
      status: 503,
      statusText: 'Offline - Image not cached',
      headers: { 'Content-Type': 'text/plain' },
    });
  }
}

/**
 * Handle share target POST requests
 */
async function handleShareTarget(request) {
  const formData = await request.formData();
  const image = formData.get('image');

  // Store the image temporarily - the client page will request it
  pendingSharedImage = image;

  // Redirect to the share page
  return Response.redirect('/share?received=true', 303);
}

// Listen for messages from clients
self.addEventListener('message', (event) => {
  const { type } = event.data || {};

  switch (type) {
    case 'GET_SHARED_IMAGE':
      handleGetSharedImage(event);
      break;

    case 'CACHE_RECIPE_IMAGE':
      // Client requesting to cache an image
      handleCacheRecipeImage(event.data.url);
      break;

    case 'REMOVE_CACHED_IMAGE':
      // Client requesting to remove a cached image
      handleRemoveCachedImage(event.data.url);
      break;
  }
});

function handleGetSharedImage(event) {
  const client = event.source;
  if (client && pendingSharedImage) {
    client.postMessage({
      type: 'SHARED_IMAGE',
      image: pendingSharedImage
    });
    pendingSharedImage = null;
  } else if (client) {
    client.postMessage({
      type: 'NO_SHARED_IMAGE'
    });
  }
}

async function handleCacheRecipeImage(url) {
  if (!url) return;
  try {
    const response = await fetch(url);
    if (response.ok) {
      const cache = await caches.open(IMAGE_CACHE_NAME);
      await cache.put(url, response);
    }
  } catch (error) {
    console.warn('Failed to cache recipe image:', error);
  }
}

async function handleRemoveCachedImage(url) {
  if (!url) return;
  try {
    const cache = await caches.open(IMAGE_CACHE_NAME);
    await cache.delete(url);
  } catch (error) {
    console.warn('Failed to remove cached image:', error);
  }
}
