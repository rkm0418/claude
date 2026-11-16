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
    def wall_left(s, d0, d1, h, x=0, seed=1):
        """왼쪽 건물 벽(안쪽 면)과 창. 평면 x 고정, 깊이 d0..d1."""
        r = random.Random(seed)
        s.poly([(x, d0, 0), (x, d1, 0), (x, d1, h), (x, d0, h)], WALL)
        for z in range(10, int(h) - 4, 12): s.poly([(x, d0, z), (x, d1, z), (x, d1, z + .8), (x, d0, z + .8)], WALLD)
        for dd in range(int(d0) + 6, int(d1) - 8, 16):
            for z in range(14, int(h) - 8, 12):
                c = WIN_OFF
                s.poly([(x, dd, z), (x, dd + 8, z), (x, dd + 8, z + 6), (x, dd, z + 6)], c)
        s.poly([(x, d0, h - 3), (x, d1, h - 3), (x, d1, h), (x, d0, h)], dk(WALL, .7))
    def wall_back(s, x0, x1, d, h, seed=2, sign=False):
        r = random.Random(seed)
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
def asphalt(x, d): return ASPH2 if (int(x * 7 + d * 3) % 11 == 0) else ASPH

# ---------------- 장면 1: 광장 ----------------
def landing():
    W, D = 150, 80; s = Scene(W, D, 70); rng = random.Random(5)
    s.floor(paving)
    s.floor(lambda x, d: (CURBT if d < 1 else asphalt(x, d)), x0=96, x1=W)                     # 오른쪽 차도(출구)
    for k in range(0, D - 8, 10):                                                                 # 횡단보도 줄
        s.poly([(100, k + 2, 0), (W, k + 2, 0), (W, k + 7, 0), (100, k + 2 + 5, 0)], PAINT)
    s.poly([(82, 36, 0), (88, 36, 0), (88, 33, 0), (94, 40, 0), (88, 47, 0), (88, 44, 0), (82, 44, 0)], (150, 150, 138))  # 출구 화살표(바닥)
    s.glow(30, 30, 70, power=.35); s.glow(100, 40, 44, power=.5)
    s.wall_back(0, W, D, 60, sign=True); s.wall_left(0, D, 60)
    s.lamp(100, 56, 44, -1); s.lamp(132, 18, 44, -1)
    # 인공 수풀 화단(왼쪽 안쪽): 낮은 콘크리트 화단 위에 같은 모양의 덩어리
    px0, pd0, pw, pdp, ph = 12, 38, 70, 30, 9
    s.box(px0, pd0, pw, pdp, ph, (60, 64, 88), (66, 70, 96), (52, 56, 80))
    s.poly([(px0, pd0, ph), (px0 + pw, pd0, ph), (px0 + pw, pd0 + pdp, ph), (px0, pd0 + pdp, ph)], (48, 40, 36))   # 흙
    def clump(x, d, r=9, dent=0):
        def draw():
            cx, cy = s.P(x, d, ph + 8 - dent); hedge(s.d, cx, cy, r, rng)
        s.jobs.append((d, draw))
    for x in range(20, 80, 12):
        for d, dent in ((62, 0), (51, 0), (41, 0)):
            if d == 51 and 38 < x < 66: continue                                                   # 가운데는 움푹(아이가 있는 곳)
            clump(x, d, 9, dent)
    for x in (44, 56): clump(x, 58, 9, 6)                                                         # 꺼진 덩어리
    ch = Image.open(os.path.join(SPR, 'child8', 'child_d_idle.png')).convert('RGBA'); ch = ch.resize((21, 36), Image.NEAREST)
    def child():
        cx, cy = s.P(50, 50, ph + 2); s.img.paste(ch, (cx - 10, cy - 30), ch)
    s.jobs.append((52, child))
    for _ in range(26):                                                                            # 흩어진 잎
        lx, ld = rng.uniform(20, 84), rng.uniform(26, 38)
        px_, py_ = s.P(lx, ld, 0); s.px[px_, py_] = (60, 150, 80); s.px[px_ + 1, py_] = (46, 122, 66)
    # 소품: 벤치, 쓰레기통
    s.box(96, 62, 16, 5, 4, (74, 58, 46), (56, 44, 36), (44, 34, 28), z0=5); s.box(98, 62, 2, 4, 5, POLE, POLE, POLE); s.box(110, 62, 2, 4, 5, POLE, POLE, POLE)
    s.run(); return s.save('city3d_landing')

