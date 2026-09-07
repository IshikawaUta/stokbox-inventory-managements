// Service Worker untuk offline caching static assets
const CACHE_NAME = 'inventaris-v1';
const STATIC_ASSETS = [
    '/',
    '/static/css/style.css',
    '/static/css/bootstrap-icons.css',
    '/static/js/api.js',
    '/static/js/ui.js',
    '/static/vendor/jquery/jquery-3.7.1.min.js',
];

// Install: cache static assets
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(STATIC_ASSETS);
        })
    );
    self.skipWaiting();
});

// Activate: cleanup old caches
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

// Fetch: network first, fallback to cache for static assets
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Skip non-GET requests
    if (request.method !== 'GET') return;

    // Skip API requests (always network)
    if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/ws/')) return;

    // Skip auth pages (always network)
    if (url.pathname === '/login' || url.pathname === '/auth/logout') return;

    // Static assets: cache first, network fallback
    if (url.pathname.startsWith('/static/') || url.pathname.endsWith('.js') || url.pathname.endsWith('.css')) {
        event.respondWith(
            caches.match(request).then((cached) => {
                if (cached) return cached;
                return fetch(request).then((response) => {
                    if (response.ok) {
                        const responseClone = response.clone();
                        caches.open(CACHE_NAME).then((cache) => {
                            cache.put(request, responseClone);
                        });
                    }
                    return response;
                });
            })
        );
        return;
    }

    // HTML pages: network first, cache fallback
    event.respondWith(
        fetch(request)
            .then((response) => {
                if (response.ok && request.headers.get('accept')?.includes('text/html')) {
                    const responseClone = response.clone();
                    caches.open(CACHE_NAME).then((cache) => {
                        cache.put(request, responseClone);
                    });
                }
                return response;
            })
            .catch(() => {
                return caches.match(request);
            })
    );
});
