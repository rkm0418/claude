#!/usr/bin/env python3
"""베란다 바깥(사선 시점, 방·복도와 같은 형식): 깊은 새벽 하늘 / 뒤쪽 철창 / 왼쪽 옆 철창(사선) / 어두운 나무판자 바닥 / 쇠 의자와 탁자.
오른쪽·앞은 잘라낸 단면. 그림자 없음.  사용: python3 tools/render_balcony_oblique.py -> maps/out/4_balcony_oblique.png (+_x2: 화면 2배)"""
import os, random, sys
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render, render_maps as R

SK = SS = .5
W, D, PAD, RAIL, SKY = 80, 48, 6, 26, 40
CW, CH = int(PAD * 2 + W + SK * D), int(PAD * 2 + SKY + RAIL + SS * D)
X0, Y0 = PAD, CH - PAD
ML, MR = (112, 114, 128, 255), (82, 84, 98, 255)

def main():
    pal = render.load_palette(); lib = R.load_library(); rng = random.Random(8); fr = random.Random(21)
    img = Image.new('RGBA', (CW, CH), tuple(pal['X'][:3]) + (255,)); px = img.load()
    for _ in range(8): px[rng.randrange(8, CW - 8), rng.randrange(6, SKY + 10)] = tuple(pal[rng.choice('WwWq')][:3]) + (255,)
    def seg(p0, p1, col):
        (x0, y0), (x1, y1) = p0, p1; n = int(max(abs(x1 - x0), abs(y1 - y0))) or 1
        for i in range(n + 1):
            x, y = round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n)
            if 0 <= x < CW and 0 <= y < CH: px[x, y] = col
    by = Y0 - SS * D                                          # 뒤쪽 철창이 서 있는 바닥 높이
    bx0, bx1 = X0 + SK * D, X0 + SK * D + W
    # 뒤쪽 철창(정면): 윗줄 2칸, 아랫줄 1칸, 창살 1칸 간격 5
    seg((bx0, by - RAIL), (bx1, by - RAIL), ML); seg((bx0, by - RAIL + 1), (bx1, by - RAIL + 1), MR)
    for x in range(int(bx0) + 4, int(bx1), 5): seg((x, by - RAIL + 2), (x, by - 1), MR)
    # 바닥: 가로 판자(깊이 d가 같은 줄), 판 끝 이음은 사선으로 보인다. 폭·색·이음 위치 불규칙, 짙은 갈색
    rows, d0 = [], 0.0
    while d0 < D: rows.append((d0, d0 + fr.uniform(6, 12))); d0 = rows[-1][1]
    base_cols = [(60, 40, 27), (52, 34, 24), (66, 44, 29), (56, 37, 26), (48, 32, 22)]
    info = []
    for _ in rows:
        js, xj = [], fr.uniform(-40, 0)
        while xj < W + 40: xj += fr.uniform(22, 60); js.append(xj)
        info.append((js, [tuple(max(0, v + fr.randint(-4, 4)) for v in fr.choice(base_cols)) for _ in js]))
    for Y in range(int(Y0 - SS * D), int(Y0) + 1):
        d = (Y0 - Y - .5) / SS
        if not (0 <= d < D): continue
        ri = next(i for i, r in enumerate(rows) if r[0] <= d < r[1]) if d < rows[-1][1] else len(rows) - 1
        js, cols = info[ri]
        for X in range(int(X0), int(X0 + W + SK * D) + 1):
            x = X + .5 - X0 - SK * d
            if not (0 <= x < W): continue
            n = next((k for k, jx in enumerate(js) if x < jx), len(js) - 1); c = cols[n]
            if (Y0 - Y - .5) / SS - rows[ri][0] < 1.6 / 1: c = (26, 16, 12)            # 줄 사이 이음(가로선)
            elif n > 0 and x - js[n - 1] < 1: c = (26, 16, 12)                          # 판 끝 이음(사선)
            elif fr.random() < .035: c = tuple(v + 12 for v in c)                        # 나뭇결 점
            px[X, Y] = c + (255,)
    # 왼쪽 옆은 집 외벽(벽으로 막음): 방·복도의 왼쪽 벽과 같은 사선 눌림, 철창보다 높다
    WH = RAIL + 24
    from collections import Counter
    flat = lambda t: Counter(t.getdata()).most_common(1)[0][0]     # 타일의 점(얼룩) 제거: 가장 많은 색 한 가지
    for X in range(int(X0), int(X0 + SK * D) + 1):
        d = (X + .5 - X0) / SK
        if not (0 <= d < D): continue
        for Y in range(int(Y0 - SS * d - WH), int(Y0 - SS * d) + 1):
            z = (Y0 - SS * d) - (Y + .5)
            if not (0 <= z < WH): continue
            nm, ty = ('wall_base_bal', 15 - int(z)) if z < 16 else ('wall_top_bal', int(WH - 1 - z)) if z >= WH - 16 else ('wall_bal', 15 - int(z - 16) % 16)
            r, g, bb, a = flat(lib[nm]); px[X, Y] = (int(r * .82), int(g * .82), int(bb * .86), a)
    # 가구(그림자 없음): 바닥의 (x, 깊이) 한 점 아래 가운데에 놓는다
    def put(name, x, d):
        s = lib[name]; img.alpha_composite(s, (int(X0 + x + SK * d - s.width / 2), int(Y0 - SS * d - s.height)))
    put('iron_table_m', 58, 26); put('iron_chair_m', 32, 20)
    # 밤의 색조
    for Y in range(CH):
        for X in range(CW):
            r, g, b, a = px[X, Y]; px[X, Y] = (int(r * .85), int(g * .92), min(255, int(b * 1.15)), a)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'maps', 'out', '4_balcony_oblique.png')
    img.save(out); img.resize((CW * 2, CH * 2), Image.NEAREST).save(out.replace('.png', '_x2.png')); img.resize((CW * 5, CH * 5), Image.NEAREST).save(out.replace('.png', '_x5.png')); print(out, CW, CH)

if __name__ == '__main__': main()
