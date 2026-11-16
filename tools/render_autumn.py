#!/usr/bin/env python3
"""터널 너머 판타지 세계: 낙엽 지는 가을 시골(완전히 다른 세계). 사선 3차원 시점(도시·집과 같은 투영).
뒤·왼쪽은 하늘과 먼 산(떠 있는 한 조각의 풍경처럼 잘린 단면), 따뜻한 호박색 빛, 흙길, 낮은 돌담, 단풍·은행·감나무, 짚더미, 허수아비, 장승, 먼 기와집.
사용: python3 tools/render_autumn.py -> maps/out/autumn_country.png (+_x2)"""
import math, os, random, sys
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from render_city3d import Scene, dk, OUT

def noise(x, d, s=0): return ((int(x * 12.9898 + d * 78.233 + s * 37.7) * 2654435761) >> 7) % 100 / 100.0
def blob(sc, cx, cy, r, cols, rng):
    """잎덩어리: 어두운 바탕 원 + 밝은 원들 + 잎 점. cols = (어둠, 중간, 밝음, 점)"""
    d = sc.d; dark, mid, lite, dot = cols
    d.ellipse([cx - r, cy - r * .85, cx + r, cy + r * .85], fill=dark)
    for _ in range(6):
        ox, oy = rng.uniform(-r * .55, r * .55), rng.uniform(-r * .5, r * .3); rr = r * rng.uniform(.38, .6)
        d.ellipse([cx + ox - rr, cy + oy - rr * .85, cx + ox + rr, cy + oy + rr * .85], fill=mid)
    for _ in range(5):
        ox, oy = rng.uniform(-r * .6, r * .2), rng.uniform(-r * .6, r * .1); rr = r * rng.uniform(.18, .3)
        d.ellipse([cx + ox - rr, cy + oy - rr * .85, cx + ox + rr, cy + oy + rr * .85], fill=lite)
    for _ in range(int(r)): d.point((int(cx + rng.uniform(-r, r) * .9), int(cy + rng.uniform(-r, r) * .7)), fill=dot)
FALL = {'red': ((120, 40, 30), (176, 66, 40), (222, 110, 56), (240, 160, 80)),
        'orange': ((140, 70, 28), (204, 112, 40), (240, 164, 66), (250, 204, 110)),
        'gold': ((150, 104, 28), (226, 170, 52), (250, 214, 100), (255, 240, 160))}

def tree(sc, x, d, h, kind, rng, spread=14):
    def draw():
        b = sc.P(x, d, 0); t = sc.P(x, d, h * .55)
        sc.d.ellipse([b[0] - 10, b[1] - 3, b[0] + 10, b[1] + 3], fill=(58, 44, 30))
        sc.d.polygon([(b[0] - 5, b[1] + 1), (b[0] - 2, b[1] - 6), (b[0] + 1, b[1] - 6), (b[0] + 4, b[1] + 1)], fill=(70, 46, 32))
        sc.d.rectangle([b[0] - 2, t[1], b[0] + 1, b[1] - 5], fill=(70, 46, 32)); sc.d.line([(b[0] + 1, t[1]), (b[0] + 1, b[1] - 5)], fill=(48, 32, 24))
        for k, gx in enumerate((-6, -4, -1, 2, 4, 6)):
            c = ((120, 100, 46), (150, 116, 44), (100, 86, 40))[k % 3]; sc.d.line([(b[0] + gx, b[1] + 1), (b[0] + gx + (1 if gx < 0 else -1), b[1] - 3 - k % 2)], fill=c)
        top = sc.P(x, d, h)
        for dx, dy, r in ((-spread * .45, 6, spread * .75), (spread * .45, 5, spread * .7), (0, -2, spread * .9), (-spread * .2, 12, spread * .6), (spread * .3, 11, spread * .6)):
            blob(sc, top[0] + dx, top[1] + dy, r, FALL[kind], rng)
    sc.jobs.append((d, draw))

