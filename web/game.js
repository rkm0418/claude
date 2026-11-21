// 역상 — 터치 이동 엔진 (시험판). 화면 320x240, 그림은 2배. 바닥 좌표 (x, d) <-> 화면: X = X0 + x + d/2, Y = Y0 - d/2.
(() => {
'use strict';
const G = window.GAME_DATA, cv = document.getElementById('c'); let ctx = cv.getContext('2d');
const fpC = document.createElement('canvas'); fpC.width = 160; fpC.height = 120; const fpX = fpC.getContext('2d', { willReadFrequently: true });   // 클로즈업은 도트 해상도(160x120)로 그려 2배로 키운다
const mgC = document.createElement('canvas'); mgC.width = 160; mgC.height = 24; const mgX = mgC.getContext('2d', { willReadFrequently: true });
const VW = 320, VH = 240; let S = 2;            // 논리 화면, 그림 배율(큰 방은 1로 줄여 3차원 틀 전체가 보이게 한다)
const CELL = 2;                              // 길찾기 격자 한 칸 = 바닥 2px
const BODY = { rx: 4, rd: 2.2 };             // 아이 발 자리(가구와 벽에서 띄우는 여유)
const SPEED = 36;                            // 화면에서 느끼는 걸음 속도(그림 px/초)
const SHOW_MARKER = false, WALK_FPS = 7, WALK_FPS_HD = 8;                                              // 고해상도 걷기(8장)는 더 빠르게 넘겨 부드럽게
const DIRS = ['r', 'dr', 'd', 'dl', 'l', 'ul', 'u', 'ur'];   // 화면 각도 0도(오른쪽)부터 시계 방향 45도씩
let fadeCol = '20,14,16'; const TRAVEL = { L: [-1, 0], R: [1, 0], B: [0, 1], F: [0, -1] }; let debug = false, room = null, R = null, fade = 0, fadeDir = 0, pending = null, marker = null, msg = null;
const P = { x: 0, d: 0, path: [], dir: 'd', moving: false, t: 0 };
const STATE = { lit: {}, solved: {}, seq: {}, flags: {}, got: {}, sw: {}, vi: {}, pv: {}, bag: [] };                                                  // 퍼즐 상태(방을 옮겨도 유지): 켠 등불
const C = { st: 'none', x: 0, d: 0, t: 0, path: [], rep: 0, flip: false };    // 추격자(나무 머리): hidden(나무인 척) -> rise(일어남) -> chase / wait(뒤따라 들어옴)
const CSPEED = 38, chFrames = {}; const NOCHASE = !/chase/.test(location.hash);                  // 추격 없음: 등장한 뒤 그 자리에 서서 지켜볼 뿐 쫓아오지도 붙잡지도 않는다(주소에 #chase 를 붙이면 옛 추격)
function setupChaser() {
  C.path = []; C.t = 0; C.rep = 0; C.tp = null; C.pl = null; C.face0 = false; C.preview = false;
  if (R.chaser && STATE.real === undefined) STATE.real = 2 + Math.floor(Math.random() * (R.chaser.spots.length - 2));   // 어느 나무가 진짜인지는 판마다 다르다
  if (R.chaser && !STATE.flags.met) { [C.x, C.d] = R.chaser.spots[STATE.real]; C.st = 'hidden'; }
  else if ((R.chase || R.chaser) && STATE.flags.met && !NOCHASE) { C.x = P.x; C.d = P.d; C.st = 'wait'; }
  else C.st = 'none';
}
function route(ax, ad, bx, bd) {
  if (clear(ax, ad, bx, bd)) return [[bx, bd]];
  const a = nearestFree(...cellOf(ax, ad)), b = nearestFree(...cellOf(bx, bd)); if (!a || !b) return []; const raw = astar(a[0], a[1], b[0], b[1]); return raw ? smooth(raw).slice(1) : [];
}
function updChaser(dt) {
  if (C.st === 'none') return false; C.t += dt;
  if (C.st === 'hidden') { if (sdist(P.x, P.d, C.x, C.d) < R.chaser.radius) { C.st = 'rise'; C.t = 0; C.pl = null; C.trail = []; P.path = []; P.act = null; marker = null; C.face = (P.x - C.x) + (P.d - C.d) / 2 < 0 ? -1 : 1; } }
  else if (C.st === 'rise' && (STATE.riseKind || 7) > 1) {                         // 등장 후보 2~6: 정해진 길이만큼 재생
    const K = STATE.riseKind || 7, dur = RDUR[K];
    if (C.t > dur) { if (C.preview) C.t = dur; else { if (K === 6 || K === 7) { const [ox, oy] = K === 7 ? blinkOff(9, 4, 6) : blinkOff(dur), d = -2 * oy; C.x += ox - d / 2; C.d += d; } C.st = NOCHASE ? 'stand' : 'chase'; C.tp = null; C.t0 = -99; C.lt = 0; STATE.flags.met = true; if (!NOCHASE) msg = { text: '도망쳐야 한다', t: 1.6 }; } }
  }
  else if (C.st === 'rise') {
    const t = C.t; if (C.preview && t > 2.6) { C.t = 2.6; return false; }
    if (t >= 2.15 && !C.pl) { const q = sdist(C.x, C.d, P.x, P.d), k = Math.max(0, Math.min(16, q - 14)) / (q || 1); C.pl = [[C.x, C.d], [C.x + (P.x - C.x) * k, C.d + (P.d - C.d) * k]]; }
    if (C.pl && t < 2.6) { const k = ease((t - 2.15) / .35); C.x = C.pl[0][0] + (C.pl[1][0] - C.pl[0][0]) * k; C.d = C.pl[0][1] + (C.pl[1][1] - C.pl[0][1]) * k; }   // 마지막에 한 걸음 다가온다
    if (t > 2.6) { C.st = NOCHASE ? 'stand' : 'chase'; C.tp = null; C.t0 = C.t; C.lt = 0; C.pl = null; STATE.flags.met = true; if (!NOCHASE) msg = { text: '도망쳐야 한다', t: 1.6 }; }
  }
  else if (C.st === 'stand') { C.face = (P.x - C.x) + (P.d - C.d) / 2 < 0 ? -1 : 1; }                                        // 추격 없음: 서서 아이 쪽을 바라볼 뿐
  else if (C.st === 'wait') { if (C.t >= .5 && !C.face0) { C.face0 = true; C.face = (P.x - C.x) + (P.d - C.d) / 2 < 0 ? -1 : 1; } if (C.t > 2.5) { C.st = 'chase'; C.tp = null; C.t0 = -99; C.lt = 0; } }
  else if (C.st === 'chase') {
    C.rep -= dt; if (C.rep <= 0) { C.rep = .4; C.path = route(C.x, C.d, P.x, P.d); }
    if (!C.tp || C.t > C.tp.until) { const r = Math.random(), u = Math.random();                 // 템포가 제멋대로: 뚝 멈춤 / 느릿느릿 / 보통 / 확 달려듦
      C.tp = r < .1 ? { v: -.8, until: C.t + .12 + u * .14 } : r < .24 ? { v: 0, until: C.t + .2 + u * .5 } : r < .45 ? { v: .35 + u * .25, until: C.t + .6 + u * .9 } : r < .75 ? { v: .9 + u * .2, until: C.t + .6 + u * .8 } : { v: 1.8 + u * .6, until: C.t + .3 + u * .4 }; }
    const cq = sdist(C.x, C.d, P.x, P.d); let cv = C.tp.v;                                             // 바로 뒤에 붙어 따라온다: 멀어지면 따라붙고, 등 뒤(약 22px)에서는 늦춘다. 확 달려들 때만 예외
    if (cq > 34) cv = cq > 110 ? 3.4 : cq > 70 ? 2.4 : Math.max(cv, 1.5);                              // 멀어진 걸 알아채면 멈춤·뒷걸음 없이 빠르게 따라붙는다(멀수록 더 빠르게)
    else if (cv > 0 && cq < 22 && cv < 1.7) cv *= .25;
    C.an = (C.an || 0) + dt * (2 + Math.abs(cv) * 7); C.lt = (C.lt || 0) + ((C.tp.v === 0 ? .52 : 0) - (C.lt || 0)) * Math.min(1, dt * 2.4);   // 멈출 때마다 고개가 천천히 기운다
    if (cv < 0 && cq > 1) { const k = cv * CSPEED * dt / cq, nx = C.x + (P.x - C.x) * k, nd = C.d + (P.d - C.d) * k; if (isFree(...cellOf(nx, nd))) { C.x = nx; C.d = nd; } }   // 뒷걸음
    let left = CSPEED * dt * Math.max(0, cv);                        // 걸음이 고르지 않다: 멈칫하다가 훅 다가온다
    while (left > 0 && C.path.length) { const [tx, td] = C.path[0], dist = sdist(C.x, C.d, tx, td); if (Math.abs(tx - C.x + (td - C.d) / 2) > .3) C.flip = (tx - C.x) + (td - C.d) / 2 < 0; if (dist <= left) { C.x = tx; C.d = td; C.path.shift(); left -= dist; } else { const k = left / dist; C.x += (tx - C.x) * k; C.d += (td - C.d) * k; left = 0; } }
    if (sdist(C.x, C.d, P.x, P.d) < 7) { msg = { text: '붙잡혔다…', t: 1.8 }; P.path = []; P.act = null; C.st = 'none'; pending = { to: room, spawn: R.start }; fadeDir = 1; return true; }
  }
  return false;
}
const CAN = [[0, -50, 13, '#101e22'], [-8, -45, 10, '#16282a'], [7.5, -51, 10, '#16282a'], [0, -57, 8, '#1e3434']];
const ease = (k) => { k = Math.max(0, Math.min(1, k)); return k * k * (3 - 2 * k); };
function canopy(alpha, sx) {                                                    // 나무의 수관처럼 보이던 것. sx: 가로로 눌림(돌아서는 중)
  ctx.globalAlpha = alpha; CAN.forEach(([ox, oy, rr, c]) => { ctx.fillStyle = c; ctx.beginPath(); ctx.ellipse(ox * sx * S, oy * S, Math.max(.4, rr * sx) * S, rr * .75 * S, 0, 0, 6.3); ctx.fill(); }); ctx.globalAlpha = 1;
}
function figure(im, bend, sx, sy, head, wob, glitch, sink) {                    // 몸통과 머리를 2줄씩 그린다. wob: 윤곽 일렁임, glitch: 몇 줄이 옆으로 어긋남, sink: 땅속에 잠긴 깊이(지면 아래는 가린다)
  const now = performance.now() / 1000, w = (r) => (wob ? wob * Math.sin(r * .9 + now * 14) : 0) + (glitch && ((r * 7 + Math.floor(now * 30)) % 11 === 0) ? (r % 4 ? 3 : -3) : 0);
  ctx.save(); ctx.beginPath(); ctx.rect(-70 * S, -170 * S, 140 * S, 170 * S); ctx.clip(); ctx.translate(0, (sink || 0) * S); ctx.scale(sx, sy);
  for (let r = 62; r >= 30; r -= 2) ctx.drawImage(im, 0, r, 30, 2, (-15 + bend * Math.pow((64 - r) / 34, 1.7) + w(r)) * S, -(64 - r) * S, 30 * S, 2 * S + 1);
  if (head && head.a > 0) { ctx.globalAlpha *= head.a; ctx.translate((bend + (head.dx || 0)) * S, -33 * S); ctx.rotate(head.ang); ctx.scale(head.sx / sx, 1 / sy); for (let r = 28; r >= 0; r -= 2) ctx.drawImage(im, 0, r, 30, 2, (-15 + w(r) * 1.3) * S, -(30 - r) * S, 30 * S, 2 * S + 1); }
  ctx.restore();
}
function camZoom() {                                                            // 마지막 한 걸음에 카메라가 살짝 당겨졌다 돌아온다
  if (C.st === 'rise' && C.t > 2.15) return 1 + .06 * ease((C.t - 2.15) / .2);
  if (C.st === 'chase' && C.t0 > 0 && C.t - C.t0 < .5) return 1 + .06 * (1 - ease((C.t - C.t0) / .5));
  return 1;
}
const DASH = [[.75, 64, 42], [1.2, 42, 20], [1.6, 20, 0]];                      // 다다닥 세 번: [시작 시각, 잠긴 깊이 처음, 끝]. 0.2초 동안 다섯 번 잘게 끊어 오른다
function climb(tt) { let sink = 64, dash = false; for (const [a, s0, s1] of DASH) { if (tt >= a + .2) sink = s1; else if (tt >= a) { sink = s0 + (s1 - s0) * Math.min(1, (Math.floor((tt - a) / .04) + 1) / 5); dash = true; } } return [sink, dash]; }
// ---------- 등장 후보 2~6 (고르기용) ----------
const RDUR = { 2: 3.2, 3: 2.9, 4: 4.8, 5: 3.2, 6: 3.1, 7: 3.8, 8: 4.8, 9: 4.8, 10: 5, 11: 5 };
const nowS = () => performance.now() / 1000;
function rows(im, r0, r1, base, wob, kf) { const n = nowS(); for (let r = r1 - 2; r >= r0; r -= 2) { const k = kf ? kf(r) : 1; ctx.drawImage(im, 0, r, 30, 2, (-15 * k + (wob ? wob * Math.sin(r * .9 + n * 14) : 0)) * S, (r - base) * S, 30 * k * S, 2 * S + 1); } }   // 스프라이트의 r0~r1행을 2줄씩(base행이 y=0)
const trunk = (h, a) => { ctx.globalAlpha = a === undefined ? 1 : a; ctx.fillStyle = '#28222e'; ctx.fillRect(-1.5 * S, -h * S, 3 * S, h * S); ctx.fillStyle = '#463c4e'; ctx.fillRect(-1.5 * S, -h * S, S, h * S); ctx.globalAlpha = 1; };
const burst = (t, starts, len = .2) => { let p = 0, d = false; for (const s0 of starts) { if (t >= s0 + len) p += 1; else if (t >= s0) { p += Math.min(1, (Math.floor((t - s0) / .04) + 1) / 5); d = true; } } return [p / starts.length, d]; };
const skf = (d) => d ? 'w' + (1 + Math.floor(nowS() * 26) % 4) : 'idle';
function specks(X, Y, k, h) { for (let i = 0; i < 16 * k; i++) { ctx.fillStyle = Math.random() < .5 ? 'rgba(8,6,12,.8)' : 'rgba(216,204,196,.7)'; ctx.fillRect((R.ox + X - 22 + Math.random() * 44) * S, (R.oy + Y - (h || 72) * Math.random()) * S, S * (Math.random() < .2 ? 3 : 1), S); } for (let i = 0; i < 50 * k; i++) { ctx.fillStyle = 'rgba(200,200,210,.12)'; ctx.fillRect(Math.random() * VW, Math.random() * VH, 2, 2); } }
function blinkOff(t, sa = 3, sb = 5) { const [X, Y] = scr(C.x, C.d), [px, py] = scr(P.x, P.d), q = Math.hypot(px - X, py - Y) || 1, st = BLINKS.filter(b => t >= b + .08).length, m = st >= sb ? Math.max(0, q - 15) : st >= sa ? 8 : 0; return [(px - X) / q * m, (py - Y) / q * m, st]; }
const BLINKS = [.5, .95, 1.4, 1.85, 2.3, 2.7];
const SNAP = [[0, 0], [2.7, 0], [2.95, -1.22], [3.3, -1.22], [3.36, .1], [3.62, .1], [3.68, 1.05], [4, 1.05], [4.06, -1.57], [4.4, -1.57], [4.46, .6], [4.7, .6], [4.76, -.9], [99, -.9]];
function snapAng(tt, bounce) {                                                // 목이 각지게 꺾인다: 한 프레임에 확 꺾여 잠깐 멈췄다가 또 확 꺾인다(되튐은 효과 있는 버전만)
  let i = 0; while (i < SNAP.length - 1 && tt >= SNAP[i + 1][0]) i++; const [t0, v] = SNAP[i], pv = i ? SNAP[i - 1][1] : 0, u = tt - t0;
  return u < .06 && i > 0 ? pv + (v - pv) * u / .06 : v + (bounce && i > 0 && u < .3 ? (v - pv) * .16 * Math.exp(-(u - .06) * 14) * Math.cos((u - .06) * 44) : 0);
}
function drawAlt(K, t) {
  const [X, Y] = scr(C.x, C.d), face = C.face || 1, n = nowS(); let nz = 0; C.black = false;
  ctx.save(); ctx.translate((R.ox + X) * S, (R.oy + Y + 1) * S);
  if (K === 2) {                                                                // 거꾸로 내려옴: 수관 속에서 거꾸로 매달려 머리부터 내려온다 -> 몸만 목을 축으로 반 바퀴 돌아 내려선다 -> 거꾸로였던 머리가 천천히 돌아 선다
    const [p, d] = burst(t, [.4, .85, 1.3]), N = -74 + 40 * p, sw = ease((t - 1.8) / .5), hr = ease((t - 2.45) / .6), im = chFrames[skf(d || (sw > 0 && sw < 1))], wob = d ? 1.5 : t < .4 ? 2 * t / .4 : .7; nz = t > .4 && t < 3 ? (d ? .9 : .3) : 0;
    trunk(52); ctx.save(); ctx.beginPath(); ctx.rect(-60 * S, -57 * S, 120 * S, 57 * S); ctx.clip(); if (face < 0) ctx.scale(-1, 1); ctx.translate((d ? (Math.floor(n * 26) % 2 ? 2 : -2) : 0) * S, N * S);
    ctx.save(); ctx.rotate(Math.PI * (1 - sw)); rows(im, 30, 64, 30, wob); ctx.restore();                         // 몸: 목에서 위로(거꾸로) -> 아래로
    ctx.save(); ctx.rotate(Math.PI * (1 - hr) + (t > 1.5 && t < 1.8 ? .07 * Math.sin(n * 120) : 0)); rows(im, 0, 30, 30, wob); ctx.restore(); ctx.restore();
    canopy(1, 1);
  } else if (K === 3) {                                                         // 껍질 벗기: 줄기가 두 쪽으로 갈라져 벌어지고, 사이에서 너무 가는 몸이 빠져나와 숨 쉬듯 부풀어 제 폭이 된다
    const a = t < 1 ? .5 * ease((t - .3) / .7) : .5 + .95 * ease((t - 1) / .9), em = ease((t - .45) / .6), sw = ease((t - 1.4) / .9), k = (.14 + .2 * em + .66 * sw) * (1 + (t > 1.4 && t < 2.6 ? .1 * Math.sin((t - 1.4) * 11) : 0)), wob = t < .3 ? 2 * t / .3 : 3 - 2.3 * ease((t - 2) / .7); nz = t > .3 && t < 2.7 ? .6 : 0;
    if (em > 0) { ctx.save(); ctx.globalAlpha = em; if (face < 0) ctx.scale(-1, 1); rows(chFrames.idle, 30, 64, 64, wob, () => k); ctx.translate(0, -34 * S); rows(chFrames.idle, 0, 30, 30, wob * 1.3, () => Math.min(1, k * 1.15)); ctx.restore(); }
    for (const sg of [-1, 1]) { ctx.save(); ctx.translate(sg * (1 + 3 * Math.min(1, a * 2)) * S, 0); ctx.rotate(sg * a); ctx.fillStyle = sg < 0 ? '#28222e' : '#3a3242'; ctx.fillRect((sg < 0 ? -2 : 0) * S, -52 * S, 2 * S, 52 * S); ctx.fillStyle = '#0c0a10'; ctx.fillRect((sg < 0 ? 0 : -1) * S, -52 * S, S, 52 * S);
      CAN.forEach(([ox, oy, rr, c], i) => { if ((i % 2 ? 1 : -1) !== sg) return; ctx.fillStyle = c; ctx.beginPath(); ctx.ellipse((ox + sg * 3) * S, oy * S, rr * S, rr * .75 * S, 0, 0, 6.3); ctx.fill(); }); ctx.restore(); }
  } else if (K === 4 || K === 8 || K === 9 || K === 10 || K === 11) {           // 4 회로식 악령(노이즈 있음) / 8 노이즈 뺌 / 9 모션블러 / 10 목이 각지게 꺾임 / 11 목 꺾임 + 움직일 때 효과(떨림·프레임 흔들림·번짐·노이즈) 전혀 없음
    const clean = K !== 4, blur = K === 9, neck = K >= 10, fx = K !== 11;
    const KF = [[0, 0], [.9, 0], [1, .1], [1.2, .1], [1.26, .06], [1.55, .06], [1.62, .3], [1.95, .3], [2.01, .26], [2.4, .26], [2.46, .55], [2.7, .55], [2.77, .5], [3.1, .5], [3.15, .82], [3.4, .82], [3.46, .78], [3.8, .78], [3.86, 1], [99, 1]], HL = [0, .55, -.4, .7, -.6, .25, -.15, .5];
    const pose = (tt) => {                                                      // tt 시각의 자세(잔상은 지난 시각의 자세를 다시 그린다)
      let ki = 0; while (ki < KF.length - 2 && tt >= KF[ki + 1][0]) ki++; const kt = tt - KF[ki][0], u = kt < .05 && ki > 0 ? KF[ki - 1][1] + (KF[ki][1] - KF[ki - 1][1]) * kt / .05 : KF[ki][1];
      const ca = 1 - ease((tt - .5) / .4), mv = kt < .14 && ki > 0 && tt < 3.95, st = tt > 3.9, sway = st ? Math.sin(tt * 1.9) : 0, hl = neck ? snapAng(tt, fx) : tt > 2.9 ? HL[Math.floor(tt / .38) % HL.length] * Math.min(1, (tt - 2.9) / .5) : 0;
      const jit = !fx ? 0 : mv ? (Math.floor(tt * 30) % 2 ? 2 : -2) : (tt < .9 && tt > .2 ? Math.sin(tt * 90) * .8 : 0), glitch = !clean && (Math.sin(tt * 5.3) > .96 || Math.sin(tt * 8.7 + 2) > .97);
      return { th: Math.PI * (1 - u), ca, mv, st, sway, hl, jit, glitch, sy: 1 + .1 * ease((tt - 3.9) / .5) + (st ? .03 * Math.sin(tt * 1.9) : 0), tt };
    };
    const body = (o, al) => {
      const im = chFrames[fx ? skf(o.mv) : 'idle'], wob = !fx ? 0 : o.mv ? 1.8 : o.tt < .5 ? 2 * o.tt / .5 : .7;
      ctx.save(); if (face < 0) ctx.scale(-1, 1); ctx.translate((o.jit + o.sway * 3 + (o.glitch ? 3 : 0)) * S, 0); ctx.scale(1, o.sy); ctx.globalAlpha = Math.min(1, (1 - o.ca) * 2.5) * al; rows(im, 46, 64, 64, wob);
      ctx.translate(0, -18 * S); ctx.rotate(-o.th + (o.st ? o.sway * .07 : 0)); rows(im, 30, 46, 46, wob);                                  // 상체: 엉덩이를 축으로 조금씩 넘어온다(서서는 좌우로 휘청)
      ctx.translate((neck && Math.abs(o.hl) > .9 ? (o.hl > 0 ? 1.5 : -1.5) : 0) * S, -16 * S); ctx.rotate(o.th + o.hl + (o.st ? -o.sway * .05 : 0)); ctx.globalAlpha = (1 - o.ca) * al; rows(im, 0, 30, 30, wob * 1.3); ctx.restore();   // 머리: 툭 꺾였다 돌아온다
    };
    const o = pose(t); nz = clean ? 0 : (o.mv ? .4 : t > .3 && t < 3.9 ? .12 : .05) + (o.glitch ? .3 : 0);
    if (o.ca > 0) { trunk(52, o.ca); canopy(o.ca, 1); }
    if (blur && t > .5) for (const [d, al] of [[.12, .12], [.08, .2], [.04, .32]]) body(pose(Math.max(0, t - d)), al);                       // 모션블러: 0.04·0.08·0.12초 전 자세를 옅게 겹친다
    body(o, 1);
  } else if (K === 5) {                                                         // 여럿이 하나로: 세 그루가 녹아 땅을 기어와 뭉치고, 위로 뽑히듯 늘어나 몸이 된다. 머리가 마지막에 벌어진다
    const OFF = [[-36, -5], [31, -9], [9, 13]], melt = ease(t / .6), [p, d] = burst(t, [.65, 1, 1.35], .22), up = ease((t - 1.65) / .7), bloom = ease((t - 2.45) / .6); nz = t > .2 && t < 3 ? (d ? .9 : .5) : 0;
    OFF.forEach(([ox, oy], i) => { const cx = ox * (1 - p), cy = oy * (1 - p); ctx.save(); ctx.translate(cx * S, cy * S);
      if (melt < 1) { ctx.save(); ctx.scale(1 + melt, 1 - melt); ctx.translate(2 * Math.sin(n * 14 + i) * melt * S, 0); trunk(46 + i * 4); canopy(1 - melt, 1); ctx.restore(); }
      if (melt > 0 && up < 1) { const w = (5 + 6 * melt) * (1 - up * .6), jx = d ? (Math.floor(n * 26 + i) % 2 ? 2 : -2) : 0; ctx.fillStyle = '#0e0b12'; ctx.beginPath(); ctx.ellipse(jx * S, 0, w * S, w * .36 * S, 0, 0, 6.3); ctx.fill(); ctx.strokeStyle = '#0e0b12'; ctx.lineWidth = S;
        for (let l = -2; l <= 2; l++) { if (!l) continue; const ph = d ? Math.sin(n * 60 + l + i) * 2 : 0; ctx.beginPath(); ctx.moveTo((jx + l * 2) * S, 0); ctx.lineTo((jx + l * (w / 2 + 2) + ph) * S, (l % 2 ? 3 : -3) * S); ctx.stroke(); } }
      ctx.restore(); });
    if (up > 0) { const sy = up < .7 ? 1.25 * up / .7 : 1.25 - .25 * (up - .7) / .3, kx = 1.7 - .7 * up; ctx.save(); if (face < 0) ctx.scale(-1, 1); ctx.scale(1, Math.max(.02, sy)); rows(chFrames.idle, 30, 64, 64, 3 - 2.3 * bloom, () => kx);
      if (bloom > 0) { ctx.translate(0, -34 * S); ctx.scale(bloom, .2 + .8 * bloom); rows(chFrames.idle, 0, 30, 30, 2.5 * (1 - bloom) + .6); } ctx.restore(); }
  } else if (K === 7) {                                                         // 껍질이 뚜둑, 뚜둑 벌어진다: 깜빡임 없이, 잠깐 떨다가 한 번에 뚝 꺾이고 살짝 되튀는 움직임을 여섯 번
    const [px, py] = scr(P.x, P.d), q = Math.hypot(px - X, py - Y) || 1, st = BLINKS.filter(b => t >= b).length;
    const sv = (arr) => { if (!st) return arr[0]; const b = BLINKS[st - 1], u = t - b, v0 = arr[st - 1], v1 = arr[st]; return u < .07 ? v0 + (v1 - v0) * u / .07 : v1 + (v1 - v0) * .2 * Math.exp(-(u - .07) * 16) * Math.cos((u - .07) * 44); };
    const nb = st < 4 ? BLINKS[st] : undefined, pre = nb !== undefined && nb - t < .22 ? (1 - (nb - t) / .22) : 0, tj = pre ? Math.sin(n * 190) * pre * 1.2 : 0;                       // 꺾이기 직전의 잔떨림
    const a = sv([0, .1, .46, 1.45, 1.45, 1.45, 1.45]), k = Math.max(0, sv([0, .22, .62, 1, 1, 1, 1])), far = Math.max(0, q - 15 - 8), hsh = (i) => { const v = Math.sin(i * 127.1 + 311.7) * 43758.5453; return v - Math.floor(v); };
    const KEY = [[2.3, 0], [2.42, 0], [2.46, .3], [2.7, .3], [2.73, .2], [2.86, .2], [2.9, .62], [3.0, .62], [3.02, .5], [3.06, .5], [3.1, .55], [3.3, .55], [3.34, 1]];   // 다가오는 속도가 뒤죽박죽: 멈춤, 확, 뒷걸음, 찔끔, 확
    let pr = 0; if (t >= 2.3) { pr = 1; for (let i = 1; i < KEY.length; i++) if (t < KEY[i][0]) { const [t0, v0] = KEY[i - 1], [t1, v1] = KEY[i]; pr = v0 + (v1 - v0) * (t - t0) / (t1 - t0); break; } }
    const gl = t >= 2.3, gi = Math.floor(t * (hsh(Math.floor(t * 3)) < .5 ? 19 : 7)), gr = hsh(gi);                                                    // 고개가 오류 난 것처럼 꺾였다 돌아왔다 한다(각진 값만, 박자도 제멋대로)
    const m = gl ? 8 + far * pr : sv([0, 0, 0, 0, 8, 8, 8]), ha = gl ? (gr < .42 ? -1.22 : gr < .7 ? 0 : gr < .86 ? .79 : -1.57) : 0, hx = gl && gr > .8 ? (gr > .9 ? 2 : -2) : 0, sy = t > 3.34 ? 1.15 : 1, mvg = gl && pr > 0 && pr < 1 && t > 2.42, ox = (px - X) / q * m, oy = (py - Y) / q * m;
    const bark = () => { for (const sg of [-1, 1]) { ctx.save(); ctx.translate((sg * (st ? 1 + 3 * Math.min(1, a * 2) : 0) + (st < 3 ? tj : 0)) * S, 0); ctx.rotate(sg * a); ctx.fillStyle = sg < 0 ? '#28222e' : '#3a3242'; ctx.fillRect((sg < 0 ? -2 : 0) * S, -52 * S, 2 * S, 52 * S); if (st) { ctx.fillStyle = '#0c0a10'; ctx.fillRect((sg < 0 ? 0 : -1) * S, -52 * S, S, 52 * S); }
      CAN.forEach(([cx, cy, rr, c], i) => { if ((i % 2 ? 1 : -1) !== sg) return; ctx.fillStyle = c; ctx.beginPath(); ctx.ellipse((cx + sg * (st ? 3 : 0)) * S, cy * S, rr * S, rr * .75 * S, 0, 0, 6.3); ctx.fill(); }); ctx.restore(); } };
    if (st >= 3) bark();
    if (k > 0) { ctx.save(); ctx.translate((ox + (st >= 3 ? tj : 0)) * S, oy * S); if (face < 0) ctx.scale(-1, 1); ctx.scale(1, sy); rows(chFrames[mvg ? 'w' + (1 + Math.floor(n * 22) % 4) : st === 4 && t - BLINKS[3] < .25 ? 'w2' : 'idle'], 30, 64, 64, 0, () => k); ctx.translate(hx * S, -34 * S); ctx.rotate(ha + (st >= 3 && !gl ? tj * .04 : 0)); rows(chFrames.idle, 0, 30, 30, 0, () => Math.min(1, k * 1.15)); ctx.restore(); }
    if (st < 3) bark();
    if (st && st < 5 && t - BLINKS[st - 1] < .1) { ctx.fillStyle = 'rgba(216,204,196,.8)'; for (let i = 0; i < 6; i++) ctx.fillRect((ox + (Math.random() - .5) * 26) * S, (oy - Math.random() * 60) * S, S, S); }   // 꺾이는 순간 튀는 부스러기
  } else {                                                                      // 6 깜빡일 때마다: 화면이 꺼졌다 켜질 때마다 달라져 있다. 움직이는 순간은 보이지 않는다
    const [ox, oy, st] = blinkOff(t); C.black = BLINKS.some(b => t >= b && t < b + .08);
    ctx.translate(ox * S, oy * S); if (face < 0) ctx.scale(-1, 1);
    if (st < 3) { ctx.save(); ctx.scale(st >= 2 ? 1 : .6, 1); rows(chFrames.idle, 30, 64, 64, 0); ctx.restore(); ctx.save(); ctx.translate(0, -34 * S); ctx.rotate(st >= 1 ? .42 : 0); ctx.translate(0, 34 * S); trunkTop(); canopy(1, 1); ctx.restore(); }
    else { ctx.save(); ctx.scale(1, st >= 5 ? 1.15 : 1); rows(chFrames[st === 3 ? 'w2' : 'idle'], 30, 64, 64, 0); ctx.translate(0, -34 * S); ctx.rotate(st >= 4 ? -1.22 : 0); rows(chFrames.idle, 0, 30, 30, 0); ctx.restore(); }
  }
  ctx.restore(); ctx.globalAlpha = 1; if (nz > 0) specks(X, Y, nz);
}
const trunkTop = () => { ctx.fillStyle = '#1a1820'; ctx.fillRect(-1.5 * S, -52 * S, 3 * S, 20 * S); };
function drawChaser() {
  if ((C.st === 'rise' || C.st === 'hidden') && (STATE.riseKind || 7) > 1) return drawAlt(STATE.riseKind || 7, C.st === 'hidden' ? 0 : C.t);
                                                         // 등장: 나무 줄기가 땅속으로 꺼진다 -> 빈 틈 -> 다다닥(머리·어깨) -> 멈춤 -> 다다닥(허리) -> 멈춤 -> 다다닥(전신) -> 키가 늘어나며 한 걸음
  if (C.st === 'none') return;
  const t = C.t, face = C.face || 1, now = performance.now() / 1000; let f = 'idle', flip = C.flip, bend = 0, sx = 1, sy = 1, alpha = 1, can = 0, wob = 0, dash = false, noise = 0, sink = 0, gap = 0, jx = 0, head = { ang: 0, sx: 1, a: 1 };
  if (C.st === 'hidden') { sx = .6; can = 1; head = null; flip = false; }
  else if (C.st === 'rise' && t < .55) { flip = false; sx = .6; head = null; can = 1 - ease((t - .3) / .2); sink = 64 * ease((t - .3) / .25); wob = Math.min(2, 2 * t / .3); noise = t > .3 ? .6 : .2; gap = ease((t - .3) / .2); }   // 줄기가 일렁이다 땅속으로 빨려 들어간다
  else if (C.st === 'rise' || C.st === 'wait') {
    const tt = C.st === 'rise' ? t : t - .25, v = C.st === 'rise' ? ease((t - 2.15) / .35) : 0; flip = face < 0; gap = C.st === 'rise' ? 1 : ease((t - .5) / .3); if (gap <= 0) return;
    [sink, dash] = climb(tt); const up = tt >= .75, calm = tt >= 1.8;
    if (dash) { f = 'w' + (1 + Math.floor(now * 26) % 4); jx = Math.floor(now * 26) % 2 ? 3 : -3; }                    // 잔걸음: 다리·팔이 흐려 보이게, 좌우로 빠르게 흔들리며 기어오른다
    wob = !up ? 0 : dash ? 1.5 : v > 0 ? 3 : calm ? 2 - 1.4 * ease((tt - 1.8) / .35) : .8; noise = (!up ? 0 : dash ? .9 : v > 0 ? 1 : .3) * (C.st === 'wait' ? .5 : 1);
    head.ang = (!dash && up && !calm ? .07 * Math.sin(now * 120) : 0) - 1.22 * v; sy = 1 + .15 * v; bend = 3 * v;              // 멈춘 동안 고개만 더듬이처럼 떤다
    if (gap >= 1 && sink >= 64) gap = 1;
  }
  else if (C.st === 'stand') { flip = face < 0; head.ang = 0; }
  else if (C.st === 'chase') {
    f = 'w' + (1 + Math.floor(C.an || 0) % 4); bend = C.tp ? Math.min(4, C.tp.v * 2) : 0; const back = 1 - ease((t - C.t0) / 2), fs = flip === (face < 0) ? 1 : -1;
    const hsh = (i) => { const v = Math.sin(i * 127.1 + 311.7) * 43758.5453; return v - Math.floor(v); }, gi = Math.floor(t * (hsh(Math.floor(t * 3)) < .5 ? 19 : 7)), gr = hsh(gi);   // 쫓아오는 내내 목이 오류 난 것처럼 꺾였다 돌아왔다 한다
    sy = 1 + .15 * back; head.ang = (gr < .42 ? -1.22 : gr < .7 ? 0 : gr < .86 ? .79 : -1.57) * fs; head.dx = gr > .8 ? (gr > .9 ? 2 : -2) : 0; wob = 3 * Math.max(0, 1 - (t - C.t0) / .4);
  }
  const im = chFrames[f]; if (!im) return; const [X, Y] = scr(C.x, C.d);
  const pose = (sk, a) => { ctx.save(); ctx.globalAlpha = a; ctx.translate((R.ox + X + jx) * S, (R.oy + Y + 1) * S); if (flip) ctx.scale(-1, 1);
    if (can > 0) { ctx.globalAlpha = a * can; ctx.fillStyle = '#1a1820'; ctx.fillRect(-1.5 * S, Math.min(0, -52 + sk) * S, 3 * S, Math.max(0, Math.min(22, 52 - sk)) * S); ctx.globalAlpha = a; }
    figure(im, bend, sx, sy, head, wob, dash, sk); if (can > 0 && sk < 30) canopy(a * can, 1); ctx.restore(); ctx.globalAlpha = 1; };
  if (gap > 0) { const cx = (R.ox + X) * S, cy = (R.oy + Y + 1) * S; ctx.fillStyle = '#07060a'; ctx.beginPath(); ctx.ellipse(cx, cy, 11 * gap * S, 3 * gap * S, 0, 0, 6.3); ctx.fill(); ctx.fillStyle = '#3c5048'; for (const [dx, dy] of [[-12, -1], [-8, 2], [9, 2], [13, -1], [0, 3]]) ctx.fillRect(cx + dx * gap * S, cy + dy * S, 2 * S, S); }   // 땅의 어두운 틈과 흙 부스러기
  else if (C.st === 'chase') { ctx.fillStyle = 'rgba(10,6,16,.5)'; ctx.beginPath(); ctx.ellipse((R.ox + X) * S, (R.oy + Y + 1) * S, 9 * S, 2.4 * S, 0, 0, 6.3); ctx.fill(); }
  if (dash) { pose(sink + 12, .15 * alpha); pose(sink + 6, .3 * alpha); }                                              // 아래로 끌리는 잔상
  pose(sink, alpha);
  if (noise > 0) { for (let i = 0; i < 16 * noise; i++) { ctx.fillStyle = Math.random() < .5 ? 'rgba(8,6,12,.8)' : 'rgba(216,204,196,.7)'; ctx.fillRect((R.ox + X - 22 + Math.random() * 44) * S, (R.oy + Y - (72 - sink) * Math.random()) * S, S * (Math.random() < .2 ? 3 : 1), S); }
    for (let i = 0; i < 50 * noise; i++) { ctx.fillStyle = 'rgba(200,200,210,.12)'; ctx.fillRect(Math.random() * VW, Math.random() * VH, 2, 2); } }
}
// ---------- 두 시선 퍼즐(§31): 방마다 아이의 눈 -> 바깥의 눈. 글 없음 ----------
let adultIm = null, AC = null; const VW_ = { look: null, t: 0, kn: [], flash: {}, hintT: 0 };
function audio() { if (AC || !(window.AudioContext || window.webkitAudioContext)) return; try { AC = new (window.AudioContext || window.webkitAudioContext)(); } catch (e) { AC = null; } }
function beep(f, dur = .25, type = 'sine', vol = .12, when = 0) { if (!AC) return; try { const o = AC.createOscillator(), g = AC.createGain(), t0 = AC.currentTime + when; o.type = type; o.frequency.value = f; g.gain.setValueAtTime(vol, t0); g.gain.exponentialRampToValueAtTime(.001, t0 + dur); o.connect(g); g.connect(AC.destination); o.start(t0); o.stop(t0 + dur); } catch (e) {} }
const TONES = [262, 330, 392];
function curView(r = R) { if (!r || !r.views) return null; if (r.vreq && !STATE.flags[r.vreq]) return null; const i = STATE.vi[r.name] || 0; return i < r.views.length ? r.views[i] : null; }
function viewObjs(r) { const v = curView(r); return v ? v.objects : (r.views ? [] : (r.objects || [])); }
const pv = (o) => { const v = STATE.pv[o.id]; return v === undefined ? (o.init === undefined ? 0 : o.init) : v; };
function viewSolved(v) {
  if (v.objects.some(o => o.want !== undefined && pv(o) !== o.want)) return false;
  if (v.seq && (STATE.pv[R.name + '_p'] || 0) < v.seq.length) return false;
  if (v.knock && !STATE.pv[R.name + '_k']) return false;
  return true;
}
function checkView() { const v = curView(); if (!v || VW_.t > 0) return; if (viewSolved(v)) { VW_.t = 1.1; beep(523, .5, 'triangle', .1); beep(659, .6, 'triangle', .1, .12); } }
function actObj(o) {
  const v = curView(); if (!v || VW_.t > 0) return;
  if (o.kind === 'look') { VW_.look = { o, t: 1.7 }; if (o.tick) beep(900, .03, 'square', .05); }
  else if (o.kind === 'dial' || o.kind === 'toggle' || o.kind === 'slot') {
    if (o.look === 'cup' && STATE.bag.length < 3) { beep(120, .12, 'square', .06); return; }
    STATE.pv[o.id] = (pv(o) + 1) % o.n; beep(o.kind === 'dial' ? 700 : 300, .05, 'square', .06); checkView();
  }
  else if (o.kind === 'play') { STATE.pv[o.sets] = 1; o.notes.forEach((nt, i) => { beep(TONES[nt], .4, 'sine', .14, i * .5); VW_.flash[o.bells[nt] + '_' + i] = performance.now() / 1000 + i * .5; }); }
  else if (o.kind === 'press') {
    const key = R.name + '_p', prog = STATE.pv[key] || 0;
    if (v.gate && !STATE.pv[v.gate]) { beep(90, .1, 'square', .08); return; }
    if (v.seq.slice(0, prog).includes(o.id) && o.look !== 'bell') return;
    if (o.tone !== undefined) beep(TONES[o.tone], .45, 'sine', .14); VW_.flash[o.id + '_x'] = performance.now() / 1000;
    if (v.seq[prog] === o.id) { STATE.pv[key] = prog + 1; if (o.tone === undefined) beep(200, .12, 'triangle', .1); checkView(); }
    else { STATE.pv[key] = 0; if (o.tone === undefined) { beep(110, .25, 'sawtooth', .08); } else beep(98, .3, 'sawtooth', .06, .3); }
  }
  else if (o.kind === 'knock') { VW_.kn.push(performance.now() / 1000); beep(150, .08, 'square', .14); VW_.flash[o.id + '_x'] = performance.now() / 1000; }
}
function viewTick(dt) {
  const v = curView(); if (VW_.look) { VW_.look.t -= dt; if (VW_.look.t <= 0) VW_.look = null; }
  if (!v) return; const now = performance.now() / 1000;
  if (v.knock && VW_.kn.length && now - VW_.kn[VW_.kn.length - 1] > 1.1) {                       // 두드림이 멎으면 박자를 읽는다(간격이 벌어지면 다음 묶음)
    const g = [1]; for (let i = 1; i < VW_.kn.length; i++) { if (VW_.kn[i] - VW_.kn[i - 1] > .55) g.push(1); else g[g.length - 1]++; }
    VW_.kn = []; if (g.length === v.knock.length && g.every((n, i) => n === v.knock[i])) { STATE.pv[R.name + '_k'] = 1; checkView(); } else beep(98, .3, 'sawtooth', .06);
  }
  if (v.knock && !STATE.pv[R.name + '_k']) { VW_.hintT -= dt; if (VW_.hintT <= 0) { VW_.hintT = 4.2; let tt = 0; v.knock.forEach((n, gi) => { for (let i = 0; i < n; i++) { VW_.flash['hint_' + gi + '_' + i] = now + tt; beep(110, .07, 'square', .05, tt); tt += .28; } tt += .5; }); } }
  if (VW_.t > 0) { VW_.t -= dt; if (VW_.t <= 0 && !fadeDir) {                                    // 풀렸다: 품을 것을 품고, 방이 다음 시선으로 넘어간다
    VW_.t = 0; FP = null; if (v.give) STATE.bag.push(v.give); STATE.vi[R.name] = (STATE.vi[R.name] || 0) + 1; delete STATE.pv[R.name + '_p']; delete STATE.pv[R.name + '_k']; VW_.kn = []; VW_.hintT = .8;
    if (STATE.vi[R.name] >= R.views.length) STATE.flags[R.vflag] = true; P.path = []; P.act = null; pending = { to: room, spawn: [P.x, P.d] }; fadeDir = 1; } }
}
const flashed = (k, dur = .35) => { const t = VW_.flash[k]; if (t === undefined) return false; const n = performance.now() / 1000; return n >= t && n < t + dur; };
function line3(a, b, col, w = 1, al = 1) { const [ax, ay] = scr(a[0], a[1]), [bx, by] = scr(b[0], b[1]); ctx.save(); ctx.globalAlpha = al; ctx.strokeStyle = col; ctx.lineWidth = w * S; ctx.beginPath(); ctx.moveTo((R.ox + ax) * S, (R.oy + ay - (a[2] || 0)) * S); ctx.lineTo((R.ox + bx) * S, (R.oy + by - (b[2] || 0)) * S); ctx.stroke(); ctx.restore(); }
function drawViewBack() {
  const v = curView(); if (!v) return; const now = performance.now() / 1000, ob = (id) => v.objects.find(o => o.id === id), at = (o) => [o.x, o.d, (o.z || 0) + 3];
  if (v.mode === 'adult') { ctx.fillStyle = 'rgba(255,214,160,.13)'; ctx.fillRect(0, 0, VW, VH); }                       // 바깥의 눈: 같은 방이 따뜻하고 평범하게 보인다
  if (v.box) { const [X, Y] = scr((v.box[0] + v.box[1]) / 2, v.box[2]); ctx.fillStyle = '#5a3c28'; ctx.fillRect((R.ox + X - 11) * S, (R.oy + Y - v.box[3] - 9) * S, 22 * S, 9 * S); ctx.fillStyle = '#7a5438'; ctx.fillRect((R.ox + X - 11) * S, (R.oy + Y - v.box[3] - 10) * S, 22 * S, 2 * S); }
  if (v.tray) { const [X, Y] = scr((v.tray[0] + v.tray[1]) / 2, (v.tray[2] + v.tray[3]) / 2); ctx.fillStyle = '#8a6a48'; ctx.beginPath(); ctx.ellipse((R.ox + X) * S, (R.oy + Y - 2) * S, 12 * S, 6 * S, 0, 0, 6.3); ctx.fill(); ctx.fillStyle = '#a88660'; ctx.beginPath(); ctx.ellipse((R.ox + X) * S, (R.oy + Y - 3) * S, 11 * S, 5 * S, 0, 0, 6.3); ctx.fill(); }
  if (v.trail) for (const [i, p] of v.trail.entries()) { const [X, Y] = scr(p[0], p[1]); ctx.fillStyle = 'rgba(40,30,30,.55)'; ctx.fillRect((R.ox + X + (i % 2 ? 1 : -1)) * S, (R.oy + Y) * S, 2 * S, S); }
  if (v.kid && (!v.seq || v.mode !== 'adult' || (STATE.pv[R.name + '_p'] || 0) >= 2 || !v.trail)) { const im = frames.d_idle; if (im) { const [X, Y] = scr(v.kid[0], v.kid[1]), [w, h] = G.childSize; ctx.save(); ctx.globalAlpha = .9; ctx.drawImage(im, (R.ox + X - w / 2) * S, (R.oy + Y - h * .72) * S, w * S, h * .72 * S); ctx.restore(); } }   // 웅크린 아이
  if (v.beam) { const b = v.beam, col = 'rgba(255,240,190,.85)';
    if (b.kind === 'cut') { for (const id of b.via) { const o = ob(id); if (pv(o) !== o.want) line3(at(o), b.to, col, 1.5, .8); } }
    else if (b.kind === 'block') { const ok = b.via.every(id => pv(ob(id)) === ob(id).want) && pv(ob(b.trap)) === ob(b.trap).want, mid = [(b.frm[0] + b.to[0]) / 2, (b.frm[1] + b.to[1]) / 2, (b.frm[2] + b.to[2]) / 2]; line3(b.frm, ok ? mid : b.to, col, 3, ok ? .5 : .75); if (!ok) { const [X, Y] = scr(b.to[0], b.to[1]); ctx.fillStyle = 'rgba(255,240,190,.3)'; ctx.beginPath(); ctx.ellipse((R.ox + X) * S, (R.oy + Y) * S, 9 * S, 4 * S, 0, 0, 6.3); ctx.fill(); } }
    else { let p = b.frm, alive = true; for (const id of b.via) { const o = ob(id); line3(p, at(o), col, 1.5, .85); p = at(o); if (pv(o) !== o.want) { alive = false; const dir = pv(o) === 0 ? null : [p[0] + (pv(o) === 1 ? 30 : -6), p[1] + (pv(o) === 1 ? -22 : 26), 2]; if (dir) line3(p, dir, col, 1.5, .45); break; } } if (alive) line3(p, b.to, col, 1.5, .9); } }
  if (v.shadows) { const L = ob(v.shadows.lamp), n = pv(L) === L.want ? 0 : 3 - pv(L); v.shadows.at.slice(0, n).forEach(([x, d], i) => { const [X, Y] = scr(x, d); ctx.fillStyle = 'rgba(8,4,12,.8)'; ctx.fillRect((R.ox + X - 2) * S, (R.oy + Y - 22 - i * 3 + Math.sin(now * 2 + i) * 1) * S, 4 * S, (22 + i * 3) * S); ctx.fillRect((R.ox + X - 3) * S, (R.oy + Y - 27 - i * 3) * S, 6 * S, 6 * S); }); }
  if (v.wave) { const a = ob(v.wave.ids[0]), b2 = ob(v.wave.ids[1]), df = pv(a) - a.want, dv = pv(b2) - b2.want, [X, Y] = scr(v.wave.at[0], v.wave.at[1]), cy = (R.oy + Y - v.wave.at[2]) * S, cx = (R.ox + X - 14) * S; ctx.fillStyle = 'rgba(10,10,16,.7)'; ctx.fillRect(cx - 2 * S, cy - 8 * S, 32 * S, 16 * S);
    for (const [k, c] of [[0, '#7fd0a0'], [1, '#f0e0a0']]) { ctx.strokeStyle = c; ctx.lineWidth = S; ctx.beginPath(); for (let i = 0; i <= 28; i++) { const y = k ? Math.sin(i * (.5 + df * .14) + now * 4) * (4 + dv * 1.2) + (df || dv ? Math.sin(i * 2.3 + now * 9) * 1.2 : 0) : Math.sin(i * .5 + now * 4) * 4; ctx.lineTo(cx + i * S, cy + y * S); } ctx.stroke(); } }
  if (v.knock) { const [X, Y] = scr(45, 0); let k = 0; v.knock.forEach((n, gi) => { for (let i = 0; i < n; i++) { ctx.fillStyle = flashed('hint_' + gi + '_' + i, .2) ? '#ffe9b0' : 'rgba(255,233,176,.18)'; ctx.fillRect((R.ox + X - 14 + k * 5) * S, (R.oy + Y - 34) * S, 3 * S, 3 * S); k++; } k++; }); }
  if (v.stack) { const done = v.seq.slice(0, STATE.pv[R.name + '_p'] || 0); done.forEach((id, i) => { const o = ob(id), [X, Y] = scr(v.stack[0], v.stack[1]); chairAt((R.ox + X) * S, (R.oy + Y - i * 9) * S, o.size); }); }
}
function chairAt(cx, cy, size) { const w = 5 + size * 2; ctx.fillStyle = '#6a4a34'; ctx.fillRect(cx - w * S, cy - 7 * S, w * 2 * S, 2 * S); ctx.fillRect(cx - w * S, cy - 7 * S, S, 7 * S); ctx.fillRect(cx + (w - 1) * S, cy - 7 * S, S, 7 * S); ctx.fillStyle = '#8a6444'; ctx.fillRect(cx - w * S, cy - (14 + size) * S, 2 * S, (8 + size) * S); ctx.fillRect(cx - w * S, cy - (14 + size) * S, w * 2 * S, 2 * S); }
function clockFace(cx, cy, r, time, tick) { const now = performance.now() / 1000, h = time[0] + time[1] / 60, ha = h / 12 * 6.283 - 1.571, ma = (tick ? (time[1] + now * 2) : time[1]) / 60 * 6.283 - 1.571; ctx.fillStyle = '#3a2c24'; ctx.beginPath(); ctx.arc(cx, cy, r + 1.2 * S, 0, 6.3); ctx.fill(); ctx.fillStyle = '#e8dcc0'; ctx.beginPath(); ctx.arc(cx, cy, r, 0, 6.3); ctx.fill(); ctx.fillStyle = '#fff8e0'; ctx.beginPath(); ctx.arc(cx - r * .3, cy - r * .35, r * .32, 0, 6.3); ctx.fill(); ctx.fillStyle = '#c8a478'; ctx.beginPath(); ctx.arc(cx + r * .35, cy + r * .4, r * .3, 0, 6.3); ctx.fill(); ctx.fillStyle = '#e8dcc0'; ctx.beginPath(); ctx.arc(cx, cy, r * .78, 0, 6.3); ctx.fill(); ctx.strokeStyle = '#2a2024'; ctx.lineWidth = Math.max(1, r / 9);
  if (r > 20) for (let i = 0; i < 12; i++) { const a = i / 12 * 6.283; ctx.beginPath(); ctx.moveTo(cx + Math.cos(a) * r * .86, cy + Math.sin(a) * r * .86); ctx.lineTo(cx + Math.cos(a) * r * .96, cy + Math.sin(a) * r * .96); ctx.stroke(); }
  ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(cx + Math.cos(ha) * r * .5, cy + Math.sin(ha) * r * .5); ctx.stroke(); ctx.lineWidth = Math.max(1, r / 14); ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(cx + Math.cos(ma) * r * .8, cy + Math.sin(ma) * r * .8); ctx.stroke(); }
const SHAPES = { battery: [[2, 3], [3, 6], [5, 8], [6, 4]], piece: [[6, 3], [2, 7], [4, 4]], cup: [[3, 3], [4, 5], [6, 7]] };
const DIG = ['111101101101111', '010110010010111', '111001111100111', '111001111001111', '101101111001001', '111100111001111', '111100111101111', '111001001001001', '111101111101111', '111101111001111'];
function drawObj(o, fp) {
  const v = curView(); if (!v) return;
  const [X, Y0] = scr(o.x, o.d), cx = (R.ox + X) * S, cy = (R.oy + Y0 - (o.z || 0)) * S, val = pv(o), now = performance.now() / 1000, rect = (x, y, w, h, c) => { ctx.fillStyle = c; ctx.fillRect(cx + x * S, cy + y * S, w * S, h * S); };
  if (o.look === 'clock') clockFace(cx, cy - 4 * S, 4 * S, o.time, o.tick);
  else if (o.look === 'num') { rect(-3, -8, 6, 8, '#2a2024'); rect(-2, -7, 4, 6, '#e8dcc0'); rect(-3, -8, 6, 1, '#c8a040'); const g = DIG[val] || DIG[0]; ctx.fillStyle = '#2a2024'; for (let yy = 0; yy < 5; yy++) for (let xx = 0; xx < 3; xx++) if (g[yy * 3 + xx] === '1') ctx.fillRect(cx + (-1.5 + xx) * S, cy + (-6.6 + yy * .9) * S, S, .9 * S + 1); }
  else if (o.look === 'knob') { ctx.fillStyle = '#c8b88a'; ctx.beginPath(); ctx.arc(cx, cy - 3 * S, 2.6 * S, 0, 6.3); ctx.fill(); const a = val / o.n * 6.283 - 1.571; ctx.strokeStyle = '#2a2024'; ctx.lineWidth = S; ctx.beginPath(); ctx.moveTo(cx, cy - 3 * S); ctx.lineTo(cx + Math.cos(a) * 2.6 * S, cy - 3 * S + Math.sin(a) * 2.6 * S); ctx.stroke(); }
  else if (o.look === 'radio') { rect(-8, -11, 16, 11, '#5a4030'); rect(-7, -10, 8, 6, '#2a2024'); rect(2, -9, 4, 1, '#c8b88a'); rect(3, -17, 1, 6, '#888'); if (o.kind === 'play' && Math.sin(now * 5) > .6) rect(7, -14, 1, 1, '#fff'); }
  else if (o.look === 'lamp') { const p = o.pos[val], [lx, ly] = scr(p[0], p[1]), px = (R.ox + lx) * S, py = (R.oy + ly) * S; for (const q of o.pos) { const [qx, qy] = scr(q[0], q[1]); ctx.fillStyle = '#6a5a4a'; ctx.fillRect((R.ox + qx - 1) * S, (R.oy + qy - 1) * S, 2 * S, S); }
    const g = ctx.createRadialGradient(px, py - 8 * S, 2, px, py - 4 * S, 30 * S); g.addColorStop(0, 'rgba(255,226,150,.5)'); g.addColorStop(1, 'rgba(255,226,150,0)'); ctx.fillStyle = g; ctx.fillRect(px - 34 * S, py - 34 * S, 68 * S, 60 * S); ctx.fillStyle = '#6a5430'; ctx.fillRect(px - S, py - 12 * S, 2 * S, 12 * S); ctx.fillStyle = '#ffe6a0'; ctx.fillRect(px - 2 * S, py - 16 * S, 4 * S, 4 * S); }
  else if (o.look === 'crate') { const gone = o.kind === 'press' && v.seq && v.seq.slice(0, STATE.pv[R.name + '_p'] || 0).includes(o.id); let dx = 0, dy = 0; if (o.kind === 'toggle' && val) { const [sx2, sy2] = scr(o.x + o.shift[0], o.d + o.shift[1]); dx = sx2 - X; dy = sy2 - Y0; } if (gone) { dx = 9; dy = 3; } const sh = flashed(o.id + '_x', .2) ? 1 : 0;
    rect(-6 + dx + sh, -11 + dy, 12, 11, '#7a5a3c'); rect(-6 + dx + sh, -12 + dy, 12, 2, '#9a7650'); rect(-6 + dx + sh, -6 + dy, 12, 1, '#5a4028'); rect(5 + dx + sh, -11 + dy, 1, 11, '#5a4028'); }
  else if (o.look === 'frame' || o.look === 'frame3') { const up = o.look === 'frame' ? val === 0 : val > 0; if (up) { rect(-4, -9, 8, 9, '#8a6a40'); rect(-3, -8, 6, 7, '#d8d0c0'); rect(-1, -6, 2, 2, '#b0a898'); rect(-2, -4, 4, 3, '#b0a898'); if (o.look === 'frame3') rect(val === 1 ? 2 : -3, -8, 1, 7, '#fff'); } else { rect(-5, -2, 10, 2, '#6a4e30'); rect(-4, -3, 8, 1, '#8a6a40'); } }
  else if (o.kind === 'slot') { const sh = SHAPES[o.look], w = sh[o.want], lab = o.look === 'cup' ? 'ring' : 'out';
    if (lab === 'ring') { ctx.strokeStyle = 'rgba(60,40,30,.7)'; ctx.lineWidth = S; ctx.beginPath(); ctx.ellipse(cx, cy, (w[0] / 2 + 1) * S, (w[0] / 4 + .6) * S, 0, 0, 6.3); ctx.stroke(); } else { ctx.strokeStyle = 'rgba(30,20,20,.8)'; ctx.lineWidth = S; ctx.strokeRect(cx - (w[0] / 2 + 1) * S, cy - (w[1] + 1) * S, (w[0] + 2) * S, (w[1] + 1) * S); }
    if (val >= 0) { const q = sh[val], c = o.look === 'battery' ? '#c8a040' : o.look === 'cup' ? '#e8e0d0' : ['#e8e0d0', '#b8b8c0', '#d0c8b0'][val]; rect(-q[0] / 2, -q[1], q[0], q[1], c); rect(-q[0] / 2, -q[1], q[0], 1, '#fff8'); if (o.look === 'battery') rect(-1, -q[1] - 1, 2, 1, '#888'); } }
  else if (o.look === 'bell') { const sw = (flashed(o.id + '_x', .5) || [0, 1, 2, 3].some(i => flashed(o.id + '_' + i, .4))) ? Math.sin(now * 40) * 2 : 0, z = o.size; ctx.fillStyle = '#4a3a2a'; ctx.fillRect(cx - S * .5, cy - (z + 8) * S, S, 8 * S); rect(-z + sw, -z, z * 2, z, sw ? '#ffe9a0' : '#c8a850'); rect(-z + 1 + sw, -z - 2, z * 2 - 2, 2, sw ? '#fff4c8' : '#d8b860'); rect(-1 + sw * 1.4, 0, 2, 2, '#6a5430'); }
  else if (o.look === 'chair') { if (v.seq.slice(0, STATE.pv[R.name + '_p'] || 0).includes(o.id)) return; chairAt(cx + (flashed(o.id + '_x', .2) ? S : 0), cy, o.size); }
  else if (o.look === 'door') { if (flashed(o.id + '_x', .12)) { ctx.fillStyle = 'rgba(255,240,200,.25)'; ctx.fillRect(cx - 9 * S, cy - 4 * S, 18 * S, 8 * S); } }
}
// ---------- 1인칭 클로즈업(§31.1): 퍼즐을 정면(또는 위에서)으로 크게 본다. 글 없음 ----------
let FP = null;
const FPL = { row: null };
function fpLayout(v) {                                                          // 사물 id -> 화면 위치와 배율(320x240 기준, 발 밑이 기준점)
  const m = {}, objs = v.objects, put = (o, x, y, k) => { m[o.id] = { x, y, k }; };
  const spread = (arr, y, k, x0 = 36, x1 = 284) => arr.forEach((o, i) => put(o, arr.length === 1 ? 160 : x0 + (x1 - x0) * i / (arr.length - 1), y, k));
  const top = objs.filter(o => ['clock', 'bell'].includes(o.look)), bot = objs.filter(o => !top.includes(o) && o.reach !== 0), dec = objs.filter(o => o.reach === 0);
  const kb = top.length >= 4 ? 3.1 : 3.4, small = bot.some(o => ['cup', 'piece', 'chair'].includes(o.look));
  spread(top, 96, kb, top.length >= 4 ? 52 : 60, top.length >= 4 ? 268 : 260);
  spread(bot, top.length ? 190 : (small ? 160 : 150), bot.some(o => o.look === 'num') ? 4.5 : bot.some(o => o.look === 'knob') ? 4.5 : bot.some(o => o.look === 'chair') ? 2.6 : bot.some(o => o.look === 'cup' || o.look === 'piece') ? 3.6 : bot.some(o => o.look === 'radio') ? 3.5 : bot.some(o => o.look === 'lamp') ? 5 : 5, small ? 70 : 36, small ? 250 : 284);
  dec.forEach(o => put(o, 160, 150, 3.4));
  if (objs.some(o => o.id === 'tm_b')) { const b = objs.find(o => o.id === 'tm_b'), k = objs.find(o => o.id === 'tm_k'); if (b) put(b, 160, 195, 5); if (k) put(k, 160, 105, 4); }
  return m;
}
function planMap(v) {                                                           // 방 바닥 좌표 -> 위에서 본 화면 좌표
  const x0 = 24, y0 = 26, w = 272, h = 170; return (x, d) => [x0 + x / R.W * w, y0 + (1 - d / R.D) * h];
}
function enterFP(o) {
  const v = curView(); if (!v || FP) return; const plan = !!(v.beam || v.trail);
  FP = { a: 0, mode: plan ? 'plan' : 'row', lay: plan ? null : fpLayout(v), from: o.id, flash: 0 }; P.path = []; P.act = null; marker = null; audio();
}
function leaveFP() { FP = null; }
function fpHits(v) {
  const hits = [];
  if (FP.mode === 'plan') { const mp = planMap(v); for (const o of v.objects) { const [px, py] = mp(o.x, o.d); hits.push({ o, x: px - 14, y: py - 14, w: 28, h: 28 }); } }
  else for (const o of v.objects) { const l = FP.lay[o.id]; if (!l || o.reach === 0) continue; const k = l.k; hits.push({ o, x: l.x - 10 * k, y: l.y - 18 * k, w: 20 * k, h: 20 * k }); }
  return hits;
}
function fpPress(x, y) {
  const v = curView(); if (!v || !FP) return;
  if (y > 210 && Math.abs(x - 160) < 26) { leaveFP(); return; }                                // 나가기: 아래 화살표
  if (VW_.t > 0) return;
  for (const h of fpHits(v).reverse()) if (x >= h.x && x <= h.x + h.w && y >= h.y && y <= h.y + h.h) { FP.flash = .15; actObj(h.o); return; }
}
const PAL16 = ['#07060b', '#0e0c14', '#14121c', '#1a1824', '#242034', '#34304a', '#4a4460', '#2a1810', '#3a2418', '#4e3222', '#6a4630', '#8a6244', '#a8825a', '#c8a478', '#1c2420', '#2c3a34', '#42564a', '#5c7260', '#4a4a52', '#6c6c78', '#9a9aa8', '#c4c4d0', '#e8dcc0', '#fff8e0', '#c8a040', '#ffe070', '#a03a3a', '#e05a50', '#5a8a6a', '#7fd0a0', '#f0d4b0', '#2c3c4c'];
const PALRGB = PAL16.map(h => [parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)]);
const fpO = document.createElement('canvas'); fpO.width = 160; fpO.height = 120; const fpOX = fpO.getContext('2d', { willReadFrequently: true });
function layer(on) { if (on) { fpOX.setTransform(.5, 0, 0, .5, 0, 0); fpOX.imageSmoothingEnabled = false; ctx = fpOX; } else ctx = fpX; }
const BAYER = [0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5];
function ditherRect(x, y, w, h, c1, c2, lv) {                                    // 16비트식 디더: 4x4 오더드 행렬로 두 색을 섞는다(좌표는 320x240 기준, 도트 2칸 단위)
  for (let j = 0; j < h; j += 2) for (let i = 0; i < w; i += 2) { const th = BAYER[(((y + j) / 2 | 0) & 3) * 4 + (((x + i) / 2 | 0) & 3)]; ctx.fillStyle = th < lv ? c2 : c1; ctx.fillRect(x + i, y + j, 2, 2); }
}
function fpBackdrop(v) {
  const adult = v.mode === 'adult', k = Math.min(1, FP.a * 1.4); ctx.save(); ctx.globalAlpha = k;
  const wall = adult ? ['#4e3222', '#3a2418', '#2a1810'] : ['#1a1824', '#14121c', '#0e0c14'], fl = adult ? ['#8a6244', '#6a4630', '#4e3222'] : ['#34304a', '#242034', '#1a1824'], hi = adult ? '#a8825a' : '#4a4460';
  if (FP.mode === 'row') {
    for (let i = 0; i < 3; i++) { ctx.fillStyle = wall[i]; ctx.fillRect(0, i * 50, VW, 50); if (i < 2) ditherRect(0, i * 50 + 38, VW, 12, wall[i], wall[i + 1], 8); }
    for (let x = 0; x < VW; x += 32) { ctx.fillStyle = wall[1]; ctx.fillRect(x, 0, 2, 150); ctx.fillStyle = wall[0]; ctx.fillRect(x + 2, 0, 2, 150); }           // 벽 널 줄무늬
    ctx.fillStyle = fl[0]; ctx.fillRect(0, 150, VW, 90); ctx.fillStyle = hi; ctx.fillRect(0, 148, VW, 2); ctx.fillStyle = wall[2]; ctx.fillRect(0, 150, VW, 6);
    for (let y = 164; y < VH; y += 20) { ctx.fillStyle = fl[1]; ctx.fillRect(0, y, VW, 2); for (let x = ((y / 20 | 0) % 2) * 40; x < VW; x += 80) ctx.fillRect(x, y, 2, 20); }   // 바닥 널 이음
    ditherRect(0, 156, VW, 84, fl[0], fl[2], 5);
  } else {
    ctx.fillStyle = adult ? '#2a1810' : '#0e0c14'; ctx.fillRect(0, 0, VW, VH); ctx.fillStyle = fl[1]; ctx.fillRect(18, 20, 284, 182);
    for (let y = 20; y < 202; y += 22) { ctx.fillStyle = fl[2]; ctx.fillRect(18, y, 284, 2); for (let x = 18 + ((y / 22 | 0) % 2) * 50; x < 302; x += 100) ctx.fillRect(x, y, 2, 22); }
    ctx.fillStyle = hi; ctx.fillRect(16, 18, 288, 2); ctx.fillRect(16, 18, 2, 186); ctx.fillStyle = wall[2]; ctx.fillRect(16, 202, 288, 4); ctx.fillRect(302, 18, 4, 188); ditherRect(18, 150, 284, 52, fl[1], fl[2], 6);
  }
  ctx.restore();
}
function drawFP() {                                                             // 16비트 마감: 배경과 사물을 따로 그리고, 사물에 외곽선을 두른 뒤, 고정 32색 팔레트로 치환해 2배로 키운다
  const real = ctx; ctx = fpX; fpX.setTransform(.5, 0, 0, .5, 0, 0); fpX.imageSmoothingEnabled = false; fpX.clearRect(0, 0, VW, VH); fpOX.setTransform(1, 0, 0, 1, 0, 0); fpOX.clearRect(0, 0, 160, 120);
  try { drawFPInner(); } finally { ctx = real; }
  const od = fpOX.getImageData(0, 0, 160, 120), o = od.data, solid = (x, y) => x >= 0 && y >= 0 && x < 160 && y < 120 && o[(y * 160 + x) * 4 + 3] > 120, ol = (FP.flash || 0) > 0 ? [255, 248, 224] : [10, 8, 18], out = new Uint8ClampedArray(o);
  for (let y = 0; y < 120; y++) for (let x = 0; x < 160; x++) { const i = (y * 160 + x) * 4; if (o[i + 3] > 120) { out[i + 3] = 255; continue; } if (solid(x - 1, y) || solid(x + 1, y) || solid(x, y - 1) || solid(x, y + 1)) { out[i] = ol[0]; out[i + 1] = ol[1]; out[i + 2] = ol[2]; out[i + 3] = 255; } else out[i + 3] = 0; }
  fpOX.putImageData(new ImageData(out, 160, 120), 0, 0); fpX.setTransform(1, 0, 0, 1, 0, 0); fpX.drawImage(fpO, 0, 0);
  const id = fpX.getImageData(0, 0, 160, 120), d = id.data; for (let i = 0; i < d.length; i += 4) { let bi = 0, bd = 1e9; for (let k = 0; k < PALRGB.length; k++) { const q = PALRGB[k], dr = d[i] - q[0], dg = d[i + 1] - q[1], db = d[i + 2] - q[2], dd = dr * dr * .9 + dg * dg * 1.2 + db * db * .8; if (dd < bd) { bd = dd; bi = k; } } const c = PALRGB[bi]; d[i] = c[0]; d[i + 1] = c[1]; d[i + 2] = c[2]; d[i + 3] = 255; }
  fpX.putImageData(id, 0, 0); real.imageSmoothingEnabled = false; real.drawImage(fpC, 0, 0, VW, VH);
}
function drawFPInner() {
  const v = curView(); if (!v) return; fpBackdrop(v); const adult = v.mode === 'adult', now = performance.now() / 1000, ob = (id) => v.objects.find(o => o.id === id); ctx.save(); ctx.globalAlpha = Math.min(1, FP.a * 1.4);
  if (FP.mode === 'row') {
    if (v.tray) { ctx.fillStyle = '#8a6a48'; ctx.beginPath(); ctx.ellipse(160, 170, 120, 30, 0, 0, 6.3); ctx.fill(); ctx.fillStyle = '#a88660'; ctx.beginPath(); ctx.ellipse(160, 166, 112, 26, 0, 0, 6.3); ctx.fill(); }
    if (v.wave) { const a = ob(v.wave.ids[0]), b2 = ob(v.wave.ids[1]), df = pv(a) - a.want, dv = pv(b2) - b2.want; ctx.fillStyle = '#0a0a10'; ctx.fillRect(80, 14, 160, 62); for (const [k, c] of [[0, '#7fd0a0'], [1, '#f0e0a0']]) { ctx.strokeStyle = c; ctx.lineWidth = 2; ctx.beginPath(); for (let i = 0; i <= 90; i++) { const y = k ? Math.sin(i * (.22 + df * .06) + now * 4) * (12 + dv * 3) + ((df || dv) ? Math.sin(i * 1.1 + now * 9) * 3 : 0) : Math.sin(i * .22 + now * 4) * 12; ctx.lineTo(86 + i * 1.6, 45 + y * .8); } ctx.stroke(); } }
    if (v.shadows) { const L = ob(v.shadows.lamp), n = pv(L) === L.want ? 0 : 3 - pv(L); ctx.fillStyle = '#07040b'; ctx.fillRect(110, 40, 100, 110); ctx.fillStyle = '#1a1210'; ctx.fillRect(150, 40, 3, 110); for (let i = 0; i < n; i++) { const x = 118 + i * 34; ctx.fillStyle = 'rgba(0,0,0,.9)'; ctx.fillRect(x, 70 + i * 4, 14, 80 - i * 4); ctx.beginPath(); ctx.arc(x + 7, 64 + i * 4, 9, 0, 6.3); ctx.fill(); } }
    if (v.stack) { const done = v.seq.slice(0, STATE.pv[R.name + '_p'] || 0); ctx.fillStyle = 'rgba(0,0,0,.25)'; ctx.fillRect(100, 60, 120, 90); done.forEach((id, i) => chairAt(160, 146 - i * 22, ob(id).size)); }
    if (v.knock) { const dr = ob('of_k'); ctx.fillStyle = '#5a3a28'; ctx.fillRect(100, 30, 120, 150); ctx.fillStyle = '#6e4a34'; ctx.fillRect(108, 38, 104, 134); ctx.fillStyle = '#e0b860'; ctx.fillRect(196, 106, 8, 8); if (flashed('of_k_x', .15)) { ctx.fillStyle = 'rgba(255,240,200,.3)'; ctx.fillRect(100, 30, 120, 150); }
      let kk = 0; v.knock.forEach((n, gi) => { for (let i = 0; i < n; i++) { ctx.fillStyle = flashed('hint_' + gi + '_' + i, .2) ? '#ffe9b0' : 'rgba(255,233,176,.2)'; ctx.fillRect(112 + kk * 14, 16, 8, 8); kk++; } kk++; }); }
    layer(true); for (const o of v.objects) { const l = FP.lay[o.id]; if (!l || o.look === 'door') continue; if (o.look === 'lamp') { const px = [70, 160, 250][pv(o)]; for (const q of [70, 160, 250]) { ctx.fillStyle = '#4a3c30'; ctx.fillRect(q - 14, 182, 28, 4); } for (const [rx, ry, al] of [[96, 70, .05], [72, 54, .06], [50, 38, .07], [30, 24, .09]]) { ctx.fillStyle = `rgba(255,226,150,${al})`; ctx.beginPath(); ctx.ellipse(px, 150, rx, ry, 0, 0, 6.3); ctx.fill(); } ctx.fillStyle = '#6a5430'; ctx.fillRect(px - 3, 150, 6, 32); ctx.fillStyle = '#ffe6a0'; ctx.fillRect(px - 9, 134, 18, 16); continue; } ctx.save(); ctx.translate(l.x, l.y); ctx.scale(l.k, l.k); const [X, Y0] = scr(o.x, o.d); ctx.translate(-(R.ox + X) * S, -(R.oy + Y0 - (o.z || 0)) * S); drawObj(o, true); ctx.restore(); }
    layer(false);
  } else {
    const mp = planMap(v), at = (id) => { const o = ob(id); return mp(o.x, o.d); }, col = 'rgba(255,240,190,.9)'; const ln = (a, b, w = 3, al = 1) => { ctx.save(); ctx.globalAlpha *= al; ctx.strokeStyle = col; ctx.lineWidth = w; ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); ctx.stroke(); ctx.restore(); };
    if (v.trail) for (const [i, pt] of v.trail.entries()) { const [px, py] = mp(pt[0], pt[1]); ctx.fillStyle = 'rgba(20,12,10,.6)'; ctx.fillRect(px + (i % 2 ? 2 : -2), py, 4, 3); }
    if (v.beam) { const b = v.beam, F = mp(b.frm ? b.frm[0] : v.kid[0], b.frm ? b.frm[1] : v.kid[1]), T = mp(b.to[0], b.to[1]);
      if (b.kind === 'cut') { for (const id of b.via) { const o = ob(id); if (pv(o) !== o.want) ln(at(id), T, 3, .85); } }
      else if (b.kind === 'block') { const ok = b.via.every(id => pv(ob(id)) === ob(id).want) && pv(ob(b.trap)) === ob(b.trap).want; ln(F, ok ? [(F[0] + T[0]) / 2, (F[1] + T[1]) / 2] : T, 8, .6); }
      else { let p = F, alive = true; for (const id of b.via) { const q = at(id); ln(p, q, 3); p = q; if (pv(ob(id)) !== ob(id).want) { alive = false; break; } } if (alive) ln(p, T, 3); }
      ctx.fillStyle = col; ctx.fillRect(F[0] - 5, F[1] - 5, 10, 10); ctx.strokeStyle = '#e8d8b0'; ctx.strokeRect(T[0] - 6, T[1] - 8, 12, 16); }
    if (v.kid) { const [kx, ky] = mp(v.kid[0], v.kid[1]); ctx.fillStyle = '#f0d4b0'; ctx.beginPath(); ctx.arc(kx, ky, 6, 0, 6.3); ctx.fill(); ctx.fillStyle = '#2c4a3a'; ctx.fillRect(kx - 5, ky + 4, 10, 6); }
    layer(true); for (const o of v.objects) { const [px, py] = mp(o.x, o.d), val = pv(o);
      if (o.look === 'crate') { let dx = 0, dy = 0; const gone = o.kind === 'press' && v.seq.slice(0, STATE.pv[R.name + '_p'] || 0).includes(o.id); if (o.kind === 'toggle' && val) { dx = o.shift[0] / R.W * 272; dy = -o.shift[1] / R.D * 170; } if (gone) { dx = 22; dy = 8; } ctx.fillStyle = '#7a5a3c'; ctx.fillRect(px - 13 + dx, py - 13 + dy, 26, 26); ctx.fillStyle = '#9a7650'; ctx.fillRect(px - 13 + dx, py - 13 + dy, 26, 5); ctx.fillStyle = '#5a4028'; ctx.fillRect(px - 13 + dx, py + dy, 26, 2); }
      else { const up = o.look === 'frame' ? val === 0 : val > 0; ctx.save(); ctx.translate(px, py); if (up) { ctx.rotate(o.look === 'frame3' ? (val === 1 ? .9 : -.9) : 0); ctx.fillStyle = '#8a6a40'; ctx.fillRect(-12, -3, 24, 7); ctx.fillStyle = '#d8d0c0'; ctx.fillRect(-10, -2, 20, 5); } else { ctx.fillStyle = '#6a4e30'; ctx.fillRect(-12, 0, 24, 5); ctx.fillStyle = '#8a6a40'; ctx.fillRect(-11, -2, 22, 3); } ctx.restore(); } }
  }
  layer(false); ctx.restore();
  ctx.fillStyle = '#b8b0c0'; for (let i = 0; i < 5; i++) ctx.fillRect(150 + i * 2, 222 + i * 2, 20 - i * 4, 2);                  // 나가기 화살표(글 없음)
}
function drawViewHud() {
  STATE.bag.forEach((b, i) => { const q = SHAPES.cup[{ cup_s: 0, cup_m: 1, cup_l: 2 }[b]]; ctx.fillStyle = '#0008'; ctx.fillRect(VW - 16 - i * 14, 26, 12, 14); ctx.fillStyle = '#e8e0d0'; ctx.fillRect(VW - 10 - i * 14 - q[0], 38 - q[1] * 1.4, q[0] * 2, q[1] * 1.4); });
  if (VW_.look) { const o = VW_.look.o, a = Math.min(1, VW_.look.t * 3, (1.7 - VW_.look.t) * 6); ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = 'rgba(8,6,12,.72)'; ctx.fillRect(0, 0, VW, VH); if (o.look === 'clock') clockFace(VW / 2, VH / 2, 56, o.time, o.tick); ctx.restore(); }
}
function cellsOf(r, c) { const a = []; for (let j = 0; j < r.gh; j++) for (let i = 0; i < r.gw; i++) { const x = (i + .5) * CELL, d = (j + .5) * CELL; if (((x - c.x) / c.rx) ** 2 + ((d - c.d) / c.rd) ** 2 < 1) a.push(j * r.gw + i); } return a; }
const inCrack = (c, x, d, pad = 0) => ((x - c.x) / (c.rx + pad)) ** 2 + ((d - c.d) / (c.rd + pad)) ** 2 < 1;
function restoreCracks() { for (const c of R.cr) { if (c.st === 'broken') for (const k of c.cells) if (R.free0[k]) R.free[k] = 1; c.st = 'ok'; c.t = 0; } }
function respawn() { P.path = []; P.x = R.start[0]; P.d = R.start[1]; marker = null; cam.init = false; msg = { text: '얼음이 깨져 물에 빠졌다', t: 1.8 }; }
const cam = { x: 0, y: 0, init: false };                                   // 카메라(그림 px): 지도가 화면보다 크면 아이를 따라간다
function isCorr(sc, vw) { return !!sc && (sc.kind === 'passage' || sc.x1 - sc.x0 > vw + 10); }       // 복도(통로)나 화면보다 긴 공간만 아이를 따라간다
function camTarget() {
  let [fx, fy1] = scr(P.x, P.d); const fy = fy1 - zAt(P.x, P.d), vw = VW / S, vh = VH / S, c = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
  if (R.sections) {
    // 카메라는 아이의 가로 위치만으로 정해지는 연속 함수다(스프링·지연 없음). 방 안에서는 방 가운데에 멈춰 있고,
    // 방을 벗어나면 아이와 같은 속도로(아이는 화면에 거의 고정, 맵이 움직인다) 다음 방 가운데까지 가서, 방에 들어오면 다시 멈춘다.
    const pts = CAMK, n = pts.length, fk = (x) => { if (!n) return x; if (x <= pts[0][0]) return pts[0][1]; if (x >= pts[n - 1][0]) return pts[n - 1][1]; for (let i = 1; i < n; i++) if (x <= pts[i][0]) { const [x1, f1] = pts[i - 1], [x2, f2] = pts[i]; return x2 > x1 ? f1 + (f2 - f1) * (x - x1) / (x2 - x1) : f2; } return x; };
    let f = 0; for (let k = -4; k <= 4; k++) f += fk(P.x + k * 3) / 9;                    // 멈춤↔이동 모서리를 ±12px 로 둥글려 출발·정지가 뚝 끊기지 않게 한다
    const sc = R.sections[secIdx(P.x)], cx = R.X0 + f + R.D / 4;
    return [c(cx - vw / 2, 0, Math.max(0, R.CW - vw)), (sc && !isCorr(sc, vw)) ? (R.CH <= vh ? -(vh - R.CH) / 2 : c(R.CH / 2 - vh / 2, 0, R.CH - vh)) : (R.CH <= vh ? -(vh - R.CH) / 2 : c(fy - vh * .6, 0, R.CH - vh))];
  }
  return [R.CW <= vw ? -(vw - R.CW) / 2 : c(fx - vw / 2 + LEAD.v, 0, R.CW - vw), R.CH <= vh ? -(vh - R.CH) / 2 : c(fy - vh * .6, 0, R.CH - vh)];
}

