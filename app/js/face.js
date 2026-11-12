/* 얼굴 편집: 사진 → 자동 윤곽(face-api) → 점 끌기/추가/삭제, 사진 이동·확대·회전 */
import { $, showDialog, loadScript, decodeImage, loadImage } from "./util.js";
import { kv } from "./db.js";
import { setFace } from "./character.js";

const FW = 800, FH = 900; // 편집 캔버스 크기
const cv = $("cv"), cx = cv.getContext("2d");
let src = null, base = 1, mode = "shape", pts = [];
let view = { x: 0, y: 0, s: 1, a: 0 }; // 사진 이동·배율·각도

const defaultPts = () => Array.from({ length: 20 }, (_, i) => {
  const t = i / 20 * Math.PI * 2 - Math.PI / 2;
  return { x: FW / 2 + Math.cos(t) * FW * .36, y: FH * .5 + Math.sin(t) * FW * .36 };
});

/* ── 윤곽 곡선 ── */
function bez(P) {
  const n = P.length, seg = [];
  for (let i = 0; i < n; i++) {
    const p0 = P[(i - 1 + n) % n], p1 = P[i], p2 = P[(i + 1) % n], p3 = P[(i + 2) % n];
    seg.push([p1, { x: p1.x + (p2.x - p0.x) / 6, y: p1.y + (p2.y - p0.y) / 6 }, { x: p2.x - (p3.x - p1.x) / 6, y: p2.y - (p3.y - p1.y) / 6 }, p2]);
  }
  return seg;
}
function tracePath(c) {
  const seg = bez(pts);
  c.beginPath(); c.moveTo(seg[0][0].x, seg[0][0].y);
  seg.forEach(s => c.bezierCurveTo(s[1].x, s[1].y, s[2].x, s[2].y, s[3].x, s[3].y));
  c.closePath();
}
function samples() {
  const out = [];
  bez(pts).forEach((s, i) => {
    for (let k = 0; k < 12; k++) {
      const t = k / 12, u = 1 - t;
      out.push({ i,
        x: u * u * u * s[0].x + 3 * u * u * t * s[1].x + 3 * u * t * t * s[2].x + t * t * t * s[3].x,
        y: u * u * u * s[0].y + 3 * u * u * t * s[1].y + 3 * u * t * t * s[2].y + t * t * t * s[3].y });
    }
  });
  return out;
}