def build():
    W, D, H = 112, 112, 66
    kx, kd = W / 170.0, D / 200.0
    sc = Scene(W, D, H); rng = random.Random(14); sc.img.paste((30, 22, 24), (0, 0, sc.CW, sc.CH)); sc.d = ImageDraw.Draw(sc.img)
    # 하늘(뒤 평면과 왼쪽 평면): 위는 옅은 살구색, 아래(지평선)는 호박색
    def sky(z): f = z / H; return (int(244 - 30 * f), int(196 - 40 * f), int(140 + 30 * f))
    for z in range(0, H):
        sc.poly([(0, D, z), (W, D, z), (W, D, z + 1.2), (0, D, z + 1.2)], sky(z)); sc.poly([(0, 0, z), (0, D, z), (0, D, z + 1.2), (0, 0, z + 1.2)], sky(z))
    for layer, (col, base, amp, ph) in enumerate(((  (190, 130, 100), 22, 14, 0), ((164, 104, 84), 14, 12, 2), ((132, 84, 70), 6, 10, 4))):   # 먼 산 능선 3겹
        pts = [(0, D, 0)] + [(x, D, base + amp * (.5 + .5 * math.sin(x / 26 + ph) * math.cos(x / 61 + ph))) for x in range(0, W + 1, 4)] + [(W, D, 0)]
        sc.poly(pts, col)
        pts = [(0, 0, 0)] + [(0, dd, base - 4 + amp * (.5 + .5 * math.sin(dd / 30 + ph))) for dd in range(0, D + 1, 4)] + [(0, D, 0)]
        sc.poly(pts, col)
    # 땅: 가을 풀밭 + 구불구불한 흙길
    def ground(x, d):
        c = 78 + int(noise(x, d) * 14); n = noise(x, d, 3)
        grass = (c + 40, c + 22, 40) if n < .55 else (c + 66, c + 28, 30) if n < .8 else (c + 20, c + 10, 34)
        px = 56 + 8 * math.sin(d / 16.0) + 3 * math.sin(d / 7.0)
        a = abs(x - px)
        if a < 11: return (150 + int(noise(x, d, 1) * 18), 106 + int(noise(x, d, 2) * 14), 70)
        if a < 13: return (122, 90, 56)
        return grass
    sc.floor(ground)
    # 단면(앞·오른쪽) 흙 두께
    sc.poly([(0, 0, -7), (W, 0, -7), (W, 0, 0), (0, 0, 0)], (84, 58, 40)); sc.poly([(W, 0, -7), (W, D, -7), (W, D, 0), (W, 0, 0)], (62, 42, 30))
    # 낙엽(바닥) 점
    LC = [(214, 104, 44), (236, 160, 60), (170, 56, 36), (246, 206, 92)]
    for _ in range(130):
        x, d = rng.uniform(2, W - 2), rng.uniform(2, D - 2); X, Y = sc.P(x, d, 0); sc.px[X, Y] = rng.choice(LC); sc.px[X + 1, Y] = rng.choice(LC)
    # 왼쪽 낮은 돌담
    for d in range(0, D, 10):
        for k, tone in enumerate(((120, 112, 104), (104, 96, 90), (132, 122, 112))):
            sc.box(1, d + k * 3.3, 5, 3.3, 10, tone, dk(tone, .82), dk(tone, .68))
    # 소품: 짚더미, 장승, 허수아비, 나무 울타리, 먼 기와집
    def hay(x, d):
        def f():
            b = sc.P(x, d, 0); sc.d.polygon([(b[0] - 9, b[1]), (b[0] + 9, b[1]), (b[0] + 3, b[1] - 22), (b[0] - 3, b[1] - 22)], fill=(214, 170, 78))
            for k in range(0, 18, 4): sc.d.line([(b[0] - 8 + k // 3, b[1] - k), (b[0] + 8 - k // 3, b[1] - k)], fill=(176, 132, 56))
        sc.jobs.append((d, f))
    for d in range(6, D - 8, 11): sc.box(W - 10, d, 2, 2, 10, (98, 68, 44), (80, 54, 36), (62, 42, 30)); 
    sc.box(W - 10, 6, 2, D - 14, 1.6, (98, 68, 44), (80, 54, 36), (62, 42, 30), z0=7)
    def house(x, d, w, dp, h):
        """스케치 그대로: 정면(창+문) 벽, 오른쪽 옆벽, 처마가 벽 밖으로 길게 나온 네모 지붕(앞면은 사다리꼴, 오른쪽은 모임지붕)."""
        def f():
            sc.box(x, d, w, dp, h, (236, 220, 190), (232, 214, 182), (196, 176, 146))
            o, o2, rh, dm = 4, w * .2, h * .75, d + dp / 2
            # 창(4칸)과 문
            wx0, wx1, wz0, wz1 = x + w * .12, x + w * .38, h * .42, h * .82
            sc.poly([(wx0, d, wz0), (wx1, d, wz0), (wx1, d, wz1), (wx0, d, wz1)], (96, 70, 48))
            sc.poly([(wx0 + 1, d, wz0 + 1), (wx1 - 1, d, wz0 + 1), (wx1 - 1, d, wz1 - 1), (wx0 + 1, d, wz1 - 1)], (74, 90, 120))
            mx, mz = (wx0 + wx1) / 2, (wz0 + wz1) / 2
            sc.poly([(mx - .5, d, wz0), (mx + .5, d, wz0), (mx + .5, d, wz1), (mx - .5, d, wz1)], (96, 70, 48)); sc.poly([(wx0, d, mz - .5), (wx1, d, mz - .5), (wx1, d, mz + .5), (wx0, d, mz + .5)], (96, 70, 48))
            dx0, dx1, dz1 = x + w * .58, x + w * .8, h * .72
            sc.poly([(dx0 - 1, d, 0), (dx1 + 1, d, 0), (dx1 + 1, d, dz1 + 1), (dx0 - 1, d, dz1 + 1)], (96, 70, 48)); sc.poly([(dx0, d, 0), (dx1, d, 0), (dx1, d, dz1), (dx0, d, dz1)], (132, 94, 62))
            # 지붕: 처마 아래 그늘 띠 -> 앞 사다리꼴 -> 오른쪽 모임면
            sc.poly([(x - o, d - o, h - 1), (x + w + o, d - o, h - 1), (x + w + o, d - o, h + 1), (x - o, d - o, h + 1)], (52, 50, 66))
            sc.poly([(x - o, d - o, h + 1), (x + w + o, d - o, h + 1), (x + w - o2, dm, h + rh), (x + o2, dm, h + rh)], (96, 94, 114))
            sc.poly([(x + w + o, d - o, h + 1), (x + w + o, d + dp + o, h + 1), (x + w - o2, dm, h + rh)], (70, 68, 88))
            for k in range(1, 5):                                                                                       # 기와 줄
                z = h + 1 + (rh - 1) * k / 5; ax = (x - o) + (o + o2) * k / 5; bx = (x + w + o) - (o + o2) * k / 5; dd = d - o + (dm - d + o) * k / 5
                sc.d.line([sc.P(ax, dd, z), sc.P(bx, dd, z)], fill=(84, 82, 102))
        sc.jobs.append((d, f))
    house(14, D - 34, 40, 22, 16)
    # 나무: 단풍(주황·빨강)·은행(노랑)·감나무
    for x, d, h, k, sp in ((16, 26, 42, 'orange', 11), (8, 56, 46, 'red', 11), (106, 14, 46, 'gold', 12), (102, 62, 42, 'orange', 11), (104, 94, 38, 'red', 10)):
        tree(sc, x, d, h, k, rng, sp)
    sc.run()
    # 감나무의 감(주황 점)과 떨어지는 낙엽(공중)
    for _ in range(36):
        X, Y = rng.randrange(8, sc.CW - 8), rng.randrange(8, sc.CH - 20); c = rng.choice(LC)
        if sc.px[X, Y] != (30, 22, 24) and sc.px[X, Y][0] > 60: sc.d.rectangle([X, Y, X + 1, Y + 1], fill=c)
    # 따뜻한 빛: 전체에 호박색 안개 + 위쪽에서 아래로 약한 비네팅
    ov = Image.new('RGB', sc.img.size, (255, 190, 120)); sc.img = Image.blend(sc.img, ov, .08)
    return sc

def main():
    sc = build(); out = os.path.join(OUT, 'autumn_country.png'); sc.img.save(out); sc.img.resize((sc.CW * 2, sc.CH * 2), Image.NEAREST).save(out.replace('.png', '_x2.png')); print(out, sc.img.size)
if __name__ == '__main__': main()
