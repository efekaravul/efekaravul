/* Uygulama kabuğunu önbelleğe alır: mağazada internet zayıfken de açılır.
   Sunucu çağrıları (POST/rpc) hiçbir zaman önbelleğe alınmaz.            */
const SURUM = "vardiya-v3";

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(SURUM).then((c) => c.addAll(["./", "./index.html"])).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys()
      .then((k) => Promise.all(k.filter((x) => x !== SURUM).map((x) => caches.delete(x))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  const istek = e.request;
  if (istek.method !== "GET") return;
  const url = new URL(istek.url);
  if (url.origin !== self.location.origin) return;

  if (istek.mode === "navigate") {
    e.respondWith(
      fetch(istek).catch(() => caches.match("./index.html").then((c) => c || caches.match("./")))
    );
    return;
  }
  e.respondWith(
    caches.match(istek).then((bellek) =>
      bellek ||
      fetch(istek).then((cevap) => {
        const kopya = cevap.clone();
        if (cevap.ok) caches.open(SURUM).then((c) => c.put(istek, kopya));
        return cevap;
      })
    )
  );
});
