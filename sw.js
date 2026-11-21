const CACHE = "fred-creek-v2";
const ASSETS = [
  ".", "index.html", "manifest.json",
  "icon-192.png", "icon-512.png", "icon-maskable-512.png",
  "assets/amur-honeysuckle.jpg", "assets/armadillo.jpg", "assets/black-cherry.jpg",
  "assets/black-gum.jpg", "assets/callery-pear.webp", "assets/cherry-laurel.jpg",
  "assets/coyote.jpg", "assets/deer.jpg", "assets/english-ivy.webp",
  "assets/fragrant-sumac.jpg", "assets/poison-ivy.jpg",
  "assets/giant-funnel.jpg", "assets/green-ash.jpg", "assets/japanese-honeysuckle.jpg",
  "assets/nandina.jpg", "assets/opossum.jpg", "assets/persimmon.jpg",
  "assets/privet.jpg", "assets/raccoon-scat.jpg", "assets/raccoon.jpg",
  "assets/skunk.jpg", "assets/slippery-elm.jpg", "assets/wintercreeper.jpg"
];
self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(keys =>
    Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
  ).then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  if (e.request.method !== "GET") return;
  e.respondWith(caches.match(e.request, {ignoreSearch: true}).then(hit =>
    hit || fetch(e.request).then(res => {
      const copy = res.clone();
      caches.open(CACHE).then(c => c.put(e.request, copy));
      return res;
    })
  ));
});
