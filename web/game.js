// 역상 — 터치 이동 엔진 (시험판). 화면 320x240, 그림은 2배. 바닥 좌표 (x, d) <-> 화면: X = X0 + x + d/2, Y = Y0 - d/2.
(() => {
'use strict';
const G = window.GAME_DATA, cv = document.getElementById('c'), ctx = cv.getContext('2d');
const VW = 320, VH = 240, S = 2;            // 논리 화면, 그림 배율
const CELL = 2;                              // 길찾기 격자 한 칸 = 바닥 2px
const BODY = { rx: 5, rd: 2.5 };             // 아이 발 자리(가구와 벽에서 띄우는 여유)
const SPEED = 46;                            // 화면에서 느끼는 걸음 속도(그림 px/초)
const WALK_FPS = 7;
const DIRS = ['r', 'dr', 'd', 'dl', 'l', 'ul', 'u', 'ur'];   // 화면 각도 0도(오른쪽)부터 시계 방향 45도씩
let debug = false, room = null, R = null, fade = 0, fadeDir = 0, pending = null, marker = null, msg = null;
const P = { x: 0, d: 0, path: [], dir: 'd', moving: false, t: 0 };
const STATE = { lit: {}, solved: {}, seq: {}, flags: {}, got: {}, sw: {} };                                                  // 퍼즐 상태(방을 옮겨도 유지): 켠 등불
const C = { st: 'none', x: 0, d: 0, t: 0, path: [], rep: 0, flip: false };    // 추격자(나무 머리): hidden(나무인 척) -> rise(일어남) -> chase / wait(뒤따라 들어옴)
const CSPEED = 38, chFrames = {};
function setupChaser() {
  C.path = []; C.t = 0; C.rep = 0; C.tp = null; C.pl = null; C.face0 = false; C.preview = false;
  if (R.chaser && STATE.real === undefined) STATE.real = 2 + Math.floor(Math.random() * (R.chaser.spots.length - 2));   // 어느 나무가 진짜인지는 판마다 다르다
  if (R.chaser && !STATE.flags.met) { [C.x, C.d] = R.chaser.spots[STATE.real]; C.st = 'hidden'; }
  else if ((R.chase || R.chaser) && STATE.flags.met) { C.x = P.x; C.d = P.d; C.st = 'wait'; }
  else C.st = 'none';
}
function route(ax, ad, bx, bd) {
  if (clear(ax, ad, bx, bd)) return [[bx, bd]];
  const a = nearestFree(...cellOf(ax, ad)), b = nearestFree(...cellOf(bx, bd)); if (!a || !b) return []; const raw = astar(a[0], a[1], b[0], b[1]); return raw ? smooth(raw).slice(1) : [];
}
function updChaser(dt) {
  if (C.st === 'none') return false; C.t += dt;
  if (C.st === 'hidden') { if (sdist(P.x, P.d, C.x, C.d) < R.chaser.radius) { C.st = 'rise'; C.t = 0; C.pl = null; C.trail = []; P.path = []; P.act = null; marker = null; C.face = (P.x - C.x) + (P.d - C.d) / 2 < 0 ? -1 : 1; } }
  else if (C.st === 'rise' && (STATE.riseKind || 1) > 1) {                         // 등장 후보 2~6: 정해진 길이만큼 재생
    const K = STATE.riseKind, dur = RDUR[K];
    if (C.t > dur) { if (C.preview) C.t = dur; else { if (K >= 6) { const [ox, oy] = K === 7 ? blinkOff(dur, 4, 6) : blinkOff(dur), d = -2 * oy; C.x += ox - d / 2; C.d += d; } C.st = 'chase'; C.tp = null; C.t0 = -99; C.lt = 0; STATE.flags.met = true; msg = { text: '도망쳐야 한다', t: 1.6 }; } }
  }
  else if (C.st === 'rise') {
    const t = C.t; if (C.preview && t > 2.6) { C.t = 2.6; return false; }
    if (t >= 2.15 && !C.pl) { const q = sdist(C.x, C.d, P.x, P.d), k = Math.max(0, Math.min(16, q - 14)) / (q || 1); C.pl = [[C.x, C.d], [C.x + (P.x - C.x) * k, C.d + (P.d - C.d) * k]]; }
    if (C.pl && t < 2.6) { const k = ease((t - 2.15) / .35); C.x = C.pl[0][0] + (C.pl[1][0] - C.pl[0][0]) * k; C.d = C.pl[0][1] + (C.pl[1][1] - C.pl[0][1]) * k; }   // 마지막에 한 걸음 다가온다
    if (t > 2.6) { C.st = 'chase'; C.tp = null; C.t0 = C.t; C.lt = 0; C.pl = null; STATE.flags.met = true; msg = { text: '도망쳐야 한다', t: 1.6 }; }
  }
  else if (C.st === 'wait') { if (C.t >= .5 && !C.face0) { C.face0 = true; C.face = (P.x - C.x) + (P.d - C.d) / 2 < 0 ? -1 : 1; } if (C.t > 2.5) { C.st = 'chase'; C.tp = null; C.t0 = -99; C.lt = 0; } }
  else if (C.st === 'chase') {
    C.rep -= dt; if (C.rep <= 0) { C.rep = .4; C.path = route(C.x, C.d, P.x, P.d); }
    if (!C.tp || C.t > C.tp.until) { const r = Math.random(), u = Math.random();                 // 템포가 제멋대로: 뚝 멈춤 / 느릿느릿 / 보통 / 확 달려듦
      C.tp = r < .15 ? { v: 0, until: C.t + .3 + u * .5 } : r < .45 ? { v: .35 + u * .25, until: C.t + .6 + u * .9 } : r < .75 ? { v: .9 + u * .2, until: C.t + .6 + u * .8 } : { v: 1.8 + u * .6, until: C.t + .3 + u * .4 }; }
    C.an = (C.an || 0) + dt * (2 + C.tp.v * 7); C.lt = (C.lt || 0) + ((C.tp.v === 0 ? .52 : 0) - (C.lt || 0)) * Math.min(1, dt * 2.4);   // 멈출 때마다 고개가 천천히 기운다
    let left = CSPEED * dt * C.tp.v;                        // 걸음이 고르지 않다: 멈칫하다가 훅 다가온다
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
  if (head && head.a > 0) { ctx.globalAlpha *= head.a; ctx.translate(bend * S, -33 * S); ctx.rotate(head.ang); ctx.scale(head.sx / sx, 1 / sy); for (let r = 28; r >= 0; r -= 2) ctx.drawImage(im, 0, r, 30, 2, (-15 + w(r) * 1.3) * S, -(30 - r) * S, 30 * S, 2 * S + 1); }
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
const RDUR = { 2: 3.2, 3: 2.9, 4: 2.9, 5: 3.2, 6: 3.1, 7: 3.2 };
const nowS = () => performance.now() / 1000;
function rows(im, r0, r1, base, wob, kf) { const n = nowS(); for (let r = r1 - 2; r >= r0; r -= 2) { const k = kf ? kf(r) : 1; ctx.drawImage(im, 0, r, 30, 2, (-15 * k + (wob ? wob * Math.sin(r * .9 + n * 14) : 0)) * S, (r - base) * S, 30 * k * S, 2 * S + 1); } }   // 스프라이트의 r0~r1행을 2줄씩(base행이 y=0)
const trunk = (h, a) => { ctx.globalAlpha = a === undefined ? 1 : a; ctx.fillStyle = '#28222e'; ctx.fillRect(-1.5 * S, -h * S, 3 * S, h * S); ctx.fillStyle = '#463c4e'; ctx.fillRect(-1.5 * S, -h * S, S, h * S); ctx.globalAlpha = 1; };
const burst = (t, starts, len = .2) => { let p = 0, d = false; for (const s0 of starts) { if (t >= s0 + len) p += 1; else if (t >= s0) { p += Math.min(1, (Math.floor((t - s0) / .04) + 1) / 5); d = true; } } return [p / starts.length, d]; };
const skf = (d) => d ? 'w' + (1 + Math.floor(nowS() * 26) % 4) : 'idle';
function specks(X, Y, k, h) { for (let i = 0; i < 16 * k; i++) { ctx.fillStyle = Math.random() < .5 ? 'rgba(8,6,12,.8)' : 'rgba(216,204,196,.7)'; ctx.fillRect((R.ox + X - 22 + Math.random() * 44) * S, (R.oy + Y - (h || 72) * Math.random()) * S, S * (Math.random() < .2 ? 3 : 1), S); } for (let i = 0; i < 50 * k; i++) { ctx.fillStyle = 'rgba(200,200,210,.12)'; ctx.fillRect(Math.random() * VW, Math.random() * VH, 2, 2); } }
function blinkOff(t, sa = 3, sb = 5) { const [X, Y] = scr(C.x, C.d), [px, py] = scr(P.x, P.d), q = Math.hypot(px - X, py - Y) || 1, st = BLINKS.filter(b => t >= b + .08).length, m = st >= sb ? Math.max(0, q - 15) : st >= sa ? 8 : 0; return [(px - X) / q * m, (py - Y) / q * m, st]; }
const BLINKS = [.5, .95, 1.4, 1.85, 2.3, 2.7];
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
  } else if (K === 4) {                                                         // 접힌 몸 펴기: 허리에서 뒤로 반 접혀 머리가 발밑에 있다가, 상체가 뒤로 큰 호를 그리며 넘어와 선다. 머리는 내내 똑바로 이쪽을 본다
    const u = t < .6 ? 0 : t < 2.1 ? ease((t - .6) / 1.5) : 1, th = Math.PI * (1 - u), ca = 1 - ease((t - .25) / .35), mv = u > 0 && u < 1, im = chFrames[skf(mv && Math.floor(t / .18) % 2 === 0)], sy = 1 + .15 * ease((t - 2.2) / .4), wob = mv ? 1.6 : t < .6 ? 2 * t / .6 : .6; nz = t > .25 && t < 2.6 ? (mv ? .7 : .3) : 0;
    if (ca > 0) { trunk(52, ca); canopy(ca, 1); }
    ctx.save(); if (face < 0) ctx.scale(-1, 1); ctx.scale(1, sy); rows(im, 46, 64, 64, wob);
    ctx.translate(0, -18 * S); ctx.rotate(-th); rows(im, 30, 46, 46, wob);                                         // 상체: 엉덩이를 축으로 뒤로 넘어온다
    ctx.translate(0, -16 * S); ctx.rotate(th); ctx.globalAlpha = 1 - ca; rows(im, 0, 30, 30, wob * 1.3); ctx.restore();   // 머리: 방향은 그대로
  } else if (K === 5) {                                                         // 여럿이 하나로: 세 그루가 녹아 땅을 기어와 뭉치고, 위로 뽑히듯 늘어나 몸이 된다. 머리가 마지막에 벌어진다
    const OFF = [[-36, -5], [31, -9], [9, 13]], melt = ease(t / .6), [p, d] = burst(t, [.65, 1, 1.35], .22), up = ease((t - 1.65) / .7), bloom = ease((t - 2.45) / .6); nz = t > .2 && t < 3 ? (d ? .9 : .5) : 0;
    OFF.forEach(([ox, oy], i) => { const cx = ox * (1 - p), cy = oy * (1 - p); ctx.save(); ctx.translate(cx * S, cy * S);
      if (melt < 1) { ctx.save(); ctx.scale(1 + melt, 1 - melt); ctx.translate(2 * Math.sin(n * 14 + i) * melt * S, 0); trunk(46 + i * 4); canopy(1 - melt, 1); ctx.restore(); }
      if (melt > 0 && up < 1) { const w = (5 + 6 * melt) * (1 - up * .6), jx = d ? (Math.floor(n * 26 + i) % 2 ? 2 : -2) : 0; ctx.fillStyle = '#0e0b12'; ctx.beginPath(); ctx.ellipse(jx * S, 0, w * S, w * .36 * S, 0, 0, 6.3); ctx.fill(); ctx.strokeStyle = '#0e0b12'; ctx.lineWidth = S;
        for (let l = -2; l <= 2; l++) { if (!l) continue; const ph = d ? Math.sin(n * 60 + l + i) * 2 : 0; ctx.beginPath(); ctx.moveTo((jx + l * 2) * S, 0); ctx.lineTo((jx + l * (w / 2 + 2) + ph) * S, (l % 2 ? 3 : -3) * S); ctx.stroke(); } }
      ctx.restore(); });
    if (up > 0) { const sy = up < .7 ? 1.25 * up / .7 : 1.25 - .25 * (up - .7) / .3, kx = 1.7 - .7 * up; ctx.save(); if (face < 0) ctx.scale(-1, 1); ctx.scale(1, Math.max(.02, sy)); rows(chFrames.idle, 30, 64, 64, 3 - 2.3 * bloom, () => kx);
      if (bloom > 0) { ctx.translate(0, -34 * S); ctx.scale(bloom, .2 + .8 * bloom); rows(chFrames.idle, 0, 30, 30, 2.5 * (1 - bloom) + .6); } ctx.restore(); }
  } else if (K === 7) {                                                         // 3+6 껍질이 깜빡일 때마다 벌어진다: 생겨나는 게 아니라 안에 끼어 있던 것이 드러난다. 변화는 화면이 꺼진 사이에만 일어난다
    const [ox, oy, st] = blinkOff(t, 4, 6); C.black = BLINKS.some(b => t >= b && t < b + .08);
    const a = [0, .1, .46, 1.45][Math.min(3, st)] + (st > 0 && st < 3 ? .025 * Math.sin(n * 2.3) : 0), k = [0, .22, .62, 1][Math.min(3, st)];
    const bark = () => { for (const sg of [-1, 1]) { ctx.save(); ctx.translate(sg * (st ? 1 + 3 * Math.min(1, a * 2) : 0) * S, 0); ctx.rotate(sg * a); ctx.fillStyle = sg < 0 ? '#28222e' : '#3a3242'; ctx.fillRect((sg < 0 ? -2 : 0) * S, -52 * S, 2 * S, 52 * S); if (st) { ctx.fillStyle = '#0c0a10'; ctx.fillRect((sg < 0 ? 0 : -1) * S, -52 * S, S, 52 * S); }
      CAN.forEach(([cx, cy, rr, c], i) => { if ((i % 2 ? 1 : -1) !== sg) return; ctx.fillStyle = c; ctx.beginPath(); ctx.ellipse((cx + sg * (st ? 3 : 0)) * S, cy * S, rr * S, rr * .75 * S, 0, 0, 6.3); ctx.fill(); }); ctx.restore(); } };
    if (st >= 3) bark();                                                          // 쓰러진 껍질은 제자리에 남는다
    if (k > 0) { ctx.save(); ctx.translate(ox * S, oy * S); if (face < 0) ctx.scale(-1, 1); ctx.scale(1, st >= 6 ? 1.15 : 1); rows(chFrames[st === 4 ? 'w2' : 'idle'], 30, 64, 64, 0, () => k); ctx.translate(0, -34 * S); ctx.rotate(st >= 5 ? -1.22 : 0); rows(chFrames.idle, 0, 30, 30, 0, () => Math.min(1, k * 1.15)); ctx.restore(); }
    if (st < 3) bark();
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
  if ((C.st === 'rise' || C.st === 'hidden') && (STATE.riseKind || 1) > 1) return drawAlt(STATE.riseKind, C.st === 'hidden' ? 0 : C.t);
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
  else if (C.st === 'chase') {
    f = 'w' + (1 + Math.floor(C.an || 0) % 4); bend = C.tp ? Math.min(4, C.tp.v * 2) : 0; const back = 1 - ease((t - C.t0) / 2), fs = flip === (face < 0) ? 1 : -1;
    sy = 1 + .15 * back; head.ang = -1.22 * back * fs + (C.lt || 0); wob = 3 * Math.max(0, 1 - (t - C.t0) / .4);
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
function cellsOf(r, c) { const a = []; for (let j = 0; j < r.gh; j++) for (let i = 0; i < r.gw; i++) { const x = (i + .5) * CELL, d = (j + .5) * CELL; if (((x - c.x) / c.rx) ** 2 + ((d - c.d) / c.rd) ** 2 < 1) a.push(j * r.gw + i); } return a; }
const inCrack = (c, x, d, pad = 0) => ((x - c.x) / (c.rx + pad)) ** 2 + ((d - c.d) / (c.rd + pad)) ** 2 < 1;
function restoreCracks() { for (const c of R.cr) { if (c.st === 'broken') for (const k of c.cells) if (R.free0[k]) R.free[k] = 1; c.st = 'ok'; c.t = 0; } }
function respawn() { P.path = []; P.x = R.start[0]; P.d = R.start[1]; marker = null; cam.init = false; msg = { text: '얼음이 깨져 물에 빠졌다', t: 1.8 }; }
const cam = { x: 0, y: 0, init: false };                                   // 카메라(그림 px): 지도가 화면보다 크면 아이를 따라간다
function camTarget() {
  const [fx, fy] = scr(P.x, P.d), vw = VW / S, vh = VH / S, c = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
  return [R.CW <= vw ? -(vw - R.CW) / 2 : c(fx - vw / 2, 0, R.CW - vw), R.CH <= vh ? -(vh - R.CH) / 2 : c(fy - vh * .6, 0, R.CH - vh)];
}

const img = (src) => new Promise((ok) => { const i = new Image(); i.onload = () => ok(i); i.src = src; });
const scr = (x, d) => [R.X0 + x + d / 2, R.Y0 - d / 2];                    // 바닥 -> 그림 화소
const world = (X, Y) => { const d = (R.Y0 - Y) * 2; return [X - R.X0 - d / 2, d]; };
const sdist = (ax, ad, bx, bd) => Math.hypot((bx - ax) + (bd - ad) / 2, (bd - ad) / 2);   // 화면에서 보이는 거리

// ---------- 방 준비: 그림, 깊이 지도, 걸을 수 있는 격자 ----------
async function prepare(key) {
  const r = G.rooms[key]; if (r.ready) return r;
  r.name = key; r.im = await img(r.img); const dim = await img(r.depth);
  const oc = document.createElement('canvas'); oc.width = r.CW; oc.height = r.CH; const o = oc.getContext('2d'); o.drawImage(dim, 0, 0);
  const px = o.getImageData(0, 0, r.CW, r.CH).data; r.dep = new Float32Array(r.CW * r.CH);
  for (let i = 0; i < r.dep.length; i++) { const v = px[i * 4]; r.dep[i] = v === 255 ? 1e9 : v / 3 - 2; }
  r.gw = Math.ceil(r.W / CELL); r.gh = Math.ceil(r.D / CELL); r.free = new Uint8Array(r.gw * r.gh);
  for (let j = 0; j < r.gh; j++) for (let i = 0; i < r.gw; i++) r.free[j * r.gw + i] = walkable(r, (i + .5) * CELL, (j + .5) * CELL) ? 1 : 0;
  if (r.walk) {                                                                  // 지형 지도: 걸을 수 있는 칸 마스크(흰색)와 겹쳐 자른다
    const wim = await img(r.walk), wc = document.createElement('canvas'); wc.width = r.gw; wc.height = r.gh; const w = wc.getContext('2d'); w.drawImage(wim, 0, 0);
    const wd = w.getImageData(0, 0, r.gw, r.gh).data; for (let i = 0; i < r.free.length; i++) if (wd[i * 4] < 128) r.free[i] = 0;
  }
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

// ---------- 움직임 ----------
function update(dt) {
  if (fadeDir) {
    fade += fadeDir * dt / .22;
    if (fade >= 1 && pending) { fade = 1; const p = pending; pending = null; enter(p.to, p.spawn).then(() => { fadeDir = -1; }); fadeDir = 0; }
    if (fade <= 0) { fade = 0; fadeDir = 0; }
    return;
  }
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
      if (o.type === 'note') msg = { text: o.text, t: 3.6 };
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
    } else msg = { text: '조금 더 가까이 가야 한다', t: 1 };
  }
  if (!P.path.length) { P.moving = false; P.t = 0; return; }
  let left = SPEED * dt; P.moving = true; P.t += dt;
  while (left > 0 && P.path.length) {
    const [tx, td] = P.path[0], dist = sdist(P.x, P.d, tx, td);
    const sx = (tx - P.x) + (td - P.d) / 2, sy = -(td - P.d) / 2;                      // 화면에서의 이동 방향
    if (dist > .01) P.dir = DIRS[((Math.round(Math.atan2(sy, sx) / (Math.PI / 4)) % 8) + 8) % 8];
    if (dist <= left) { P.x = tx; P.d = td; P.path.shift(); left -= dist; }
    else { const k = left / dist; P.x += (tx - P.x) * k; P.d += (td - P.d) * k; left = 0; }
  }
  const e = inExit(R, P.x, P.d);
  if (e && !P.path.length) {
    if (e.need && !STATE.flags[e.need]) { if (!msg) { msg = { text: e.needMsg || '아직 열리지 않는다', t: 2.2 }; const z = e.zone; goTo((z[0] + z[1]) / 2, e.side === 'back' ? z[2] - 12 : (z[2] + z[3]) / 2 - 10); } }
    else if (e.to) { pending = e; fadeDir = 1; } else if (!msg) { msg = { text: e.endMsg || '여기서부터는 아직 만들지 않았어요', t: 2.6 }; P.path = []; const s = e.zone; goTo((s[0] + s[1]) / 2 + (e.side === 'left' ? 10 : e.side === 'right' ? -10 : 0), (s[2] + s[3]) / 2 + (e.side === 'front' ? 10 : e.side === 'back' ? -10 : 0)); }
  }
}
async function enter(key, spawn) { R = await prepare(key); room = key; P.x = spawn[0]; P.d = spawn[1]; P.path = []; marker = null; cam.init = false; setupChaser(); }

// ---------- 그리기: 방 -> 아이(가구 뒤에 있으면 깊이 지도로 가림) -> 표시 ----------
const sprC = document.createElement('canvas'), sprX = sprC.getContext('2d'); const frames = {};
function drawChild() {
  const [w, h] = G.childSize; sprC.width = w; sprC.height = h;
  const f = P.moving ? 'w' + (1 + (Math.floor(P.t * WALK_FPS) % 4)) : 'idle'; const im = frames[P.dir + '_' + f]; if (!im) return;
  sprX.clearRect(0, 0, w, h); sprX.drawImage(im, 0, 0);
  const [fx, fy] = scr(P.x, P.d), x0 = Math.round(fx - w / 2), y0 = Math.round(fy - h + 1);
  const id = sprX.getImageData(0, 0, w, h), a = id.data;
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const X = x0 + x, Y = y0 + y; if (X < 0 || Y < 0 || X >= R.CW || Y >= R.CH) continue;
    if (R.dep[Y * R.CW + X] < P.d - .5) a[(y * w + x) * 4 + 3] = 0;                   // 더 앞에 있는 가구가 덮는다
  }
  sprX.putImageData(id, 0, 0); ctx.drawImage(sprC, (R.ox + x0) * S, (R.oy + y0) * S, w * S, h * S);
}
function draw(dt) {
  ctx.imageSmoothingEnabled = false; ctx.fillStyle = '#1e1618'; ctx.fillRect(0, 0, VW, VH); if (!R) return;
  const cz = camZoom(); ctx.save(); if (cz !== 1) { ctx.translate(VW / 2, VH * .55); ctx.scale(cz, cz); ctx.translate(-VW / 2, -VH * .55); }
  const [tx, ty] = camTarget(); if (!cam.init) { cam.x = tx; cam.y = ty; cam.init = true; } else { const k = 1 - Math.exp(-(dt || .016) * 7); cam.x += (tx - cam.x) * k; cam.y += (ty - cam.y) * k; }
  R.ox = -Math.round(cam.x); R.oy = -Math.round(cam.y);
  ctx.drawImage(R.im, R.ox * S, R.oy * S, R.CW * S, R.CH * S);
  const dot = (x, d, c, r = 1) => { const [X, Y] = scr(x, d); ctx.fillStyle = c; ctx.fillRect((R.ox + X - r / 2) * S, (R.oy + Y - r / 2) * S, r * S, r * S); };
  if (debug) {
    for (let j = 0; j < R.gh; j++) for (let i = 0; i < R.gw; i++) dot((i + .5) * CELL, (j + .5) * CELL, R.free[j * R.gw + i] ? '#5f85' : '#f556');
    for (const e of R.exits) for (let x = e.zone[0]; x <= e.zone[1]; x += 2) for (let d = e.zone[2]; d <= e.zone[3]; d += 2) dot(x, d, '#fd4a');
    let px = P.x, pd = P.d; for (const [x, d] of P.path) { const n = Math.ceil(sdist(px, pd, x, d)); for (let k = 0; k <= n; k++) dot(px + (x - px) * k / n, pd + (d - pd) * k / n, '#fff'); px = x; pd = d; }
  }
  if (marker) {                                   // 누른 자리: 바닥에 퍼지는 고리
    const [X, Y] = scr(marker.x, marker.d), k = Math.min(1, marker.t / .35), rx = 2 + 5 * k; ctx.strokeStyle = `rgba(255,236,190,${.9 - .6 * k})`; ctx.lineWidth = S;
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
  for (const o of R.objects) {                                                  // 조작할 수 있는 사물: 엔진이 그림 위에 덧그린다
    const [X, Y0] = scr(o.x, o.d), cx = (R.ox + X) * S, cy = (R.oy + Y0 - (o.z || 0)) * S, sp = (Math.sin(tnow / 300 + o.x) + 1) / 2;
    const rect = (x, y, w, h, c) => { ctx.fillStyle = c; ctx.fillRect(cx + x * S, cy + y * S, w * S, h * S); };
    if (o.type === 'note') { rect(-4, -2, 8, 5, '#f2e8c8'); rect(-3, -1, 6, 1, '#b8a888'); rect(-3, 1, 4, 1, '#b8a888'); if (sp > .6) rect(4, -5, 1, 1, '#fff'); }
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
  if (C.d >= P.d) { drawChaser(); drawChild(); } else { drawChild(); drawChaser(); }
  if (R.mood === 'dark' || C.st === 'rise' || C.st === 'chase' || C.st === 'wait') {                                                     // 추격 구간의 꺼림칙한 분위기: 어둡게 가라앉히고, 아이 둘레만 흐릿하게 보이며, 가장자리가 맥박처럼 숨 쉰다
    const [fx0, fy0] = scr(P.x, P.d), rs = C.st === 'rise', [qx, qy] = rs ? scr(C.x, C.d - 30) : [fx0, fy0], fx = (fx0 + qx) / 2, fy = (fy0 + qy) / 2, px = (R.ox + fx) * S, py = (R.oy + fy - 14) * S, t = performance.now() / 1000, br = (rs ? 2.4 : 1) * (1 + .06 * Math.sin(t * 2.2) + (Math.sin(t * 13) > .96 ? .12 : 0));
    ctx.fillStyle = 'rgba(14,10,30,.38)'; ctx.fillRect(0, 0, VW, VH);
    const g = ctx.createRadialGradient(px, py, 18 * S * br, px, py, 70 * S * br); g.addColorStop(0, 'rgba(6,2,14,0)'); g.addColorStop(.6, 'rgba(6,2,14,.55)'); g.addColorStop(1, 'rgba(4,0,10,.93)'); ctx.fillStyle = g; ctx.fillRect(0, 0, VW, VH);
    ctx.fillStyle = 'rgba(120,20,40,.05)'; ctx.fillRect(0, 0, VW, VH);
    for (let k = 0; k < 14; k++) { const nx = (Math.sin(t * .7 + k * 12.9) * .5 + .5) * VW, ny = (Math.sin(t * .5 + k * 7.3) * .5 + .5) * VH; ctx.fillStyle = 'rgba(0,0,0,.25)'; ctx.fillRect(nx, ny, 2, 6); }
  }
  ctx.restore();
  if (C.black && C.st === 'rise') { ctx.fillStyle = '#000'; ctx.fillRect(0, 0, VW, VH); }
  if (R.puzzle && R.puzzle.hud) { const cs = R.objects.filter(o => o.type === 'candle'), n = cs.filter(o => STATE.lit[o.id]).length; ctx.font = '11px sans-serif'; ctx.textAlign = 'left'; ctx.fillStyle = '#0008'; ctx.fillRect(6, 6, 70, 16); ctx.fillStyle = '#ffe6a0'; ctx.fillText(`촛불 ${n}/${cs.length}`, 12, 18); }
  if (STATE.flags.cabin_key) { ctx.fillStyle = '#0008'; ctx.fillRect(VW - 40, 6, 34, 16); ctx.fillStyle = '#e8c050'; ctx.fillRect(VW - 34, 11, 8, 5); ctx.fillRect(VW - 27, 13, 8, 2); ctx.fillRect(VW - 21, 13, 2, 4); }
  if (msg) { ctx.font = '12px sans-serif'; ctx.textAlign = 'center'; ctx.fillStyle = '#000a'; ctx.fillRect(60, VH - 30, 200, 20); ctx.fillStyle = '#fed'; ctx.fillText(msg.text, VW / 2, VH - 16); }
  if (fade > 0) { ctx.fillStyle = `rgba(20,14,16,${fade})`; ctx.fillRect(0, 0, VW, VH); }
}

// ---------- 입력: 누른 화면 점 -> 바닥 좌표 ----------
function onDown(ev) {
  if (fadeDir || !R || (C.st === 'rise' && C.t < 2.15)) return; ev.preventDefault();
  const b = cv.getBoundingClientRect(), X = (ev.clientX - b.left) * VW / b.width / S - R.ox, Y = (ev.clientY - b.top) * VH / b.height / S - R.oy;
  let [x, d] = world(X, Y);
  x = Math.max(0, Math.min(R.W, x)); d = Math.max(0, Math.min(R.D, d));                // 벽이나 바깥을 눌러도 가장 가까운 바닥으로
  const o = R.objects.find(o => { const [ox, oy] = scr(o.x, o.d); return Math.hypot(X - ox, Y - (oy - (o.z || 0) - (o.h || 28) / 2)) < (o.type === 'note' || o.type === 'key' || o.type === 'book' ? 9 : 12); });   // 등불 기둥 근처를 눌렀는가
  if (o) { P.act = o; goTo(o.x, o.d + 8); if (!P.path.length && sdist(P.x, P.d, o.x, o.d) < 14) { /* 이미 곁에 있다 */ } return; }
  P.act = null; goTo(x, d);
}
cv.addEventListener('pointerdown', onDown);
document.getElementById('dbg').addEventListener('click', () => { debug = !debug; });
function fit() { const k = Math.max(1, Math.floor(Math.min(innerWidth / VW, innerHeight / VH))); cv.style.width = VW * k + 'px'; cv.style.height = VH * k + 'px'; }
addEventListener('resize', fit); fit();

(async () => {
  for (const k in G.child) frames[k] = await img(G.child[k]);
  for (const k in (G.chaser || {})) chFrames[k] = await img(G.chaser[k]);
  const sk = (location.hash || '#snow').slice(1), st = G.starts[sk] || G.starts.snow;
  await enter(st.room, [st.x, st.d]);
  let last = performance.now();
  const loop = (now) => { const dt = Math.min(.05, (now - last) / 1000); last = now; update(dt); draw(dt); requestAnimationFrame(loop); };
  requestAnimationFrame(loop);
  window.__game = { STATE, C, preview: async (k) => { STATE.riseKind = k; STATE.flags.met = false; STATE.real = 4; const sp = G.rooms.woods.chaser.spots[4]; await enter('woods', [sp[0] - 44, sp[1] - 8]); [C.x, C.d] = sp; C.st = 'rise'; C.t = 0; C.pl = null; C.preview = true; C.face = -1; P.dir = 'r'; msg = null; }, msg: () => msg && msg.text, tapObject: (o) => { P.act = o; goTo(o.x, o.d + 8); }, enter, start: (k) => { const s = G.starts[k]; return enter(s.room, [s.x, s.d]); }, P, goTo, get room() { return room; }, get R() { return R; }, setDebug: (v) => { debug = v; } };
})();
})();