/* ── 그리기 ── */
function paintPhoto(c) {
  if (!src) return;
  const sc = base * view.s;
  c.save(); c.translate(FW / 2 + view.x, FH / 2 + view.y); c.rotate(view.a); c.scale(sc, sc);
  c.drawImage(src, -src.width / 2, -src.height / 2); c.restore();
}
function handlePos() { // 크기·각도 조절 핸들 (사진 오른쪽 아래 모서리)
  const sc = base * view.s, w2 = src.width / 2 * sc, h2 = src.height / 2 * sc, co = Math.cos(view.a), si = Math.sin(view.a);
  return { x: FW / 2 + view.x + w2 * co - h2 * si, y: FH / 2 + view.y + w2 * si + h2 * co };
}
function draw() {
  cx.clearRect(0, 0, FW, FH); cx.fillStyle = "#22223a"; cx.fillRect(0, 0, FW, FH);
  if (!src) { cx.fillStyle = "#ffffffcc"; cx.font = "700 40px Gmarket,sans-serif"; cx.textAlign = "center"; cx.fillText("얼굴 사진을 올려주세요", FW / 2, FH * .88) }
  paintPhoto(cx);
  // 윤곽 밖은 어둡게
  cx.save(); cx.fillStyle = "rgba(10,10,25,.6)";
  const pp = new Path2D(); pp.rect(0, 0, FW, FH);
  const sg = bez(pts); pp.moveTo(sg[0][0].x, sg[0][0].y);
  sg.forEach(q => pp.bezierCurveTo(q[1].x, q[1].y, q[2].x, q[2].y, q[3].x, q[3].y));
  pp.closePath(); cx.fill(pp, "evenodd"); cx.restore();
  tracePath(cx); cx.lineWidth = 4; cx.strokeStyle = "#e060e0"; cx.stroke();
  if (mode === "shape") pts.forEach(p => { cx.beginPath(); cx.arc(p.x, p.y, 9, 0, 7); cx.fillStyle = "#fff"; cx.fill(); cx.lineWidth = 3; cx.strokeStyle = "#e060e0"; cx.stroke() });
  if (mode === "move" && src) {
    const h = handlePos();
    cx.beginPath(); cx.arc(h.x, h.y, 22, 0, 7); cx.fillStyle = "#ffe36a"; cx.fill(); cx.lineWidth = 4; cx.strokeStyle = "#1f2a26"; cx.stroke();
    cx.beginPath(); cx.arc(h.x, h.y, 9, -2.4, 2.4); cx.lineWidth = 4; cx.stroke(); // 회전 화살표
    cx.beginPath(); cx.moveTo(h.x + 4, h.y - 11); cx.lineTo(h.x + 13, h.y - 3); cx.lineTo(h.x + 1, h.y - 2); cx.closePath(); cx.fillStyle = "#1f2a26"; cx.fill();
  }
}
const msg = t => { $("faceMsg").textContent = t };
function syncSliders() { $("zoom").value = view.s; $("rot").value = Math.round(view.a * 180 / Math.PI) }
function setSrc(im, keepView) {
  src = im; base = Math.max(FW / im.width, FH / im.height);
  if (!keepView) view = { x: 0, y: 0, s: 1, a: 0 };
  syncSliders(); draw();
}

/* ── 자동 윤곽 ── */
let modelsReady = null;
function loadModels() {
  if (!modelsReady) modelsReady = (async () => {
    await loadScript("vendor/face-api.js");
    const tf = window.faceapi.tf;
    let ok = false; try { ok = await tf.setBackend("webgl") } catch {}
    if (!ok) await tf.setBackend("cpu");
    await tf.ready();
    await window.faceapi.nets.tinyFaceDetector.loadFromUri("vendor/models");
    await window.faceapi.nets.faceLandmark68TinyNet.loadFromUri("vendor/models");
  })().catch(e => { modelsReady = null; throw e });
  return modelsReady;
}
/** 68점 랜드마크 → 턱선 17점 + 이마 6점 윤곽 */
function outlineFrom(L) {
  const dx = L[16].x - L[0].x, dy = L[16].y - L[0].y, w = Math.hypot(dx, dy), ux = dy / w, uy = -dx / w; // 위쪽 방향
  const jaw = L.slice(0, 17).map(p => ({ x: p.x, y: p.y }));
  const top = [[26, .4], [24, .62], [22, .7], [21, .7], [19, .62], [17, .4]].map(([i, k]) => ({ x: L[i].x + ux * k * w, y: L[i].y + uy * k * w }));
  return jaw.concat(top);
}
async function autoOutline() {
  if (!src) return;
  msg("얼굴을 찾는 중…");
  try {
    await loadModels();
    const c = document.createElement("canvas"); c.width = FW; c.height = FH;
    const g = c.getContext("2d"); g.fillStyle = "#808080"; g.fillRect(0, 0, FW, FH); paintPhoto(g);
    const fa = window.faceapi;
    const det = await fa.detectSingleFace(c, new fa.TinyFaceDetectorOptions({ inputSize: 416, scoreThreshold: .25 })).withFaceLandmarks(true);
    if (!det) throw new Error("none");
    pts = outlineFrom(det.landmarks.positions);
    msg("얼굴을 찾았어요. 점을 끌어 다듬고 '붙이기'를 누르세요.");
  } catch {
    pts = defaultPts();
    msg("자동으로 얼굴을 찾지 못했어요. 점을 끌어 직접 맞춰주세요.");
  }
  draw();
}
async function loadPhoto(file) {
  if (!file) return;
  msg("사진을 불러오는 중…");
  try { setSrc(await decodeImage(file, 1600)); await autoOutline() }
  catch { msg("이 사진은 읽을 수 없어요. JPG나 PNG로 다시 골라주세요. (아이폰 HEIC는 '가장 호환성 높은 형식'으로 바꿔야 할 수 있어요)") }
}

