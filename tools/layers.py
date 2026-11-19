#!/usr/bin/env python3
"""레이어(몸 가림) 규칙 — 한곳에 모은 계산과 검사. 규칙 설명: docs/layer-rules.md

사선 투영 X = X0 + x + .5d, Y = Y0 - .5d - z 에서 한 화소를 지나는 시선 위의 점은 d 가 작을수록 보는 사람에게 가깝다.
그래서 '화소마다 보이는 면의 d'(Scene.zb) 하나만 있으면 앞면·윗면·오른쪽 면 어느 쪽이든 정확히 가린다:
엔진은 아이 그림의 화소마다 zb < 아이 d - .5 이면 그 화소를 지운다.

남은 문제는 아이 몸(세로로 선 납작한 판: 가로 x-7.5..x+7, 높이 0..24, 깊이 d)이 물체 속으로 파고드는 것뿐이다.
파고들면 몸 일부가 물체 면에 잘려 '가려지면 안 되는데 가려지는' 것처럼 보인다. 그래서 걷는 칸을 만들 때
몸이 어떤 단단한 물체·벽 면과도 겹치지 않는 칸만 남긴다(body_blocked).

사용:
  from layers import walk_grid              # build_plaza.room() 이 쓴다
  python3 tools/layers.py                   # 모든 방 검사(겹침·그리는 순서·출발점), 문제 있으면 0 이 아닌 값으로 끝난다
"""
import math, os, sys
import numpy as np

CELL = 2                      # 걷기 격자 한 칸(논리 화소)
BODY_L, BODY_R = 7.5, 7.0     # 아이 그림(14px)이 발 중심에서 왼쪽·오른쪽으로 차지하는 폭
BODY_H = 24                   # 아이 키
STEP = 4                      # 이 높이 이하(연석·턱·바닥 무늬)는 걸음을 막지 않는다: 넘어 다닌다
CELL_SLACK = 1.0              # 한 칸 안에서 발이 움직일 수 있는 여유(칸 중심 ±1)


def _range(lo, hi, n):
    """칸 중심 (i+.5)*CELL 이 열린 구간 (lo, hi) 안에 드는 i 범위."""
    a = max(0, int(math.floor(lo / CELL - .5)) + 1); b = min(n - 1, int(math.ceil(hi / CELL - .5)) - 1)
    return a, b


def _minus(a0, a1, holes):
    """구간 [a0,a1] 에서 구멍들을 뺀 조각들."""
    segs = [(a0, a1)]
    for h0, h1 in holes:
        out = []
        for s0, s1 in segs:
            if h1 <= s0 or h0 >= s1: out.append((s0, s1)); continue
            if s0 < h0: out.append((s0, h0))
            if h1 < s1: out.append((h1, s1))
        segs = out
    return segs


def body_blocked(s, W, D):
    """몸이 단단한 물체(s.log 상자)나 키 STEP 보다 높은 면(s.faces)과 겹치는 칸 = True. 구멍(s.holes)에 든 면은 막지 않는다."""
    gw, gh = math.ceil(W / CELL), math.ceil(D / CELL); B = np.zeros((gh, gw), bool); sl = CELL_SLACK
    def mark(x0, x1, d0, d1):                       # 몸 판이 x 로 [x0,x1], d 로 (d0,d1) 와 겹치는 칸
        i0, i1 = _range(x0 - BODY_R - sl, x1 + BODY_L + sl, gw); j0, j1 = _range(d0 - sl, d1 + sl, gh)
        if i0 <= i1 and j0 <= j1: B[j0:j1 + 1, i0:i1 + 1] = True
    for (x, d, w, dp, h, z0) in s.log:                                   # 상자(부피): 몸 판이 상자 속을 지나면 겹친다
        if z0 + h <= STEP or z0 >= BODY_H: continue
        mark(x, x + w, d, d + dp)
    hx = {}; hd = {}
    for ax, v, a0, a1 in s.holes: (hx if ax == 'x' else hd).setdefault(round(v, 3), []).append((a0, a1))
    for f in s.faces:
        ax, v, a0, a1, b0, b1 = f
        if ax == 'z':
            if not (STEP < v < BODY_H): continue
            mark(a0, a1, b0, b1)
        else:
            if b1 <= STEP or b0 >= BODY_H: continue
            for p0, p1 in _minus(a0, a1, (hx if ax == 'x' else hd).get(round(v, 3), [])):
                if p1 - p0 < 1e-6: continue
                if ax == 'x': mark(v, v, p0, p1)                         # 세로 벽(x 고정): 몸 판이 그 x 를 가로지르면
                else: mark(p0, p1, v, v)                                 # 정면 벽(d 고정): 몸 판이 그 d 에 있으면
    return B


