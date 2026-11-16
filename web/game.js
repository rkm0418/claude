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
async function enter(key, spawn) { R = await prepare(key); room = key; P.x = spawn[0]; P.d = spawn[1]; P.path = []; marker = null; cam.init = false; }

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
  drawChild();
  if (R.mood === 'dark') {                                                     // 추격 구간의 꺼림칙한 분위기: 어둡게 가라앉히고, 아이 둘레만 흐릿하게 보이며, 가장자리가 맥박처럼 숨 쉰다
    const [fx, fy] = scr(P.x, P.d), px = (R.ox + fx) * S, py = (R.oy + fy - 14) * S, t = performance.now() / 1000, br = 1 + .06 * Math.sin(t * 2.2) + (Math.sin(t * 13) > .96 ? .12 : 0);
    ctx.fillStyle = 'rgba(14,10,30,.38)'; ctx.fillRect(0, 0, VW, VH);
    const g = ctx.createRadialGradient(px, py, 18 * S * br, px, py, 70 * S * br); g.addColorStop(0, 'rgba(6,2,14,0)'); g.addColorStop(.6, 'rgba(6,2,14,.55)'); g.addColorStop(1, 'rgba(4,0,10,.93)'); ctx.fillStyle = g; ctx.fillRect(0, 0, VW, VH);
    ctx.fillStyle = 'rgba(120,20,40,.05)'; ctx.fillRect(0, 0, VW, VH);
    for (let k = 0; k < 14; k++) { const nx = (Math.sin(t * .7 + k * 12.9) * .5 + .5) * VW, ny = (Math.sin(t * .5 + k * 7.3) * .5 + .5) * VH; ctx.fillStyle = 'rgba(0,0,0,.25)'; ctx.fillRect(nx, ny, 2, 6); }
  }
  if (R.puzzle && R.puzzle.hud) { const cs = R.objects.filter(o => o.type === 'candle'), n = cs.filter(o => STATE.lit[o.id]).length; ctx.font = '11px sans-serif'; ctx.textAlign = 'left'; ctx.fillStyle = '#0008'; ctx.fillRect(6, 6, 70, 16); ctx.fillStyle = '#ffe6a0'; ctx.fillText(`촛불 ${n}/${cs.length}`, 12, 18); }
  if (STATE.flags.cabin_key) { ctx.fillStyle = '#0008'; ctx.fillRect(VW - 40, 6, 34, 16); ctx.fillStyle = '#e8c050'; ctx.fillRect(VW - 34, 11, 8, 5); ctx.fillRect(VW - 27, 13, 8, 2); ctx.fillRect(VW - 21, 13, 2, 4); }
  if (msg) { ctx.font = '12px sans-serif'; ctx.textAlign = 'center'; ctx.fillStyle = '#000a'; ctx.fillRect(60, VH - 30, 200, 20); ctx.fillStyle = '#fed'; ctx.fillText(msg.text, VW / 2, VH - 16); }
  if (fade > 0) { ctx.fillStyle = `rgba(20,14,16,${fade})`; ctx.fillRect(0, 0, VW, VH); }
}

// ---------- 입력: 누른 화면 점 -> 바닥 좌표 ----------
function onDown(ev) {
  if (fadeDir || !R) return; ev.preventDefault();
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
  const sk = (location.hash || '#snow').slice(1), st = G.starts[sk] || G.starts.snow;
  await enter(st.room, [st.x, st.d]);
  let last = performance.now();
  const loop = (now) => { const dt = Math.min(.05, (now - last) / 1000); last = now; update(dt); draw(dt); requestAnimationFrame(loop); };
  requestAnimationFrame(loop);
  window.__game = { STATE, msg: () => msg && msg.text, tapObject: (o) => { P.act = o; goTo(o.x, o.d + 8); }, enter, start: (k) => { const s = G.starts[k]; return enter(s.room, [s.x, s.d]); }, P, goTo, get room() { return room; }, get R() { return R; }, setDebug: (v) => { debug = v; } };
})();
})();
