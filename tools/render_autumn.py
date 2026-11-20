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
        b = sc.P(x, d, 0); t = (sc.P(x, d, 0)[0], sc.P(x, d, h)[1] + 8); pxs = sc.px     # 줄기는 잎덩어리 속까지 올라가 가려진다
        for yy in range(b[1] - 3, b[1] + 4):                                                                  # 땅에 드리운 그늘: 풀 질감은 두고 어둡게만 한다
            for xx in range(b[0] - 11, b[0] + 12):
                if ((xx - b[0]) / 11.0) ** 2 + ((yy - b[1]) / 3.5) ** 2 < 1: r_, g_, b_ = pxs[xx, yy]; pxs[xx, yy] = (int(r_ * .72), int(g_ * .72), int(b_ * .75))
        sc.d.polygon([(b[0] - 4, b[1] + 1), (b[0] - 2, b[1] - 5), (b[0] + 1, b[1] - 5), (b[0] + 3, b[1] + 1)], fill=(70, 46, 32))
        sc.d.rectangle([b[0] - 2, t[1], b[0] + 1, b[1] - 4], fill=(70, 46, 32)); sc.d.line([(b[0] + 1, t[1]), (b[0] + 1, b[1] - 4)], fill=(48, 32, 24))
        rr = random.Random(int(x * 31 + d * 17))                                                              # 줄기 밑을 주변 풀 픽셀로 덮는다(같은 색·같은 질감)
        for yy in range(b[1] - 5, b[1] + 2):
            for xx in range(b[0] - 5, b[0] + 5):
                if rr.random() < .55 + (yy - (b[1] - 5)) * .09:
                    sx = xx + rr.choice((-13, 13)); c = pxs[sx, yy]
                    if c[0] > 50 and c != (30, 22, 24): pxs[xx, yy] = (int(c[0] * .85), int(c[1] * .85), int(c[2] * .85))
        for gx in (-5, -2, 2, 5): sc.d.line([(b[0] + gx, b[1] + 1), (b[0] + gx + (1 if gx < 0 else -1), b[1] - 3)], fill=(112, 94, 40))
        top = sc.P(x, d, h)
        for dx, dy, r in ((-spread * .45, 6, spread * .75), (spread * .45, 5, spread * .7), (0, -2, spread * .9), (-spread * .2, 12, spread * .6), (spread * .3, 11, spread * .6)):
            blob(sc, top[0] + dx, top[1] + dy, r, FALL[kind], rng)
        sc.zmin_only = True; sc.zbox(x - 2, d - 1.5, 4, 3, h)                                                                          # 레이어 규칙: 줄기는 단단한 물체, 잎덩어리는 둥근 깊이
        for ox_, oz_, rr_ in ((0, 4, .95), (-.45, 2, .75), (.45, 2, .75)): sc.zsphere(x + ox_ * spread, d, h + oz_, spread * rr_)
        sc.zmin_only = False
    sc.jobs.append((d, draw))

