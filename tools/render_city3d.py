#!/usr/bin/env python3
"""추락 이후 밤 도시 — 처음 집(방·복도·베란다)과 같은 사선 3차원 시점. 투영 X = X0 + x + .5d, Y = Y0 - .5d - z.
보이는 면: 앞면, 윗면, 오른쪽 면. 왼쪽은 건물 벽(안쪽 면이 보임), 오른쪽·앞은 잘라낸 단면.
장면 1: 광장(인공 수풀 화단에서 시작, 오른쪽이 출구)  장면 2: 세로로 긴 거리(인도 | 도로 | 인도, 도로 위 표시 네 개).
사용: python3 tools/render_city3d.py -> maps/out/city3d_landing.png, city3d_street.png, city3d_overview.png (+ _x2)"""
import math, os, random, sys
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
    def __init__(s, W, D, H, pad=8):
        s.W, s.D, s.pad = W, D, pad; s.CW = int(W + .5 * D + pad * 2); s.CH = int(H + .5 * D + pad * 2)
        s.X0, s.Y0 = pad, s.CH - pad
        s.img = Image.new('RGB', (s.CW, s.CH), (12, 14, 30)); s.d = ImageDraw.Draw(s.img); s.px = s.img.load()
        s.jobs = []                                     # (깊이, 그리기 함수) — 먼 것부터
    def P(s, x, d, z=0): return (round(s.X0 + x + .5 * d), round(s.Y0 - .5 * d - z))
    def poly(s, pts, col): s.d.polygon([s.P(*p) for p in pts], fill=col)
    def floor(s, fn, x0=0, x1=None, d0=0, d1=None, z=0):
        """바닥(높이 z) 영역을 화소마다 칠한다. fn(x, d) -> 색 또는 None."""
        x1 = s.W if x1 is None else x1; d1 = s.D if d1 is None else d1
        for Y in range(int(s.Y0 - .5 * d1 - z) - 1, int(s.Y0 - .5 * d0 - z) + 2):
            d = (s.Y0 - z - Y - .5) / .5
            if not (d0 <= d < d1): continue
            for X in range(int(s.X0 + x0), int(s.X0 + x1 + .5 * d1) + 2):
                x = X + .5 - s.X0 - .5 * d
                if x0 <= x < x1 and 0 <= X < s.CW and 0 <= Y < s.CH:
                    c = fn(x, d)
                    if c: s.px[X, Y] = c
    def glow(s, x, d, r, col=LAMPC, power=.5, z=0):
        cx, cy = s.P(x, d, z)
        for Y in range(max(0, cy - r // 2 - 1), min(s.CH, cy + r // 2 + 2)):
            for X in range(max(0, cx - r), min(s.CW, cx + r + 1)):
                q = math.hypot(X - cx, (Y - cy) * 2)
                if q < r:
                    f = round((1 - q / r) ** 2.2 * power * 8) / 8; p = s.px[X, Y]
                    s.px[X, Y] = tuple(int(p[i] + (col[i] - p[i]) * f) for i in range(3))
    def box(s, x, d, w, dp, h, top, front, right, z0=0):
        s.poly([(x, d, z0 + h), (x + w, d, z0 + h), (x + w, d + dp, z0 + h), (x, d + dp, z0 + h)], top)
        s.poly([(x, d, z0), (x + w, d, z0), (x + w, d, z0 + h), (x, d, z0 + h)], front)
        s.poly([(x + w, d, z0), (x + w, d + dp, z0), (x + w, d + dp, z0 + h), (x + w, d, z0 + h)], right)
    def lamp(s, x, d, h=46, side=1):
        """가로등: 기둥 + 꺾인 팔 + 등. 불빛은 바닥에 번진다(등 아래)."""
        def draw():
            b = s.P(x, d, 0); t = s.P(x, d, h); tt = s.P(x + side * 9, d, h + 1)
            s.d.rectangle([b[0] - 1, b[1] + 0, b[0] + 1, b[1] + 1], fill=dk(POLE, .7))
            s.d.line([b, t], fill=POLE, width=2); s.d.line([t, tt], fill=POLE, width=2)
            s.d.rectangle([tt[0] - 3, tt[1], tt[0] + 3, tt[1] + 2], fill=(255, 228, 164)); s.d.line([tt[0] - 3, tt[1] - 1, tt[0] + 3, tt[1] - 1], fill=(96, 98, 124))
        s.jobs.append((d, draw)); s.glow(x + side * 9, d, 30, power=.55)
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
        s.img.save(os.path.join(OUT, name + '.png')); s.img.resize((s.CW * 2, s.CH * 2), Image.NEAREST).save(os.path.join(OUT, name + '_x2.png'))
        return s.img

def paving(x, d):
    c = PAVE2 if ((int(x // 16) + int(d // 16)) % 3 == 0) else PAVE
    return JOINT if (x % 16 < 1 or d % 16 < 1) else c
def asphalt(x, d): return ASPH

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
    s.img.paste(lay, (0, 0), mask); s.px = s.img.load(); s.d = ImageDraw.Draw(s.img)
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
        s.img.paste(lay, (0, 0), mask); s.px = s.img.load(); s.d = ImageDraw.Draw(s.img)
        for q in pts[1:-1]:                                                                                  # 아치 테두리(밝은 콘크리트 띠)
            a = s.P(*q); s.d.rectangle([a[0], a[1] - 3, a[0] + 1, a[1]], fill=(74, 80, 112))
        return
    for xx in (x0 + 4, x0 + 7): poly([(xx, D + depth, z), (xx + 1.5, D + depth, z), (xx + 1.5, D + depth, h), (xx, D + depth, h)], (34, 38, 60))   # 배관
    poly([(x0 + 14, D + depth, z), (x0 + 23, D + depth, z), (x0 + 23, D + depth, z + 24), (x0 + 14, D + depth, z + 24)], (22, 20, 34))           # 막다른 문
    poly([(x0 + 18, D + depth, z + 26), (x0 + 20, D + depth, z + 26), (x0 + 20, D + depth, z + 28), (x0 + 18, D + depth, z + 28)], (58, 54, 46))  # 꺼진 전구
    s.img.paste(lay, (0, 0), mask); s.px = s.img.load(); s.d = ImageDraw.Draw(s.img)

# ---------------- 장면 1: 광장 ----------------
def landing(W=150, corridor=False, name='city3d_landing', bed=True, save=True, baked=True, fade=None, dent=True):
    D = 80; s = Scene(W, 120 if corridor else D, 130 if corridor else 70); rng = random.Random(5)
    if corridor:                                                                                   # 같은 보도블록 바닥의 긴 복도: 앞쪽은 낮은 연석, 맨 끝은 아래(앞)로 열려 어둠으로 나간다
        EX = W
        s.floor(paving, x0=0, x1=W, d0=34, d1=D)
        s.box(0, 31, W, 3, 4, CURBT, CURBF, CURBR)
    else: s.floor(paving)
    if baked: s.glow(30, 30, 70, power=.35)
    if corridor:
        s.box(0, D, W, 14, 6, CURBT, CURBF, CURBR)                                                  # 위쪽(뒤) 연석
        bx = 0; br = random.Random(11)
        while bx < W:                                                                              # 연석 너머: 불 꺼진 현대 건물들
            bw = br.randint(40, 70); bh = br.randint(70, 125); bd = br.randint(24, 34); g = br.randint(4, 10); c = br.choice(((22, 24, 46), (26, 28, 50), (20, 22, 40)))
            s.box(bx, D + 16, bw, bd, bh, dk(c, 1.15), c, dk(c, .7))
            def wins(bx=bx, bw=bw, bh=bh):
                for xx in range(int(bx) + 5, int(bx + bw) - 8, 10):
                    for zz in range(8, int(bh) - 8, 12): s.poly([(xx, D + 16, zz), (xx + 5, D + 16, zz), (xx + 5, D + 16, zz + 7), (xx, D + 16, zz + 7)], (14, 16, 32))
            s.jobs.append((D + 15.5, wins)); bx += bw + g
    else: s.wall_back(0, W, D, 60)
    if bed: s.wall_left(0, D, 60)
    s.lamp(140, 74, 44, -1)
    if corridor:
        for lx in range(210, W - 40, 70): s.lamp(lx, 74, 44, -1)                                 # 같은 가로등을 뒷벽 쪽 한 줄로 나열
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
                cx, cy = s.P(x, d, ph + 8 - dent); hedge(s.d, cx, cy, r, rng)
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
                u = (X - (s.X0 + W - 46)) / 46.0 if side == 'r' else ((s.X0 + 46) - X) / 46.0
                if u <= 0: continue
                f = min(1.0, u) * .92
                for Y in range(s.CH): q = s.px[X, Y]; s.px[X, Y] = tuple(int(v * (1 - f) + (6, 7, 16)[i] * f) for i, v in enumerate(q))
    s.lampx = list(range(140, W - 40, 70)) if corridor else [140]
    return s.save(name) if save else s

# ---------------- 장면 2: 긴 거리 (새벽 직전의 큰 도시: 길고 넓다) ----------------
def street():
    W, D = 176, 520; s = Scene(W, D, 84); rng = random.Random(9)
    for Y in range(s.CH):                                                    # 새벽 직전: 아래(먼 쪽 아님) 가장자리로 갈수록 살짝 밝은 남색
        f = Y / s.CH; c = (int(14 + 12 * f), int(16 + 14 * f), int(36 + 30 * f))
        s.d.line([(0, Y), (s.CW, Y)], fill=c)
    LS, RS = 36, 140                                                          # 도로 x 범위 36..140 (폭 104, 4차로 느낌)
    s.floor(paving, x0=0, x1=LS, z=3); s.floor(paving, x0=RS, x1=W, z=3); s.floor(asphalt, x0=LS, x1=RS)
    s.poly([(LS, 0, 0), (LS, 0, 3), (LS, D, 3), (LS, D, 0)], CURBF); s.poly([(RS, 0, 0), (RS, 0, 3), (RS, D, 3), (RS, D, 0)], CURBR)
    # 도로 표시: 얇고 길고 간격이 넓은 네 개(맨 위 하나만 비스듬히)
    for x in (87, 89): s.poly([(x, 76, 0), (x + 1, 76, 0), (x + 1, D, 0), (x, D, 0)], (196, 170, 90))   # 얇은 이중 중앙선(횡단보도 뒤부터 끝까지)
    for k in range(10, D, 28):                                                # 차로 점선(가장자리 선, 얇게)
        for x in (LS + 3, RS - 4): s.poly([(x, k, 0), (x + 1.5, k, 0), (x + 1.5, k + 9, 0), (x, k + 9, 0)], (150, 150, 130))
        for x in (62, 114): s.poly([(x, k, 0), (x + 1.5, k, 0), (x + 1.5, k + 7, 0), (x, k + 7, 0)], (110, 110, 100))
    # 횡단보도 + 신호등(첫 가로등 자리): 얇은 줄 여러 개, 줄은 차가 가는 방향
    for x in range(LS + 4, RS - 4, 7): s.poly([(x, 56, 0), (x + 3, 56, 0), (x + 3, 74, 0), (x, 74, 0)], PAINT)
    s.poly([(LS, 52, 0), (RS, 52, 0), (RS, 53, 0), (LS, 53, 0)], (150, 150, 130))        # 정지선
    for x, c in ((LS - 6, (230, 60, 60)), (RS + 6, (230, 60, 60))):               # 보행 신호등(빨간불 점등)
        def sig(x=x, c=c):
            b = s.P(x, 56, 3); t = s.P(x, 56, 30)
            s.d.line([b, t], fill=POLE, width=2); s.d.rectangle([t[0] - 3, t[1] - 8, t[0] + 3, t[1] + 1], fill=(30, 32, 48)); s.d.rectangle([t[0] - 1, t[1] - 7, t[0] + 1, t[1] - 5], fill=c); s.d.point((t[0], t[1] - 2), fill=(30, 90, 50))
        s.jobs.append((56, sig)); s.glow(x, 56, 18, col=(230, 60, 60), power=.35, z=3)
    s.wall_left(0, D, 72, seed=4); s.wall_back(0, W, D, 60, seed=6)
    # 왼쪽 건물 벽에 골목 입구: 광장으로 이어지는 통로(아래) + 골목 3개. 모두 어둡다.
    alley(s, 14, 44, 'link', depth=34); alley_back(s, 36, 140, h=46, z=0, depth=40, road=True)
    s.box(176, 236, 40, 56, 30, (22, 24, 44), (16, 18, 34), (12, 14, 28)); s.box(176, 292, 40, 30, 20, (22, 24, 44), (16, 18, 34), (12, 14, 28))   # 오른쪽: 골목 대신 막힌 구조물
    for x, d, side in [(30, 170, 1), (146, 240, -1), (30, 330, 1), (146, 400, -1), (30, 452, 1)]: s.lamp(x, d, 50, side)
    s.box(12, 200, 5, 18, 5, (74, 58, 46), (56, 44, 36), (44, 34, 28), z0=4); s.box(12, 202, 3, 2, 4, POLE, POLE, POLE, z0=3); s.box(12, 214, 3, 2, 4, POLE, POLE, POLE, z0=3)
    s.box(158, 270, 8, 8, 10, (60, 64, 88), (50, 54, 78), (40, 44, 66), z0=3)
    s.box(14, 420, 5, 5, 9, (70, 70, 96), (96, 40, 40), (70, 30, 30), z0=3)
    for d in range(30, D, 60):
        s.box(172, d, 2, 2, 12, POLE, POLE, POLE, z0=3)
    s.run(); return s.save('city3d_street')

def main():
    a, b = landing(), street(); landing(520, True, 'city3d_corridor')
    ov = Image.new('RGB', (a.width * 2 + b.width * 2 + 50, max(a.height, b.height) * 2 + 20), (40, 40, 48))
    ov.paste(a.resize((a.width * 2, a.height * 2), Image.NEAREST), (10, 10)); ov.paste(b.resize((b.width * 2, b.height * 2), Image.NEAREST), (a.width * 2 + 40, 10))
    ov.save(os.path.join(OUT, 'city3d_overview.png')); print('city3d ok', a.size, b.size)
if __name__ == '__main__': main()