/* ── 포인터: 점 끌기, 사진 이동, 핸들, 두 손가락 ── */
let drag = null, pinch = null;
const ptrs = new Map();
const cpos = e => { const r = cv.getBoundingClientRect(); return { x: (e.clientX - r.left) / r.width * FW, y: (e.clientY - r.top) / r.height * FH } };
function hitPt(q) { let b = -1, d = 26; pts.forEach((p, i) => { const k = Math.hypot(p.x - q.x, p.y - q.y); if (k < d) { d = k; b = i } }); return b }
function two() { const [a, b] = [...ptrs.values()]; return { d: Math.hypot(b.x - a.x, b.y - a.y) || 1, ang: Math.atan2(b.y - a.y, b.x - a.x) } }
const clampS = s => Math.min(5, Math.max(.1, s));

cv.onpointerdown = e => {
  cv.setPointerCapture(e.pointerId); ptrs.set(e.pointerId, { x: e.clientX, y: e.clientY });
  const q = cpos(e);
  if (ptrs.size === 2) { const t = two(); pinch = { d: t.d, ang: t.ang, s: view.s, a: view.a }; drag = null; return }
  if (mode === "move" && src) {
    const h = handlePos();
    if (Math.hypot(h.x - q.x, h.y - q.y) < 46) {
      const c0x = FW / 2 + view.x, c0y = FH / 2 + view.y;
      drag = { handle: 1, cx: c0x, cy: c0y, r0: Math.hypot(q.x - c0x, q.y - c0y) || 1, an0: Math.atan2(q.y - c0y, q.x - c0x), s0: view.s, a0: view.a };
      return;
    }
  }
  if (mode === "shape") {
    let i = hitPt(q);
    if (i < 0) { // 선을 누르면 점 추가
      let best = null, bd = 22;
      samples().forEach(s => { const k = Math.hypot(s.x - q.x, s.y - q.y); if (k < bd) { bd = k; best = s } });
      if (best) { pts.splice(best.i + 1, 0, { x: q.x, y: q.y }); i = best.i + 1 }
    }
    if (i >= 0) { drag = { pt: i }; draw(); return }
  }
  drag = { x: e.clientX, y: e.clientY, vx: view.x, vy: view.y };
};
cv.onpointermove = e => {
  if (ptrs.has(e.pointerId)) ptrs.set(e.pointerId, { x: e.clientX, y: e.clientY });
  if (pinch && ptrs.size >= 2) { const t = two(); view.s = clampS(pinch.s * t.d / pinch.d); view.a = pinch.a + (t.ang - pinch.ang); syncSliders(); draw(); return }
  if (!drag) return;
  const q = cpos(e);
  if (drag.handle) {
    const r = Math.hypot(q.x - drag.cx, q.y - drag.cy) || 1;
    view.s = clampS(drag.s0 * r / drag.r0); view.a = drag.a0 + (Math.atan2(q.y - drag.cy, q.x - drag.cx) - drag.an0); syncSliders();
  } else if (drag.pt !== undefined) pts[drag.pt] = { x: q.x, y: q.y };
  else { const k = FW / cv.getBoundingClientRect().width; view.x = drag.vx + (e.clientX - drag.x) * k; view.y = drag.vy + (e.clientY - drag.y) * k }
  draw();
};
const release = e => { ptrs.delete(e.pointerId); if (ptrs.size < 2) pinch = null; if (!ptrs.size) drag = null };
cv.onpointerup = cv.onpointercancel = release;
cv.ondblclick = e => { if (mode !== "shape" || pts.length <= 6) return; const i = hitPt(cpos(e)); if (i >= 0) { pts.splice(i, 1); draw() } };
cv.onwheel = e => {
  e.preventDefault();
  if (e.shiftKey) view.a += e.deltaY < 0 ? .05 : -.05; else view.s = clampS(view.s * (e.deltaY < 0 ? 1.06 : .94));
  syncSliders(); draw();
};

