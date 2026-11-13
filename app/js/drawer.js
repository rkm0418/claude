/* 문제 올리기 화면: 사진/글 입력, 문제 부분 선택, 작게 줄이기 */
import { $, decodeImage, showDialog } from "./util.js";

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

/** 사진을 큰 창에 꽉 차게 그리고, 고른 영역만 밝게 */
function paint(sel) {
  const cv = $("probCv"), st = $("cropStage"), dpr = devicePixelRatio || 1;
  const fit = Math.min(st.clientWidth / src.width, st.clientHeight / src.height) || 1;
  cv.style.width = src.width * fit + "px"; cv.style.height = src.height * fit + "px";
  cv.width = Math.round(src.width * fit * dpr); cv.height = Math.round(src.height * fit * dpr);
  const sc = fit * dpr, g = cv.getContext("2d"), r = sel || rect;
  g.drawImage(src, 0, 0, cv.width, cv.height);
  g.fillStyle = "rgba(0,0,0,.6)"; g.fillRect(0, 0, cv.width, cv.height);
  g.save(); g.beginPath(); g.rect(r.x * sc, r.y * sc, r.w * sc, r.h * sc); g.clip(); g.drawImage(src, 0, 0, cv.width, cv.height); g.restore();
  g.strokeStyle = "#fff"; g.lineWidth = 3 * dpr; g.strokeRect(r.x * sc, r.y * sc, r.w * sc, r.h * sc);
}

/** 고른 영역 → 긴 변 1024px, 흑백·대비, JPEG 0.72 */
function rebuild() {
  const k = Math.min(1, MAXD / Math.max(rect.w, rect.h)), w = Math.max(8, Math.round(rect.w * k)), h = Math.max(8, Math.round(rect.h * k));
  const c = document.createElement("canvas"); c.width = w; c.height = h;
  const g = c.getContext("2d");
  try { g.filter = "grayscale(1) contrast(1.25)" } catch {}
  g.fillStyle = "#fff"; g.fillRect(0, 0, w, h);
  g.drawImage(src, rect.x, rect.y, rect.w, rect.h, 0, 0, w, h);
  c.toBlob(b => { blob = b; dims = { w, h }; $("probInfo").textContent = `${w}×${h}px · 약 ${Math.round(w * h / 750)}토큰` }, "image/jpeg", .72);
}

async function loadPhoto(file) {
  try { useSource(await decodeImage(file, 1600)) }
  catch { $("err").textContent = "이 사진은 읽을 수 없어요. 다른 사진으로 올려주세요." }
}

/** 사진·캡처 어느 쪽이든 큰 범위 선택 창으로 */
function useSource(canvas) {
  try {
    src = canvas;
    rect = autoTrim();
    $("err").textContent = "";
    openCrop(); rebuild();
  } catch { $("err").textContent = "이 사진은 읽을 수 없어요. 다른 사진으로 올려주세요." }
}

/* ── 화면 캡처: 원하는 앱·화면을 고르고 3초 안에 넘어가면 그 장면을 찍음 (누르면 바로 캡처) ── */
const sleep = ms => new Promise(r => setTimeout(r, ms));
async function captureScreen() {
  let stream;
  try { stream = await navigator.mediaDevices.getDisplayMedia({ video: true, audio: false }) }
  catch { return } // 취소
  try {
    const video = document.createElement("video");
    video.srcObject = stream; video.muted = true; await video.play();
    const cd = $("countdown"), num = $("cdNum");
    cd.classList.remove("hide");
    let now = false; cd.onclick = () => { now = true };
    const end = Date.now() + 3000; // 다른 앱으로 넘어가 이 탭이 느려져도 시간 기준으로 끝남
    while (!now && Date.now() < end) { num.textContent = Math.ceil((end - Date.now()) / 1000); await sleep(100) }
    cd.classList.add("hide"); await sleep(250); // 안내 화면이 캡처에 안 찍히게
    const k = Math.min(1, 2000 / Math.max(video.videoWidth, video.videoHeight));
    const c = document.createElement("canvas"); c.width = Math.round(video.videoWidth * k); c.height = Math.round(video.videoHeight * k);
    c.getContext("2d").drawImage(video, 0, 0, c.width, c.height);
    useSource(c);
  } catch { $("err").textContent = "화면을 가져오지 못했어요." }
  finally { stream.getTracks().forEach(t => t.stop()); $("countdown").classList.add("hide") }
}

function openCrop() {
  showDialog($("cropDlg"));
  requestAnimationFrame(() => src && paint());
}

function initCropDrag() {
  const cv = $("probCv"); let st = null;
  const pos = e => { const b = cv.getBoundingClientRect(), sc = src.width / b.width; return { x: Math.max(0, Math.min(src.width, (e.clientX - b.left) * sc)), y: Math.max(0, Math.min(src.height, (e.clientY - b.top) * sc)) } };
  const rc = (a, b) => ({ x: Math.min(a.x, b.x), y: Math.min(a.y, b.y), w: Math.abs(a.x - b.x), h: Math.abs(a.y - b.y) });
  cv.onpointerdown = e => { if (!src) return; cv.setPointerCapture(e.pointerId); st = pos(e) };
  cv.onpointermove = e => { if (st) paint(rc(st, pos(e))) };
  cv.onpointerup = e => { if (!st) return; const r = rc(st, pos(e)); st = null; if (r.w > 30 && r.h > 30) { rect = r; rebuild() } paint() };
  $("cropDone").onclick = () => $("cropDlg").close();
  $("cropDlg").addEventListener("close", () => { if (src) $("probPrev").classList.remove("hide") });
  $("recrop").onclick = openCrop;
  addEventListener("resize", () => { if (src && $("cropDlg").open) paint() });
  $("resetCrop").onclick = () => { if (src) { rect = autoTrim(); paint(); rebuild() } };
  $("fullCrop").onclick = () => { if (src) { rect = { x: 0, y: 0, w: src.width, h: src.height }; paint(); rebuild() } };
}

/** 지금 입력된 문제 (세션이 가져가 씀) */
export const getProblem = () => ({ text: "", blob, dims, src, rect: rect && { ...rect }, rmColor: $("rmColor").checked });

export function resetDrawer() {
  src = rect = blob = dims = null;
  $("probPrev").classList.add("hide"); $("err").textContent = "";
}

export function initDrawer({ onStart }) {
  initCropDrag();
  const drop = $("drop");
  $("pickPhoto").onclick = () => $("probFile").click();
  $("camPhoto").onclick = () => $("probCam").click();
  const sc = $("screenCap"); // 화면 캡처를 지원하는 브라우저에서만 아이콘을 보임
  if (sc && navigator.mediaDevices?.getDisplayMedia) { sc.classList.remove("hide"); sc.onclick = captureScreen }
  for (const id of ["probFile", "probCam"]) $(id).onchange = e => { const f = e.target.files[0]; if (f) loadPhoto(f); e.target.value = "" };
  drop.ondragover = e => e.preventDefault();
  drop.ondrop = e => { e.preventDefault(); const f = e.dataTransfer.files[0]; if (f?.type.startsWith("image/")) loadPhoto(f) };
  document.addEventListener("paste", e => {
    const f = [...(e.clipboardData?.files || [])].find(f => f.type.startsWith("image/"));
    if (f) loadPhoto(f)
  });
  $("go").onclick = () => {
    onStart(getProblem()); // 사진이 없으면 문제 글도 질문 칸에 적으면 됨
  };
}
