#!/usr/bin/env python3
"""베란다 바깥, 어둑어둑한 숲 버전(수미상관의 마지막 장면). 사선 시점, 방·복도 숲 버전과 같은 구성.
하늘 = 안개 낀 숲 속(먼 나무 실루엣, 반딧불), 뒤쪽 철창 = 부러진 나무 울타리, 왼쪽 벽 = 거대한 나무 둥치, 바닥 = 썩은 널빤지 + 이끼·낙엽,
의자·탁자 = 부서진 나무.  사용: python3 tools/render_balcony_forest.py -> maps/out/4_balcony_forest.png (+_x2,_x5)"""
import os, random, sys
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render_maps as R
from forest_draw import leafy, trunk as tdraw, fir, canopy

SK = SS = .5
W, D, PAD, RAIL, SKY = 80, 48, 6, 26, 40
CW, CH = int(PAD * 2 + W + SK * D), int(PAD * 2 + SKY + RAIL + SS * D)
X0, Y0 = PAD, CH - PAD
WOOD, WOODL, WOODD = (70, 58, 92), (100, 86, 128), (40, 32, 58)

def main():
    lib = R.load_library(); rng = random.Random(5); fr = random.Random(33)
    img = Image.new('RGBA', (CW, CH), (0, 0, 0, 255)); px = img.load()
    def put(x, y, c):
        if 0 <= x < CW and 0 <= y < CH: px[int(x), int(y)] = c + (255,) if len(c) == 3 else c
    # 배경(참고 이미지: 안개 낀 울창한 남보라 밤 숲): 하늘 → 아주 흐린 먼 전나무 → 조금 진한 중간 전나무 → 안개띠 → 덤불, 양옆에 활엽수 둥치와 잎
    by = Y0 - SS * D; top_rail = by - RAIL
    for y in range(CH):
        t = min(1, max(0, y / (by + 1)))
        for x in range(CW): put(x, y, (int(12 + 20 * t), int(14 + 24 * t), int(34 + 40 * t)))
    xl, xr = int(X0 + SK * D) + 4, CW - 4
    def scatter(n, hmin, hmax, wr, base_lo, base_hi, cols, trunkc=None, margin=6):
        """원근법: 멀수록(base 가 높을수록) 작고 흐리며, 위치·높이·너비·단 수가 제각각이다."""
        xs = sorted(rng.randrange(xl - margin, xr + margin) for _ in range(n))
        for cx in xs:
            base = rng.randrange(base_lo, base_hi + 1); depth = (by - base) / max(1, by - base_lo)     # 1=가장 멀다, 0=가까움
            h = int(rng.randrange(hmin, hmax + 1) * (1 - .35 * depth)); w = int(h * rng.uniform(.5, .75))
            fir(put, cx, base, h, w, *cols, trunkc, rng=rng, n=rng.choice((4, 5, 6)))
    scatter(9, 22, 34, .7, int(by) - 18, int(by) - 9, ((30, 34, 70), (34, 38, 78), (40, 44, 88)))          # 먼 전나무: 작고 흐리며 높은 곳에
    scatter(6, 30, 42, .7, int(by) - 10, int(by) - 3, ((20, 24, 52), (26, 30, 62), (34, 40, 76)), (20, 18, 36))   # 중간
    for yy in range(int(by) - 30, int(by) + 1):                            # 안개띠: 지평선 쪽이 밝아져 뒤쪽 나무가 묻힘
        for x in range(CW):
            r_, g_, b_, a_ = px[x, yy]; k = ((yy - (by - 30)) / 30) ** 1.5 * .5; px[x, yy] = (int(r_ + (52 - r_) * k), int(g_ + (58 - g_) * k), int(b_ + (104 - b_) * k), 255)
    fir(put, CW - 40, int(by) + 3, 60, 40, (14, 28, 40), (20, 40, 54), (30, 58, 72), (30, 24, 40), rng=rng, n=6)     # 앞쪽 큰 전나무(가장 크고 진함)
    fir(put, int(X0 + SK * D) + 20, int(by) + 1, 44, 30, (14, 28, 40), (20, 40, 54), (30, 58, 72), (30, 24, 40), rng=rng, n=5)
    for _ in range(12):                                                    # 덤불(울타리 뒤)
        cx = rng.randrange(int(X0 + SK * D), CW); cy = int(by) - rng.randrange(1, 7)
        leafy(lambda x, y, c: put(x, y, c) if y < by else None, cx, cy, rng.randrange(4, 7), rng, (12, 26, 38), (20, 44, 54), (32, 66, 74))
    for cx in (CW - 6,):                                                   # 오른쪽 끝 활엽수 둥치
        tdraw(put, cx, 8, 24, int(by) + 4, (28, 24, 54), (44, 38, 80), (18, 16, 36), rng, root=12)
    for _ in range(6):                                                     # 반딧불: 청록빛
        sx = rng.randrange(int(X0 + SK * D) + 6, CW - 16); sy = rng.randrange(24, int(top_rail) - 2)
        put(sx, sy, (170, 220, 230)); put(sx + 1, sy, (80, 120, 150))
    # 뒤쪽 울타리: 부러진 나무 기둥(높이 제각각, 일부는 사라짐), 기울어진 가로대
    bx0, bx1 = int(X0 + SK * D), int(X0 + SK * D + W)
    # (울타리는 그리지 않는다: 바닥 끝이 바로 숲으로 열려 있음)
    # 바닥: 썩은 널빤지(가로, 틈과 구멍) + 이끼·낙엽
    rows, d0 = [], 0.0
    while d0 < D: rows.append((d0, d0 + fr.uniform(6, 12))); d0 = rows[-1][1]
    cols = [(52, 48, 76), (44, 40, 66), (58, 54, 86), (38, 54, 66), (48, 44, 72)]
    info = []
    for _ in rows:
        js, xj = [], fr.uniform(-40, 0)
        while xj < W + 40: xj += fr.uniform(20, 56); js.append(xj)
        info.append((js, [tuple(max(0, v + fr.randint(-4, 4)) for v in fr.choice(cols)) for _ in js]))
    holes = []                             # (x, 깊이 d, 가로, 세로) 구멍
    for Y in range(int(Y0 - SS * D), int(Y0) + 1):
        d = (Y0 - Y - .5) / SS
        if not (0 <= d < D): continue
        ri = next(i for i, r in enumerate(rows) if r[0] <= d < r[1]) if d < rows[-1][1] else len(rows) - 1
        js, cl = info[ri]
        for X in range(int(X0), int(X0 + W + SK * D) + 1):
            x = X + .5 - X0 - SK * d
            if not (0 <= x < W): continue
            n = next((k for k, jx in enumerate(js) if x < jx), len(js) - 1); c = cl[n]
            if d - rows[ri][0] < 1.6: c = (18, 16, 34)
            elif n > 0 and x - js[n - 1] < 1: c = (18, 16, 34)
            elif fr.random() < .05: c = (30, 70, 68) if fr.random() < .6 else (70, 62, 100)             # 이끼·낙엽
            for hx, hd, hw, hh in holes:                                   # 썩어 내려앉은 구멍
                if hx <= x < hx + hw and hd <= d < hd + hh: c = (4, 4, 12)
            px[X, Y] = c + (255,)
    # 왼쪽 벽: 거대한 나무 둥치
    WH = RAIL + 24
    bark = lib['wall_forest_a']; barkb = lib['wall_base_forest_a']
    for X in range(int(X0), int(X0 + SK * D) + 1):
        d = (X + .5 - X0) / SK
        if not (0 <= d < D): continue
        for Y in range(int(Y0 - SS * d - WH), int(Y0 - SS * d) + 1):
            z = (Y0 - SS * d) - (Y + .5)
            if not (0 <= z < WH): continue
            if z < 10: r_, g_, b_, a_ = barkb.load()[int(d) % 16, 15 - int(z)]
            else:
                bx = int(d) % 7; c0 = (40, 34, 66) if bx else (24, 20, 44)
                if (int(d) * 3 + int(z) // 3) % 11 == 0: c0 = (20, 16, 38)
                r_, g_, b_, a_ = c0 + (255,)
            px[X, Y] = (int(r_ * .9), int(g_ * .9), int(b_ * .95), 255)
    # 가구: 부서진 나무 의자·탁자(오른쪽 끝, 의자가 앞)
    def put_sprite(name, x, d):
        s = lib[name]; img.alpha_composite(s, (int(X0 + x + SK * d - s.width / 2), int(Y0 - SS * d - s.height)))
    put_sprite('broken_table', 66, 26); put_sprite('broken_chair', 58, 18)
    wd, wz = 22, 22                                                   # 벽 횃불: 왼쪽 벽(깊이 22칸), 바닥에서 22칸 위
    tspr = lib['torch_wall']; img.alpha_composite(tspr, (int(X0 + SK * wd - 4), int(Y0 - SS * wd - wz - 14)))
    tx, ty = int(X0 + SK * wd + 1), int(Y0 - SS * wd - wz - 8)          # 횃불 불꽃 위치
    for Y in range(max(0, ty - 34), min(CH, ty + 34)):
        for X in range(max(0, tx - 34), min(CW, tx + 34)):
            dd = ((X - tx) ** 2 + (Y - ty) ** 2) ** .5
            if dd < 34:
                f = (1 - dd / 34) ** 1.6 * .55; r_, g_, b_, a_ = px[X, Y]; px[X, Y] = (int(r_ + (240 - r_) * f), int(g_ + (150 - g_) * f), int(b_ + (70 - b_) * f), a_)
    # 색조(차갑고 푸른 숲 빛)
    for Y in range(CH):
        for X in range(CW):
            r, g, b, a = px[X, Y]; px[X, Y] = (int(r * .95), int(g * .95), int(min(255, b * 1.05)), a)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'maps', 'out', '4_balcony_forest.png')
    img.save(out); img.resize((CW * 2, CH * 2), Image.NEAREST).save(out.replace('.png', '_x2.png')); img.resize((CW * 5, CH * 5), Image.NEAREST).save(out.replace('.png', '_x5.png')); print(out, CW, CH)

if __name__ == '__main__': main()
