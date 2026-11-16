#!/usr/bin/env python3
"""베란다 바깥, 어둑어둑한 숲 버전(수미상관의 마지막 장면). 사선 시점, 방·복도 숲 버전과 같은 구성.
하늘 = 안개 낀 숲 속(먼 나무 실루엣, 반딧불), 뒤쪽 철창 = 부러진 나무 울타리, 왼쪽 벽 = 거대한 나무 둥치, 바닥 = 썩은 널빤지 + 이끼·낙엽,
의자·탁자 = 부서진 나무.  사용: python3 tools/render_balcony_forest.py -> maps/out/4_balcony_forest.png (+_x2,_x5)"""
import os, random, sys
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render_maps as R
from forest_draw import leafy, trunk as tdraw

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
    # 배경(참고 이미지: 짙은 남보라 밤 숲, 겹겹의 깊이): 안개 낀 먼 나무 → 중간 나무 → 덤불, 위는 큰 나뭇잎 덩어리, 양옆 큰 둥치
    by = Y0 - SS * D; top_rail = by - RAIL
    for y in range(CH):
        t = min(1, max(0, y / (by + 1)))
        for x in range(CW): put(x, y, (int(10 + 26 * t), int(12 + 28 * t), int(30 + 46 * t)))              # 위는 어둡고 지평선 쪽은 안개로 밝음
    def trunk(cx, w, col, hi, y0=0, y1=None, root=0):
        y1 = int(by) if y1 is None else y1
        tdraw(put, cx, w, y0, y1, col, hi, tuple(int(v * .65) for v in col), rng, root=root)
    for x0 in range(int(X0 + SK * D) + 4, CW, 13):                      # 먼 나무: 안개에 묻혀 흐릿
        trunk(x0 + rng.randrange(-2, 3), rng.choice((4, 5, 6)), (28, 30, 62), (34, 36, 72))
    for x0 in (int(X0 + SK * D) + 20, int(X0 + SK * D) + 54, CW - 26):  # 중간 나무: 더 짙고 굵음
        trunk(x0, rng.choice((6, 7)), (20, 20, 44), (30, 30, 62), root=6)
    for yy in range(int(by) - 14, int(by) + 1):                         # 지평선 안개띠
        for x in range(CW):
            r_, g_, b_, a_ = px[x, yy]; k = (yy - (by - 14)) / 14 * .45; px[x, yy] = (int(r_ + (60 - r_) * k), int(g_ + (66 - g_) * k), int(b_ + (112 - b_) * k), 255)
    for _ in range(14):                                                 # 덤불(울타리 뒤): 잎 덩어리
        cx = rng.randrange(int(X0 + SK * D), CW); cy = int(by) - rng.randrange(1, 8)
        leafy(lambda x, y, c: put(x, y, c) if y < by else None, cx, cy, rng.randrange(4, 7), rng, (12, 28, 40), (22, 50, 58), (38, 80, 84))
    for _ in range(26):                                                 # 위쪽 나뭇잎 덩어리(캐노피)
        leafy(put, rng.randrange(-4, CW + 4), rng.randrange(-6, 20), rng.randrange(6, 11), rng, (12, 26, 38), (22, 46, 58), (38, 78, 82))
    trunk(CW - 16, 13, (28, 24, 54), (46, 40, 84), 18, int(by) + 4, root=14)       # 오른쪽 큰 둥치(프레임)
    for _ in range(8):                                                  # 반딧불: 청록빛
        sx = rng.randrange(int(X0 + SK * D) + 6, CW - 16); sy = rng.randrange(24, int(top_rail) - 2)
        put(sx, sy, (170, 220, 230)); put(sx + 1, sy, (80, 120, 150))
    # 뒤쪽 울타리: 부러진 나무 기둥(높이 제각각, 일부는 사라짐), 기울어진 가로대
    bx0, bx1 = int(X0 + SK * D), int(X0 + SK * D + W)
    posts = [x for x in range(bx0 + 2, bx1, 9)]
    for i, x in enumerate(posts):
        if i in (3, 6): continue                                        # 빠진 기둥
        h = RAIL if i not in (2, 5, 7) else RAIL - rng.randrange(7, 14)    # 부러진 기둥은 짧음
        for y in range(int(by - h), int(by)):
            for k in range(2): put(x + k, y, WOODL if k == 0 else WOOD)
        if h < RAIL:
            put(x, int(by - h) - 1, WOODD); put(x + 1, int(by - h) - 2, WOODL)     # 부러진 끝
    for a, b2 in ((0, 2), (4, 5), (7, 8)):                              # 남은 가로대(끊겨 있음, 기울어짐)
        xa, xb = posts[a], posts[b2]
        for x in range(xa, xb + 2):
            y = int(by - RAIL + 3 + (x - xa) * (1 if a == 4 else 0) // 6)
            put(x, y, WOODL); put(x, y + 1, WOOD)
    # 바닥: 썩은 널빤지(가로, 틈과 구멍) + 이끼·낙엽
    rows, d0 = [], 0.0
    while d0 < D: rows.append((d0, d0 + fr.uniform(6, 12))); d0 = rows[-1][1]
    cols = [(52, 48, 76), (44, 40, 66), (58, 54, 86), (38, 54, 66), (48, 44, 72)]
    info = []
    for _ in rows:
        js, xj = [], fr.uniform(-40, 0)
        while xj < W + 40: xj += fr.uniform(20, 56); js.append(xj)
        info.append((js, [tuple(max(0, v + fr.randint(-4, 4)) for v in fr.choice(cols)) for _ in js]))
    holes = [(30, 18, 9, 5), (58, 8, 7, 4)]                             # (x, 깊이 d, 가로, 세로) 구멍
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
    put_sprite('torch_stand', 30, 30); put_sprite('broken_table', 66, 26); put_sprite('broken_chair', 58, 18); put_sprite('plank_piece', 44, 12); put_sprite('plank_piece', 28, 34)
    tx, ty = int(X0 + 30 + SK * 30), int(Y0 - SS * 30 - 22)          # 횃불 불꽃 위치
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
