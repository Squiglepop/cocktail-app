// Service Worker for Cocktail Recipe Library PWA

const CACHE_NAME = 'cocktail-recipes-v4';

// Store for shared images (temporary, in-memory)
let pendingSharedImage = null;

// Install event - cache essential files
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      // Cache files individually to avoid failing if one request fails
      const urlsToCache = ['/', '/upload', '/recipes'];
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

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME)
          .map((name) => caches.delete(name))
      );
    })
  );
  self.clients.claim();
});

// Fetch event - network first, fall back to cache
self.addEventListener('fetch', (event) => {
  // Skip non-GET requests and API calls
  if (event.request.method !== 'GET' || event.request.url.includes('/api/')) {
    return;
  }

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
      .catch(() => {
        return caches.match(event.request);
      })
  );
});

// Handle share target - receive shared images
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  if (url.pathname === '/share' && event.request.method === 'POST') {
    event.respondWith(
      (async () => {
        const formData = await event.request.formData();
        const image = formData.get('image');

        // Store the image temporarily - the client page will request it
        pendingSharedImage = image;

        // Redirect to the share page
        return Response.redirect('/share?received=true', 303);
      })()
    );
  }
});

// Listen for messages from clients requesting the shared image
self.addEventListener('message', (event) => {
  if (event.data?.type === 'GET_SHARED_IMAGE') {
    const client = event.source;
    if (client && pendingSharedImage) {
      client.postMessage({
        type: 'SHARED_IMAGE',
        image: pendingSharedImage
      });
      // Clear after sending
      pendingSharedImage = null;
    } else if (client) {
      // No image available
      client.postMessage({
        type: 'NO_SHARED_IMAGE'
      });
    }
  }
});