const img = (src) => new Promise((ok) => { const i = new Image(); i.onload = () => ok(i); i.src = src; });
const scr = (x, d) => [R.X0 + x + d / 2, R.Y0 - d / 2];                    // 바닥 -> 그림 화소
const world = (X, Y) => { const d = (R.Y0 - Y) * 2; return [X - R.X0 - d / 2, d]; };
function zAt(x, d) {
  if (R && R.zr && R.zr.length) { let z = 0; for (const r of R.zr) if (x >= r[0] && x < r[1] && d >= (r[2] == null ? -1e9 : r[2]) && d < (r[3] == null ? 1e9 : r[3])) z = Math.max(z, r[4]); return z; }   // 인도처럼 높은 바닥(장면이 기록): 그 위에서는 발이 그 높이
                                                            // 3차원 바닥 높이: S자 통로의 계단·단(앞 칸 0 → 가운데 칸 → 뒤 칸 → 오른쪽 끝에서 내려옴)
  if (!R || !R.sections) return 0;
  for (const s of R.sections) {
    const z = s.z3; if (!z || x < s.x0 || x >= s.x1) continue; const hw = z.hw;
    if (d <= z.dA + hw) return 0;
    if (d < z.dB - hw) return z.zB * (d - (z.dA + hw)) / ((z.dB - hw) - (z.dA + hw));
    if (d <= z.dB + hw) return z.zB;
    if (d < z.dC - hw) return z.zB + (z.zC - z.zB) * (d - (z.dB + hw)) / ((z.dC - hw) - (z.dB + hw));
    return z.zC * (x > z.xd ? 1 - Math.min(1, (x - z.xd) / (s.x1 - z.xd)) : 1);
  }
  return 0;
}
function worldZ(X, Y) {                                                         // 화면 → 바닥(높이 포함): d/2 + z(d) 가 단조 증가라 이분법으로 푼다
  let [x, d] = worldZ(X, Y); if (!R.sections || !R.sections.some((s) => s.z3)) return [x, d];
  let lo = 0, hi = R.D; for (let i = 0; i < 30; i++) { const m = (lo + hi) / 2, xm = X - R.X0 - m / 2; if (m / 2 + zAt(xm, m) - (R.Y0 - Y) > 0) hi = m; else lo = m; }
  d = (lo + hi) / 2; return [X - R.X0 - d / 2, d];
}
const sdist = (ax, ad, bx, bd) => Math.hypot((bx - ax) + (bd - ad) / 2, (bd - ad) / 2);   // 화면에서 보이는 거리