def build(mode='original'):
    """mode='original': 처음 만든 112x112 가을 시골(집·울타리 포함, 보관용). mode='forest': 터널 출구에서 오른쪽(가로)으로 쭉 이어지는 나무 빽빽한 가을 숲."""
    FOREST = mode == 'forest'
    W, D, H = (420, 100, 66) if FOREST else (112, 112, 66)                                                                              # 공간을 넓혔다(원래 112x112): 터널 출구·흙길·집은 그대로 두고 오른쪽·뒤쪽 들판과 나무를 늘림
    sc = Scene(W, D, H); rng = random.Random(14); sc.img.paste((30, 22, 24), (0, 0, sc.CW, sc.CH)); sc.d = ImageDraw.Draw(sc.img)
    # 하늘(뒤 평면과 왼쪽 평면): 위는 옅은 살구색, 아래(지평선)는 호박색
    def sky(z): f = z / H; return (int(244 - 30 * f), int(196 - 40 * f), int(140 + 30 * f))
    for z in range(0, H):
        sc.poly([(0, D, z), (W, D, z), (W, D, z + 1.2), (0, D, z + 1.2)], sky(z)); sc.poly([(0, 0, z), (0, D, z), (0, D, z + 1.2), (0, 0, z + 1.2)], sky(z))
    for layer, (col, base, amp, ph) in enumerate(((  (190, 130, 100), 22, 14, 0), ((164, 104, 84), 14, 12, 2), ((132, 84, 70), 6, 10, 4))):   # 먼 산 능선 3겹
        pts = [(0, D, 0)] + [(x, D, base + amp * (.5 + .5 * math.sin(x / 26 + ph) * math.cos(x / 61 + ph))) for x in range(0, W + 1, 4)] + [(W, D, 0)]
        sc.poly(pts, col)
        rid = lambda u: base + amp * (.5 + .5 * math.sin(u / 26 + ph) * math.cos(u / 61 + ph))                 # 뒤 평면 능선식을 왼쪽 평면으로 그대로 이어 편다(꺾이는 모서리에서 끊김 없음)
        pts = [(0, 0, 0)] + [(0, dd, rid(-(D - dd))) for dd in range(0, D + 1, 2)] + [(0, D, 0)]
        sc.poly(pts, col)
    # 땅: 가을 풀밭 + 구불구불한 흙길
    pxm = lambda d: 56 + 8 * math.sin(d / 16.0) + 3 * math.sin(d / 7.0)
    rd = lambda x: 20 + 5 * math.sin(x / 30.0)                                                                       # 숲길: 앞쪽(아래)에 붙어 오른쪽으로 구불구불
    P0, P3 = (22.0, 20.0), ((60.0, rd(60.0)) if FOREST else (pxm(48), 48.0)); P1, P2 = (P0[0] + 26, 20.0), ((P3[0] - 12, P3[1]) if FOREST else (P3[0], 26.0))               # 터널 입구에서 시작해 부드럽게 위쪽 길과 이어지는 곡선
    bez = [tuple((1 - u) ** 3 * P0[i] + 3 * (1 - u) ** 2 * u * P1[i] + 3 * (1 - u) * u * u * P2[i] + u ** 3 * P3[i] for i in (0, 1)) for u in [k / 60.0 for k in range(61)]]
    def ground(x, d):
        c = 78 + int(noise(x, d) * 14); n = noise(x, d, 3)
        grass = (c + 40, c + 22, 40) if n < .55 else (c + 66, c + 28, 30) if n < .8 else (c + 20, c + 10, 34)
        a = min(math.hypot(x - bx, d - bd) for bx, bd in bez)
        if FOREST:
            if x >= 60: a = abs(d - rd(x))
            if a < 7.5: return (150 + int(noise(x, d, 1) * 18), 106 + int(noise(x, d, 2) * 14), 70)
            if a < 9.5: return (122, 90, 56)
            return grass
        if d >= 48: a = abs(x - pxm(d))
        if a < 7.5 + 2.5 * min(1.0, d / 40.0): return (150 + int(noise(x, d, 1) * 18), 106 + int(noise(x, d, 2) * 14), 70)
        if a < 9.5 + 2.5 * min(1.0, d / 40.0): return (122, 90, 56)
        return grass
    sc.floor(ground)
    # 단면(앞·오른쪽) 흙 두께
    sc.poly([(0, 0, -7), (W, 0, -7), (W, 0, 0), (0, 0, 0)], (84, 58, 40)); sc.poly([(W, 0, -7), (W, D, -7), (W, D, 0), (W, 0, 0)], (62, 42, 30))
    # 낙엽(바닥) 점
    LC = [(214, 104, 44), (236, 160, 60), (170, 56, 36), (246, 206, 92)]
    for _ in range(900 if FOREST else 130):
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
            sc.zbox(x - 5, d - 2.5, 10, 5, 20)                                                                     # 짚더미: 단단한 물체
        sc.jobs.append((d, f))
    if not FOREST:
        for d in range(6, D - 8, 11): sc.box(W - 10, d, 2, 2, 10, (98, 68, 44), (80, 54, 36), (62, 42, 30))
        sc.box(W - 10, 6, 2, D - 14, 1.6, (98, 68, 44), (80, 54, 36), (62, 42, 30), z0=7)
    from prop_house import house as _house
    house = lambda x, d, w, dp, h: _house(sc, x, d, w, dp, h)                                            # 집 그림은 tools/prop_house.py 에 보관
    if not FOREST: house(14, D - 34, 40, 22, 16)                                                        # 숲 맵에서는 집을 뺐다(보관: tools/prop_house.py)
    # 나무: 단풍(주황·빨강)·은행(노랑)·감나무
    if not FOREST:
        for x, d, h, k, sp in ((27, 33, 36, 'red', 10), (94, 38, 38, 'orange', 10), (97, 12, 48, 'gold', 12), (101, 70, 42, 'red', 10), (104, 98, 34, 'orange', 9)):
            tree(sc, x, d, h, k, rng, sp)
    else:                                                                                                      # 빽빽한 숲: 길 뒤쪽(위)을 나무로 가득 채운다. 길 앞쪽(아래)에는 나무를 두지 않아 길과 아이가 가려지지 않는다
        fr = random.Random(31); kinds = ['red', 'orange', 'gold', 'orange', 'red', 'gold']
        for row, d0 in enumerate(range(38, D - 4, 16)):                                                      # 줄 간격 16, 나무 간격 17(처음보다 훨씬 성기게)
            for i in range(0, int(W / 17.0)):
                x = 30 + i * 17.0 + (8.5 if row % 2 else 0) + fr.uniform(-4, 4); d = d0 + fr.uniform(-3, 3)
                if x > W - 6 or abs(d - rd(x)) < 13: continue
                tree(sc, x, d, fr.uniform(34, 54), fr.choice(kinds), rng, fr.uniform(9, 12.5))
    # 터널 출구(약간만 보임): 왼쪽 앞 구석, 풀이 덮인 언덕 속 콘크리트 아치. 오른쪽 면에 아치 입구, 흙길이 거기서 시작한다
    def portal():
        x0, x1, d0, d1, h = 4, 22, 2, 38, 28
        sc.box(x0, d0, x1 - x0, d1 - d0, h, (86, 96, 58), (120, 118, 108), (98, 98, 90))                      # 언덕(윗면 풀색) + 콘크리트 벽
        mask = Image.new('L', sc.img.size, 0); cx, hw = (d0 + d1) / 2, 11
        pts = [(x1, cx - hw, 0)] + [(x1, cx - hw * math.cos(math.pi * k / 20), 12 + 9 * math.sin(math.pi * k / 20)) for k in range(21)] + [(x1, cx + hw, 0)]
        ImageDraw.Draw(mask).polygon([sc.P(*q) for q in pts], fill=255)
        lay = sc.img.copy(); ld = ImageDraw.Draw(lay)
        ld.polygon([sc.P(x1, d0, 0), sc.P(x1, d1, 0), sc.P(x1, d1, h), sc.P(x1, d0, h)], fill=(18, 20, 34))
        ld.polygon([sc.P(x1 - 14, cx - hw, 0), sc.P(x1, cx - hw, 0), sc.P(x1, cx + hw, 0), sc.P(x1 - 14, cx + hw, 0)], fill=(30, 34, 56))   # 안쪽 바닥(차가운 푸른 기운)
        sc.img.paste(lay, (0, 0), mask); sc.px = sc.img.load(); sc.d = ImageDraw.Draw(sc.img); sc.zclear(mask); sc.holes.append(('x', x1, cx - hw, cx + hw))     # 아치 입구는 걸어 들어갈 수 있는 구멍
        for k in range(21):                                                                                          # 아치 테두리(밝은 콘크리트)
            a = sc.P(x1, cx - hw * math.cos(math.pi * k / 20), 12 + 9 * math.sin(math.pi * k / 20)); sc.d.rectangle([a[0], a[1] - 2, a[0] + 1, a[1]], fill=(150, 148, 138))
        LC2 = [(214, 104, 44), (236, 160, 60), (170, 56, 36), (246, 206, 92), (190, 80, 40)]; rl = random.Random(77)
        for _ in range(520):                                                                                         # 언덕 위에 쌓인 낙엽(윗면을 거의 덮는다)
            X, Y = sc.P(rl.uniform(x0, x1), rl.uniform(d0, d1), h); sc.d.rectangle([X, Y, X + 1, Y + 1], fill=rl.choice(LC2))
        for _ in range(150):                                                                                         # 아치 윗부분으로 흘러내린 낙엽: 입구 윗선을 가린다
            q = sc.P(x1, cx + rl.uniform(-hw, hw), 21 + rl.uniform(-4, 5)); y0_ = q[1] + rl.randint(-4, 0); sc.d.rectangle([q[0], y0_, q[0] + 1, y0_ + rl.randint(1, 3)], fill=rl.choice(LC2))
        for _ in range(110):                                                                                         # 입구 오른쪽 바닥 모서리의 낙엽 더미
            q = sc.P(x1 + rl.uniform(0, 3), cx + hw * rl.uniform(.15, 1.1), rl.uniform(0, 5)); sc.d.rectangle([q[0], q[1], q[0] + 1, q[1] + 1], fill=rl.choice(LC2))
    sc.jobs.append((20, portal))
    sc.run()
    # 감나무의 감(주황 점)과 떨어지는 낙엽(공중)
    for _ in range(36):
        X, Y = rng.randrange(8, sc.CW - 8), rng.randrange(8, sc.CH - 20); c = rng.choice(LC)
        if sc.px[X, Y] != (30, 22, 24) and sc.px[X, Y][0] > 60: sc.d.rectangle([X, Y, X + 1, Y + 1], fill=c)
    # 따뜻한 빛: 전체에 호박색 안개 + 위쪽에서 아래로 약한 비네팅
    ov = Image.new('RGB', sc.img.size, (255, 190, 120)); sc.img = Image.blend(sc.img, ov, .08)
    if FOREST:                                                                                                  # 오른쪽 끝(아직 안 이어진 곳)은 검게 사라지는 그라데이션: 이동 통로 표시
        import numpy as np
        arr = np.array(sc.img.convert('RGB')).astype(float); Xs = np.arange(arr.shape[1])[None, :, None]; u = np.clip((Xs - (sc.X0 + W - 70)) / 70.0, 0, 1) * .94
        sc.img = Image.fromarray((arr * (1 - u) + np.array([6, 7, 16]) * u).astype('uint8'))
    return sc

def main():
    sc = build(sys.argv[1] if len(sys.argv) > 1 else 'original'); out = os.path.join(OUT, 'autumn_country.png' if len(sys.argv) < 2 else 'autumn_%s.png' % sys.argv[1]); sc.img.save(out); sc.img.resize((sc.CW * 2, sc.CH * 2), Image.NEAREST).save(out.replace('.png', '_x2.png')); print(out, sc.img.size)
if __name__ == '__main__': main()
