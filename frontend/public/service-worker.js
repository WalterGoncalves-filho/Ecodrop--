const CACHE = 'ecodrop-v1';
const ASSETS = [
  '/',
  '/index.html',
  '/css/style.css',
  '/script.js',
  '/api.js',
  '/assets/Logo.png'
];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(ASSETS))
  );
});

self.addEventListener('fetch', e => {
  e.respondWith(
    caches.match(e.request).then(cached => cached || fetch(e.request))
  );
});