// ---------- 방 준비: 그림, 깊이 지도, 걸을 수 있는 격자 ----------
async function prepare(key) {
  const r = G.rooms[key]; if (r.ready) return r;
  r.name = key; r.im = await img(r.img); const dim = await img(r.depth); if (r.props) for (const q of r.props) if (!q.im) q.im = await img(q.img);
  const oc = document.createElement('canvas'); oc.width = r.CW; oc.height = r.CH; const o = oc.getContext('2d'); o.drawImage(dim, 0, 0);
  const px = o.getImageData(0, 0, r.CW, r.CH).data; r.dep = new Float32Array(r.CW * r.CH);
  if (r.dep16) for (let i = 0; i < r.dep.length; i++) { const v = px[i * 4] * 256 + px[i * 4 + 1]; r.dep[i] = v === 65535 ? 1e9 : v / 50 - 64; }   // 16비트 깊이(레이어 규칙: docs/layer-rules.md)
  else for (let i = 0; i < r.dep.length; i++) { const v = px[i * 4]; r.dep[i] = v === 255 ? 1e9 : v / 3 - 2; }
  r.gw = Math.ceil(r.W / CELL); r.gh = Math.ceil(r.D / CELL); r.free = new Uint8Array(r.gw * r.gh);
  for (let j = 0; j < r.gh; j++) for (let i = 0; i < r.gw; i++) r.free[j * r.gw + i] = walkable(r, (i + .5) * CELL, (j + .5) * CELL) ? 1 : 0;
  if (r.walk) {                                                                  // 지형 지도: 걸을 수 있는 칸 마스크(흰색)와 겹쳐 자른다
    const wim = await img(r.walk), wc = document.createElement('canvas'); wc.width = r.gw; wc.height = r.gh; const w = wc.getContext('2d'); w.drawImage(wim, 0, 0);
    const wd = w.getImageData(0, 0, r.gw, r.gh).data; for (let i = 0; i < r.free.length; i++) if (wd[i * 4] < 128) r.free[i] = 0;
  }
  if (r.reveal) for (const v of r.reveal) { v.im = await img(v.img); v.a = 0; }
  r.free0 = r.free.slice(); r.start = r.start || [r.W / 2, r.D / 2]; r.objects = r.objects || [];
  r.cr = (r.cracks || []).map(c => ({ ...c, st: 'ok', t: 0, cells: [] })); r.cr.forEach(c => { c.cells = cellsOf(r, c); });
  r.ready = true; return r;
}
function inExit(r, x, d) { return r.exits.find(e => x >= e.zone[0] && x <= e.zone[1] && d >= e.zone[2] && d <= e.zone[3] && !(e.hidden && e.need && !STATE.flags[e.need])); }
function walkable(r, x, d) {
  if (x < 0 || d < 0 || x > r.W || d > r.D) return false;
  if (!inExit(r, x, d) && (x < BODY.rx - 1 || x > r.W - BODY.rx + 1 || d < 1.5 || d > r.D - 2.5)) return false;   // 벽·단면 가장자리(문 자리는 예외)
  for (const [bx, bd, bw, bp] of r.rects) if (x > bx - BODY.rx && x < bx + bw + BODY.rx && d > bd - BODY.rd && d < bd + bp + BODY.rd) return false;
  return true;
}
const cellOf = (x, d) => [Math.max(0, Math.min(R.gw - 1, Math.floor(x / CELL))), Math.max(0, Math.min(R.gh - 1, Math.floor(d / CELL)))];
const isFree = (i, j) => i >= 0 && j >= 0 && i < R.gw && j < R.gh && R.free[j * R.gw + i] === 1;