/* ── 탭 · 크게 보기 ── */
const TABS = [["shape", "tabShape"], ["move", "tabMove"]];
function setTab() { for (const [k, id] of TABS) $(id).classList.toggle("on", mode === k); draw() }
function setBig(on) {
  const d = $("faceDlg");
  d.classList.toggle("big", on); $("cropBig").textContent = on ? "작게 보기" : "크게 보기";
  try { if (on && document.fullscreenEnabled && !document.fullscreenElement) d.requestFullscreen().catch(() => {}); else if (!on && document.fullscreenElement) document.exitFullscreen() } catch {}
  draw();
}

/* ── 저장: 윤곽대로 오려서 PNG로 ── */
async function save() {
  if (!src) { msg("먼저 사진을 올려주세요."); return }
  try {
    let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
    samples().forEach(p => { x0 = Math.min(x0, p.x); y0 = Math.min(y0, p.y); x1 = Math.max(x1, p.x); y1 = Math.max(y1, p.y) });
    x0 = Math.max(0, x0 - 4); y0 = Math.max(0, y0 - 4); x1 = Math.min(FW, x1 + 4); y1 = Math.min(FH, y1 + 4);
    const w = x1 - x0, h = y1 - y0, out = document.createElement("canvas");
    out.width = w; out.height = h;
    const o = out.getContext("2d"); o.translate(-x0, -y0); tracePath(o); o.clip(); paintPhoto(o);
    const url = out.toDataURL("image/png");
    // 다시 편집할 수 있게 원본(줄인 것)과 윤곽 상태도 저장
    const k = Math.min(1, 1000 / Math.max(src.width, src.height)), c = document.createElement("canvas");
    c.width = src.width * k; c.height = src.height * k; c.getContext("2d").drawImage(src, 0, 0, c.width, c.height);
    await kv.set("face", { url, ar: w / h });
    await kv.set("faceSrc", c.toDataURL("image/jpeg", .85));
    await kv.set("faceState", { pts, view });
    await setFace(url, w / h);
    $("faceDlg").close();
  } catch (e) { msg("붙이는 중 문제가 생겼어요: " + (e.message || e)) }
}

export async function openFaceEditor() {
  src = null; pts = defaultPts(); view = { x: 0, y: 0, s: 1, a: 0 }; mode = "shape"; msg("");
  const st = await kv.get("faceState");
  if (st?.pts) { pts = st.pts; view = Object.assign({ a: 0 }, st.view) }
  syncSliders(); setTab(); showDialog($("faceDlg"));
  try { await document.fonts.load("700 40px Gmarket") } catch {}
  const sv = await kv.get("faceSrc");
  if (sv) { try { setSrc(await loadImage(sv), true) } catch {} } else draw();
}

export function initFaceEditor() {
  $("facePick").onclick = () => $("faceFile").click();
  $("faceCam").onclick = () => $("faceSelfie").click();
  for (const id of ["faceFile", "faceSelfie"]) $(id).onchange = e => { loadPhoto(e.target.files[0]); e.target.value = "" };
  $("zoom").oninput = e => { view.s = +e.target.value; draw() };
  $("rot").oninput = e => { view.a = +e.target.value * Math.PI / 180; draw() };
  $("resetOutline").onclick = () => { if (!src) msg("먼저 사진을 올려주세요."); else autoOutline() };
  for (const [k, id] of TABS) $(id).onclick = () => { mode = k; setTab() };
  $("cropBig").onclick = () => setBig(!$("faceDlg").classList.contains("big"));
  $("faceDlg").addEventListener("close", () => { if ($("faceDlg").classList.contains("big")) setBig(false) });
  $("faceCancel").onclick = () => $("faceDlg").close();
  $("faceSave").onclick = save;
}
