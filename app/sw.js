/* 서비스 워커: 앱 파일을 저장해 두어 오프라인에서도 열리게 함 (Anthropic API 요청은 건드리지 않음) */
const VERSION = "v10";
const CACHE = "study-tutor-" + VERSION;
const SHELL = [
  "./",
  "css/base.css",
  "css/dialogs.css",
  "css/panels.css",
  "css/pdf.css",
  "css/stage.css",
  "fonts/f4.woff2",
  "fonts/f6.woff2",
  "fonts/f8.woff2",
  "fonts/g5.woff2",
  "fonts/g7.woff2",
  "fonts/l4.woff2",
  "icons/apple-touch-icon.png",
  "icons/icon-192.png",
  "icons/icon-512.png",
  "icons/icon-maskable-512.png",
  "icons/icon.svg",
  "index.html",
  "js/cats.js",
  "js/claude.js",
  "js/db.js",
  "js/drawer.js",
  "js/figures.js",
  "js/main.js",
  "js/notes.js",
  "js/pdf.js",
  "js/picker.js",
  "js/rich.js",
  "js/session.js",
  "js/settings.js",
  "js/util.js",
  "manifest.webmanifest",
  "vendor/html2canvas.min.js",
  "vendor/jspdf.umd.min.js",
  "vendor/katex/fonts/KaTeX_AMS-Regular.woff2",
  "vendor/katex/fonts/KaTeX_Caligraphic-Bold.woff2",
  "vendor/katex/fonts/KaTeX_Caligraphic-Regular.woff2",
  "vendor/katex/fonts/KaTeX_Fraktur-Bold.woff2",
  "vendor/katex/fonts/KaTeX_Fraktur-Regular.woff2",
  "vendor/katex/fonts/KaTeX_Main-Bold.woff2",
  "vendor/katex/fonts/KaTeX_Main-BoldItalic.woff2",
  "vendor/katex/fonts/KaTeX_Main-Italic.woff2",
  "vendor/katex/fonts/KaTeX_Main-Regular.woff2",
  "vendor/katex/fonts/KaTeX_Math-BoldItalic.woff2",
  "vendor/katex/fonts/KaTeX_Math-Italic.woff2",
  "vendor/katex/fonts/KaTeX_SansSerif-Bold.woff2",
  "vendor/katex/fonts/KaTeX_SansSerif-Italic.woff2",
  "vendor/katex/fonts/KaTeX_SansSerif-Regular.woff2",
  "vendor/katex/fonts/KaTeX_Script-Regular.woff2",
  "vendor/katex/fonts/KaTeX_Size1-Regular.woff2",
  "vendor/katex/fonts/KaTeX_Size2-Regular.woff2",
  "vendor/katex/fonts/KaTeX_Size3-Regular.woff2",
  "vendor/katex/fonts/KaTeX_Size4-Regular.woff2",
  "vendor/katex/fonts/KaTeX_Typewriter-Regular.woff2",
  "vendor/katex/katex.min.css",
  "vendor/katex/katex.min.js"
];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys().then(keys => Promise.all(keys.filter(k => k.startsWith("study-tutor-") && k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

/* 저장된 파일을 먼저 보여주고, 뒤에서 새 버전을 받아 둠 */
self.addEventListener("fetch", e => {
  const req = e.request, url = new URL(req.url);
  if (req.method !== "GET" || url.origin !== location.origin) return;
  e.respondWith(
    caches.open(CACHE).then(async c => {
      const hit = await c.match(req, { ignoreSearch: true });
      const net = fetch(req).then(res => { if (res.ok) c.put(req, res.clone()); return res }).catch(() => null);
      return hit || (await net) || (req.mode === "navigate" ? c.match("./index.html") : Response.error());
    })
  );
});