// ---------- 길찾기: A* (8방향, 모서리 끼어들기 금지, 화면 거리 기준) + 직선으로 펴기 ----------
function nearestFree(i, j) {                 // 막힌 곳을 누르면 가장 가까운 빈 칸으로
  if (isFree(i, j)) return [i, j];
  let best = null, bd = 1e9;
  for (let b = 0; b < R.gh; b++) for (let a = 0; a < R.gw; a++) if (R.free[b * R.gw + a]) { const q = sdist(i, j, a, b); if (q < bd) { bd = q; best = [a, b]; } }
  return best;
}
function astar(si, sj, ti, tj) {
  const n = R.gw * R.gh, g = new Float32Array(n).fill(1e9), from = new Int32Array(n).fill(-1), closed = new Uint8Array(n), open = [];
  const h = (i, j) => sdist(i, j, ti, tj); const s = sj * R.gw + si; g[s] = 0; open.push([h(si, sj), s]);
  while (open.length) {
    let bi = 0; for (let k = 1; k < open.length; k++) if (open[k][0] < open[bi][0]) bi = k;
    const [, cur] = open.splice(bi, 1)[0]; if (closed[cur]) continue; closed[cur] = 1;
    const ci = cur % R.gw, cj = (cur / R.gw) | 0; if (ci === ti && cj === tj) break;
    for (let dj = -1; dj <= 1; dj++) for (let di = -1; di <= 1; di++) {
      if (!di && !dj) continue; const ni = ci + di, nj = cj + dj; if (!isFree(ni, nj)) continue;
      if (di && dj && (!isFree(ci + di, cj) || !isFree(ci, cj + dj))) continue;          // 모서리를 비스듬히 뚫지 않는다
      const k = nj * R.gw + ni, ng = g[cur] + sdist(ci, cj, ni, nj);
      if (ng < g[k]) { g[k] = ng; from[k] = cur; open.push([ng + h(ni, nj), k]); }
    }
  }
  const t = tj * R.gw + ti; if (from[t] < 0 && t !== s) return null;
  const out = []; for (let k = t; k >= 0; k = from[k]) { out.push([(k % R.gw + .5) * CELL, (((k / R.gw) | 0) + .5) * CELL]); if (k === s) break; }
  return out.reverse();
}
function clear(ax, ad, bx, bd) {             // 두 점 사이가 막힘 없이 보이는가
  const n = Math.ceil(Math.hypot(bx - ax, bd - ad) / (CELL / 2));
  for (let k = 0; k <= n; k++) { const x = ax + (bx - ax) * k / n, d = ad + (bd - ad) * k / n; const [i, j] = cellOf(x, d); if (!isFree(i, j)) return false; }
  return true;
}
function smooth(pts) {                       // 계단 모양 경로를 가장 먼 '보이는' 점끼리 직선으로 잇는다
  const out = [pts[0]]; let a = 0;
  while (a < pts.length - 1) { let b = pts.length - 1; while (b > a + 1 && !clear(pts[a][0], pts[a][1], pts[b][0], pts[b][1])) b--; out.push(pts[b]); a = b; }
  return out;
}
function goTo(x, d) {
  const [si, sj] = cellOf(P.x, P.d); const t = nearestFree(...cellOf(x, d)); if (!t) return;
  const s = isFree(si, sj) ? [si, sj] : nearestFree(si, sj); const raw = astar(s[0], s[1], t[0], t[1]); if (!raw) return;
  const exact = isFree(...cellOf(x, d)) && walkable(R, x, d);
  if (exact) raw[raw.length - 1] = [x, d];                                             // 빈 곳을 눌렀으면 정확히 그 점까지
  raw[0] = [P.x, P.d]; P.path = smooth(raw).slice(1); marker = { x: raw[raw.length - 1][0], d: raw[raw.length - 1][1], t: 0 };
}

