#!/usr/bin/env python3
"""추락 이후 밤 도시 — 처음 집(방·복도·베란다)과 같은 사선 3차원 시점. 투영 X = X0 + x + .5d, Y = Y0 - .5d - z.
보이는 면: 앞면, 윗면, 오른쪽 면. 왼쪽은 건물 벽(안쪽 면이 보임), 오른쪽·앞은 잘라낸 단면.
장면 1: 광장(인공 수풀 화단에서 시작, 오른쪽이 출구)  장면 2: 세로로 긴 거리(인도 | 도로 | 인도, 도로 위 표시 네 개).
사용: python3 tools/render_city3d.py -> maps/out/city3d_landing.png, city3d_street.png, city3d_overview.png (+ _x2)"""
import math, os, random, sys
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from render_city import hedge, WIN_OFF, WIN_W, WIN_B, WALL, WALLD
OUT = os.path.join(HERE, '..', 'maps', 'out'); SPR = os.path.join(HERE, '..', 'art', 'out', 'sprites')
PAVE, PAVE2, JOINT = (44, 48, 72), (38, 42, 64), (28, 31, 50)
ASPH, ASPH2 = (26, 28, 42), (30, 32, 48)
CURBT, CURBF, CURBR = (96, 100, 130), (66, 70, 96), (52, 56, 80)
LAMPC = (255, 214, 140); PAINT = (214, 214, 196); POLE = (58, 62, 88)
def dk(c, f): return tuple(int(v * f) for v in c)

def grad(s, quad, h, k):                                                        # 벽 세로 그라데이션: 바닥 쪽은 연하고 위로 갈수록 어둡게
    n = int(h)
    for i in range(n):
        f = i / max(1, n - 1); c = tuple(int(v * k * .72) for v in WALL); s.poly(quad(i * h / n, (i + 1) * h / n + .6), c)