# ---------------- 장면 2: 긴 거리 ----------------
def street():
    W, D = 112, 360; s = Scene(W, D, 80); rng = random.Random(9)
    s.floor(paving, x0=0, x1=28, z=3); s.floor(paving, x0=84, x1=W, z=3)                          # 인도(연석만큼 높음)
    s.floor(asphalt, x0=28, x1=84)
    s.poly([(28, 0, 0), (28, 0, 3), (28, D, 3), (28, D, 0)], CURBF); s.poly([(84, 0, 0), (84, 0, 3), (84, D, 3), (84, D, 0)], CURBR)
    # 도로 표시: 가운데의 큰 직사각형 네 개(맨 위 하나는 비스듬히)
    quads = [(120, 38), (190, 40), (250, 36), (304, 42)]
    for i, (d, ln) in enumerate(quads):
        sk = 5 if i == 0 else 0
        s.poly([(51 + sk, d, 0), (61 + sk, d, 0), (61, d + ln, 0), (51, d + ln, 0)] if i == 0 else [(51, d, 0), (61, d, 0), (61, d + ln, 0), (51, d + ln, 0)], PAINT)
    for k in range(10, 360, 24): s.poly([(31, k, 0), (32.5, k, 0), (32.5, k + 8, 0), (31, k + 8, 0)], (150, 150, 130)); s.poly([(79.5, k, 0), (81, k, 0), (81, k + 8, 0), (79.5, k + 8, 0)], (150, 150, 130))
    for k in range(0, 40, 8): s.poly([(30, 4 + k, 0), (82, 4 + k, 0), (82, 8 + k, 0), (30, 8 + k, 0)], PAINT)   # 아래쪽 횡단보도(광장 쪽)
    for ld in (70, 160, 250, 330): s.glow(26 if ld % 160 else 70, ld, 40, power=.5)
    s.wall_left(0, D, 68, seed=4); s.wall_back(0, W, D, 56, seed=6)
    for i, (x, d, side) in enumerate([(24, 70, 1), (88, 130, -1), (24, 220, 1), (88, 290, -1), (24, 340, 1)]): s.lamp(x, d, 46, side)
    s.glow(88, 130, 40, power=.5); s.glow(88, 290, 40, power=.5)
    s.box(10, 100, 5, 18, 5, (74, 58, 46), (56, 44, 36), (44, 34, 28), z0=4); s.box(10, 102, 3, 2, 4, POLE, POLE, POLE, z0=3); s.box(10, 114, 3, 2, 4, POLE, POLE, POLE, z0=3)
    s.box(96, 190, 8, 8, 10, (60, 64, 88), (50, 54, 78), (40, 44, 66), z0=3)                      # 쓰레기통
    s.box(14, 270, 5, 5, 9, (70, 70, 96), (96, 40, 40), (70, 30, 30), z0=3)                       # 소화전
    for d in range(30, 360, 60):                                                                   # 오른쪽 가장자리 난간(잘린 단면 쪽)
        s.box(108, d, 2, 2, 12, POLE, POLE, POLE, z0=3)
    s.run(); return s.save('city3d_street')

def main():
    a, b = landing(), street()
    ov = Image.new('RGB', (a.width * 2 + b.width * 2 + 50, max(a.height, b.height) * 2 + 20), (40, 40, 48))
    ov.paste(a.resize((a.width * 2, a.height * 2), Image.NEAREST), (10, 10)); ov.paste(b.resize((b.width * 2, b.height * 2), Image.NEAREST), (a.width * 2 + 40, 10))
    ov.save(os.path.join(OUT, 'city3d_overview.png')); print('city3d ok', a.size, b.size)
if __name__ == '__main__': main()