// ---------- 조이스틱: 누르고 있을 때만 나타나는 떠 있는 조이스틱(누른 자리가 중심). 끌면 그 방향으로 걷는다 ----------
let JOY = null; const JOY_R = 44;
const px4 = (n) => 'polygon(' + n + 'px 0,calc(100% - ' + n + 'px) 0,calc(100% - ' + n + 'px) ' + n + 'px,100% ' + n + 'px,100% calc(100% - ' + n + 'px),calc(100% - ' + n + 'px) calc(100% - ' + n + 'px),calc(100% - ' + n + 'px) 100%,' + n + 'px 100%,' + n + 'px calc(100% - ' + n + 'px),0 calc(100% - ' + n + 'px),0 ' + n + 'px,' + n + 'px ' + n + 'px)';
function pixBox(size, notch, border, fill, z) {                              // 네모난 도트 상자: 모서리가 계단으로 깎인 사각형 테두리 + 안쪽 칠(둥근 곳 없음)
  const o = document.createElement('div'), i = document.createElement('div'), m = Math.round(size / 2);
  o.style.cssText = 'position:fixed;width:' + size + 'px;height:' + size + 'px;margin:-' + m + 'px 0 0 -' + m + 'px;background:' + border + ';clip-path:' + px4(notch) + ';pointer-events:none;z-index:' + z + ';display:none;image-rendering:pixelated';
  i.style.cssText = 'position:absolute;inset:' + notch + 'px;background:' + fill + ';clip-path:' + px4(notch) + ';image-rendering:pixelated'; o.appendChild(i); return o;
}
const joyBase = pixBox(JOY_R * 2, 12, 'rgba(255,255,255,.55)', 'rgba(20,16,24,.35)', 9), joyKnob = pixBox(40, 8, 'rgba(255,255,255,.95)', 'rgba(224,214,196,.85)', 10);
document.body.appendChild(joyBase); document.body.appendChild(joyKnob); document.body.style.touchAction = 'none';
function joyShow() { joyBase.style.left = JOY.x0 + 'px'; joyBase.style.top = JOY.y0 + 'px'; joyKnob.style.left = JOY.x + 'px'; joyKnob.style.top = JOY.y + 'px'; joyBase.style.display = joyKnob.style.display = 'block'; }
function joyHide() { joyBase.style.display = joyKnob.style.display = 'none'; }
function joyMove(ev) {
  if (!JOY || ev.pointerId !== JOY.id) return; let dx = ev.clientX - JOY.x0, dy = ev.clientY - JOY.y0; const r = Math.hypot(dx, dy);
  if (r > 10) JOY.moved = true;
  if (r > JOY_R) { dx *= JOY_R / r; dy *= JOY_R / r; }
  JOY.x = JOY.x0 + dx; JOY.y = JOY.y0 + dy; const rr = Math.min(r, JOY_R);
  if (r < 8) { JOY.mag = 0; } else { JOY.mag = Math.min(1, (rr - 8) / (JOY_R - 8) * 1.6); JOY.vx = dx / (Math.hypot(dx, dy) || 1); JOY.vy = dy / (Math.hypot(dx, dy) || 1); }
  joyShow();
}
function stepJoy(dt) {
  const sp = SPEED * dt * Math.min(1, JOY.mag), nx = P.x + (JOY.vx + JOY.vy) * sp, nd = P.d - 2 * JOY.vy * sp, ok = (x, d) => isFree(...cellOf(x, d));      // 화면 방향 → 바닥 이동(dx = X + Y, dd = -2Y)
  if (ok(nx, nd)) { P.x = nx; P.d = nd; } else if (ok(nx, P.d)) P.x = nx; else if (ok(P.x, nd)) P.d = nd;                 // 벽에 닿으면 벽을 따라 미끄러진다
  P.dir = DIRS[((Math.round(Math.atan2(JOY.vy, JOY.vx) / (Math.PI / 4)) % 8) + 8) % 8];
}
document.addEventListener('pointermove', joyMove);
const joyUp = (ev) => {
  if (!JOY || ev.pointerId !== JOY.id) return; const j = JOY; JOY = null; joyHide();
  if (!j.moved && performance.now() - j.t0 < 500 && ev.type === 'pointerup') { ripple(j.x0, j.y0); onDown({ clientX: j.x0, clientY: j.y0, preventDefault() {}, target: ev.target }); }     // 짧게 톡 누르면 문·통로·물건만 반응(맨바닥은 반응 없음)
};
document.addEventListener('pointerup', joyUp); document.addEventListener('pointercancel', joyUp);
// ---------- 움직임 ----------
const lbC = document.createElement('canvas'); lbC.width = 160; lbC.height = 10; const lbX = lbC.getContext('2d', { willReadFrequently: true }); let lbKey = '', lbW = 0;
function drawLabel() {                                                          // 장면 번호표: #037 눈 숲길 3 (주소에 #nolabel 이 있으면 숨김)
  if (/nolabel/.test(location.hash) || !R || !(R.no || R.sections)) return;
  const sec = R.sections && R.sections[secIdx(P.x)], tx = '#' + String((sec ? sec.no : R.no)).padStart(3, '0') + ' ' + (sec ? sec.label : (R.label || room));
  if (tx !== lbKey) {
    lbKey = tx; lbX.clearRect(0, 0, 160, 10); lbX.font = 'bold 8px monospace'; lbX.textAlign = 'left'; lbX.fillStyle = '#fff'; lbW = Math.min(150, Math.ceil(lbX.measureText(tx).width)); lbX.fillText(tx, 2, 8);
    const im = lbX.getImageData(0, 0, 160, 10), dd = im.data; for (let i = 0; i < dd.length; i += 4) { const on = dd[i + 3] > 110; dd[i] = 255; dd[i + 1] = 238; dd[i + 2] = 208; dd[i + 3] = on ? 255 : 0; } lbX.putImageData(im, 0, 0);
  }
  ctx.fillStyle = 'rgba(11,9,16,.7)'; ctx.fillRect(4, 3, lbW * 2 + 8, 22); ctx.imageSmoothingEnabled = false; ctx.drawImage(lbC, 0, 0, 160, 10, 6, 5, 320, 20);
}
// ---- 구간 조명: 한 장의 긴 띠 안에서 아이가 걷는 대로 앞 구간은 켜지고 지나온 구간은 어두워진다
let LS = null, DIVX = [], ROOMS = [], CAMK = [], zone = 0; const FLK = [.2, .7, .1, .6, .3, .8, .5, .9, 1];
const secIdx = (x) => { const s = R.sections; for (let i = 0; i < s.length; i++) if (x < s[i].x1) return i; return s.length - 1; };
// 분기점(통로 한가운데)이 띠를 구역으로 나눈다. 아이가 있는 구역만 켜지고, 분기점을 넘으면 뒤는 무너지듯 꺼지고 앞은 켜진다. 경계는 검은 띠.
const zoneOf = (x) => { let z = 0; for (let i = 0; i < DIVX.length; i++) if (x > DIVX[i]) z = i + 1; return z; };
const CAMG = { t: 0, sec: -1 }, CAMV = { x: 0, y: 0 };                           // 공간을 넘어갈 때 카메라가 그쪽으로 부드럽게 쑥 이동한다(느린 감쇠 스프링 + 가속·감속)
function smoothDamp(cur, target, vel, key, smooth, dt) { const w = 2 / smooth, x = w * dt, e = 1 / (1 + x + .48 * x * x + .235 * x * x * x), ch = cur - target, tmp = (vel[key] + w * ch) * dt; vel[key] = (vel[key] - w * tmp) * e; return target + (ch + tmp) * e; }
const LEAD = { v: 0, dir: 1 };                                                // 카메라 선행: 다음 분기점이 가까워지면 카메라가 아이보다 먼저 앞(어두운 구역)을 비춘다
function leadTarget() {
  return 0;                                                                         // 카메라 선행 대신 아래 camTarget 의 방 쏠림이 공간 쪽으로 카메라를 이끈다
  if (!R.sections) return 0;
  if (!isCorr(R.sections[secIdx(P.x)], VW / S)) return 0;                              // 고정 카메라인 방에서는 선행 없음
  if (P.path.length) { const dx = P.path[P.path.length - 1][0] - P.x; if (Math.abs(dx) > 6) LEAD.dir = dx > 0 ? 1 : -1; }
  const dir = LEAD.dir; let nd = null;
  if (dir > 0) { for (const d of DIVX) if (d > P.x) { nd = d; break; } } else { for (let i = DIVX.length - 1; i >= 0; i--) if (DIVX[i] < P.x) { nd = DIVX[i]; break; } }
  if (nd === null) return 0; const f = Math.max(0, Math.min(1, (170 - Math.abs(nd - P.x)) / 170)); return dir * 60 * f * f * (3 - 2 * f);
}
function updLight(dt, snap) {
  if (!LS || !R.sections) return; const x = P.x;
  { const si = secIdx(x); if (snap) { CAMG.sec = si; CAMG.t = 0; CAMV.x = 0; CAMV.y = 0; } else if (si !== CAMG.sec) { CAMG.sec = si; CAMG.t = 1.4; } }                  // 다른 공간으로 넘어가면 카메라 글라이드 시작
  if (snap) zone = zoneOf(x); else { const lo = zone > 0 ? DIVX[zone - 1] : -1e9, hi = zone < DIVX.length ? DIVX[zone] : 1e9; if (x > hi + 6) zone++; else if (x < lo - 6) zone--; }   // 분기점 ±6px 히스테리시스
  LEAD.v += (leadTarget() - LEAD.v) * (snap ? 1 : 1 - Math.exp(-dt * 3.2));
  for (let i = 0; i < LS.length; i++) {
    const o = LS[i], T = i === zone ? 1 : 0; if (snap) { o.L = T; o.on = T === 1; continue; }
    if (T === 1 && !o.on) o.fl = .6; o.on = T === 1; o.L = Math.max(0, Math.min(1, o.L + (T ? dt / .45 : -dt / .7))); if (o.fl > 0) o.fl -= dt;
  }
}
function zonePath(a, b, w) {                                                  // 분기점 a~b(없으면 끝까지) 사이 구역의 3/4 시점 경계: 바닥 위 45° 대각선 + 뒷벽 수직
  const X0s = (R.ox + R.X0) * S, Y0s = (R.oy + R.Y0) * S, hD = R.D / 2 * S, yt = R.oy * S - 12, yb = (R.oy + R.CH) * S + 12; ctx.beginPath();
  if (a === null) { ctx.moveTo(-60, yt); ctx.lineTo(-60, yb); } else { const xa = X0s + a * S + w; ctx.moveTo(xa + hD, yt); ctx.lineTo(xa + hD, Y0s - hD); ctx.lineTo(xa, Y0s); ctx.lineTo(xa, yb); }
  if (b === null) { ctx.lineTo(VW + 60, yb); ctx.lineTo(VW + 60, yt); } else { const xb = X0s + b * S - w; ctx.lineTo(xb, yb); ctx.lineTo(xb, Y0s); ctx.lineTo(xb + hD, Y0s - hD); ctx.lineTo(xb + hD, yt); }
  ctx.closePath();
}
function drawLight() {
  if (!LS || !R.sections) return; const n = LS.length, bw = 3 * S;
  for (let z = 0; z < n; z++) {
    const o = LS[z]; if (o.L >= .999 && !(o.fl > 0)) continue; ctx.save(); zonePath(z > 0 ? DIVX[z - 1] : null, z < DIVX.length ? DIVX[z] : null, bw); ctx.clip();
    if (z === zone) { const fk = o.fl > 0 ? FLK[Math.min(8, Math.floor((.6 - o.fl) / .07))] : 1; ctx.fillStyle = `rgba(4,3,8,${(1 - o.L * fk) * .94})`; ctx.fillRect(-60, 0, VW + 120, VH); }
    else if (o.L <= .001) { ctx.fillStyle = 'rgba(4,3,8,.94)'; ctx.fillRect(-60, 0, VW + 120, VH); }
    else { const pg = 1 - o.L; ctx.fillStyle = 'rgba(4,3,8,.94)'; for (let i = 0; i < TRANK.length; i++) if (TRANK[i] < pg * 1.1) ctx.fillRect((i % TCOLS) * TCELL, Math.floor(i / TCOLS) * TCELL, TCELL, TCELL); }   // 무너지듯 칸이 검게 채워진다
    ctx.restore();
  }
  const X0s = (R.ox + R.X0) * S, Y0s = (R.oy + R.Y0) * S, hD = R.D / 2 * S, yt = R.oy * S - 12, yb = (R.oy + R.CH) * S + 12;
  for (const c of DIVX) {                                                      // 검은 경계 띠(문턱): 아이는 이 위를 지나간다
    const xl = X0s + c * S - bw, xr = X0s + c * S + bw; ctx.fillStyle = '#000'; ctx.beginPath(); ctx.moveTo(xl + hD, yt); ctx.lineTo(xl + hD, Y0s - hD); ctx.lineTo(xl, Y0s); ctx.lineTo(xl, yb); ctx.lineTo(xr, yb); ctx.lineTo(xr, Y0s); ctx.lineTo(xr + hD, Y0s - hD); ctx.lineTo(xr + hD, yt); ctx.closePath(); ctx.fill();
    ctx.strokeStyle = '#2a2632'; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(xl + hD, Y0s - hD); ctx.lineTo(xl, Y0s); ctx.moveTo(xr + hD, Y0s - hD); ctx.lineTo(xr, Y0s); ctx.stroke();
  }
}
const TCOLS = 20, TROWS = 15, TCELL = 16, TRANK = []; for (let i = 0; i < TCOLS * TROWS; i++) { const r = Math.floor(i / TCOLS) / TROWS, n = (Math.sin(i * 12.9898) * 43758.5453) % 1; TRANK.push(r * .55 + Math.abs(n) * .45); }
const panC = document.createElement('canvas'); panC.width = 320; panC.height = 240; const panX = panC.getContext('2d'); let trans = null;
// 통로를 지나면 나가던 그 높이(가로로 나가면 d, 세로로 나가면 x) 그대로 다음 방에 나온다(걸을 수 없는 곳이면 가장 가까운 걸을 수 있는 곳으로). e.carry 가 있는 출구만.
const carrySpawn = (e) => { const sp = e.spawn.slice(); if (e.carry) { if (e.dir === 'R' || e.dir === 'L') sp[1] = P.d; else if (e.dir === 'B' || e.dir === 'F') sp[0] = P.x; } return sp; };
const EXIT_FACE = { R: 'r', L: 'l', B: 'u', F: 'd' };
function faceAfter(e, prev) {                                                 // 나간 방향이 아니라 다음 방에서 '진행할 방향'을 본다: 들어온 문 말고 나가는 문이 하나뿐이면 그 문 쪽, 아니면 나간 방향
  const nx = (R.exits || []).filter((x) => x.to && x.to !== prev && x.dir); P.dir = nx.length === 1 ? EXIT_FACE[nx[0].dir] : (EXIT_FACE[e.dir] || P.dir);
}                        // 통로로 나간 방향 그대로 다음 방에서도 그쪽을 본다(예전 방향이 남지 않게)
function startTrans(e) {                                                      // 문을 지나면: 아이는 화면에 고정, 시선이 문 쪽으로 움직이며 이전 장면이 무너지듯 검게 사라진다 → 다음 장면은 불이 켜지듯 깜빡이며 밝아진다
  const sn = document.createElement('canvas'); sn.width = VW; sn.height = VH; sn.getContext('2d').drawImage(cv, 0, 0); const v = TRAVEL[e.dir] || [1, 0];
  trans = { phase: 'out', t: 0, snap: sn, e, prev: room, sv: [v[0] + v[1] * .5, -v[1] * .5] }; P.path = []; P.act = null; marker = null;
}
function drawTrans() {
  if (!trans) return; const q = trans.t, ph = trans.phase, sv = trans.sv, ease = (x) => x < .5 ? 2 * x * x : 1 - Math.pow(-2 * x + 2, 2) / 2;
  if (ph === 'out') {
    const e = ease(Math.min(1, q)); ctx.fillStyle = '#000'; ctx.fillRect(0, 0, VW, VH); ctx.drawImage(trans.snap, -sv[0] * e * 24 + (Math.random() - .5) * e * 5, -sv[1] * e * 24 + (Math.random() - .5) * e * 3);
    ctx.fillStyle = '#000'; for (let i = 0; i < TRANK.length; i++) if (TRANK[i] < e * 1.1) ctx.fillRect((i % TCOLS) * TCELL, Math.floor(i / TCOLS) * TCELL, TCELL, TCELL);
    for (let g = 0; g < 4 * e; g++) { ctx.fillStyle = 'rgba(0,0,0,.8)'; ctx.fillRect(0, Math.random() * VH, VW, 1 + Math.random() * 3); }
  } else if (ph === 'wait') { ctx.fillStyle = '#000'; ctx.fillRect(0, 0, VW, VH); }
  else {
    const e = ease(Math.min(1, q)); panX.clearRect(0, 0, VW, VH); panX.drawImage(cv, 0, 0); ctx.fillStyle = '#000'; ctx.fillRect(0, 0, VW, VH); ctx.drawImage(panC, sv[0] * (1 - e) * 24, sv[1] * (1 - e) * 24);
    ctx.fillStyle = '#000'; for (let i = 0; i < TRANK.length; i++) if (TRANK[i] < (1 - e) * 1.1) ctx.fillRect((i % TCOLS) * TCELL, Math.floor(i / TCOLS) * TCELL, TCELL, TCELL);   // 나올 때도 나갈 때와 같은 도트 칸으로(거꾸로) 걷힌다
  }
}
let cut = null, shotImg = null;                                                               // 컷씬: 배경(실제 장면)은 그대로 보이고 위아래에 검은 띠만. 글 없이 카메라가 길을 따라 쭉 가서 보여 주고 아이 곁으로 돌아온다(누르면 건너뜀)
function startCut(c) { STATE.flags['cut_' + c.id] = true; cut = { t: 0, out: c.out || 3.2, hold: c.hold || 1.2, back: c.back || 3.2, dist: c.dist || 400, bar: 0, after: c.after, shot: c.shot }; if (c.shot) { shotImg = new Image(); shotImg.src = G.rooms[c.shot.room].img; for (const q of G.rooms[c.shot.room].shotProps || []) if (!q.im) img(q.img).then((i) => { q.im = i; }); } cut.T = cut.out + cut.hold + cut.back; if (c.face) P.dir = c.face; P.path = []; P.act = null; marker = null; if (c.walk) { goTo(c.walk[0], c.walk[1]); cut.walking = true; } else if (c.to) { goTo(c.to[0], c.to[1]); cut.walking = true; } }                     // walk 가 있으면 먼저 그곳까지 걸어 나온 뒤 컷씬(띠·카메라)이 시작된다
let skipBtn = null, skipTm = 0;                                               // 컷씬 중 화면을 한 번 누르면 오른쪽 위에 >> 가 나오고, 그걸 누르면 컷씬 전체를 건너뛴다
function hideSkip() { if (skipBtn) skipBtn.style.display = 'none'; clearTimeout(skipTm); }
function showSkip() {
  if (!skipBtn) {
    skipBtn = document.createElement('button'); skipBtn.textContent = '>>'; skipBtn.style.cssText = 'position:fixed;right:8px;top:48px;z-index:12;font:bold 18px system-ui,sans-serif;color:#fff;background:rgba(0,0,0,.6);border:1px solid #aaa;border-radius:6px;padding:6px 16px;cursor:pointer;display:none';
    skipBtn.onclick = (e) => { e.stopPropagation(); if (cut) { cut.walking = false; cut.t = Math.max(cut.t, cut.T); } hideSkip(); };
    ['pointerdown', 'touchstart', 'mousedown'].forEach((ev) => skipBtn.addEventListener(ev, (e) => e.stopPropagation())); document.body.appendChild(skipBtn);
  }
  skipBtn.style.display = 'block'; clearTimeout(skipTm); skipTm = setTimeout(hideSkip, 3500);
}
function updCut(dt) {
  if (!cut) return;
  if (cut.walking) { cut.bar = Math.min(1, cut.bar + dt / .5); if (P.dir === 'r') cut.lw = (cut.lw || 0) + dt; if (P.path.length || P.moving) { if ((cut.wt = (cut.wt || 0) + dt) < 20) return; } cut.walking = false; cut.t = .5; }   // 걸어 나오는 것도 컷씬: 띠가 먼저 내려오고 천천히 걷는 동안 기다린다
  cut.t += dt; const end = cut.T + .5;
  cut.bar = Math.max(0, Math.min(1, (end - cut.t) / .5)); if (cut.t >= end) { cut = null; hideSkip(); }
}
function cutPan() {                                                           // 카메라 이동 비율 0→1→0 (부드럽게)
  if (!cut) return 0; const t = cut.t - .5, sm = (x) => { x = Math.max(0, Math.min(1, x)); return x * x * (3 - 2 * x); };
  return t < cut.out ? sm(t / cut.out) : t < cut.out + cut.hold ? 1 : 1 - sm((t - cut.out - cut.hold) / cut.back);
}
function update(dt) {
  updLight(dt);
  if (trans) {
    if (trans.phase === 'out') { trans.t += dt / .75; if (trans.t >= 1) { trans.phase = 'wait'; enter(trans.e.to, carrySpawn(trans.e)).then(() => { if (trans) { trans.phase = 'in'; trans.t = 0; faceAfter(trans.e, trans.prev); if (cut && cut.after) { P.dir = 'r'; goTo(cut.after[0], cut.after[1]); } const ce = trans.e.cut; if (ce && !STATE.flags['cut_' + ce.id]) startCut(ce); } }); } }                    // 나오자마자(불이 켜지는 동안) 컷씬을 시작한다
    else if (trans.phase === 'in') { trans.t += dt / 1.0; if (trans.t >= 1) trans = null; }
    if (trans && trans.phase === 'in') updCut(dt);
    return;
  }
  if (fadeDir) {
    fade += fadeDir * dt / .22;
    if (fade >= 1 && pending) { fade = 1; const p = pending; pending = null; enter(p.to, carrySpawn(p)).then(() => { fadeDir = -1; if (p.dir) faceAfter(p, p.from); }); fadeDir = 0; }
    if (fade <= 0) { fade = 0; fadeDir = 0; fadeCol = '20,14,16'; }
    return;
  }
  if (R && R.cutAt && !cut && !trans && !fadeDir && !STATE.flags['cut_' + R.cutAt.id] && P.d > R.cutAt.d) startCut(R.cutAt);       // 터널 안에서 어느 지점을 넘으면 컷씬: 걸어 나가는 것부터 컷씬이다
  updCut(dt);
  viewTick(dt);
  if (FP) { FP.a = Math.min(1, FP.a + dt / .25); FP.flash = Math.max(0, (FP.flash || 0) - dt); if (!curView()) FP = null; return; }
  if (marker) { marker.t += dt; if (marker.t > .6 && !P.path.length) marker = null; }
  if (msg) { msg.t -= dt; if (msg.t <= 0) msg = null; }
  for (const c of R.cr) {                                                      // 약한 얼음: 밟으면 금이 가고, 떠나면 깨져 물이 된다. 오래 서 있으면 빠진다
    const inside = inCrack(c, P.x, P.d, .5);
    if (c.st === 'ok' && inside) { c.st = 'armed'; c.t = 0; }
    else if (c.st === 'armed') { if (inside) { c.t += dt; if (c.t > 2.2) { for (const k of c.cells) R.free[k] = 0; c.st = 'broken'; respawn(); fadeDir = 0; return; } } else { c.st = 'breaking'; c.t = 0; } }
    else if (c.st === 'breaking') { c.t += dt; if (c.t > .35) { for (const k of c.cells) R.free[k] = 0; c.st = 'broken'; } }
  }
  if (updChaser(dt)) return;
  if (P.act && !P.path.length) {                                               // 사물에 다가가 멈추면 조작한다: 쪽지·열쇠·책·레버·촛불
    const o = P.act; P.act = null; const pz = R.puzzle || {};
    if (sdist(P.x, P.d, o.x, o.d) < (o.reach || 18)) {
      if (o.kind) enterFP(o);
      else if (o.type === 'note') msg = { text: o.text, t: 3.6 };
      else if (o.type === 'poem') { POEM = { lines: o.lines }; STATE.flags.poem_read = true; }
      else if (o.type === 'tool') { if (!STATE.got[o.id]) { STATE.got[o.id] = true; addItem('tool'); beep(520, .12, 'square', .08); msg = { text: '낡은 도구를 얻었다', t: 2.6 }; } else msg = { text: '더는 쓸 만한 게 없다', t: 1.4 }; }
      else if (o.type === 'key') { if (!STATE.got[o.id]) { STATE.got[o.id] = true; STATE.flags[o.flag] = true; msg = { text: o.text, t: 2.8 }; } else msg = { text: '빈 양동이다', t: 1.2 }; }
      else if (o.type === 'book') { if (STATE.flags[pz.flag]) msg = { text: '이미 펼쳐 놓았다', t: 1.2 }; else if (o.correct) { STATE.flags[pz.flag] = true; STATE.got[o.id] = true; msg = { text: pz.solvedMsg, t: 3 }; } else msg = { text: o.text, t: 2.2 }; }
      else if (o.type === 'switch') {
        STATE.sw[o.id] = STATE.sw[o.id] ? 0 : 1; const sws = R.objects.filter(x => x.type === 'switch');
        if (sws.every(x => (STATE.sw[x.id] ? 1 : 0) === x.want)) { STATE.flags[pz.flag] = true; msg = { text: pz.solvedMsg, t: 3 }; } else { STATE.flags[pz.flag] = false; msg = { text: STATE.sw[o.id] ? '레버를 올렸다' : '레버를 내렸다', t: 1.2 }; }
      }
      else if (o.type === 'candle') {
        if (STATE.lit[o.id]) msg = { text: '이미 켜져 있다', t: 1.2 };
        else {                                                                      // 순서 퍼즐: 책장에 꽂힌 책의 색 순서대로 켠다
          const seq = STATE.seq[R.name] = STATE.seq[R.name] || [], total = R.objects.filter(x => x.type === 'candle').length;
          if (o.order === seq.length) {
            STATE.lit[o.id] = true; seq.push(o.id);
            if (seq.length === total) { STATE.flags[pz.flag] = true; msg = { text: pz.solvedMsg, t: 3.2 }; } else msg = { text: `촛불이 켜졌다 (${seq.length}/${total})`, t: 1.4 };
          } else { for (const id of seq) delete STATE.lit[id]; STATE.seq[R.name] = []; msg = { text: '촛불이 모두 꺼졌다. 순서가 아닌 모양이다', t: 2.2 }; }
        }
      }
    } else if (!o.kind) msg = { text: '조금 더 가까이 가야 한다', t: 1 };
  }
  const joyOn = !!(JOY && JOY.mag > 0 && !cut && !trans && !fadeDir);
  if (joyOn) { P.path = []; P.act = null; marker = null; stepJoy(dt); }
  if (!P.path.length && !joyOn) { P.moving = false; P.t = 0; return; }
  const slow = cut && cut.walking ? .5 : 1; let left = SPEED * slow * dt; P.moving = true; P.t += dt * slow;      // 컷씬의 걸어 나오기는 천천히
  while (left > 0 && P.path.length) {
    const [tx, td] = P.path[0], dist = sdist(P.x, P.d, tx, td);
    const sx = (tx - P.x) + (td - P.d) / 2, sy = -(td - P.d) / 2;                      // 화면에서의 이동 방향
    if (dist > .01) P.dir = DIRS[((Math.round(Math.atan2(sy, sx) / (Math.PI / 4)) % 8) + 8) % 8];
    if (dist <= left) { P.x = tx; P.d = td; P.path.shift(); left -= dist; }
    else { const k = left / dist; P.x += (tx - P.x) * k; P.d += (td - P.d) * k; left = 0; }
  }
  const e = inExit(R, P.x, P.d);
  if (e && !P.path.length) {
    if (e.need && !STATE.flags[e.need]) { if (!msg) { msg = e.needMsg ? { text: e.needMsg, t: 2.2 } : { text: '', t: 1.2 }; const z = e.zone; goTo((z[0] + z[1]) / 2, e.side === 'back' ? z[2] - 12 : (z[2] + z[3]) / 2 - 10); } }
    else if (e.to) { if (e.type === 'trans' && !trans) startTrans(e); else if (!trans) { e.from = room; pending = e; fadeDir = 1; fadeCol = e.fc || '20,14,16'; } } else if (!msg) { msg = { text: e.endMsg || '여기서부터는 아직 만들지 않았어요', t: 2.6 }; P.path = []; const s = e.zone; goTo((s[0] + s[1]) / 2 + (e.side === 'left' ? 10 : e.side === 'right' ? -10 : 0), (s[2] + s[3]) / 2 + (e.side === 'front' ? 10 : e.side === 'back' ? -10 : 0)); }
  }
}
async function enter(key, spawn) { FP = null; R = await prepare(key); room = key; S = R.sections ? 1.5 : (R.S || (R.CH > 140 ? 1 : 2)); R.objects = viewObjs(R); P.x = spawn[0]; P.d = spawn[1]; { const [ci, cj] = cellOf(P.x, P.d); if (!isFree(ci, cj)) { const t = nearestFree(ci, cj); if (t) { P.x = (t[0] + .5) * CELL; P.d = (t[1] + .5) * CELL; } } } LEAD.v = 0; LEAD.dir = 1; DIVX = R.sections ? R.sections.filter((s) => s.kind === 'passage').map((s) => s.mid[0]) : []; ROOMS = R.sections ? R.sections.filter((s) => s.kind === 'room') : []; CAMK = []; { const vw = VW / S; for (const rm of ROOMS) { const w = rm.x1 - rm.x0, cr = rm.x0 + w / 2; if (w <= vw + 10) { const h = Math.min(w / 2 + 4, 50); CAMK.push([cr - h, cr], [cr + h, cr]); } else CAMK.push([rm.x0 + 70, rm.x0 + 70], [rm.x1 - 70, rm.x1 - 70]); } } LS = R.sections ? Array.from({ length: DIVX.length + 1 }, () => ({ L: 0, fl: 0, on: false })) : null; if (LS) updLight(0, true); P.path = []; marker = null; cam.init = false; setupChaser(); }

