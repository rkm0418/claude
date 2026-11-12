/* 캐릭터: 얼굴 표시, 화면 배치(가운데 ↔ 왼쪽), 머리 흔들기 */
import { $, reduceMotion, loadImage } from "./util.js";
import { kv } from "./db.js";

let faceAr = 1; // 얼굴 가로/세로 비
let hasFace = false;

/** 얼굴 이미지를 캔버스에 한 번에 그림 (이음선이 생기지 않게) */
export async function setFace(url, ar) {
  const im = await loadImage(url);
  faceAr = ar; hasFace = true;
  try { // 목 색을 얼굴 아래쪽 피부색에 맞춤
    const c = document.createElement("canvas"); c.width = im.width; c.height = im.height;
    const g = c.getContext("2d"); g.drawImage(im, 0, 0);
    const p = g.getImageData(Math.round(im.width * .5), Math.round(im.height * .62), 1, 1).data;
    $("neck").setAttribute("fill", `rgb(${p[0]},${p[1]},${p[2]})`);
  } catch {}
  const cv = $("faceCv");
  cv.width = im.width; cv.height = Math.round(im.height * 1.12);
  cv.getContext("2d").drawImage(im, 0, 0);
  $("head").style.setProperty("--ar", ar);
  $("head").classList.remove("hide"); $("emptyHead").classList.add("hide");
  layout();
}

export async function loadSavedFace() {
  const f = await kv.get("face");
  if (f) await setFace(f.url, f.ar);
}

/* ── 화면 배치 ── */
let asking = false;

/** 얼굴을 화면 위쪽 공간에 맞추고, 어깨 아래는 화면 아래로 잘리게 */
export function layout() {
  const narrow = innerWidth <= 760, t = $("tutor"), topPad = 62, root = document.documentElement.style;
  const head = 1 / (hasFace ? faceAr : 1), tot = head + .40, vis = head + .28;
  let w, left = "50%", bottom;
  if (!asking) {
    w = Math.max(110, Math.min((innerHeight - topPad) / vis, innerWidth * .6, 900));
    bottom = innerHeight + .12 * w;
  } else if (!narrow) {
    const zone = Math.min(innerWidth * .36, 620);
    root.setProperty("--zone", zone + "px");
    w = Math.max(120, Math.min((innerHeight - topPad) / vis, (zone - 16) / 1.12, 800));
    left = (zone / 2 + 8) + "px"; bottom = innerHeight + .12 * w;
  } else {
    const zh = Math.max(150, innerHeight * .30);
    root.setProperty("--zoneH", zh + "px");
    w = Math.max(100, Math.min(zh / vis, innerWidth * .5));
    bottom = topPad + zh + .12 * w;
  }
  t.style.width = w + "px"; t.style.top = (bottom - w * tot / 2) + "px"; t.style.left = left;
}

export function setAskMode(on) {
  if (asking === on) return;
  asking = on;
  document.body.classList.toggle("ask-mode", on);
  layout();
}

/* ── 머리 흔들기: 시작과 멈춤 모두 부드럽게 ── */
let talking = false, thinking = false, shake = 0, nod = 0, running = false, talkTimer = null;

function frame(t) {
  shake += ((talking ? 1 : 0) - shake) * .06;
  nod += ((thinking ? 1 : 0) - nod) * .06;
  if (shake < .003) shake = 0;
  if (nod < .003) nod = 0;
  const hd = $("head");
  if (!reduceMotion() && (shake || nod)) {
    const a = shake * 5 * Math.sin(t / 170) + nod * 3.2 * Math.sin(t / 420);
    const y = -shake * 3.2 * (1 + Math.sin(t / 85)) / 2;
    hd.style.transform = `rotate(${a.toFixed(2)}deg) translateY(${y.toFixed(2)}px)`;
  } else hd.style.transform = "";
  if (talking || thinking || shake || nod) requestAnimationFrame(frame);
  else { running = false; hd.style.transform = "" }
}
function kick() { if (!running) { running = true; requestAnimationFrame(frame) } }

export function setThinking(on) { thinking = on; kick() }

/** 답을 말하는 동안 머리를 흔들었다가 멈춤 (글자 수에 비례) */
export function speak(text) {
  clearTimeout(talkTimer); talking = true; kick();
  talkTimer = setTimeout(() => { talking = false }, Math.max(1800, Math.min(14000, text.length * 90)));
}

export function initCharacter() {
  addEventListener("resize", layout);
  document.addEventListener("fullscreenchange", layout);
  layout();
  // 첫 배치 뒤에 이동 애니메이션을 켬 (처음부터 미끄러져 들어오지 않게)
  requestAnimationFrame(() => requestAnimationFrame(() => $("tutor").classList.add("anim")));
}
