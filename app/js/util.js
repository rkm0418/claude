/* 공용 도구 */
export const $ = id => document.getElementById(id);

/** localStorage (막혀 있어도 오류 없이) */
export const store = {
  get(k, d = "") { try { return localStorage.getItem(k) ?? d } catch { return d } },
  set(k, v) { try { localStorage.setItem(k, v) } catch {} },
};

export const reduceMotion = () => matchMedia("(prefers-reduced-motion: reduce)").matches;

export function showDialog(d) {
  try { d.showModal() } catch { d.setAttribute("open", "") }
}

/** 스크립트를 처음 필요할 때 한 번만 불러오기 */
const loaded = new Map();
export function loadScript(src) {
  if (!loaded.has(src)) {
    loaded.set(src, new Promise((res, rej) => {
      const s = document.createElement("script");
      s.src = src; s.onload = res; s.onerror = () => { loaded.delete(src); rej(new Error("load " + src)) };
      document.head.appendChild(s);
    }));
  }
  return loaded.get(src);
}

/** 사진 파일 → 캔버스(긴 변 maxSide 이하). 회전 정보 반영 */
export async function decodeImage(file, maxSide) {
  let bmp = null;
  try { bmp = await createImageBitmap(file, { imageOrientation: "from-image" }) } catch {}
  if (!bmp) {
    bmp = await new Promise((res, rej) => {
      const fr = new FileReader();
      fr.onerror = () => rej(new Error("read"));
      fr.onload = () => { const im = new Image(); im.onload = () => res(im); im.onerror = () => rej(new Error("decode")); im.src = fr.result };
      fr.readAsDataURL(file);
    });
  }
  const k = Math.min(1, maxSide / Math.max(bmp.width, bmp.height));
  const c = document.createElement("canvas");
  c.width = Math.round(bmp.width * k); c.height = Math.round(bmp.height * k);
  c.getContext("2d").drawImage(bmp, 0, 0, c.width, c.height);
  return c;
}

export const blobToDataUrl = b => new Promise(r => { const f = new FileReader(); f.onload = () => r(f.result); f.readAsDataURL(b) });

export const loadImage = src => new Promise((res, rej) => { const im = new Image(); im.onload = () => res(im); im.onerror = rej; im.src = src });

export function shuffle(a) {
  for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]] }
  return a;
}

/** 버튼 물결 효과 + 전체화면 버튼 */
export function initButtonEffects() {
  document.addEventListener("pointerdown", e => {
    const b = e.target.closest?.(".btn,.btn-top,.big-btn,.tabs button");
    if (!b || b.disabled || reduceMotion()) return;
    const r = b.getBoundingClientRect(), d = Math.max(r.width, r.height) * 2, sp = document.createElement("span");
    sp.className = "rp";
    sp.style.cssText = `width:${d}px;height:${d}px;left:${e.clientX - r.left - d / 2}px;top:${e.clientY - r.top - d / 2}px`;
    b.appendChild(sp); setTimeout(() => sp.remove(), 600);
  });
}

/** 전체화면: 첫 터치/클릭에서 자동으로 켜고 계속 유지. 버튼이나 Esc로 직접 나가면 다시 누를 때까지 그대로 둠 */
export function initFullscreen(btn) {
  if (!document.fullscreenEnabled) return;
  btn.hidden = false;
  let auto = true;
  const enter = () => { try { document.documentElement.requestFullscreen({ navigationUI: "hide" }).catch(() => {}) } catch {} };
  btn.onclick = () => {
    if (document.fullscreenElement) { auto = false; document.exitFullscreen() }
    else { auto = true; enter() }
  };
  document.addEventListener("pointerdown", e => {
    if (auto && !document.fullscreenElement && !e.target.closest("#" + btn.id)) enter();
  }, true);
  document.addEventListener("fullscreenchange", () => {
    if (!document.fullscreenElement) auto = false;
    btn.setAttribute("aria-label", document.fullscreenElement ? "전체화면 닫기" : "전체화면");
  });
}