class Scene:
    def __init__(s, W, D, H, pad=8, k=1):                                                    # k: 그림 해상도 배율(2면 도트가 절반 크기, 좌표·크기는 그대로)
        s.W, s.D, s.pad, s.k = W, D, pad, k; s.CW = int(W + .5 * D + pad * 2); s.CH = int(H + .5 * D + pad * 2)
        s.X0, s.Y0 = pad, s.CH - pad
        s.img = Image.new('RGB', (s.CW * k, s.CH * k), (12, 14, 30)); s.d = ImageDraw.Draw(s.img); s.px = s.img.load()
        s.jobs = []                                     # (깊이, 그리기 함수) — 먼 것부터
        # ---- 레이어(몸 가림) 규칙의 바탕: docs/layer-rules.md ----
        # zb: 논리 화소마다 '지금 그림에 보이는 면'의 깊이 d (그리는 순서대로 덮어쓴다 = 그림과 똑같다). 아이는 zb < 아이 d 인 화소에서 가려진다.
        # zmin: 같은 화소의 모든 면 중 가장 앞(d 최소) — zb 와 다르면 그리는 순서가 틀린 곳(검사기가 찾아낸다).
        s.zb = np.full((s.CH, s.CW), 1e9); s.zmin = np.full((s.CH, s.CW), 1e9)
        s.log = []                                      # 단단한 물체(상자) (x,d,w,dp,h,z0): 아이 몸이 겹치지 않게 걷는 곳을 자동으로 막는다
        s.faces = []                                    # 그린 평면 (축, 값, a0, a1, b0, b1): 'x' 면은 (d0,d1,z0,z1), 'd' 면은 (x0,x1,z0,z1), 'z' 면은 (x0,x1,d0,d1)
        s.holes = []                                    # 벽에 뚫린 구멍 (축, 값, a0, a1): 이 범위의 같은 면은 걸음을 막지 않는다(골목·비상구 입구)
    def P1(s, x, d, z=0): return (round(s.X0 + x + .5 * d), round(s.Y0 - .5 * d - z))          # 논리 좌표(깊이 지도용)
    def P(s, x, d, z=0): return (round((s.X0 + x + .5 * d) * s.k), round((s.Y0 - .5 * d - z) * s.k))
    def poly(s, pts, col, z=True):                                                              # z=False: 면이 아니라 그림자·어둠을 칠한 것(깊이를 남기지 않는다)
        s.d.polygon([s.P(*p) for p in pts], fill=col)
        if z: s.zpoly(pts)
    def zpunch(s, pts): s.zpoly(pts, face=False, punch=True)                                     # 벽에 구멍을 낸다: 그 자리의 깊이를 비운다(뒤에 그리는 구멍 안쪽이 채운다)
    def zpoly(s, pts, face=True, punch=False):
        """평면 다각형 하나의 깊이를 zb 에 덮어쓴다(그리지는 않는다). 화면 화소 (X,Y) 를 지나는 시선 위 점은 x = X-X0-.5d, z = Y0-Y-.5d.
        시선을 따라 앞(보는 사람 쪽)으로 갈수록 d 가 작아지므로, 같은 화소에서 d 가 작은 면이 앞이다 — 앞면·윗면·오른쪽 면 모두 정확하다."""
        if len(pts) < 3: return
        q = [(s.X0 + x + .5 * d, s.Y0 - .5 * d - z) for (x, d, z) in pts]
        X0b, X1b = int(math.floor(min(a for a, _ in q))), int(math.ceil(max(a for a, _ in q))); Y0b, Y1b = int(math.floor(min(b for _, b in q))), int(math.ceil(max(b for _, b in q)))
        X0c, Y0c, X1c, Y1c = max(0, X0b), max(0, Y0b), min(s.CW, X1b + 1), min(s.CH, Y1b + 1)
        if X1c <= X0c or Y1c <= Y0c: return
        p0 = np.array(pts[0], float); n = None
        for i in range(1, len(pts) - 1):
            c = np.cross(np.array(pts[i], float) - p0, np.array(pts[i + 1], float) - p0)
            if np.abs(c).max() > 1e-9: n = c; break
        if n is None: return
        a, b, c = n; e = float(n @ p0); den = b - .5 * (a + c)
        if abs(den) < 1e-9: return                                                                 # 시선과 나란한 면(화면에서 선) — 깊이 없음
        PX, PY = np.meshgrid(np.arange(X0c, X1c) + .5, np.arange(Y0c, Y1c) + .5)                   # 화소 중심이 다각형 안에 드는가(바닥 floor() 와 같은 기준)
        area = sum(q[i][0] * q[(i + 1) % len(q)][1] - q[(i + 1) % len(q)][0] * q[i][1] for i in range(len(q)))
        if abs(area) < 1e-9: return
        cr = [(q[(i + 1) % len(q)][0] - q[i][0]) * (PY - q[i][1]) - (q[(i + 1) % len(q)][1] - q[i][1]) * (PX - q[i][0]) for i in range(len(q))]
        convex = all(((q[(i + 1) % len(q)][0] - q[i][0]) * (q[(i + 2) % len(q)][1] - q[i][1]) - (q[(i + 1) % len(q)][1] - q[i][1]) * (q[(i + 2) % len(q)][0] - q[i][0])) * area >= -1e-9 for i in range(len(q)))
        if convex: mk = np.all([(c_ * area >= -1e-9) for c_ in cr], axis=0)
        else:
            m = Image.new('L', (X1c - X0c, Y1c - Y0c), 0); ImageDraw.Draw(m).polygon([(u - X0c - .5, v - Y0c - .5) for u, v in q], fill=1); mk = np.array(m, bool)
        if not mk.any(): return
        Xs = np.arange(X0c, X1c) + .5 - s.X0; Ys = s.Y0 - (np.arange(Y0c, Y1c) + .5)
        dv = (e - a * Xs[None, :] - c * Ys[:, None]) / den
        zb = s.zb[Y0c:Y1c, X0c:X1c]; zm = s.zmin[Y0c:Y1c, X0c:X1c]
        if punch: zb[mk] = 1e9; zm[mk] = 1e9; return
        zb[mk] = dv[mk]; np.minimum(zm, np.where(mk, dv, 1e9), out=zm)
        if face:
            xs, ds, zs = [p_[0] for p_ in pts], [p_[1] for p_ in pts], [p_[2] for p_ in pts]
            if max(xs) - min(xs) < 1e-6: s.faces.append(('x', xs[0], min(ds), max(ds), min(zs), max(zs)))
            elif max(ds) - min(ds) < 1e-6: s.faces.append(('d', ds[0], min(xs), max(xs), min(zs), max(zs)))
            elif max(zs) - min(zs) < 1e-6: s.faces.append(('z', zs[0], min(xs), max(xs), min(ds), max(ds)))
    def zbox(s, x, d, w, dp, h, z0=0, solid=True):
        """그림 없이 상자 깊이만 기록(선·점으로 그린 기둥 같은 것에 쓴다). solid 면 걷는 곳도 막는다."""
        if solid: s.log.append((x, d, w, dp, h, z0))
        for f in ([(x, d, z0 + h), (x + w, d, z0 + h), (x + w, d + dp, z0 + h), (x, d + dp, z0 + h)], [(x, d, z0), (x + w, d, z0), (x + w, d, z0 + h), (x, d, z0 + h)], [(x + w, d, z0), (x + w, d + dp, z0), (x + w, d + dp, z0 + h), (x + w, d, z0 + h)]): s.zpoly(f, face=False)
    def zsphere(s, cx, cd, cz, r):
        """둥근 덩어리(수풀 등)의 깊이: 화소마다 시선과 구의 가장 앞 교점."""
        C = np.array([cx, cd, cz], float); X, Y = s.X0 + cx + .5 * cd, s.Y0 - .5 * cd - cz; R = int(r * 1.6) + 2
        X0c, Y0c, X1c, Y1c = max(0, int(X) - R), max(0, int(Y) - R), min(s.CW, int(X) + R + 1), min(s.CH, int(Y) + R + 1)
        Xs, Ys = np.meshgrid(np.arange(X0c, X1c) + .5 - s.X0, s.Y0 - (np.arange(Y0c, Y1c) + .5))
        wx, wd, wz = Xs - C[0], -C[1], Ys - C[2]                                                    # 시선의 d=0 점 - 중심
        B = 2 * (wx - 2 * wd + wz); Cc = wx ** 2 + wd ** 2 + wz ** 2 - r * r; disc = B * B - 24 * Cc
        hit = disc >= 0; t = (-B + np.sqrt(np.where(hit, disc, 0))) / 12.0; dv = -2 * t
        zb = s.zb[Y0c:Y1c, X0c:X1c]; np.minimum(zb, np.where(hit, dv, 1e9), out=zb); zm = s.zmin[Y0c:Y1c, X0c:X1c]; np.minimum(zm, np.where(hit, dv, 1e9), out=zm)   # 둥근 덩어리끼리는 가장 앞 면(그리는 순서로는 정확히 못 맞춘다)
    def zclear(s, mask_img):
        """붙여 넣은 구멍(골목 안쪽 등) 자리: 그 뒤는 먼 곳이라 아무것도 가리지 않는다."""
        m = np.array(mask_img.resize((s.CW, s.CH), Image.NEAREST), bool) if mask_img.size != (s.CW, s.CH) else np.array(mask_img, bool)
        s.zb[m] = 1e9; s.zmin[m] = 1e9
    def depth_rgb(s):
        """엔진용 깊이 지도(16비트: R*256+G = (d+64)*50, 65535 = 가리는 것 없음)."""
        v = np.where(s.zb >= 1e8, 65535, np.clip(np.round((s.zb + 64) * 50), 0, 65534)).astype(np.uint32)
        return Image.fromarray(np.stack([(v >> 8).astype(np.uint8), (v & 255).astype(np.uint8), np.zeros_like(v, np.uint8)], -1), 'RGB')
    def floor(s, fn, x0=0, x1=None, d0=0, d1=None, z=0):
        """바닥(높이 z) 영역을 화소마다 칠한다. fn(x, d) -> 색 또는 None."""
        x1 = s.W if x1 is None else x1; d1 = s.D if d1 is None else d1; k = s.k; IW, IH = s.img.size
        for Y in range(int((s.Y0 - .5 * d1 - z) * k) - 1, int((s.Y0 - .5 * d0 - z) * k) + 2):
            d = (s.Y0 - z - (Y + .5) / k) / .5
            if not (d0 <= d < d1): continue
            for X in range(int((s.X0 + x0) * k), int((s.X0 + x1 + .5 * d1) * k) + 2):
                x = (X + .5) / k - s.X0 - .5 * d
                if x0 <= x < x1 and 0 <= X < IW and 0 <= Y < IH:
                    c = fn(x, d)
                    if c: s.px[X, Y] = c
        Xs, Ys = np.meshgrid(np.arange(s.CW) + .5 - s.X0, np.arange(s.CH) + .5)                  # 바닥 깊이도 그림처럼 덮어쓴다(바닥은 아이를 가리지 않지만 앞서 그린 것을 덮는다)
        dv = 2 * (s.Y0 - z - Ys); xv = Xs - .5 * dv; m = (xv >= x0) & (xv < x1) & (dv >= d0) & (dv < d1); s.zb[m] = dv[m]; np.minimum(s.zmin, np.where(m, dv, 1e9), out=s.zmin)
    def glow(s, x, d, r, col=LAMPC, power=.5, z=0):
        cx, cy = s.P(x, d, z); r = r * s.k; IW, IH = s.img.size
        for Y in range(max(0, cy - r // 2 - 1), min(IH, cy + r // 2 + 2)):
            for X in range(max(0, cx - r), min(IW, cx + r + 1)):
                q = math.hypot(X - cx, (Y - cy) * 2)
                if q < r:
                    f = round((1 - q / r) ** 2.2 * power * 8) / 8; p = s.px[X, Y]
                    s.px[X, Y] = tuple(int(p[i] + (col[i] - p[i]) * f) for i in range(3))
    def box(s, x, d, w, dp, h, top, front, right, z0=0):
        s.log.append((x, d, w, dp, h, z0))
        s.poly([(x, d, z0 + h), (x + w, d, z0 + h), (x + w, d + dp, z0 + h), (x, d + dp, z0 + h)], top)
        s.poly([(x, d, z0), (x + w, d, z0), (x + w, d, z0 + h), (x, d, z0 + h)], front)
        s.poly([(x + w, d, z0), (x + w, d + dp, z0), (x + w, d + dp, z0 + h), (x + w, d, z0 + h)], right)
    def lamp(s, x, d, h=46, side=1):
        """가로등: 기둥 + 꺾인 팔 + 등. 불빛은 바닥에 번진다(등 아래)."""
        def draw():
            k = s.k; b = s.P(x, d, 0); t = s.P(x, d, h); tt = s.P(x + side * 9, d, h + 1)
            s.d.rectangle([b[0] - k, b[1], b[0] + k, b[1] + k], fill=dk(POLE, .7))
            s.d.line([b, t], fill=POLE, width=2 * k); s.d.line([t, tt], fill=POLE, width=2 * k)
            s.d.rectangle([tt[0] - 3 * k, tt[1], tt[0] + 3 * k, tt[1] + 2 * k], fill=(255, 228, 164)); s.d.rectangle([tt[0] - 3 * k, tt[1] - k, tt[0] + 3 * k, tt[1] - 1], fill=(96, 98, 124))
            s.zbox(x - 1, d - .5, 2, 1, h, solid=False); s.zbox(min(x, x + side * 9) - 1, d - .5, 10, 1, 3, z0=h - 1, solid=False)   # 선으로 그린 기둥·팔도 깊이를 남긴다
        s.log.append((x - 1, d - .5, 2, 1, h, 0)); s.jobs.append((d, draw)); s.glow(x + side * 9, d, 30, power=.55)
    def run(s):
        for _, f in sorted(s.jobs, key=lambda j: -j[0]): f()
        s.jobs = []
    def wall_left(s, d0, d1, h, x=0, seed=1, plain=False):
        """왼쪽 건물 벽(안쪽 면)과 창. 평면 x 고정, 깊이 d0..d1."""
        r = random.Random(seed)
        if plain: grad(s, lambda z0, z1: [(x, d0, z0), (x, d1, z0), (x, d1, z1), (x, d0, z1)], h, 1.0); return
        s.poly([(x, d0, 0), (x, d1, 0), (x, d1, h), (x, d0, h)], WALL)
        for z in range(10, int(h) - 4, 12): s.poly([(x, d0, z), (x, d1, z), (x, d1, z + .8), (x, d0, z + .8)], WALLD)
        for dd in range(int(d0) + 6, int(d1) - 8, 16):
            for z in range(14, int(h) - 8, 12):
                c = WIN_OFF
                s.poly([(x, dd, z), (x, dd + 8, z), (x, dd + 8, z + 6), (x, dd, z + 6)], c)
        s.poly([(x, d0, h - 3), (x, d1, h - 3), (x, d1, h), (x, d0, h)], dk(WALL, .7))
    def wall_back(s, x0, x1, d, h, seed=2, sign=False, plain=False):
        r = random.Random(seed)
        if plain: grad(s, lambda z0, z1: [(x0, d, z0), (x1, d, z0), (x1, d, z1), (x0, d, z1)], h, 1.0); return
        s.poly([(x0, d, 0), (x1, d, 0), (x1, d, h), (x0, d, h)], WALL)
        for z in range(10, int(h) - 4, 12): s.poly([(x0, d, z), (x1, d, z), (x1, d, z + .8), (x0, d, z + .8)], WALLD)
        for xx in range(int(x0) + 6, int(x1) - 10, 16):
            for z in range(14, int(h) - 8, 12):
                c = WIN_OFF
                s.poly([(xx, d, z), (xx + 9, d, z), (xx + 9, d, z + 6), (xx, d, z + 6)], c)
        if sign:                                                    # 분홍 네온(정지, 깜빡임 없음)
            sx = x0 + (x1 - x0) * .62
            s.poly([(sx, d, h - 18), (sx + 40, d, h - 18), (sx + 40, d, h - 8), (sx, d, h - 8)], (70, 18, 52))
            s.poly([(sx + 2, d, h - 16), (sx + 38, d, h - 16), (sx + 38, d, h - 10), (sx + 2, d, h - 10)], (236, 84, 150))
            s.poly([(sx + 4, d, h - 15), (sx + 9, d, h - 15), (sx + 9, d, h - 12), (sx + 4, d, h - 12)], (255, 220, 240))
    def save(s, name):
        s.img.save(os.path.join(OUT, name + '.png')); s.img.resize((s.CW * 2, s.CH * 2), Image.NEAREST if s.k <= 2 else Image.BOX).save(os.path.join(OUT, name + '_x2.png'))
        return s.img

def paving(x, d):
    c = PAVE2 if ((int(x // 16) + int(d // 16)) % 3 == 0) else PAVE
    return JOINT if (x % 16 < 1 or d % 16 < 1) else c
def asphalt(x, d): return ASPH

def paving2(x, d):                                                              # 분수 광장 바닥: 24x12 벽돌 포장(엇갈려 쌓기)
    row = int(d // 12); xs = x + (12 if row % 2 else 0); col = int(xs // 24)
    if d % 12 < 1 or xs % 24 < 1: return (24, 27, 44)
    return ((44, 48, 72), (40, 44, 68), (38, 42, 64))[(row * 3 + col) % 3]

def alley(s, d0, d1, kind, depth=18, h=42, z=3):
    """벽(x=0 평면)에 뚫린 어두운 골목 입구. 안쪽: 바닥, 먼 벽(x=-depth), 오른쪽 안벽, 간단한 소품. 입구 모양으로만 보이게 마스크."""
    mask = Image.new('L', s.img.size, 0)
    ImageDraw.Draw(mask).polygon([s.P(0, d0, z), s.P(0, d1, z), s.P(0, d1, h), s.P(0, d0, h)], fill=255)
    lay = s.img.copy(); ld = ImageDraw.Draw(lay)
    def poly(pts, col): ld.polygon([s.P(*q) for q in pts], fill=col)
    deep = kind == 'link'
    poly([(-depth, d0, z), (0, d0, z), (0, d1, z), (-depth, d1, z)], (18, 20, 38))                       # 바닥
    poly([(-depth, d0, z), (-depth, d1, z), (-depth, d1, h), (-depth, d0, h)], (8, 9, 20) if deep else (12, 14, 28))   # 먼 벽
    poly([(-depth, d1, z), (0, d1, z), (0, d1, h), (-depth, d1, h)], (8, 9, 20))                           # 오른쪽 안벽
    if kind == 'bins':                                                                                   # 쓰레기통 둘 + 봉투
        for dd, w in ((d0 + 4, 7), (d0 + 14, 6)):
            poly([(-depth + 2, dd, z), (-depth + 9, dd, z), (-depth + 9, dd, z + 9), (-depth + 2, dd, z + 9)], (30, 34, 56))
            poly([(-depth + 2, dd, z + 9), (-depth + 9, dd, z + 9), (-depth + 9, dd + w, z + 9), (-depth + 2, dd + w, z + 9)], (42, 46, 70))
    elif kind == 'pipes':                                                                                # 벽을 타고 내려오는 배관 + 상자
        for dd in (d0 + 6, d0 + 10): poly([(-depth, dd, z), (-depth, dd + 1.5, z), (-depth, dd + 1.5, h), (-depth, dd, h)], (36, 40, 62))
        poly([(-depth, d0 + 15, z + 12), (-depth, d0 + 22, z + 12), (-depth, d0 + 22, z + 22), (-depth, d0 + 15, z + 22)], (24, 28, 48))
    elif kind == 'door':                                                                                 # 막다른 문(꺼진 전구)
        poly([(-depth, d0 + 7, z), (-depth, d0 + 17, z), (-depth, d0 + 17, z + 26), (-depth, d0 + 7, z + 26)], (24, 22, 36))
        poly([(-depth, d0 + 12, z + 28), (-depth, d0 + 14, z + 28), (-depth, d0 + 14, z + 30), (-depth, d0 + 12, z + 30)], (60, 56, 48))
    elif deep:                                                                                           # 광장으로 이어지는 긴 통로: 끝으로 갈수록 더 어둡다
        pass
    s.img.paste(lay, (0, 0), mask); s.px = s.img.load(); s.d = ImageDraw.Draw(s.img); s.zclear(mask); s.holes.append(('x', 0, d0, d1))
    # 입구 앞 인도의 소품(안쪽은 어두워 안 보이므로 입구 곁에 놓는다)
    if kind == 'bins':
        s.box(2, d0 + 1, 6, 6, 10, (46, 50, 76), (34, 38, 60), (26, 30, 48), z0=3); s.box(2, d1 - 8, 6, 6, 8, (40, 44, 68), (30, 34, 54), (24, 28, 44), z0=3)
    elif kind == 'pipes':
        for dd in (d0 - 3, d1 + 2): s.poly([(0.5, dd, 3), (2.5, dd, 3), (2.5, dd, 60), (0.5, dd, 60)], (40, 44, 68))
    elif kind == 'door':
        s.poly([(0, d0, h), (6, d0, h), (6, d1, h), (0, d1, h)], dk(WALLD, .8)); s.poly([(1, d0 + 11, h - 3), (3, d0 + 11, h - 3), (3, d0 + 13, h - 3), (1, d0 + 13, h - 3)], (70, 62, 48))
        s.box(0, d0 + 2, 5, 22, 2, (52, 56, 82), (40, 44, 66), (32, 36, 54), z0=3)

def alley_right(s, d0, d1, x0=176, ln=36):
    """오른쪽 인도 끝(난간 사이)에서 오른쪽으로 빠지는 어두운 골목: 건물 덩어리 둘 사이의 길, 끝으로 갈수록 어둠에 잠긴다."""
    blk = ((22, 24, 44), (16, 18, 34), (12, 14, 28))
    s.box(x0, d1, ln, 40, 30, *blk)                                                   # 골목 뒤쪽 건물
    s.floor(lambda x, d: tuple(int(v * max(.15, 1 - (x - x0) / ln)) for v in PAVE), x0=x0 - 36, x1=x0 + ln, d0=d0, d1=d1, z=3)   # 골목 바닥
    s.box(x0, d0 - 30, ln, 28, 22, *blk)                                              # 골목 앞쪽 건물
    s.box(x0 - 6, d0 + 3, 5, 5, 8, (40, 44, 68), (30, 34, 54), (24, 28, 44), z0=3)    # 입구 곁 쓰레기통
    s.box(x0 - 6, d1 - 9, 5, 5, 10, (46, 50, 76), (34, 38, 60), (26, 30, 48), z0=3)

def alley_back(s, x0, x1, h=42, z=3, depth=18, road=False):
    """거리 맨 위 끝 벽(정면을 향한 면)의 왼쪽 끝에 뚫린 어두운 골목. 정면이라 안쪽(바닥·먼 벽·배관·문)이 보인다."""
    D = s.D; mask = Image.new('L', s.img.size, 0)
    if road:                                                                                             # 터널 입구는 위가 둥근 아치로 깎는다
        cx, hw, base, rise = (x0 + x1) / 2, (x1 - x0) / 2, h - 18, 18
        pts = [(x0, D, z)] + [(cx - hw * math.cos(math.pi * k / 24), D, base + rise * math.sin(math.pi * k / 24)) for k in range(0, 25)] + [(x1, D, z)]
    else: pts = [(x0, D, z), (x1, D, z), (x1, D, h), (x0, D, h)]
    ImageDraw.Draw(mask).polygon([s.P(*q) for q in pts], fill=255)
    lay = s.img.copy(); ld = ImageDraw.Draw(lay)
    def poly(pts, col): ld.polygon([s.P(*q) for q in pts], fill=col)
    poly([(x0, D, z), (x1, D, z), (x1, D + depth, z), (x0, D + depth, z)], (20, 22, 40))                 # 바닥
    poly([(x0, D + depth, z), (x1, D + depth, z), (x1, D + depth, h), (x0, D + depth, h)], (11, 12, 26))  # 먼 벽
    poly([(x0, D, z), (x0, D + depth, z), (x0, D + depth, h), (x0, D, h)], (8, 9, 20))                  # 왼쪽 안벽
    if road:                                                                                             # 도로가 벽 밑으로 이어지는 연결 지점: 중앙선이 어둠 속으로 사라진다
        poly([(x0, D + depth, z), (x1, D + depth, z), (x1, D + depth, h), (x0, D + depth, h)], (20, 24, 48))
        for x in (87, 89): poly([(x, D, z), (x + 1, D, z), (x + 1, D + depth * .6, z), (x, D + depth * .6, z)], (130, 112, 60))
        for k in range(0, 12): poly([(x0, D + k * depth / 12, z), (x1, D + k * depth / 12, z), (x1, D + (k + 1) * depth / 12, z), (x0, D + (k + 1) * depth / 12, z)], (int(26 - k * 1.8), int(28 - k * 1.8), int(44 - k * 2.5)))
        s.img.paste(lay, (0, 0), mask); s.px = s.img.load(); s.d = ImageDraw.Draw(s.img); s.zclear(mask); s.holes.append(('d', D, x0, x1))
        for q in pts[1:-1]:                                                                                  # 아치 테두리(밝은 콘크리트 띠)
            a = s.P(*q); s.d.rectangle([a[0], a[1] - 3, a[0] + 1, a[1]], fill=(74, 80, 112))
        return
    for xx in (x0 + 4, x0 + 7): poly([(xx, D + depth, z), (xx + 1.5, D + depth, z), (xx + 1.5, D + depth, h), (xx, D + depth, h)], (34, 38, 60))   # 배관
    poly([(x0 + 14, D + depth, z), (x0 + 23, D + depth, z), (x0 + 23, D + depth, z + 24), (x0 + 14, D + depth, z + 24)], (22, 20, 34))           # 막다른 문
    poly([(x0 + 18, D + depth, z + 26), (x0 + 20, D + depth, z + 26), (x0 + 20, D + depth, z + 28), (x0 + 18, D + depth, z + 28)], (58, 54, 46))  # 꺼진 전구
    s.img.paste(lay, (0, 0), mask); s.px = s.img.load(); s.d = ImageDraw.Draw(s.img); s.zclear(mask); s.holes.append(('d', D, x0, x1))

# ---------------- 장면 1: 광장 ----------------
def back_buildings(s, W, D):
    bx = 0; br = random.Random(11); BD = D + 40; bi = 0                                       # 풍경이라 연석에서 멀리(뒤로) 둔다
    while bx < W:                                                                              # 연석 너머: 불 꺼진 현대 건물들(세 동만 창 몇 개에 불이 켜져 있다)
        bw = br.randint(40, 70); bh = br.randint(70, 125); bd = br.randint(24, 34); g = br.randint(4, 10); c = br.choice(((22, 24, 46), (26, 28, 50), (20, 22, 40)))
        s.box(bx, BD, bw, bd, bh, dk(c, 1.15), c, dk(c, .7))
        cols = list(range(int(bx) + 5, int(bx + bw) - 8, 10)); rows = list(range(8, int(bh) - 8, 12)); lit = set()
        if bi in (1, 4, 6):
            want = br.randint(1, 3)
            for _ in range(40):                                                                # 불규칙하게, 서로 붙지 않게 1~3개
                cc, rr_ = br.randrange(len(cols)), br.randrange(len(rows))
                if all(max(abs(cc - a_), abs(rr_ - b_)) > 1 for a_, b_ in lit): lit.add((cc, rr_))
                if len(lit) >= want: break
        def wins(cols=cols, rows=rows, lit=lit):
            for ci, xx in enumerate(cols):
                for ri, zz in enumerate(rows): s.poly([(xx, BD, zz), (xx + 5, BD, zz), (xx + 5, BD, zz + 7), (xx, BD, zz + 7)], (226, 188, 112) if (ci, ri) in lit else (14, 16, 32))
        wins(); bx += bw + g; bi += 1

def landing(W=150, corridor=False, name='city3d_landing', bed=True, save=True, baked=True, fade=None, dent=True, flen=46):
    D = 80; s = Scene(W, 170 if corridor else D, 130 if corridor else 70); rng = random.Random(5)
    if corridor:                                                                                   # 같은 보도블록 바닥의 긴 복도: 앞쪽은 낮은 연석, 맨 끝은 아래(앞)로 열려 어둠으로 나간다
        EX = W
        s.floor(paving, x0=0, x1=W, d0=34, d1=D)
        s.box(0, 31, W, 3, 4, CURBT, CURBF, CURBR)
    else: s.floor(paving)
    if baked: s.glow(30, 30, 70, power=.35)
    if corridor:
        s.box(0, D, W, 3, 4, CURBT, CURBF, CURBR)                                                  # 위쪽(뒤) 연석
        back_buildings(s, W, D)
    else: s.wall_back(0, W, D, 60)
    if bed: s.wall_left(0, D, 60)
    s.lamp(140 if corridor else 112, 74 if corridor else 60, 52, -1)                                                  # 광장 가로등은 오른쪽 끝 그라데이션에 가리지 않게 왼쪽으로
    if corridor:
        for lx in range(210, W - 40, 70): s.lamp(lx, 74, 52, -1)                                 # 같은 가로등을 뒷벽 쪽 한 줄로 나열
    s.bed = (12, 38, 70, 30, 9)
    s.front = []
    if bed:
        # 인공 수풀 화단(왼쪽 안쪽): 낮은 콘크리트 화단 위에 같은 모양의 덩어리
        px0, pd0, pw, pdp, ph = 12, 38, 70, 30, 9
        s.box(px0, pd0, pw, pdp, ph, (60, 64, 88), (66, 70, 96), (52, 56, 80))
        s.poly([(px0, pd0, ph), (px0 + pw, pd0, ph), (px0 + pw, pd0 + pdp, ph), (px0, pd0 + pdp, ph)], (48, 40, 36))   # 흙
        s.front = []
        def clump(x, d, r=9, dent=0):
            if d == 41: s.front.append((x, d, ph + 8 - dent, r))
            def draw():
                cx, cy = s.P(x, d, ph + 8 - dent); hedge(s.d, cx, cy, r, rng); s.zsphere(x, d, ph + 8 - dent, r / s.k)
            s.jobs.append((d, draw))
        for x in range(20, 80, 12):
            for d, dent in ((62, 0), (51, 0), (41, 0)):
                if dent and d == 51 and 38 < x < 66: continue                                                   # 가운데는 움푹(아이가 있는 곳)
                clump(x, d, 9, dent)
        for x in ((44, 56) if dent else ()): clump(x, 58, 9, 6)                                                         # 꺼진 덩어리
        ch = Image.open(os.path.join(SPR, 'child8', 'child_d_idle.png')).convert('RGBA'); ch = ch.resize((21, 36), Image.NEAREST)
        def child():
            cx, cy = s.P(50, 50, ph + 2); s.img.paste(ch, (cx - 10, cy - 30), ch)
        if baked: s.jobs.append((52, child))
        for _ in range(26):                                                                            # 흩어진 잎
            lx, ld = rng.uniform(20, 84), rng.uniform(26, 38)
            px_, py_ = s.P(lx, ld, 0); s.px[px_, py_] = (60, 150, 80); s.px[px_ + 1, py_] = (46, 122, 66)
    s.run()
    if fade:                                                                                   # 이동 통로 표시: 끝쪽으로 갈수록 검게 사라지는 그라데이션('r' 오른쪽 끝, 'l' 왼쪽 끝)
        for side in fade:
            for X in range(s.CW):
                u = (X - (s.X0 + W - flen)) / float(flen) if side == 'r' else ((s.X0 + flen) - X) / float(flen)
                if u <= 0: continue
                f = min(1.0, u) * .92
                for Y in range(s.CH): q = s.px[X, Y]; s.px[X, Y] = tuple(int(v * (1 - f) + (6, 7, 16)[i] * f) for i, v in enumerate(q))
    s.lampx = list(range(140, W - 40, 70)) if corridor else [140]
    return s.save(name) if save else s

# ---------------- 장면 2: 긴 거리 (새벽 직전의 큰 도시: 길고 넓다) ----------------
def street(ret=False):
    W, D = 176, 520; s = Scene(W, D, 84, k=2); rng = random.Random(9)
    for Y in range(s.img.size[1]):                                           # 새벽 직전: 아래(먼 쪽 아님) 가장자리로 갈수록 살짝 밝은 남색
        f = Y / s.img.size[1]; c = (int(14 + 12 * f), int(16 + 14 * f), int(36 + 30 * f))
        s.d.line([(0, Y), (s.img.size[0], Y)], fill=c)
    LS, RS = 36, 140                                                          # 도로 x 범위 36..140 (폭 104, 4차로 느낌)
    s.wall_left(0, D, 72, seed=4); s.wall_back(0, W, D, 60, seed=6)                           # 벽을 먼저: 높은 인도가 벽 밑동을 덮는다
    s.floor(asphalt, x0=LS, x1=RS); s.floor(paving, x0=0, x1=LS, z=3); s.floor(paving, x0=RS, x1=W, z=3)        # 낮은 차도 먼저, 높은 인도는 그 위에(인도가 앞을 덮는다)
    s.poly([(LS, 0, 0), (LS, 0, 3), (LS, D, 3), (LS, D, 0)], CURBF)                                           # 왼쪽 인도의 오른쪽 턱 면만 보인다(오른쪽 인도의 턱은 뒤를 향해 안 보인다)
    # 도로 표시: 얇고 길고 간격이 넓은 네 개(맨 위 하나만 비스듬히)
    for x in (87, 89): s.poly([(x, 76, 0), (x + 1, 76, 0), (x + 1, D, 0), (x, D, 0)], (196, 170, 90))   # 얇은 이중 중앙선(횡단보도 뒤부터 끝까지)
    for k in range(12, D - 12, 24):                                           # 차로 점선: 같은 굵기(2.4)·길이(11)·간격(24)
        for x in (62, 114): s.poly([(x, k, 0), (x + 2.4, k, 0), (x + 2.4, k + 11, 0), (x, k + 11, 0)], (176, 176, 160))
    # 횡단보도 + 신호등(첫 가로등 자리): 얇은 줄 여러 개, 줄은 차가 가는 방향
    for x in range(LS + 4, RS - 4, 7): s.poly([(x, 56, 0), (x + 3, 56, 0), (x + 3, 74, 0), (x, 74, 0)], PAINT)
    s.poly([(LS, 52, 0), (RS, 52, 0), (RS, 53, 0), (LS, 53, 0)], (150, 150, 130))        # 정지선
    s.floor(paving, x0=RS, x1=W, z=3, d0=40, d1=64)                                            # 바닥 표시가 높은 오른쪽 인도 가장자리를 덮지 않게 인도를 다시 덮는다
    for x, c in ((LS - 6, (230, 60, 60)), (RS + 6, (230, 60, 60))):               # 보행 신호등(빨간불 점등)
        def sig(x=x, c=c):
            b = s.P(x, 56, 3); t = s.P(x, 56, 30); k = s.k
            s.d.line([b, t], fill=POLE, width=2 * k); s.d.rectangle([t[0] - 3 * k, t[1] - 8 * k, t[0] + 3 * k, t[1] + k], fill=(30, 32, 48)); s.d.rectangle([t[0] - k, t[1] - 7 * k, t[0] + k, t[1] - 5 * k], fill=c); s.d.rectangle([t[0] - k // 2, t[1] - 2 * k, t[0] + k // 2, t[1] - k], fill=(30, 90, 50))
            s.zbox(x - 1, 55.5, 2, 1, 27, z0=3, solid=False); s.zbox(x - 3, 55.5, 6, 1, 9, z0=29, solid=False)
        s.log.append((x - 1, 55.5, 2, 1, 30, 0)); s.jobs.append((56, sig)); s.glow(x, 56, 18, col=(230, 60, 60), power=.35, z=3)
    # 왼쪽 건물 벽에 골목 입구: 광장으로 이어지는 통로(아래) + 골목 3개. 모두 어둡다.
    alley(s, 14, 44, 'link', depth=34); alley_back(s, 36, 140, h=46, z=0, depth=40, road=True)
    for x, d, side in [(30, 170, 1), (146, 240, -1), (30, 330, 1), (146, 400, -1), (30, 452, 1)]: s.lamp(x, d, 50, side)
    s.box(12, 200, 5, 18, 5, (74, 58, 46), (56, 44, 36), (44, 34, 28), z0=4); s.box(12, 202, 3, 2, 4, POLE, POLE, POLE, z0=3); s.box(12, 214, 3, 2, 4, POLE, POLE, POLE, z0=3)
    s.box(14, 420, 5, 5, 9, (70, 70, 96), (96, 40, 40), (70, 30, 30), z0=3)
    s.run()
    if ret: return s
    return s.save('city3d_street')

# ---------------- 장면: 복도가 정사각형 광장으로 커지는 곳 (가운데 인공 분수와 풀) ----------------
SQ0, SQ1 = 110, 300                                                                               # 광장(정사각형) 가로 범위
SQF, SQD = 40, 134                                                                               # 광장 앞 끝·뒤 끝(깊이)
C0, C1 = 75, 99                                                                                   # 좌우 복도(광장 한가운데 높이)
P0, P1 = 193, 217                                                                                 # 아래쪽 가운데 통로의 가로 범위
FC = (205, 87); FR = 20
BEN = [(SQ0 + 5, SQD - 8), (SQ1 - 36, SQD - 8)]; BIN = (SQ0 + 38, SQD - 6)                                                      # 풀밭 대신: 위쪽 왼쪽·오른쪽에 벤치 둘, 오른쪽에 쓰레기통 하나
LAMPS = [(50, C1 - 4)]                                              # 복도는 좁은 복도 뒤쪽 줄, 광장은 뒤쪽 모퉁이                                                                           # 분수 중심(x, d), 바깥 반지름
def disc(s, cx, cd, r, z, col, n=36):
    s.poly([(cx + r * math.cos(2 * math.pi * k / n), cd + r * math.sin(2 * math.pi * k / n), z) for k in range(n)], col)
def cyl(s, cx, cd, r, z0, z1, top, side, n=36):                                                   # 원통: 옆면은 앞쪽(d 작은 쪽)이 보인다
    segs = []
    for k in range(n):
        a0, a1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n; am = (a0 + a1) / 2
        segs.append((math.sin(am), [(cx + r * math.cos(a0), cd + r * math.sin(a0), z0), (cx + r * math.cos(a1), cd + r * math.sin(a1), z0), (cx + r * math.cos(a1), cd + r * math.sin(a1), z1), (cx + r * math.cos(a0), cd + r * math.sin(a0), z1)], am))
    for sn, q, am in sorted(segs, key=lambda t: -t[0]):
        if sn < .05: s.poly(q, dk(side, .75 + .35 * max(0, math.cos(am - math.pi / 2 * 0) ) * .5 + .15 * -sn))
    disc(s, cx, cd, r, z1, top, n)
def grass(x, d):
    return (46, 104, 64) if (int(x // 4) + int(d // 4)) % 2 == 0 else (40, 94, 58)                # 일정한 무늬의 인조 잔디
def curb_union(s, rects, H):                                                     # 연석을 하나의 덩어리로: 겹치는 사각형을 합친 바닥 모양을 1칸씩 세워 그린다
    cells = set()                                                                                 # 이음새·겹친 옆면·단차 없이 모서리가 이어지고, 보이는 면(앞·오른쪽)은 바깥 가장자리에만 생긴다
    for (x0, d0, w, dp) in rects:
        for ix in range(int(round(x0)), int(round(x0 + w))):
            for idd in range(int(round(d0)), int(round(d0 + dp))): cells.add((ix, idd))
    for (ix, idd) in sorted(cells, key=lambda c: (-c[1], c[0])):
        if (ix, idd - 1) not in cells: s.poly([(ix, idd, 0), (ix + 1.02, idd, 0), (ix + 1.02, idd, H), (ix, idd, H)], CURBF)
        if (ix + 1, idd) not in cells: s.poly([(ix + 1, idd, 0), (ix + 1, idd + 1.02, 0), (ix + 1, idd + 1.02, H), (ix + 1, idd, H)], CURBR)
        s.poly([(ix, idd, H), (ix + 1.02, idd, H), (ix + 1.02, idd + 1.02, H), (ix, idd + 1.02, H)], CURBT)

def fountain_scene(W=410, name='city3d_fountain', save=True, fade='lr'):
    D = SQD; s = Scene(W, 262, 130, k=2)                                                            # 2배 해상도: 사선 연석의 계단이 절반 크기
    back_buildings(s, W, D + PL)                                                                    # 가장 먼 건물부터 그린다(위쪽 통로 길이만큼 더 뒤)
    s.floor(lambda x, d: dk(paving2(x, d), .08 + .92 * min(1.0, (SQD + PL - d) / 34.0)), x0=P0, x1=P1, d0=SQD, d1=SQD + PL)   # 위쪽 가운데 통로
    s.floor(paving, x0=0, x1=W, d0=C0, d1=C1); s.floor(paving2, x0=SQ0, x1=SQ1, d0=SQF, d1=SQD)      # 좌우 복도 + 한가운데 높이에서 위·아래로 넓어지는 광장(벽돌 포장)
    s.floor(lambda x, d: dk(paving2(x, d), .08 + .92 * min(1.0, d / 34.0)), x0=P0, x1=P1, d0=0, d1=SQF)   # 아래쪽 가운데 통로(끝으로 갈수록 검게)
    T = W3 = 4; H = 3                                                                               # 모든 연석은 같은 실제 두께 4, 높이 3
    L, R_, F0, B1 = SQ0 - W3, SQ1 + W3, SQF - T, SQD + T                                            # 광장 바깥 테두리
    rects = [(0, C1, L, T), (R_, C1, W - R_, T), (0, C0 - T, L, T), (R_, C0 - T, W - R_, T),              # 복도 뒤·앞 연석
             (L, SQD, P0 - W3 - L, T), (P1 + W3, SQD, R_ - P1 - W3, T), (P0 - W3, SQD, W3, PL), (P1, SQD, W3, PL),   # 광장 뒤 연석 + 위쪽 통로 옆 연석
             (L, F0, W3, C0 - F0), (L, C1, W3, B1 - C1), (SQ1, F0, W3, C0 - F0), (SQ1, C1, W3, B1 - C1),   # 광장 옆 연석
             (L, F0, P0 - W3 - L, T), (P1 + W3, F0, R_ - P1 - W3, T), (P0 - W3, 0, W3, SQF), (P1, 0, W3, SQF)]   # 광장 앞 연석 + 아래 통로 옆 연석
    curb_union(s, rects, H)
    rr = random.Random(21)
    def bed(gx0, gx1, gd0, gd1):                                                                   # 회양목 울타리를 두른 장미 화단(낮은 울타리 + 안쪽 잔디와 분홍 꽃)
        s.floor(grass, x0=gx0, x1=gx1, d0=gd0, d1=gd1, z=0)
        H1, H2, H3 = (34, 84, 56), (28, 70, 48), (22, 56, 40)
        for (a_, b_, c_, d_) in ((gx0, gd0 - 3, gx1 - gx0, 3), (gx0, gd1, gx1 - gx0, 3), (gx0 - 3, gd0 - 3, 3, gd1 - gd0 + 6), (gx1, gd0 - 3, 3, gd1 - gd0 + 6)): s.box(a_, b_, c_, d_, 5, H1, H2, H3)
        def roses():
            for _ in range(int((gx1 - gx0) * (gd1 - gd0) / 26)):
                x_, d_ = rr.uniform(gx0 + 3, gx1 - 3), rr.uniform(gd0 + 2, gd1 - 2); px_, py_ = s.P(x_, d_, 6)
                col_ = rr.choice(((186, 76, 116), (186, 76, 116), (210, 120, 150), (214, 150, 96)))
                s.px[px_, py_] = col_; s.px[px_ + 1, py_] = col_; s.px[px_, py_ - 1] = dk(col_, .7)
        s.jobs.append((gd1 - 1, roses))
    WOOD, WOODD, IRON = (150, 96, 52), (112, 70, 38), (30, 30, 38)                                  # 공원 벤치(참고 사진): 주황 갈색 널 + 가는 검은 주철 지지대
    for bx_, bd_ in BEN:                                                                           # 벤치: 너비 36, 앉는 높이 9, 등받이 끝 20(아이 키 24 기준)
        for lx_ in (bx_ + 1, bx_ + 26):
            s.box(lx_, bd_ + .5, 1, 1, 7, IRON, IRON, IRON); s.box(lx_, bd_ + 5, 1, 1, 7, IRON, IRON, IRON); s.box(lx_, bd_ + 5.5, 1, 1, 16, IRON, IRON, IRON); s.box(lx_, bd_ + .5, 1, 6, 1, IRON, IRON, IRON, z0=11)
        s.box(bx_, bd_ + 1, 28, 6, 1.2, WOOD, WOODD, dk(WOODD, .8), z0=7)
        for k in range(3): s.box(bx_, bd_ + 1 + k * 1.9, 28, .3, .1, WOODD, WOODD, WOODD, z0=8.2)
        for k in range(3): s.box(bx_ + 1, bd_ + 6, 26, .9, 2, WOOD, dk(WOOD, .85), WOODD, z0=9.5 + k * 2.4)
    s.box(BIN[0], BIN[1], 5.5, 5.5, 11, (84, 92, 110), (62, 68, 86), (50, 54, 70)); s.box(BIN[0] - .5, BIN[1] - .5, 6.5, 6.5, 1.2, (104, 112, 130), (84, 92, 110), (70, 76, 92), z0=11)
    cx, cd = FC
    STONE, STONED, STONER, WATER = (112, 112, 134), (92, 94, 118), (78, 80, 104), (36, 76, 132)       # 멈춰 있는 분수: 물결·물줄기·물방울 없음, 모두 직각 상자
    def sq_water(x0, d0, x1, d1, z): s.poly([(x0, d0, z), (x1, d0, z), (x1, d1, z), (x0, d1, z)], WATER)
    s.box(cx - FR, cd - FR, 2 * FR, 2 * FR, 7, STONE, STONED, STONER); sq_water(cx - FR + 3, cd - FR + 3, cx + FR - 3, cd + FR - 3, 7.05)   # 받침 + 물
    s.box(cx - 2.5, cd - 2.5, 5, 5, 8, STONE, STONED, STONER, z0=7)                                 # 기둥
    s.box(cx - 9, cd - 9, 18, 18, 2.5, STONE, STONED, STONER, z0=15); sq_water(cx - 7, cd - 7, cx + 7, cd + 7, 17.55)   # 1단 그릇
    s.box(cx - 1.8, cd - 1.8, 3.6, 3.6, 5, STONE, STONED, STONER, z0=17.5)
    s.box(cx - 5, cd - 5, 10, 10, 2.5, STONE, STONED, STONER, z0=22.5); sq_water(cx - 3.5, cd - 3.5, cx + 3.5, cd + 3.5, 25.05)   # 2단 그릇
    for lx, ld_ in LAMPS: s.lamp(lx, ld_, 52, 1)                                                    # 왼쪽 가장자리 가로등은 좌우 반전                                          # 분수 뒤는 비우고 양옆 뒷줄에 같은 가로등
    s.run()
    for side in (fade or ''):
        for X in range(s.img.size[0]):
            Xl = X / s.k; u = (Xl - (s.X0 + W - 46)) / 46.0 if side == 'r' else ((s.X0 + 46) - Xl) / 46.0
            if u <= 0: continue
            f = min(1.0, u) * .92
            for Y in range(s.img.size[1]): q = s.px[X, Y]; s.px[X, Y] = tuple(int(v * (1 - f) + (6, 7, 16)[i] * f) for i, v in enumerate(q))
    s.lampx = [l[0] for l in LAMPS]
    return s.save(name) if save else s

# ---------------- 분수 광장에서 이어지는 두 공간: 분리수거장(오른쪽) · 같은 크기의 정사각형 공간(아래쪽) ----------------
PL = 40                                                                                           # 위쪽 통로 길이(정사각형 공간용)
def outline(s, x, d, w, dp, h, z0=0, col=(36, 34, 40), t=.6):
    """상자의 보이는 모서리에 어두운 선을 그어 경계를 또렷하게 한다(그림만, 깊이는 건드리지 않는다)."""
    X, Z = x + w, z0 + h
    for pts in ([(x, d, z0), (X, d, z0), (X, d, z0 + t), (x, d, z0 + t)],            # 앞면 아래 모서리
                [(x, d, Z - t), (X, d, Z - t), (X, d, Z), (x, d, Z)],                  # 앞면 위 모서리
                [(x, d, z0), (x + t, d, z0), (x + t, d, Z), (x, d, Z)],                # 앞면 왼쪽 세로 모서리
                [(X - t, d, z0), (X, d, z0), (X, d, Z), (X - t, d, Z)],                # 앞면 오른쪽 세로 모서리
                [(X, d + dp - t, z0), (X, d + dp, z0), (X, d + dp, Z), (X, d + dp - t, Z)],   # 오른쪽 면 뒤 세로 모서리
                [(X, d, z0), (X, d + dp, z0), (X, d + dp, z0 + t), (X, d, z0 + t)],    # 오른쪽 면 아래 모서리
                [(x, d + dp - t, Z), (X, d + dp - t, Z), (X, d + dp, Z), (x, d + dp, Z)],   # 윗면 뒤 모서리
                [(X - t, d, Z), (X, d, Z), (X, d + dp, Z), (X - t, d + dp, Z)]):        # 윗면 오른쪽 모서리
        s.poly(pts, col, z=False)
def outline_px(s, x, d, w, dp, h, z0=0, col=(36, 34, 40), wpx=1, skip=()):
    """상자의 보이는 모서리를 화면 화소 기준 같은 굵기(wpx 논리 화소)로 긋는다: 가로·세로·사선 모두 두께가 같다(그림만, 깊이는 건드리지 않는다)."""
    X, Z = x + w, z0 + h; P = s.P; wd = max(1, int(round(wpx * s.k)))
    E = [((x, d, z0), (X, d, z0)), ((x, d, Z), (X, d, Z)), ((x, d, z0), (x, d, Z)), ((X, d, z0), (X, d, Z)),                    # 앞면 네 변
         ((X, d + dp, z0), (X, d + dp, Z)), ((X, d, z0), (X, d + dp, z0)), ((X, d, Z), (X, d + dp, Z)),                          # 오른쪽 면 뒤 세로·아래·위
         ((x, d + dp, Z), (X, d + dp, Z)), ((x, d, Z), (x, d + dp, Z))]                                                          # 윗면 뒤·왼쪽
    for n_, (a_, b_) in enumerate(E):
        if n_ in skip: continue
        pa, pb = P(*a_), P(*b_); s.d.line([pa, pb], fill=col, width=wd)
        for q in (pa, pb): s.d.ellipse([q[0] - wd // 2, q[1] - wd // 2, q[0] + (wd - 1) // 2 - (1 if wd > 1 else 0), q[1] + (wd - 1) // 2 - (1 if wd > 1 else 0)], fill=col) if wd > 2 else None
def cardboard(s, x, d, w, dp, h, z0=0, tone=0):
    """쌓아 둔 종이 상자: 상자마다 색을 달리하고 모서리선·테이프 띠로 경계를 나눈다."""
    T = [((172, 132, 86), (138, 102, 62), (110, 80, 48)), ((150, 114, 74), (120, 88, 54), (96, 68, 40)), ((188, 148, 98), (152, 114, 72), (122, 90, 56))][tone % 3]
    s.box(x, d, w, dp, h, T[0], T[1], T[2], z0=z0); outline(s, x, d, w, dp, h, z0, dk(T[2], .55), .7)

def bin_box(s, x, d, col, w=12, dp=8, h=18):                                                      # 분리수거함: 몸통 + 뚜껑 + 색 띠
    s.box(x, d, w, dp, h, dk(col, .8), dk(col, .65), dk(col, .5)); s.box(x - .6, d - .6, w + 1.2, dp + 1.2, 2, dk(col, 1.0), dk(col, .8), dk(col, .6), z0=h)
    s.box(x + 1.5, d - .1, w - 3, .3, 4, (200, 204, 214), (200, 204, 214), (200, 204, 214), z0=h - 8)
BINS = [(66, 120, 210), (60, 160, 96), (220, 190, 60), (214, 214, 220), (110, 114, 128)]          # 플라스틱·유리·캔·종이·일반
def sq_scene(kind='recycle', W=300, name='city3d_recycle', save=True, fade=''):
    """분리수거장: 분수 광장 위쪽 통로에서 들어오는 아래쪽 가운데 통로 + 같은 크기의 광장. 뒤 연석 앞에 분리수거함."""
    D = SQD; s = Scene(W, 255, 130, k=2); back_buildings(s, W, D)
    s.floor(paving2, x0=SQ0, x1=SQ1, d0=SQF, d1=SQD)
    s.floor(lambda x, d: dk(paving2(x, d), .08 + .92 * min(1.0, d / 34.0)), x0=P0, x1=P1, d0=0, d1=SQF)
    T = W3 = 4; H = 3; L, R_, F0, B1 = SQ0 - W3, SQ1 + W3, SQF - T, SQD + T
    curb_union(s, [(L, SQD, R_ - L, T), (L, F0, W3, B1 - F0), (SQ1, F0, W3, B1 - F0), (L, F0, P0 - W3 - L, T), (P1 + W3, F0, R_ - P1 - W3, T), (P0 - W3, 0, W3, SQF), (P1, 0, W3, SQF)], H)
    for i, c in enumerate(BINS): bin_box(s, SQ0 + 34 + i * 18, SQD - 13, c)                        # 뒤 연석 앞에 분리수거함 다섯
    cardboard(s, SQ1 - 52, SQD - 20, 14, 9, 9, 0, 0); cardboard(s, SQ1 - 51, SQD - 19.5, 12, 8, 8, 9.4, 2); cardboard(s, SQ1 - 36, SQD - 20, 12, 9, 9, 0, 1)   # 쌓아 둔 종이 상자(색·모서리·테이프로 구분, 위 상자는 살짝 작게 얹는다)
    s.lamp(SQ1 - 14, SQD - 4, 52, -1)                                                              # 가장자리 가로등 하나(오른쪽)
    s.run()
    return s.save(name) if save else s

# ---------------- 아래쪽 공간: 주차장 ----------------
LX0, LX1 = 110, 480                                                                               # 주차장 가로 범위(분수 광장보다 넓다)
LP0, LP1 = 281, 309                                                                               # 위쪽 가운데 통로
LOT_W = 590
LSQD = SQF + 142                                                                                  # 주차장 뒤 끝(깊이): 분수 광장보다 훨씬 넓다
BAY_W, BAY_L = 27, 46                                                                             # 주차칸 폭·길이
def asphalt2(x, d):
    n = (int(x * 7 + d * 13) * 2654435761) % 97
    return (30, 32, 46) if n > 6 else (36, 38, 54)
CAR_MODELS = ('sedan', 'suv', 'hatch', 'van', 'pickup')
CK = 1.35                                                                                          # 차 크기 배율(아이 키 24 기준으로 키웠다)
def car(s, x, d, col, model='sedan'):                                                              # 세워 둔 차(앞이 화면 아래쪽, d 작은 쪽). 기본 폭 14, 길이는 모델마다 다르다 × CK
    dc, ds, GL, TIRE, LAMP = dk(col, .6), dk(col, .5), (22, 30, 50), (14, 14, 18), (124, 116, 84)
    ln = {'sedan': 28, 'suv': 28, 'hatch': 24, 'van': 30, 'pickup': 30}[model]
    def B(x0, d0, w, l, h, top, front, right, z0=0): s.box(x + x0 * CK, d + d0 * CK, w * CK, l * CK, h * CK, top, front, right, z0 * CK)
    def GP(x0, x1, dd, z0, z1): s.poly([(x + x0 * CK, d + dd * CK, z0 * CK), (x + x1 * CK, d + dd * CK, z0 * CK), (x + x1 * CK, d + dd * CK, z1 * CK), (x + x0 * CK, d + dd * CK, z1 * CK)], GL)
    for wx in (-.9, 13.1):                                                                         # 바퀴: 차체 옆으로 살짝 나오게, 차체보다 먼저 그린다
        B(wx, 3, 1.8, 6, 3.4, TIRE, TIRE, TIRE); B(wx, ln - 9, 1.8, 6, 3.4, TIRE, TIRE, TIRE)
    if model == 'sedan':
        B(0, 0, 14, ln, 6, col, dc, ds, 1.5); B(1.2, 7, 11.6, 13, 4.5, dk(col, .85), dc, ds, 7.5); GP(1.6, 12.4, 7, 8, 11.2)
    elif model == 'suv':
        B(0, 0, 14, ln, 7, col, dc, ds, 2); B(.6, 5, 12.8, 21, 6.5, dk(col, .88), dc, ds, 9); GP(1.2, 12.8, 5, 9.8, 14.5)
    elif model == 'hatch':
        B(0, 0, 14, ln, 6, col, dc, ds, 1.5); B(1.2, 4, 11.6, 18, 5, dk(col, .85), dc, ds, 7.5); GP(1.6, 12.4, 4, 8, 12)
    elif model == 'van':
        B(0, 0, 14, ln, 12, col, dc, ds, 2); GP(.6, 13.4, 0, 9, 13.5)
    else:
        B(0, 13, 14, 17, 1.5, dc, dc, ds, 1.5); B(0, 29, 14, 1.2, 4.5, col, dc, ds, 3); B(0, 13, 1.2, 17, 4.5, col, dc, ds, 3); B(12.8, 13, 1.2, 17, 4.5, col, dc, ds, 3)   # 짐칸(뒤쪽이라 먼저)
        B(0, 0, 14, 13, 6.5, col, dc, ds, 1.5); B(1.2, 2, 11.6, 9, 4.5, dk(col, .85), dc, ds, 8); GP(1.6, 12.4, 2, 8.4, 12)
    B(2, -.1, 3, .3, 1.6, LAMP, LAMP, LAMP, 4); B(9, -.1, 3, .3, 1.6, LAMP, LAMP, LAMP, 4)
def note_sprite(s, nx, nd):                                                                        # 쪽지: 보내 주신 그림(X 접힌 네모 + 엇갈려 접은 두 장)을 바닥 위에 눕혀 놓는다
    sc = 8.0 / 351; INK, PAP, PAP2 = (48, 38, 32), (232, 224, 196), (206, 196, 168)
    def fp(u, v): return (nx + (u - 175) * sc, nd - (v - 175) * sc * 1.5, .15)                   # 그림의 (가로, 세로) -> 바닥 (x, d)
    def poly(pts, fill):
        q = [s.P(*fp(*t)) for t in pts]; s.d.polygon(q, fill=fill, outline=INK)
    poly([(65, 5), (218, 5), (218, 152), (65, 152)], PAP2)
    for a_, b_ in (((65, 5), (218, 152)), ((218, 5), (65, 152))): s.d.line([s.P(*fp(*a_)), s.P(*fp(*b_))], fill=INK, width=max(1, s.k // 2))
    poly([(145, 225), (218, 152), (351, 258), (278, 352)], PAP)
    poly([(5, 215), (140, 75), (218, 152), (75, 292)], PAP)
YELLOW = (230, 186, 48)                                                                           # 이스터에그: 이 차만 색이 있다
NOTE_AT = (124, 70)                                                                                # 쪽지 자리(아래쪽 가운데 빈 칸)
def lot_scene(W=LOT_W, name='city3d_lot', save=True):
    SD = LSQD; D = SD + PL; s = Scene(W, 300, 130, k=2); s.cars = []; s.egg = None; back_buildings(s, W, D)
    s.floor(asphalt2, x0=LX0, x1=LX1, d0=SQF, d1=SD)
    s.floor(lambda x, d: dk(asphalt2(x, d), .08 + .92 * min(1.0, (SD + PL - d) / 34.0)), x0=LP0, x1=LP1, d0=SD, d1=SD + PL)
    T = W3 = 4; H = 3; L, R_, F0, B1 = LX0 - W3, LX1 + W3, SQF - T, SD + T
    curb_union(s, [(L, SD, LP0 - W3 - L, T), (LP1 + W3, SD, R_ - LP1 - W3, T), (LP0 - W3, SD, W3, PL), (LP1, SD, W3, PL), (L, F0, R_ - L, T), (L, F0, W3, B1 - F0), (LX1, F0, W3, B1 - F0)], H)
    LINE = (168, 170, 186); rr = random.Random(9)
    NEUT = [(214, 74, 72), (74, 128, 214), (92, 176, 120), (232, 232, 238), (176, 180, 194), (70, 74, 96), (226, 134, 150), (96, 190, 206)]
    back_row, front_row = SD - 6 - BAY_L, SQF + 8                                                   # 뒷줄·앞줄 주차칸 시작 d
    bays = []
    for row_d in (back_row, front_row):
        bx = LX0 + 6
        while bx + BAY_W <= LX1 - 6:
            bays.append((bx, row_d))
            if not (row_d == back_row and LP0 - 40 <= bx <= LP1 + 20 and bx != min(b_ for b_ in [LX0 + 6 + i * BAY_W for i in range(40)] if b_ >= LP0 - 40)):   # 입구 바로 앞은 선을 긋지 않는다(가장 왼쪽 칸만 남김)
                s.floor(lambda x, d, bx=bx: LINE if (abs(x - bx) < .5 or abs(x - (bx + BAY_W)) < .5) else None, x0=bx - .5, x1=bx + BAY_W + .5, d0=row_d, d1=row_d + BAY_L)
            bx += BAY_W
    egg_bay = [b_ for b_ in bays if b_[1] == back_row and b_[0] > LP1 + 40][0]
    for (bx, row_d) in sorted(bays, key=lambda b_: (-b_[1], b_[0])):
        if row_d == front_row and NOTE_AT[0] - BAY_W <= bx <= NOTE_AT[0] + 4: continue                      # 쪽지가 놓이는 빈 칸
        if row_d == back_row and (bx < LX0 + 40 or bx + BAY_W > LX1 - 40): continue                       # 모서리 가로등과 겹치지 않게
        if row_d == back_row and LP0 - 40 <= bx <= LP1 + 20 and bx != min(b_[0] for b_ in bays if b_[1] == back_row and b_[0] >= LP0 - 40): continue   # 입구 쪽 차는 없앤다
        if (bx, row_d) == egg_bay: model, col = 'hatch', YELLOW; s.egg = (bx + 4, row_d + 4)
        elif rr.random() < .6: model, col = rr.choice(CAR_MODELS), rr.choice(NEUT)
        else: continue
        car(s, bx + 4, row_d + 4, col, model); s.cars.append((bx + 4, row_d + 4))
    note_sprite(s, *NOTE_AT)
    s.lamp(LX0 + 14, SD - 4, 52, 1); s.lamp(LX1 - 14, SD - 4, 52, -1)                               # 가장자리 가로등만(왼쪽 것은 좌우 반전)
    s.run()
    return s.save(name) if save else s


# ---------------- 거리 끝 아치 안: 일자 도로 터널(주황 나트륨 조명) + 옆으로 파인 비상구 → ㄴ자 정비 통로 ----------------
RTW, RTD = 140, 420                                                                               # 도로 터널 크기(세로로 쭉)
WX = 12                                                                                           # 왼쪽 벽 면의 x(그 뒤는 비상구가 파인 자리)
RV0, RV1 = 24, 128                                                                                # 차도 가로 범위(왼쪽 인도 12..24, 오른쪽 낮은 벽 128..)
NICHE = (228, 276)                                                                                # 비상구가 파인 깊이 범위(왼쪽 벽)
def _nz(x, d, s=0): return ((int(x * 12.9898 + d * 78.233 + s * 37.7) * 2654435761) >> 7) % 100 / 100.0
def road_tunnel(name='city3d_roadtunnel', save=True, cover=False):
    s = Scene(RTW, RTD, 72, k=2); s.d.rectangle([0, 0, s.img.size[0], s.img.size[1]], fill=(10, 7, 6))
    AMB = (255, 176, 76)
    def road(x, d):
        c = (96, 66, 42) if _nz(x // 2, d // 2) > .15 else (90, 62, 40)
        if x < RV0: c = (126, 98, 70)                                                              # 인도(조금 밝다)
        c = tuple(int(v * (.86 + .14 * (.5 + .5 * math.cos(2 * math.pi * d / 56.0))) * (.92 + .1 * math.sin(math.pi * min(1.0, max(0.0, (x - WX) / (RV1 - WX)))))) for v in c)   # 길이 방향으로 부드럽게 밝아졌다 어두워지는 줄 조명(동그란 빛 없음)
        if d < 70: c = dk(c, .3 + .7 * d / 70.0)                                                   # 입구(아치) 쪽은 어둠에서 서서히 드러난다
        if d > RTD - 70: c = dk(c, .3 + .7 * (RTD - d) / 70.0)                                      # 끝은 어둠 속으로 사라진다
        return c
    s.floor(road, x0=WX, x1=RV1 + 2, d0=0, d1=RTD)
    def seg(x0, d0, x1, d1, c, z=0): s.poly([(x0, d0, z), (x1, d0, z), (x1, d1, z), (x0, d1, z)], c)
    seg(RV0, 0, RV0 + 1.6, RTD, (214, 206, 180)); seg(RV1 - 1.8, 0, RV1, RTD, (214, 206, 180))   # 차도 양옆 흰 실선
    for k in range(14, RTD - 10, 26): seg((RV0 + RV1) / 2 - 1.2, k, (RV0 + RV1) / 2 + 1.2, k + 12, (236, 214, 130))   # 가운데 점선
    E = RTD
    s.poly([(WX, E, 0), (RTW, E, 0), (RTW, E, 72), (WX, E, 72)], (22, 15, 12))                          # 맨 끝은 어두운 벽(빛 없음)
    # 왼쪽 벽: 가로 결이 있는 연한 주황 패널 타일 + 위쪽 어두운 둥근 천장 띠 + 줄지어 켜진 등
    LAMPD = list(range(20, RTD - 8, 14))
    def lit(d): return .8 + .3 * max(0.0, math.cos(math.pi * ((d - 20) % 14 - 7) / 14 * 1.0)) * 0 + .0
    def lwall(dlo, dhi):                                                                             # 왼쪽 벽 한 구간(비상구 앞쪽은 구멍 안쪽을 그린 뒤 다시 그려 앞을 덮는다)
        for d0 in range(dlo, dhi, 4):
            g = .92
            fade = min(1.0, .3 + .7 * d0 / 70.0)
            for z0 in range(0, 40, 5):
                c = (186, 134, 88) if (z0 // 5) % 2 == 0 else (176, 126, 82)
                if d0 % 24 < 4: c = dk(c, .86)                                                           # 패널 이음
                if z0 < 6: c = (150, 112, 80)                                                            # 아래 몸체 띠
                c = tuple(int(v * g * fade) for v in c)
                s.poly([(WX, d0, z0), (WX, d0 + 4.2, z0), (WX, d0 + 4.2, z0 + 5), (WX, d0, z0 + 5)], c)
            for z0 in range(40, 70, 6):                                                                  # 위쪽: 어두운 천장 곡면
                f = 1 - (z0 - 40) / 36.0; c = tuple(int(v * f * fade) for v in (84, 56, 38)); s.poly([(WX, d0, z0), (WX, d0 + 4.2, z0), (WX, d0 + 4.2, z0 + 6), (WX, d0, z0 + 6)], c)
        for d0 in range(dlo, dhi, 4):                                                                       # 천장 모서리를 따라 이어진 한 줄 조명(점이 아니라 선)
            fade = min(1.0, .25 + .75 * d0 / 70.0); c = tuple(int(v * fade) for v in (255, 226, 160)); s.poly([(WX, d0, 46), (WX, d0 + 4.2, 46), (WX, d0 + 4.2, 48.4), (WX, d0, 48.4)], c)
            c2 = tuple(int(v * fade) for v in (150, 104, 66)); s.poly([(WX, d0, 49), (WX, d0 + 4.2, 49), (WX, d0 + 4.2, 50), (WX, d0, 50)], c2)
    lwall(0, RTD)
    # 비상구(참고 사진): 벽이 큰 둥근 아치로 깊게 파이고, 안쪽에 회색 철제 미닫이 문 + 붉은 안내문 + 흰 '비상구' 표지 + 황흑 말뚝 + 작은 초록 표지
    n0, n1 = NICHE; XB = -3; HZ, RZ = 30, 12; s.holes.append(('x', WX, n0, n1))
    A0 = [(n0, 0)] + [(n0 + (n1 - n0) / 2 * (1 - math.cos(math.pi * k / 24)), HZ + RZ * math.sin(math.pi * k / 24)) for k in range(0, 25)] + [(n1, 0)]
    s.zpunch([(WX, a_[0], a_[1]) for a_ in A0])
    if cover:                                                                                            # 평소엔 벽에 난 아치 모양이 검게 가려져 있다
        s.poly([(WX, a_[0], a_[1]) for a_ in A0], (8, 6, 6))
    else:
        W = n1 - n0; CON, CONL = (128, 120, 108), (156, 148, 134)
        s.poly([(XB, n0, 0), (WX, n0, 0), (WX, n1, 0), (XB, n1, 0)], (118, 110, 98))                      # 파인 바닥(밝은 콘크리트)
        s.poly([(WX, a_[0], a_[1]) for a_ in A0], (52, 44, 38), z=False)                                   # 아치 구멍(어두운 속): 면이 아니다
        s.poly([(XB, n1, 0), (WX, n1, 0), (WX, n1, HZ), (XB, n1, HZ)], CON)                                # 먼쪽 옆면(둥근 콘크리트)
        s.poly([(XB, a_[0], a_[1]) for a_ in A0], (96, 92, 86))                                            # 안쪽 면(둥근 지붕 콘크리트)
        # 안쪽 작은 아치(문틀) + 철제 문
        i0, i1, ih = n0 + 4, n1 - 4, 30
        AI = [(i0, 0)] + [(i0 + (i1 - i0) / 2 * (1 - math.cos(math.pi * k / 24)), ih + 6 * math.sin(math.pi * k / 24)) for k in range(0, 25)] + [(i1, 0)]
        s.poly([(XB, a_[0], a_[1]) for a_ in AI], (140, 144, 144))
        d0_, d1_ = i0 + 3, i1 - 3; DH = 26; STEEL, STEELD, STEELL = (160, 164, 164), (120, 124, 126), (184, 188, 188)
        s.poly([(XB, d0_ - 1, 0), (XB, d1_ + 1, 0), (XB, d1_ + 1, DH + 4), (XB, d0_ - 1, DH + 4)], STEELD)                  # 문틀
        s.poly([(XB, d0_ - 1, DH), (XB, d1_ + 1, DH), (XB, d1_ + 1, DH + 4), (XB, d0_ - 1, DH + 4)], STEELL)                # 위 가로 보
        cuts = [d0_, d0_ + (d1_ - d0_) * .34, d0_ + (d1_ - d0_) * .62, d1_]
        for k in range(3):
            x0_, x1_ = cuts[k], cuts[k + 1]; s.poly([(XB, x0_ + .4, 0), (XB, x1_ - .4, 0), (XB, x1_ - .4, DH), (XB, x0_ + .4, DH)], STEEL if k != 1 else (170, 174, 174))
        s.poly([(XB, cuts[1] - .3, 0), (XB, cuts[1] + .3, 0), (XB, cuts[1] + .3, DH), (XB, cuts[1] - .3, DH)], STEELD); s.poly([(XB, cuts[2] - .3, 0), (XB, cuts[2] + .3, 0), (XB, cuts[2] + .3, DH), (XB, cuts[2] - .3, DH)], STEELD)
        mid = (cuts[1] + cuts[2]) / 2; s.poly([(XB, mid - .25, 0), (XB, mid + .25, 0), (XB, mid + .25, DH), (XB, mid - .25, DH)], STEELD)
        s.poly([(XB, cuts[0] + 2.2, 8), (XB, cuts[0] + 2.8, 8), (XB, cuts[0] + 2.8, 15), (XB, cuts[0] + 2.2, 15)], (96, 98, 98))      # 손잡이
        mx_ = (n0 + n1) / 2
        s.poly([(XB, mx_ - 3, HZ + 6.5), (XB, mx_ + 3, HZ + 6.5), (XB, mx_ + 3, HZ + 8.5), (XB, mx_ - 3, HZ + 8.5)], (246, 244, 232))
        for k in range(0, 24):                                                                               # 아치 테두리(밝은 콘크리트 띠, 두껍게)
            p1, p2 = A0[1 + k], A0[2 + k]; s.poly([(WX, p1[0], p1[1]), (WX, p2[0], p2[1]), (WX, p2[0], p2[1] + 2.4), (WX, p1[0], p1[1] + 2.4)], CONL)
        lwall(n0 - 40, n0)                                                                                  # 구멍 앞쪽(가까운 쪽) 벽이 구멍 안쪽 일부를 가린다: 그림 순서를 맞춘다
    # 오른쪽: 낮은 벽(윗면과 앞 단면만) 위에 등 한 줄
    s.box(RV1, 0, 10, RTD, 12, (150, 112, 80), (126, 92, 64), (100, 72, 50))
    for d in range(0, RTD, 4):
        fade = min(1.0, .25 + .75 * d / 70.0); c = tuple(int(v * fade) for v in (255, 214, 130)); s.poly([(RV1 + 4, d, 12.2), (RV1 + 6, d, 12.2), (RV1 + 6, d + 4.2, 12.2), (RV1 + 4, d + 4.2, 12.2)], c)
    s.run(); s.lamps = []
    return s.save(name) if save else s

# ---------------- 비상구 안: 오른쪽에서 시작해 왼쪽에서 끝나는 일자 정비 복도 ----------------
AL = 300                                                                                          # 복도 길이(바닥 x 0..AL)
AF, AB = 6, 50                                                                                    # 바닥 깊이 범위(앞쪽 낮은 벽 ~ 뒤 벽)
AW, AD = AL + 8, 56                                                                               # 방 크기
APASS = (18, 42)                                                                                  # 왼쪽 끝 벽의 이동통로가 열린 깊이 범위(d)
def annex(name='city3d_annex', save=True):
    """비상구 문을 지나면 나오는 일자 복도: 오른쪽 끝에서 들어와 왼쪽 끝 이동통로로 나간다. 뒤 벽은 키 큰 콘크리트 판벽(케이블 트레이·줄 조명·잠긴 문),
    앞은 안이 보이게 낮은 벽. 레이어 규칙(docs/layer-rules.md): 단단한 것은 box, 평면은 poly, 먼 것부터."""
    s = Scene(AW, AD, 60, k=2); s.d.rectangle([0, 0, s.img.size[0], s.img.size[1]], fill=(10, 7, 6))
    CON, CON2 = (116, 104, 90), (104, 93, 80)
    def fl(x, d):
        c = CON if (int(x // 11) + int(d // 11)) % 2 == 0 else CON2
        if x % 11 < .6 or d % 11 < .6: c = (74, 66, 58)
        if AF + 2 < d < AF + 3.6: c = (150, 140, 108)                                                # 앞쪽 가장자리 안내선(희미한 노랑)
        if x > AL - 40: c = tuple(int(v * (.5 + .5 * (AL - x) / 40.0)) for v in c)                    # 지나온 문 쪽(오른쪽)은 조금 어둡다
        if x < 60: f = x / 60.0; c = tuple(int(v * (.08 + .92 * f)) for v in c)                       # 이동통로 쪽(왼쪽)은 검게 사라진다
        return c
    s.floor(fl, x0=0, x1=AL, d0=AF, d1=AB)
    def tiles_d(dp, x0, x1, h, c0=(156, 140, 118)):                                                  # 평면 d=dp 콘크리트 판벽(앞을 향한 면)
        for x in range(int(x0), int(x1), 6):
            for z in range(0, int(h), 6):
                n = ((int(x * 12.9898 + z * 78.233) * 2654435761) >> 7) % 100 / 100.0; c = tuple(int(v * (.92 + .14 * n)) for v in c0)
                if x % 30 < 6: c = dk(c, .85)                                                         # 판 이음
                s.poly([(x, dp, z), (x + 6.2, dp, z), (x + 6.2, dp, min(h, z + 6)), (x, dp, min(h, z + 6))], c)
    # 가장 먼 것부터: 뒤 벽 → 왼쪽 끝 벽(이동통로) → 앞 낮은 벽
    tiles_d(AB, 0, AL, 60)
    s.poly([(0, AB, 46), (AL, AB, 46), (AL, AB, 47.6), (0, AB, 47.6)], (232, 226, 200))                  # 벽에 이어진 한 줄 조명(점이 아니라 선)
    s.poly([(0, AB, 40), (AL, AB, 40), (AL, AB, 43), (0, AB, 43)], (74, 70, 64)); s.poly([(0, AB, 38.6), (AL, AB, 38.6), (AL, AB, 40), (0, AB, 40)], (50, 46, 42))   # 케이블 트레이
    for xx in (84, 232):                                                                                # 벽의 철문 둘: 왼쪽은 잠겨 있고(붉은 점), 오른쪽은 휴게실(컵 표지)
        s.poly([(xx - 1.5, AB, 0), (xx + 14.5, AB, 0), (xx + 14.5, AB, 30), (xx - 1.5, AB, 30)], (58, 52, 46)); s.poly([(xx, AB, 0), (xx + 13, AB, 0), (xx + 13, AB, 28.5), (xx, AB, 28.5)], (128, 132, 132))
        s.poly([(xx + 6.3, AB, 0), (xx + 6.7, AB, 0), (xx + 6.7, AB, 28.5), (xx + 6.3, AB, 28.5)], (92, 96, 98)); s.poly([(xx + 10, AB, 12), (xx + 11, AB, 12), (xx + 11, AB, 16), (xx + 10, AB, 16)], (70, 72, 72))
    s.poly([(88.6, AB, 33), (90.6, AB, 33), (90.6, AB, 35), (88.6, AB, 35)], (214, 70, 60))                # 잠긴 문 위 붉은 점
    s.poly([(234, AB, 32), (243, AB, 32), (243, AB, 38.5), (234, AB, 38.5)], (236, 226, 190)); s.poly([(236.8, AB, 33.2), (240.2, AB, 33.2), (240.2, AB, 35.6), (236.8, AB, 35.6)], (120, 84, 56)); s.poly([(240.2, AB, 34.2), (241.4, AB, 34.2), (241.4, AB, 35.0), (240.2, AB, 35.0)], (120, 84, 56)); s.poly([(236.8, AB, 36.2), (240.2, AB, 36.2), (240.2, AB, 36.8), (236.8, AB, 36.8)], (214, 196, 160))   # 휴게실 표지(컵)
    # 왼쪽 끝 벽(오른쪽을 향한 면): 이동통로가 열려 있다
    q0, q1 = APASS
    for d in range(AF, AB, 6):
        for z in range(0, 60, 6): s.poly([(0, d, z), (0, d + 6.2, z), (0, d + 6.2, z + 6), (0, d, z + 6)], tuple(int(v * (.92 + .1 * (((d * 7 + z * 13) % 10) / 10.0))) for v in (150, 134, 112)))
    s.holes.append(('x', 0, q0, q1)); s.zpunch([(0, q0, 0), (0, q1, 0), (0, q1, 40), (0, q0, 40)])
    for k in range(0, 40): f = k / 40.0; s.poly([(0, q0, k), (0, q1, k), (0, q1, k + 1.2), (0, q0, k + 1.2)], (int(34 - 26 * f), int(24 - 18 * f), int(16 - 12 * f)), z=False)
    s.poly([(0, q0 - 2, 0), (0, q0, 0), (0, q0, 42), (0, q0 - 2, 42)], (70, 62, 54)); s.poly([(0, q1, 0), (0, q1 + 2, 0), (0, q1 + 2, 42), (0, q1, 42)], (70, 62, 54)); s.poly([(0, q0 - 2, 40), (0, q1 + 2, 40), (0, q1 + 2, 43), (0, q0 - 2, 43)], (70, 62, 54))
    s.glow(8, (q0 + q1) / 2, 40, col=(255, 176, 76), power=.2)
    # 소화기 함(바닥에 놓인 단단한 물체): 뒤 벽 앞에
    s.box(164, AB - 6, 6, 5, 12, (170, 60, 52), (140, 48, 42), (110, 38, 34))
    # 앞쪽: 안이 보이도록 낮은 벽(윗면과 앞 단면만)
    s.box(0, 0, AL, AF, 10, (150, 134, 112), (112, 98, 84), (86, 74, 62))
    for x in range(0, AL, 4):                                                                          # 낮은 벽 위 줄 조명
        f = min(1.0, .4 + .6 * (AL - x) / 40.0) if x > 60 else max(.1, x / 60.0); s.poly([(x, 1.2, 10.2), (x + 4.2, 1.2, 10.2), (x + 4.2, 2.6, 10.2), (x, 2.6, 10.2)], tuple(int(v * f) for v in (236, 228, 196)), z=False)
    s.run(); s.lamps = []
    return s.save(name) if save else s


# ---------------- 휴게실(정비 복도 오른쪽 문 안) ----------------
LW, LD = 168, 92                                                                                  # 방 크기
LDOOR = (14, 28)                                                                                  # 들어온 문(뒤 벽, 왼쪽)의 가로 범위
def lounge(name='city3d_lounge', save=True):
    """작은 휴게실: 뒤 벽에 들어온 문·소파·자판기, 왼쪽 벽에 창, 가운데 낮은 탁자와 화분. 레이어 규칙을 따른다(단단한 것은 box)."""
    s = Scene(LW, LD, 64, k=2); s.d.rectangle([0, 0, s.img.size[0], s.img.size[1]], fill=(10, 7, 6))
    def fl(x, d):
        c = (146, 108, 76) if (int(d // 8) % 2 == 0) else (138, 101, 70)
        if x % 24 < .5 or (int(d // 8) % 2 == 0 and d % 8 < .4): c = (112, 80, 56)
        if 46 < x < 120 and 22 < d < 56: c = (88, 104, 112) if (int(x // 4) + int(d // 4)) % 2 == 0 else (82, 98, 106)   # 가운데 러그
        return c
    s.floor(fl, x0=0, x1=LW, d0=6, d1=LD)
    d0, d1 = LDOOR; s.floor(lambda x, d: (62, 54, 48) if (int(x // 3) + int(d // 3)) % 2 == 0 else (54, 47, 42), x0=d0, x1=d1, d0=0, d1=12)   # 들어온 문 앞 매트(문은 방 앞쪽 벽에 있다: 위쪽 문으로 들어왔으니 지나온 문은 뒤쪽)
    WALL1, WALL2 = (190, 176, 148), (150, 130, 104)
    def wall_d(dp, x0, x1, h):
        for x in range(int(x0), int(x1), 6):
            for z in range(0, h, 6): s.poly([(x, dp, z), (x + 6.2, dp, z), (x + 6.2, dp, min(h, z + 6)), (x, dp, min(h, z + 6))], WALL1 if z >= 14 else WALL2)
        s.poly([(x0, dp, 13.4), (x1, dp, 13.4), (x1, dp, 14.6), (x0, dp, 14.6)], (112, 94, 74))
    wall_d(LD, 0, LW, 60)
    # 왼쪽 벽(오른쪽을 향한 면)
    for d in range(6, LD, 6):
        for z in range(0, 60, 6): s.poly([(0, d, z), (0, d + 6.2, z), (0, d + 6.2, z + 6), (0, d, z + 6)], WALL1 if z >= 14 else WALL2)
    # 소파(뒤 벽 가운데): 밑판·등받이·팔걸이, 위에 벽시계
    SOF, SOFD, SOFR = (92, 122, 108), (70, 96, 84), (58, 80, 70)
    SOFT, SOFE = (118, 152, 134), (52, 74, 64)                                                         # 윗면은 밝게, 모서리선은 어두운 초록
    def part(x, d, w, dp, h, top, front, right):                                                          # 그린 바로 뒤에 모서리선: 앞의 것이 뒤의 선을 덮도록(먼 것부터)
        s.box(x, d, w, dp, h, top, front, right); outline_px(s, x, d, w, dp, h, 0, SOFE, 1)
    s.box(46, LD - 8, 56, 6, 20, SOFT, SOF, (86, 118, 102)); outline_px(s, 46, LD - 8, 56, 6, 20, 0, SOFE, 1, skip=(0, 3, 5))      # 등받이(좁은 옆면은 앞면 오른쪽 세로선과 아래 모서리선을 빼 점처럼 튀지 않게)
    ARMR = (86, 118, 102)                                                                                 # 팔걸이 안쪽 면: 등받이 앞면과 다른 밝기로 해서 서로 비쳐 보이지 않게
    part(46, LD - 22, 6, 18, 14, SOFT, SOF, ARMR)                                                          # 왼쪽 팔걸이(왼쪽이 더 멀다: 먼 쪽부터 그린다)
    part(52, LD - 22, 44, 14, 9, SOFT, SOF, SOFR)                                                         # 앉는 면: 팔걸이 사이에만 두고 팔걸이 다음에 그려 팔걸이 안쪽 면 아랫부분을 덮는다(선이 이어진다)
    for a_, b_ in (((74, LD - 22, 9), (74, LD - 8, 9)), ((74, LD - 22, 3), (74, LD - 22, 9))): s.d.line([s.P(*a_), s.P(*b_)], fill=SOFE, width=s.k)   # 쿠션 이음선(둘로 나눔)
    part(96, LD - 22, 6, 18, 14, SOFT, SOF, ARMR)                                                          # 오른쪽 팔걸이(가장 가깝다: 마지막)
    s.poly([(70, LD, 36), (82, LD, 36), (82, LD, 46), (70, LD, 46)], (70, 58, 46)); s.poly([(71.2, LD, 37.2), (80.8, LD, 37.2), (80.8, LD, 44.8), (71.2, LD, 44.8)], (236, 228, 204)); s.poly([(75.6, LD, 38.4), (76.4, LD, 38.4), (76.4, LD, 41.6), (75.6, LD, 41.6)], (60, 50, 42)); s.poly([(75.6, LD, 40.8), (79, LD, 40.8), (79, LD, 41.6), (75.6, LD, 41.6)], (60, 50, 42))
    # 자판기(뒤 벽 오른쪽): 몸통 + 밝은 진열창 + 버튼
    s.box(124, LD - 16, 22, 12, 44, (150, 60, 56), (126, 48, 46), (100, 38, 36))
    s.poly([(126, LD - 16, 14), (140, LD - 16, 14), (140, LD - 16, 40), (126, LD - 16, 40)], (236, 230, 196), z=False); s.poly([(142, LD - 16, 14), (144, LD - 16, 14), (144, LD - 16, 34), (142, LD - 16, 34)], (70, 66, 64), z=False)
    for k in range(3):
        for j in range(2): s.poly([(127.5 + j * 6.6, LD - 16, 17 + k * 7.6), (131.5 + j * 6.6, LD - 16, 17 + k * 7.6), (131.5 + j * 6.6, LD - 16, 21 + k * 7.6), (127.5 + j * 6.6, LD - 16, 21 + k * 7.6)], [(210, 90, 70), (80, 140, 190), (230, 190, 70), (110, 170, 110), (200, 110, 150), (150, 150, 160)][k * 2 + j], z=False)
    # 가운데 낮은 탁자와 의자, 화분
    s.box(62, 34, 34, 14, 7, (170, 126, 82), (134, 98, 64), (108, 78, 50), z0=0)
    s.box(64, 36, 30, 10, 1.2, (196, 150, 100), (150, 112, 76), (120, 88, 58), z0=7)
    s.box(140, 18, 9, 9, 9, (122, 82, 60), (100, 66, 48), (80, 52, 38)); s.box(137, 21, 15, 3, 9, (66, 124, 78), (50, 100, 62), (40, 80, 52), z0=9); s.box(139, 14, 11, 11, 4, (76, 138, 88), (56, 110, 68), (46, 92, 56), z0=9)   # 화분(문 자리에서 먼 오른쪽 앞)
    # 앞쪽·오른쪽: 안이 보이도록 낮은 벽
    WT, WF, WR = (150, 134, 112), (112, 98, 84), (86, 74, 62)
    s.box(0, 0, LDOOR[0] - 2, 6, 10, WT, WF, WR); s.box(LDOOR[1] + 2, 0, LW - LDOOR[1] - 2, 6, 10, WT, WF, WR); s.box(LW, 0, 6, LD, 10, WT, WF, WR)     # 앞 낮은 벽에 문 자리 틈
    s.run(); s.lamps = []
    return s.save(name) if save else s

def main():
    a, b = landing(150, False, 'city3d_landing', True, True, True, None, True), street(); landing(520, True, 'city3d_corridor'); fountain_scene(); sq_scene('recycle', 300, 'city3d_recycle'); lot_scene()
    ov = Image.new('RGB', (a.width * 2 + b.width * 2 + 50, max(a.height, b.height) * 2 + 20), (40, 40, 48))
    ov.paste(a.resize((a.width * 2, a.height * 2), Image.NEAREST), (10, 10)); ov.paste(b.resize((b.width * 2, b.height * 2), Image.NEAREST), (a.width * 2 + 40, 10))
    ov.save(os.path.join(OUT, 'city3d_overview.png')); print('city3d ok', a.size, b.size)
if __name__ == '__main__': main()