def walk_grid(s, W, D, free, exits):
    """걷는 칸: 바닥 모양(free) ∩ 몸이 아무것과도 겹치지 않는 칸. 출구 칸은 언제나 걸을 수 있다(출구 앞이 고립되지 않게)."""
    gw, gh = math.ceil(W / CELL), math.ceil(D / CELL)
    xs = (np.arange(gw) + .5) * CELL; ds = (np.arange(gh) + .5) * CELL
    F = np.array([[bool(free(x, d)) for x in xs] for d in ds])
    Z = np.zeros((gh, gw), bool)
    for e in exits:
        z = e['zone']; Z |= (xs[None, :] >= z[0]) & (xs[None, :] <= z[1]) & (ds[:, None] >= z[2]) & (ds[:, None] <= z[3])
    return (F & ~body_blocked(s, W, D)) | Z, Z


# ---------------- 검사 ----------------
def check_room(key, s, walk, zone, start, spawns):
    """문제 목록을 돌려준다. (1) 걷는 칸에서 몸이 물체와 겹침 (2) 그리는 순서가 틀려 뒤의 것이 앞의 것을 덮은 곳(몸이 닿는 화면 범위만)
    (3) 출발점·도착점이 걷는 칸이 아님 (4) 출구 칸에 닿을 수 없음."""
    probs = []
    gh, gw = walk.shape; B = body_blocked(s, gw * CELL, gh * CELL)
    bad = walk & B & ~zone
    if bad.any():
        j, i = np.argwhere(bad)[0]; probs.append('%s: 몸이 물체와 겹치는 걷는 칸 %d개 (예: x=%.0f d=%.0f)' % (key, bad.sum(), (i + .5) * CELL, (j + .5) * CELL))
    # 그리는 순서: 아이가 설 수 있는 칸마다, 몸 그림이 덮는 화소에서 '그림대로 가림(zb)' 과 '가장 앞 면으로 가림(zmin)' 이 다르면
    # 그리는 순서가 틀려 뒤의 것이 앞의 것을 덮은 곳이다(아이가 실제로 잘못 가려지거나 드러난다).
    wrong = []
    for j, i in np.argwhere(walk & ~zone):
        x, d = (i + .5) * CELL, (j + .5) * CELL; fx, fy = s.X0 + x + .5 * d, s.Y0 - .5 * d
        X0_, Y0_ = int(round(fx - 7)), int(round(fy - BODY_H + 1)); a_ = s.zb[max(0, Y0_):int(round(fy)) + 1, max(0, X0_):X0_ + 14]; b_ = s.zmin[max(0, Y0_):int(round(fy)) + 1, max(0, X0_):X0_ + 14]
        n = int(((a_ < d - .5) != (b_ < d - .5)).sum())
        if n > 2: wrong.append((n, x, d))
    if wrong:
        n, x, d = max(wrong); probs.append('%s: 그리는 순서 때문에 몸이 잘못 가려지는 칸 %d개 (가장 심한 곳 x=%.0f d=%.0f, %d화소)' % (key, len(wrong), x, d, n))
    for nm, p in [('출발점', start)] + [('도착점(' + a + ')', q) for a, q in spawns]:
        i, j = int(p[0] // CELL), int(p[1] // CELL)
        if not (0 <= i < gw and 0 <= j < gh and walk[j, i]): probs.append('%s: %s %s 이 걷는 칸이 아님' % (key, nm, p))
    # 연결: 출발점에서 모든 출구 칸에 닿는가
    from collections import deque
    i, j = int(start[0] // CELL), int(start[1] // CELL); seen = np.zeros_like(walk)
    if 0 <= i < gw and 0 <= j < gh and walk[j, i]:
        q = deque([(j, i)]); seen[j, i] = True
        while q:
            a, b = q.popleft()
            for da, db in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                na, nb = a + da, b + db
                if 0 <= na < gh and 0 <= nb < gw and walk[na, nb] and not seen[na, nb]: seen[na, nb] = True; q.append((na, nb))
    return probs, seen


def check_dirs(rooms):
    """공간 연결 방향 규칙: 어느 방향(dir)으로 나갔으면 다음 방에는 그 방향 그대로 들어와야 한다.
    R(+x로 나감) → 다음 방 왼쪽 끝에서 시작, L → 오른쪽 끝, B(+d, 위로 나감) → 아래(앞) 끝, F → 위(뒤) 끝.
    또 출구 자체도 그 방향 쪽 끝에 있어야 한다. 방향이 꺾이는 연결(가로↔세로 방)은 출구에 turn=True 를 적어 예외로 표시한다."""
    probs = []; ext = {}
    for k, (g, w, z, st, ex, sp) in rooms.items():
        ys, xs = np.nonzero(w & ~z); ext[k] = (xs.min() * CELL, xs.max() * CELL, ys.min() * CELL, ys.max() * CELL)
    def frac(v, lo, hi): return .5 if hi <= lo else (v - lo) / float(hi - lo)
    for k, (g, w, z, st, ex, sp) in rooms.items():
        for e in ex:
            dr = e.get('dir'); to = e.get('to'); sw = e.get('spawn')
            if not dr: continue
            x0, x1, d0, d1 = ext[k]; zc = ((e['zone'][0] + e['zone'][1]) / 2, (e['zone'][2] + e['zone'][3]) / 2)
            fx, fd = frac(zc[0], x0, x1), frac(zc[1], d0, d1)
            ok = {'R': fx >= .65, 'L': fx <= .35, 'B': fd >= .65, 'F': fd <= .35}[dr]
            if not ok: probs.append('%s: 출구(→%s, dir=%s)가 그 방향 쪽 끝에 있지 않음' % (k, to, dr))
            if to and sw and not e.get('turn'):
                a0, a1, b0, b1 = ext[to]; tx, td = frac(sw[0], a0, a1), frac(sw[1], b0, b1)
                ok2 = {'R': tx <= .35, 'L': tx >= .65, 'B': td <= .35, 'F': td >= .65}[dr]
                if not ok2: probs.append('%s → %s: %s 로 나갔는데 다음 방에는 반대쪽 끝에서 시작하지 않음(spawn=%s). 가로↔세로로 꺾이는 연결이면 출구에 turn=True' % (k, to, dr, sw))
    return probs


def main():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import build_plaza
    rooms = build_plaza.build(check=True)
    allp = []
    for key, (s, walk, zone, start, exits, spawns) in rooms.items():
        probs, seen = check_room(key, s, walk, zone, start, spawns)
        for e in exits:
            z = e['zone']; gh, gw = walk.shape
            xs = (np.arange(gw) + .5) * CELL; ds = (np.arange(gh) + .5) * CELL
            m = (xs[None, :] >= z[0]) & (xs[None, :] <= z[1]) & (ds[:, None] >= z[2]) & (ds[:, None] <= z[3])
            if not (seen & m).any(): probs.append('%s: 출구(→%s) 에 걸어서 닿을 수 없음' % (key, e.get('to')))
        print(('OK  ' if not probs else 'XX  ') + key); [print('    ' + p) for p in probs]; allp += probs
    dp = check_dirs(rooms); print(('OK  ' if not dp else 'XX  ') + '방 연결 방향'); [print('    ' + p) for p in dp]; allp += dp
    print('문제 %d개' % len(allp)); sys.exit(1 if allp else 0)

if __name__ == '__main__': main()
