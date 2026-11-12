/* 문제 올리기 화면: 사진/글 입력, 문제 부분 선택, 작게 줄이기 */
import { $, decodeImage } from "./util.js";

const MAXD = 1024; // 보낼 사진의 긴 변(px)
let src = null, rect = null; // 원본(캔버스)과 고른 영역
let blob = null, dims = null; // 줄여서 보낼 JPEG

/* ── 사진 불러오기 · 영역 선택 ── */
function autoTrim() { // 종이 바깥 여백 자동 제거
  const W = src.width, H = src.height, k = Math.min(1, 320 / W), w = Math.max(8, Math.round(W * k)), h = Math.max(8, Math.round(H * k));
  const c = document.createElement("canvas"); c.width = w; c.height = h;
  const g = c.getContext("2d"); g.drawImage(src, 0, 0, w, h);
  const d = g.getImageData(0, 0, w, h).data, lum = new Float32Array(w * h);
  let mean = 0;
  for (let i = 0; i < w * h; i++) { lum[i] = .3 * d[i * 4] + .59 * d[i * 4 + 1] + .11 * d[i * 4 + 2]; mean += lum[i] }
  mean /= w * h;
  let x0 = w, y0 = h, x1 = -1, y1 = -1;
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) if (lum[y * w + x] < mean - 45) { if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y }
  if (x1 < 0) return { x: 0, y: 0, w: W, h: H };
  const px = Math.round(w * .04), py = Math.round(h * .04);
  x0 = Math.max(0, x0 - px); y0 = Math.max(0, y0 - py); x1 = Math.min(w - 1, x1 + px); y1 = Math.min(h - 1, y1 + py);
  const r = { x: x0 / k, y: y0 / k, w: (x1 - x0 + 1) / k, h: (y1 - y0 + 1) / k };
  return r.w * r.h > .85 * W * H ? { x: 0, y: 0, w: W, h: H } : r;
}

function paint(sel) {
  const cv = $("probCv"), cw = Math.min(320, $("probPrev").clientWidth || 320), sc = cw / src.width;
  cv.width = Math.round(src.width * sc); cv.height = Math.round(src.height * sc);
  const g = cv.getContext("2d"); g.drawImage(src, 0, 0, cv.width, cv.height);
  const r = sel || rect;
  g.fillStyle = "rgba(0,0,0,.55)"; g.fillRect(0, 0, cv.width, cv.height);
  g.save(); g.beginPath(); g.rect(r.x * sc, r.y * sc, r.w * sc, r.h * sc); g.clip(); g.drawImage(src, 0, 0, cv.width, cv.height); g.restore();
  g.strokeStyle = "#ef6a62"; g.lineWidth = 3; g.strokeRect(r.x * sc, r.y * sc, r.w * sc, r.h * sc);
}

/** 고른 영역 → 긴 변 1024px, 흑백·대비, JPEG 0.72 */
function rebuild() {
  const k = Math.min(1, MAXD / Math.max(rect.w, rect.h)), w = Math.max(8, Math.round(rect.w * k)), h = Math.max(8, Math.round(rect.h * k));
  const c = document.createElement("canvas"); c.width = w; c.height = h;
  const g = c.getContext("2d");
  try { g.filter = "grayscale(1) contrast(1.25)" } catch {}
  g.fillStyle = "#fff"; g.fillRect(0, 0, w, h);
  g.drawImage(src, rect.x, rect.y, rect.w, rect.h, 0, 0, w, h);
  c.toBlob(b => { blob = b; dims = { w, h }; $("probInfo").textContent = `${w}×${h}px · 약 ${Math.round(w * h / 750)}토큰 · ${Math.round(b.size / 1024)}KB` }, "image/jpeg", .72);
}

async function loadPhoto(file) {
  try {
    src = await decodeImage(file, 1600);
    rect = autoTrim();
    $("probPrev").classList.remove("hide"); $("drop").textContent = "사진 바꾸기"; $("err").textContent = "";
    paint(); rebuild();
  } catch { $("err").textContent = "이 사진은 읽을 수 없어요. 다른 사진으로 올려주세요." }
}

function initCropDrag() {
  const cv = $("probCv"); let st = null;
  const pos = e => { const b = cv.getBoundingClientRect(), sc = src.width / b.width; return { x: Math.max(0, Math.min(src.width, (e.clientX - b.left) * sc)), y: Math.max(0, Math.min(src.height, (e.clientY - b.top) * sc)) } };
  const rc = (a, b) => ({ x: Math.min(a.x, b.x), y: Math.min(a.y, b.y), w: Math.abs(a.x - b.x), h: Math.abs(a.y - b.y) });
  cv.onpointerdown = e => { if (!src) return; cv.setPointerCapture(e.pointerId); st = pos(e) };
  cv.onpointermove = e => { if (st) paint(rc(st, pos(e))) };
  cv.onpointerup = e => { if (!st) return; const r = rc(st, pos(e)); st = null; if (r.w > 30 && r.h > 30) { rect = r; rebuild() } paint() };
  $("resetCrop").onclick = () => { if (src) { rect = autoTrim(); paint(); rebuild() } };
  $("fullCrop").onclick = () => { if (src) { rect = { x: 0, y: 0, w: src.width, h: src.height }; paint(); rebuild() } };
}

/** 지금 입력된 문제 (세션이 가져가 씀) */
export const getProblem = () => ({ text: $("probText").value.trim(), blob, dims, src, rect: rect && { ...rect }, rmColor: $("rmColor").checked });

export function resetDrawer() {
  src = rect = blob = dims = null;
  $("probText").value = ""; $("probPrev").classList.add("hide"); $("err").textContent = "";
  $("drop").textContent = "문제 사진 올리기 / 붙여넣기(Ctrl+V)";
}

export function initDrawer({ onStart }) {
  initCropDrag();
  const drop = $("drop");
  drop.onclick = $("pickPhoto").onclick = () => $("probFile").click();
  $("camPhoto").onclick = () => $("probCam").click();
  for (const id of ["probFile", "probCam"]) $(id).onchange = e => { const f = e.target.files[0]; if (f) loadPhoto(f); e.target.value = "" };
  drop.onkeydown = e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); $("probFile").click() } };
  drop.ondragover = e => e.preventDefault();
  drop.ondrop = e => { e.preventDefault(); const f = e.dataTransfer.files[0]; if (f?.type.startsWith("image/")) loadPhoto(f) };
  document.addEventListener("paste", e => {
    const f = [...(e.clipboardData?.files || [])].find(f => f.type.startsWith("image/"));
    if (f) loadPhoto(f)
  });
  $("go").onclick = () => {
    const p = getProblem();
    if (!p.text && !p.blob) { $("err").textContent = "문제 사진이나 글을 먼저 올려주세요."; return }
    onStart(p);
  };
}