// ---------- 그리기: 방 -> 아이(가구 뒤에 있으면 깊이 지도로 가림) -> 표시 ----------
const sprC = document.createElement('canvas'), sprX = sprC.getContext('2d'); const shC = document.createElement('canvas'), shX = shC.getContext('2d'); const frames = {};
const prC = document.createElement('canvas'), prX = prC.getContext('2d', { willReadFrequently: true });
function drawProps(front) {                                                    // 방에 놓인 인물 그림(예: 그네에 앉은 곰): 아이보다 먼 것은 아이보다 먼저, 가까운 것은 나중에. 앞의 물체(기둥 등)에는 깊이 지도로 가려진다
  if (!R.props) return;
  for (const q of R.props) {
    if ((q.d >= P.d) !== front || !q.im) continue;
    const Kx = q.im.width / q.w, Ky = q.im.height / q.h, wK = q.im.width, hK = q.im.height; prC.width = wK; prC.height = hK; prX.clearRect(0, 0, wK, hK); prX.drawImage(q.im, 0, 0);
    const [X, Y1] = scr(q.x, q.d), Y = Y1 - q.z, x0 = Math.round((X - q.w / 2) * S) / S, y0 = Math.round((Y - q.h) * S) / S, id = prX.getImageData(0, 0, wK, hK), a = id.data;
    for (let y = 0; y < hK; y++) for (let x = 0; x < wK; x++) {
      const wx = Math.floor(x0 + x / Kx), wy = Math.floor(y0 + y / Ky); if (wx < 0 || wy < 0 || wx >= R.CW || wy >= R.CH) continue;
      if (R.dep[wy * R.CW + wx] < q.d - .5) a[(y * wK + x) * 4 + 3] = 0;
    }
    prX.putImageData(id, 0, 0); ctx.imageSmoothingEnabled = true; ctx.imageSmoothingQuality = 'high'; ctx.drawImage(prC, (R.ox + x0) * S, (R.oy + y0) * S, q.w * S, q.h * S); ctx.imageSmoothingEnabled = false;
  }
}
function drawChild() {
  const [w, h] = G.childSize, K = G.childK || 1, Ky = G.childKy || K, wK = Math.round(w * K), hK = Math.round(h * Ky); sprC.width = wK; sprC.height = hK;
  const cvw = curView(); if (cvw && cvw.mode === 'adult' && adultIm) { const [ax, ay] = scr(P.x, P.d), bob = P.moving ? Math.round(Math.sin(P.t * 12)) : 0; ctx.save(); ctx.translate((R.ox + ax) * S, (R.oy + ay + 1) * S); if (['l', 'ul', 'dl'].includes(P.dir)) ctx.scale(-1, 1); ctx.drawImage(adultIm, -6.5 * S, (-38 + bob) * S, 13 * S, 38 * S); ctx.restore(); return; }
  const SEQ = K > 1 ? ['w1', 'w2', 'w3', 'w4', 'w5', 'w6', 'w7', 'w8'] : ['w1', 'w2', 'w3', 'w4'], f0 = P.moving ? SEQ[Math.floor(P.t * (K > 1 ? WALK_FPS_HD : WALK_FPS)) % SEQ.length] : 'idle', lk = cut && cut.walking && P.dir === 'r' ? ((cut.lw || 0) > .8 && cut.lw < 1.9 ? 'lu' : (cut.lw || 0) > 3.0 && cut.lw < 4.1 ? 'ld' : '') : '', f = lk ? lk + '_' + f0 : f0; const im = frames[P.dir + '_' + f] || frames[P.dir + '_' + f0]; if (!im) return;      // 컷씬에서 걸어 나오는 동안 고개를 위·아래로 돌려 주변을 둘러본다
  sprX.clearRect(0, 0, wK, hK); sprX.drawImage(im, 0, 0);
  const bob = 0;      // 걸을 때 몸이 살짝 오르내린다(1/K 칸 단위라 부드럽다)
  if (P.zr !== R || P.zs === undefined) { P.zr = R; P.zs = zAt(P.x, P.d); } else P.zs += (zAt(P.x, P.d) - P.zs) * (1 - Math.exp(-(lastDt || .016) * 24));   // 턱을 오를 때 발 높이가 부드럽게 바뀐다
  const [fx, fy0] = scr(P.x, P.d), fy = fy0 - P.zs, x0 = Math.round((fx - w / 2) * S) / S, y0 = Math.round((fy - h + 1 + bob) * S) / S;      // 위치를 화면 칸에 맞춰 걸을 때 자글거리지 않게
  const id = sprX.getImageData(0, 0, wK, hK), a = id.data;
  let tot = 0, hid = 0; const hidden = new Uint8Array(wK * hK);
  for (let y = 0; y < hK; y++) for (let x = 0; x < wK; x++) {
    const X = Math.floor(x0 + x / K), Y = Math.floor(y0 + y / Ky); if (X < 0 || Y < 0 || X >= R.CW || Y >= R.CH) continue;
    if (a[(y * wK + x) * 4 + 3] > 0) { tot++; if (R.dep[Y * R.CW + X] < P.d - .5 - 2 * Math.max(0, Y + 1 - fy)) { hid++; hidden[y * wK + x] = 1; } }      // 발 줄 근처는 바닥 자체(발 아래 한 줄은 d 가 2 작다)를 가림으로 착각하지 않게 여유를 준다
  }
  // 80% 이상 가려지면 가린 물체를 투시(반투명)해서 아이를 보여 준다(서서히 바뀐다). 그보다 덜 가려질 때는 지금처럼 물체가 앞에서 덮는다.
  const target = tot && hid / tot >= .8 ? 1 : 0; P.st = (P.st || 0) + (target - (P.st || 0)) * (1 - Math.exp(-(lastDt || .016) * 9));
  for (let i = 0; i < hidden.length; i++) if (hidden[i]) a[i * 4 + 3] = Math.round(a[i * 4 + 3] * P.st * .62);
  // 발 밑 그림자(바닥에 붙은 납작한 타원): 걷는 동안에도 항상 있고, 물체 뒤에서는 물체에 가려진다
  { const SW = 16, SH = 6; shC.width = SW * K; shC.height = SH * K; const sx0 = Math.round((fx - SW / 2) * K) / K, sy0 = Math.round((fy - SH / 2 - .2) * K) / K, sid = shX.createImageData(SW * K, SH * K), sa = sid.data;
    for (let y = 0; y < SH * K; y++) for (let x = 0; x < SW * K; x++) {
      const u = ((x + .5) / K - SW / 2) / 5.6, v = ((y + .5) / K - SH / 2) / 2, q = u * u + v * v; if (q >= 1) continue;
      const X = Math.floor(sx0 + x / K), Y = Math.floor(sy0 + y / K); if (X < 0 || Y < 0 || X >= R.CW || Y >= R.CH) continue;
      if (R.dep[Y * R.CW + X] < P.d - 3 - 2 * Math.max(0, Y + 1 - fy)) continue;
      const i = (y * SW * K + x) * 4; sa[i] = 6; sa[i + 1] = 4; sa[i + 2] = 10; sa[i + 3] = q < .45 ? 120 : 76;
    }
    shX.putImageData(sid, 0, 0); ctx.drawImage(shC, (R.ox + sx0) * S, (R.oy + sy0) * S, SW * S, SH * S); }
  sprX.putImageData(id, 0, 0); ctx.imageSmoothingEnabled = true; ctx.imageSmoothingQuality = 'high'; ctx.drawImage(sprC, (R.ox + x0) * S, (R.oy + y0) * S, w * S, h * S); ctx.imageSmoothingEnabled = false;      // 고해상도 그림을 부드럽게 줄여 그린다(걸을 때 자글자글하지 않게)
}
let lastDt = .016;
function draw(dt) {
  lastDt = dt || .016;
  ctx.imageSmoothingEnabled = false; ctx.fillStyle = '#1e1618'; ctx.fillRect(0, 0, VW, VH); if (!R) return;
  const cz = camZoom(); ctx.save(); if (cz !== 1) { ctx.translate(VW / 2, VH * .55); ctx.scale(cz, cz); ctx.translate(-VW / 2, -VH * .55); }
  const [tx, ty] = camTarget(); if (!cam.init) { cam.x = tx; cam.y = ty; cam.init = true; } else if (R.sections) { cam.x = tx; cam.y = ty; } else { const k = 1 - Math.exp(-(dt || .016) * 7); cam.x += (tx - cam.x) * k; cam.y += (ty - cam.y) * k; }
  if (cut) { const vw_ = VW / S, mx = Math.max(0, R.CW - vw_); cam.x = tx + (Math.max(tx, Math.min(mx, tx + cut.dist)) - tx) * cutPan(); }                  // 컷씬: 카메라가 길 쪽으로 쭉 갔다 돌아온다
  R.ox = -Math.round(cam.x * S) / S; R.oy = -Math.round(cam.y * S) / S;
  ctx.drawImage(R.im, R.ox * S, R.oy * S, R.CW * S, R.CH * S);
  if (R.reveal) for (const v of R.reveal) {                                                     // 검게 가려진 벽: 가까이 가면 벽이 투시되어 안쪽이 서서히 보인다
    const z = v.zone, dx = Math.max(z[0] - P.x, 0, P.x - z[1]), dd = Math.max(z[2] - P.d, 0, P.d - z[3]), tg = Math.max(0, Math.min(1, 1 - Math.hypot(dx, dd) / (v.r || 40)));
    v.a += (tg - v.a) * (1 - Math.exp(-(dt || .016) * 6)); if (v.a > .01) { ctx.globalAlpha = v.a; ctx.drawImage(v.im, (R.ox + v.x) * S, (R.oy + v.y) * S, v.w * S, v.h * S); ctx.globalAlpha = 1; }
  }
  drawLight();
  const dot = (x, d, c, r = 1) => { const [X, Y] = scr(x, d); ctx.fillStyle = c; ctx.fillRect((R.ox + X - r / 2) * S, (R.oy + Y - r / 2) * S, r * S, r * S); };
  if (debug) {
    for (let j = 0; j < R.gh; j++) for (let i = 0; i < R.gw; i++) dot((i + .5) * CELL, (j + .5) * CELL, R.free[j * R.gw + i] ? '#5f85' : '#f556');
    for (const e of R.exits) for (let x = e.zone[0]; x <= e.zone[1]; x += 2) for (let d = e.zone[2]; d <= e.zone[3]; d += 2) dot(x, d, '#fd4a');
    let px = P.x, pd = P.d; for (const [x, d] of P.path) { const n = Math.ceil(sdist(px, pd, x, d)); for (let k = 0; k <= n; k++) dot(px + (x - px) * k / n, pd + (d - pd) * k / n, '#fff'); px = x; pd = d; }
  }
  if (marker && SHOW_MARKER) {                    // 누른 자리: 바닥에 퍼지는 고리(지금은 끔: 걸을 때 바닥 표시가 뜨지 않는다)
    const [X, Y1] = scr(marker.x, marker.d), Y = Y1 - zAt(marker.x, marker.d), k = Math.min(1, marker.t / .35), rx = 2 + 5 * k; ctx.strokeStyle = `rgba(255,236,190,${.9 - .6 * k})`; ctx.lineWidth = S;
    ctx.beginPath(); ctx.ellipse((R.ox + X) * S, (R.oy + Y) * S, rx * S, rx * S / 2, 0, 0, Math.PI * 2); ctx.stroke();
  }
  for (const c of R.cr) {                                                      // 약한 얼음 칸의 상태
    const [X, Y] = scr(c.x, c.d); const cx = (R.ox + X) * S, cy = (R.oy + Y) * S;
    if (c.st === 'broken' || (c.st === 'breaking' && c.t > .2)) { ctx.fillStyle = '#3c6088'; ctx.beginPath(); ctx.ellipse(cx, cy, (c.rx + 1) * S, 4.8 * S, 0, 0, Math.PI * 2); ctx.fill(); ctx.strokeStyle = '#7fa8d0'; ctx.lineWidth = S; ctx.beginPath(); ctx.ellipse(cx, cy, (c.rx - 2) * S, 2.6 * S, 0, 0, Math.PI * 2); ctx.stroke(); }
    else if (c.st === 'armed' || c.st === 'breaking') { ctx.strokeStyle = `rgba(255,255,255,${.5 + .4 * Math.sin(performance.now() / 60)})`; ctx.lineWidth = S; ctx.beginPath(); ctx.moveTo(cx - 5 * S, cy); ctx.lineTo(cx - S, cy - 2 * S); ctx.lineTo(cx + 2 * S, cy + S); ctx.lineTo(cx + 5 * S, cy - S); ctx.stroke(); }
  }
  for (const e of R.exits) if (e.manhole && e.need && STATE.flags[e.need]) {                       // 드러난 맨홀 뚜껑
    const [X, Y] = scr(e.mx, e.md), cx = (R.ox + X) * S, cy = (R.oy + Y) * S;
    ctx.fillStyle = '#ecf2fc'; ctx.beginPath(); ctx.ellipse(cx, cy, 10 * S, 5.4 * S, 0, 0, Math.PI * 2); ctx.fill(); ctx.fillStyle = '#566070'; ctx.beginPath(); ctx.ellipse(cx, cy, 8.6 * S, 4.5 * S, 0, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = '#8a96aa'; ctx.beginPath(); ctx.ellipse(cx, cy, 7 * S, 3.5 * S, 0, 0, Math.PI * 2); ctx.fill(); ctx.strokeStyle = '#5a6478'; ctx.lineWidth = S; for (let k = -2; k <= 2; k++) { ctx.beginPath(); ctx.moveTo(cx + k * 2.4 * S - 2 * S, cy - 3 * S); ctx.lineTo(cx + k * 2.4 * S + 2 * S, cy + 3 * S); ctx.stroke(); }
    ctx.fillStyle = 'rgba(236,244,255,.65)'; for (let k = 0; k < 3; k++) { const yy = cy - (6 + k * 4 + (performance.now() / 120) % 4) * S; ctx.fillRect(cx + (k - 1) * 2 * S, yy, 2 * S, 2 * S); }
  }
  for (const e of R.exits) if (e.open && e.need && STATE.flags[e.need]) {                                          // 열린 문: 뒷벽에 어두운 입구와 따뜻한 빛
    const x0 = R.X0 + e.open.x0 + R.D / 2, x1 = R.X0 + e.open.x1 + R.D / 2, yb = R.Y0 - R.D / 2, yt = yb - e.open.z1;
    ctx.fillStyle = '#1a1214'; ctx.fillRect((R.ox + x0) * S, (R.oy + yt) * S, (x1 - x0) * S, (yb - yt) * S); ctx.fillStyle = '#ffd9902a'; ctx.fillRect((R.ox + x0 + 2) * S, (R.oy + yt + 2) * S, (x1 - x0 - 4) * S, (yb - yt - 2) * S);
    ctx.fillStyle = '#d2a064'; ctx.fillRect((R.ox + x0) * S, (R.oy + yb - 2) * S, (x1 - x0) * S, 2 * S);
  }
  const tnow = performance.now();
  drawViewBack();
  for (const o of R.objects) { if (o.kind) { drawObj(o); continue; }                // 조작할 수 있는 사물: 엔진이 그림 위에 덧그린다
    const [X, Y0] = scr(o.x, o.d), cx = (R.ox + X) * S, cy = (R.oy + Y0 - (o.z || 0)) * S, sp = (Math.sin(tnow / 300 + o.x) + 1) / 2;
    const rect = (x, y, w, h, c) => { ctx.fillStyle = c; ctx.fillRect(cx + x * S, cy + y * S, w * S, h * S); };
    if (o.type === 'note' || (o.type === 'poem' && !o.baked)) { rect(-4, -2, 8, 5, '#f2e8c8'); rect(-3, -1, 6, 1, '#b8a888'); rect(-3, 1, 4, 1, '#b8a888'); if (sp > .6) rect(4, -5, 1, 1, '#fff'); }
    else if (o.type === 'key') { if (STATE.got[o.id]) continue; rect(-2, -3, 4, 3, '#e8c050'); rect(-1, -2, 2, 1, '#6a4a1a'); rect(-1, 0, 1, 5, '#e8c050'); rect(0, 3, 3, 1, '#e8c050'); if (sp > .5) { rect(3, -5, 1, 1, '#fff'); rect(-4, -1, 1, 1, '#fff'); } }
    else if (o.type === 'book') { const c = `rgb(${o.color.join(',')})`; rect(-5, -2, 10, 6, '#e6dcc0'); rect(-4, -3, 8, 5, c); rect(-4, -3, 1, 5, '#0004'); if (STATE.got[o.id]) { rect(-5, -8, 10, 4, '#ffffff'); rect(-4, -12, 8, 4, '#cfe0ff'); rect(-1, -16, 2, 4, '#8fb0ff'); } else if (sp > .7) rect(4, -5, 1, 1, '#fff'); }
    else if (o.type === 'switch') {
      const on = STATE.sw[o.id] ? 1 : 0, by = Y0;
      ctx.fillStyle = '#bfa66a'; ctx.beginPath(); ctx.ellipse((R.ox + X) * S, (R.oy + by - 10) * S, 3.4 * S, 1.8 * S, 0, 0, 6.3); ctx.fill();
      ctx.strokeStyle = '#d8d0e0'; ctx.lineWidth = 2 * S; ctx.beginPath(); ctx.moveTo((R.ox + X) * S, (R.oy + by - 10) * S); ctx.lineTo((R.ox + X + (on ? 3 : -3)) * S, (R.oy + by - (on ? 20 : 4)) * S); ctx.stroke();
      ctx.fillStyle = on ? '#ffe070' : '#5a5060'; ctx.fillRect((R.ox + X - 2) * S, (R.oy + by - 26) * S, 4 * S, 3 * S);
    }
    else if (o.type === 'candle') {
      const c = o.color ? `rgb(${o.color.join(',')})` : '#f0e8c8'; const bx = cx, by = (R.oy + Y0) * S;
      ctx.fillStyle = '#8a7040'; ctx.fillRect(bx - 3 * S, by - 2 * S, 6 * S, 2 * S); ctx.fillStyle = '#6a5430'; ctx.fillRect(bx - S, by - 8 * S, 2 * S, 6 * S); ctx.fillStyle = c; ctx.fillRect(bx - 2 * S, by - 14 * S, 4 * S, 6 * S); ctx.fillStyle = '#0003'; ctx.fillRect(bx + S, by - 14 * S, S, 6 * S);
      if (STATE.lit[o.id]) { const fy = by - 18 * S, g = ctx.createRadialGradient(bx, fy, 2, bx, fy + 6 * S, 30 * S); g.addColorStop(0, 'rgba(255,226,150,.55)'); g.addColorStop(1, 'rgba(255,226,150,0)'); ctx.fillStyle = g; ctx.fillRect(bx - 40 * S, fy - 30 * S, 80 * S, 80 * S); ctx.fillStyle = '#ffd070'; ctx.fillRect(bx - S, fy - S, 2 * S, 4 * S); ctx.fillStyle = '#fff6d6'; ctx.fillRect(bx - S * .5, fy + S, S, 2 * S); }
      else if (sp > .8) { ctx.fillStyle = '#fff'; ctx.fillRect(bx + 3 * S, by - 14 * S, S, S); }
    }
  }
  drawProps(true); if (C.d >= P.d) { drawChaser(); drawChild(); } else { drawChild(); drawChaser(); } drawProps(false);
  if (R.mood === 'dark' || C.st === 'rise' || C.st === 'chase' || C.st === 'wait') {                                                     // 추격 구간의 꺼림칙한 분위기: 어둡게 가라앉히고, 아이 둘레만 흐릿하게 보이며, 가장자리가 맥박처럼 숨 쉰다
    const [fx0, fy0] = scr(P.x, P.d), rs = C.st === 'rise', [qx, qy] = rs ? scr(C.x, C.d - 30) : [fx0, fy0], fx = (fx0 + qx) / 2, fy = (fy0 + qy) / 2, px = (R.ox + fx) * S, py = (R.oy + fy - 14) * S, t = performance.now() / 1000, br = (rs ? 2.4 : 1) * (1 + .06 * Math.sin(t * 2.2) + (Math.sin(t * 13) > .96 ? .12 : 0));
    ctx.fillStyle = 'rgba(14,10,30,.3)'; ctx.fillRect(0, 0, VW, VH);
    const g = ctx.createRadialGradient(px, py, 44 * br, px, py, 190 * br); g.addColorStop(0, 'rgba(6,2,14,0)'); g.addColorStop(.6, 'rgba(6,2,14,.28)'); g.addColorStop(1, 'rgba(4,0,10,.62)'); ctx.fillStyle = g; ctx.fillRect(0, 0, VW, VH);
    ctx.fillStyle = 'rgba(120,20,40,.05)'; ctx.fillRect(0, 0, VW, VH);
    for (let k = 0; k < 14; k++) { const nx = (Math.sin(t * .7 + k * 12.9) * .5 + .5) * VW, ny = (Math.sin(t * .5 + k * 7.3) * .5 + .5) * VH; ctx.fillStyle = 'rgba(0,0,0,.25)'; ctx.fillRect(nx, ny, 2, 6); }
  }
  ctx.restore();
  drawViewHud(); if (FP) drawFP();
  if (C.black && C.st === 'rise') { ctx.fillStyle = '#000'; ctx.fillRect(0, 0, VW, VH); }
  if (R.puzzle && R.puzzle.hud) { const cs = R.objects.filter(o => o.type === 'candle'), n = cs.filter(o => STATE.lit[o.id]).length; ctx.font = '11px sans-serif'; ctx.textAlign = 'left'; ctx.fillStyle = '#0008'; ctx.fillRect(6, 6, 70, 16); ctx.fillStyle = '#ffe6a0'; ctx.fillText(`촛불 ${n}/${cs.length}`, 12, 18); }
  if (STATE.flags.cabin_key) { ctx.fillStyle = '#0008'; ctx.fillRect(VW - 40, 6, 34, 16); ctx.fillStyle = '#e8c050'; ctx.fillRect(VW - 34, 11, 8, 5); ctx.fillRect(VW - 27, 13, 8, 2); ctx.fillRect(VW - 21, 13, 2, 4); }
  if (cut && cut.shot && shotImg && shotImg.complete && !cut.walking) {                                 // 지도 끝에 있는 그네: 길을 넘어갈 때와 같은 검은 도트 효과로 장면이 무너지듯 검게 사라졌다가 그네가 드러나고, 돌아올 때도 같은 효과
    const rr = G.rooms[cut.shot.room], tt = cut.t - .5, o = cut.out, h = cut.hold, Xs = rr.X0 + cut.shot.x + .5 * cut.shot.d, Ys = rr.Y0 - .5 * cut.shot.d - 10;
    const blk = (e) => { if (e <= 0) return; e = Math.min(1, e); ctx.fillStyle = '#000'; for (let i = 0; i < TRANK.length; i++) if (TRANK[i] < e * 1.1) ctx.fillRect((i % TCOLS) * TCELL, Math.floor(i / TCOLS) * TCELL, TCELL, TCELL); for (let g = 0; g < 4 * e && e < 1; g++) { ctx.fillStyle = 'rgba(0,0,0,.8)'; ctx.fillRect(0, Math.random() * VH, VW, 1 + Math.random() * 3); } };
    const shot = () => { ctx.save(); ctx.imageSmoothingEnabled = false; ctx.drawImage(shotImg, Math.round(VW / 2 - Xs * S), Math.round(VH / 2 - Ys * S), rr.CW * S, rr.CH * S); ctx.imageSmoothingEnabled = false; for (const q of rr.shotProps || []) if (q.im) ctx.drawImage(q.im, Math.round(VW / 2 + (rr.X0 + q.x + .5 * q.d - Xs) * S - q.w * S / 2), Math.round(VH / 2 + (rr.Y0 - .5 * q.d - q.z - Ys) * S - q.h * S), q.w * S, q.h * S); ctx.restore(); };
    if (tt >= o - 1.0 && tt < o) blk((tt - (o - 1.0)) / 1.0);                                          // 낙엽길이 검게 무너진다
    else if (tt >= o && tt < o + .9) { shot(); blk(1 - (tt - o) / .9); }                                // 그네가 도트로 드러난다
    else if (tt >= o + .9 && tt < o + h) shot();                                                         // 그네를 보여 준다
    else if (tt >= o + h && tt < o + h + .8) { shot(); blk((tt - o - h) / .8); }                         // 그네가 검게 무너진다
    else if (tt >= o + h + .8 && tt < o + h + 1.6) blk(1 - (tt - o - h - .8) / .8);                      // 낙엽길이 도트로 드러난다(카메라는 돌아오는 중)
  }
  if (cut) { const bh = Math.round(34 * cut.bar); ctx.fillStyle = '#000'; ctx.fillRect(0, 0, VW, bh); ctx.fillRect(0, VH - bh, VW, bh); }
  if (msg && msg.text) {                                            // 글자도 도트로: 작은 캔버스에 그려 문턱값으로 깎고 2배로 키운다
    mgX.clearRect(0, 0, 160, 24); mgX.font = 'bold 9px monospace'; mgX.textAlign = 'center'; mgX.fillStyle = '#fff'; mgX.fillText(msg.text, 80, 15);
    const mi = mgX.getImageData(0, 0, 160, 24), md = mi.data; for (let i = 0; i < md.length; i += 4) { const on = md[i + 3] > 110; md[i] = 255; md[i + 1] = 238; md[i + 2] = 208; md[i + 3] = on ? 255 : 0; } mgX.putImageData(mi, 0, 0);
    ctx.fillStyle = '#0b0910'; ctx.fillRect(40, VH - 38, 240, 28); ctx.imageSmoothingEnabled = false; ctx.drawImage(mgC, 0, VH - 46, 320, 48);
  }
  if (STATE.counts && STATE.counts.tool) { ctx.fillStyle = '#0008'; ctx.fillRect(VW - 52, 26, 46, 16); ctx.fillStyle = '#c8c8d4'; ctx.fillRect(VW - 46, 33, 14, 2); ctx.fillRect(VW - 34, 30, 4, 8); ctx.fillRect(VW - 46, 30, 3, 8); ctx.font = 'bold 9px monospace'; ctx.textAlign = 'left'; ctx.fillText('x' + STATE.counts.tool, VW - 26, 38); }   // 얻은 도구 개수(자동)   // 얻은 도구
  if (POEM) { ctx.fillStyle = 'rgba(8,6,12,.86)'; ctx.fillRect(0, 0, VW, VH); ctx.fillStyle = '#f2e8c8'; ctx.fillRect(48, 28, VW - 96, VH - 56); ctx.fillStyle = '#d8ccaa'; ctx.fillRect(48, 28, VW - 96, 3); ctx.fillStyle = '#3a2f26'; ctx.font = 'bold 11px monospace'; ctx.textAlign = 'center'; POEM.lines.forEach((ln, i) => ctx.fillText(ln, VW / 2, 56 + i * 20)); ctx.textAlign = 'left'; }
  drawLabel();
  drawTrans();
  if (fade > 0) { ctx.fillStyle = `rgba(${fadeCol},${fade})`; ctx.fillRect(0, 0, VW, VH); }
}

// ---------- 입력: 누른 화면 점 -> 바닥 좌표 ----------
const addItem = (k, n = 1) => { STATE.counts = STATE.counts || {}; STATE.counts[k] = (STATE.counts[k] || 0) + n; };      // 얻은 물건은 시스템이 개수를 센다
let POEM = null;                                                              // 쪽지에 적힌 글을 읽는 화면(누르면 닫힌다)
function onDown(ev) {
  if (POEM) { POEM = null; ev.preventDefault(); return; }
  if (cut) { ev.preventDefault(); showSkip(); return; }                                                                            // 컷씬 중에는 한 번 누르면 >> 가 나온다(그걸 눌러야 건너뛴다)
  if (fadeDir || trans || !R || (C.st === 'rise' && C.t < 2.15)) return; ev.preventDefault(); audio();
  if (FP) { const b = cv.getBoundingClientRect(); fpPress((ev.clientX - b.left) * VW / b.width, (ev.clientY - b.top) * VH / b.height); return; }
  const b = cv.getBoundingClientRect(), X = (ev.clientX - b.left) * VW / b.width / S - R.ox, Y = (ev.clientY - b.top) * VH / b.height / S - R.oy;
  let [x, d] = world(X, Y);
  x = Math.max(0, Math.min(R.W, x)); d = Math.max(0, Math.min(R.D, d));                // 벽이나 바깥을 눌러도 가장 가까운 바닥으로
  const dk_ = (R.exits || []).find((e) => { if (!e.dark) return false; if (e.dark[0] === 'rect') return x >= e.dark[1] && x <= e.dark[2] && d >= e.dark[3] && d <= e.dark[4]; const v = e.dark[0] === 'X' ? X : e.dark[0] === 'xg' ? X - R.X0 - (R.Y0 - Y) : 2 * (R.Y0 - Y); return v >= e.dark[1] && v <= e.dark[2]; });
  if (dk_) { audio(); P.act = null; const z = dk_.zone; if (dk_.dir === 'R' || dk_.dir === 'L') goTo((z[0] + z[1]) / 2, Math.max(z[2], Math.min(z[3], d))); else goTo(Math.max(z[0], Math.min(z[1], x)), (z[2] + z[3]) / 2); return; }   // 검게 사라지는 통로 표시 부분은 어디를 눌러도 그 통로로(누른 높이 그대로)
  const eh = (R.exits || []).filter((e) => e.hit && X >= e.hit[0] && X <= e.hit[2] && Y >= e.hit[1] && Y <= e.hit[3]).sort((p, q) => (p.hit[2] - p.hit[0]) * (p.hit[3] - p.hit[1]) - (q.hit[2] - q.hit[0]) * (q.hit[3] - q.hit[1]))[0];
  if (eh) { audio(); P.act = null; const z = eh.zone; goTo((z[0] + z[1]) / 2, (z[2] + z[3]) / 2); return; }            // 문·통로를 어느 부분이든 누르면 그 문까지 걸어가 다음 공간으로 넘어간다
  audio(); const o = R.objects.find(o => { if (o.reach === 0 || (o.need && !STATE.flags[o.need])) return false; const [ox, oy] = scr(o.x, o.d); return Math.hypot(X - ox, Y - (oy - (o.z || 0) - (o.h || 28) / 2)) < (o.rad || (o.type === 'note' || o.type === 'poem' || o.type === 'key' || o.type === 'book' ? 9 : 12)); });   // 등불 기둥 근처를 눌렀는가
  if (o) { P.act = o; goTo(o.x, o.d + 8); if (!P.path.length && sdist(P.x, P.d, o.x, o.d) < 14) { /* 이미 곁에 있다 */ } return; }
  P.act = null;                                                                                    // 맨바닥을 톡 눌러도 걷지 않는다(조이스틱으로만 움직인다)
}
function ripple(cx, cy) {                                                         // 눌린 곳 표시: 화면(캔버스) 안팎 어디든 누른 자리에 번지는 동그라미
  const e = document.createElement('div'); e.style.cssText = 'position:fixed;left:' + cx + 'px;top:' + cy + 'px;width:12px;height:12px;margin:-6px 0 0 -6px;border:2px solid #ffe3a0;border-radius:50%;background:rgba(255,227,160,.25);pointer-events:none;z-index:8;transition:transform .55s ease-out,opacity .55s ease-out;transform:scale(.4);opacity:1';
  document.body.appendChild(e); requestAnimationFrame(() => requestAnimationFrame(() => { e.style.transform = 'scale(3.2)'; e.style.opacity = '0'; })); setTimeout(() => e.remove(), 650);
}
document.addEventListener('pointerdown', (ev) => {
  if (ev.target.closest && ev.target.closest('button')) return;
  if (POEM || cut || FP) { ripple(ev.clientX, ev.clientY); onDown(ev); return; }                                     // 쪽지·컷씬·1인칭 화면은 예전처럼
  if (fadeDir || trans || !R || (C.st === 'rise' && C.t < 2.15)) return;
  audio(); JOY = { id: ev.pointerId, x0: ev.clientX, y0: ev.clientY, x: ev.clientX, y: ev.clientY, t0: performance.now(), moved: false, mag: 0, vx: 0, vy: 0 }; joyShow();      // 누르면 그 자리에 조이스틱이 나타난다
});   // 캔버스 밖(검은 여백)을 눌러도 그 방향으로 이동하고 표시가 뜬다
document.getElementById('dbg').addEventListener('click', () => { debug = !debug; });
function fit() { const k = Math.max(1, Math.floor(Math.min(innerWidth / VW, innerHeight / VH))); cv.style.width = VW * k + 'px'; cv.style.height = VH * k + 'px'; }
addEventListener('resize', fit); fit();

(async () => {
  for (const k in G.child) frames[k] = await img(G.child[k]);
  for (const k in (G.chaser || {})) chFrames[k] = await img(G.chaser[k]);
  if (G.adult) adultIm = await img(G.adult);
  const sk = (location.hash || '#city0').slice(1), st = G.starts[sk] || G.starts.city0 || G.starts.snow || Object.values(G.starts)[0];                  // 기본 시작: 초반 도시 띠의 첫 방
  await enter(st.room, [st.x, st.d]);
  let last = performance.now();
  const loop = (now) => { const dt = Math.min(.05, (now - last) / 1000); last = now; try { update(dt); draw(dt); } catch (e) { console.error(e); } requestAnimationFrame(loop); };
  requestAnimationFrame(loop);
  window.__game = { cutT: () => cut && +cut.t.toFixed(2), div: () => DIVX, zone: () => zone, cam, lead: () => +LEAD.v.toFixed(1), light: () => LS && LS.map((o) => +o.L.toFixed(2)), secIdx: () => R.sections ? secIdx(P.x) : -1, STATE, C, get FP() { return FP; }, fpOpen: (id) => { const o = R.objects.find(x => x.id === id); if (o) enterFP(o); return !!FP; }, fpTap: (id) => { const v = curView(); if (!v || !FP) return false; const h = fpHits(v).find(q => q.o.id === id); if (!h) return false; fpPress(h.x + h.w / 2, h.y + h.h / 2); return true; }, fpExit: () => fpPress(160, 226), curView, act: (id) => { const o = R.objects.find(x => x.id === id); if (o) actObj(o); return !!o; }, knockNow: () => VW_.kn.push(performance.now() / 1000), preview: async (k) => { STATE.riseKind = k; STATE.flags.met = false; STATE.real = 4; const sp = G.rooms.woods.chaser.spots[4]; await enter('woods', [sp[0] - 44, sp[1] - 8]); [C.x, C.d] = sp; C.st = 'rise'; C.t = 0; C.pl = null; C.preview = true; C.face = -1; P.dir = 'r'; msg = null; }, msg: () => msg && msg.text, tapObject: (o) => { P.act = o; goTo(o.x, o.d + 8); }, enter, start: (k) => { const s = G.starts[k]; return enter(s.room, [s.x, s.d]); }, P, goTo, get room() { return room; }, get R() { return R; }, setDebug: (v) => { debug = v; } };
})();
})();
