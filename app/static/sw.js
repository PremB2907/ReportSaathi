const CACHE_NAME = 'reportsaathi-v1';
const STATIC_ASSETS = [
  '/',
  '/app/static/css/main.css',
  '/app/static/js/theme.js',
  '/app/static/js/voice.js',
  '/app/static/js/location.js',
  '/app/static/js/api.js',
  '/app/static/js/app.js',
  '/app/static/manifest.json'
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS);
    })
  );
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    })
  );
});

self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);
  
  // NEVER cache medical data upload API requests
  if (url.pathname.startsWith('/api/')) {
    e.respondWith(fetch(e.request));
    return;
  }
  
  e.respondWith(
    caches.match(e.request).then((cachedResponse) => {
      return cachedResponse || fetch(e.request);
    })
  );
});
