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
    for _ in range(6):                                                     # 반딧불: 청록빛
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
    # 부서진 울타리 조각(기둥 사이사이): 기울어진 기둥, 한쪽만 걸려 늘어진 가로대, 들쭉날쭉 부러진 그루터기, 쓰러져 기댄 널빤지
    def beam(x0, y0, x1, y1, th=2):                                      # 두께 th 의 나무 막대(밝은 면 + 어두운 면)
        n = int(max(abs(x1 - x0), abs(y1 - y0))) or 1
        for s in range(n + 1):
            xx, yy = round(x0 + (x1 - x0) * s / n), round(y0 + (y1 - y0) * s / n)
            put(xx, yy, WOODL)
            for k in range(1, th): put(xx + (1 if abs(x1 - x0) < abs(y1 - y0) else 0), yy + (0 if abs(x1 - x0) < abs(y1 - y0) else k), WOOD if k == th - 1 else WOODL)
    def jag(x, y, w=3):                                                  # 부러진 끝의 들쭉날쭉한 단면
        for k in range(w): put(x + k, y - (k % 2) * 2, WOODD); put(x + k, y - 1 - (k % 2), WOODL)
    g3, g6 = posts[3], posts[6]
    beam(g3 + 1, int(by), g3 + 9, int(by - RAIL + 4)); jag(g3 + 9, int(by - RAIL + 4))                  # 빠진 기둥 자리에 비스듬히 기운 기둥
    beam(posts[1] + 2, int(by - RAIL + 3), posts[1] + 12, int(by - RAIL + 14), 2); jag(posts[1] + 12, int(by - RAIL + 14))    # 한쪽만 걸려 아래로 늘어진 가로대
    beam(posts[4] + 2, int(by - RAIL + 6), posts[4] + 8, int(by - 6), 1)                                  # 가로대 조각이 기둥에 기대 늘어짐
    for dx, hh in ((0, 5), (2, 8), (4, 3)): [put(g6 + dx, int(by) - k, WOODL if dx == 2 else WOOD) for k in range(hh)]      # 들쭉날쭉 부러진 그루터기
    jag(g6, int(by) - 5, 2); jag(g6 + 2, int(by) - 8, 2)
    beam(posts[7] + 4, int(by), posts[7] + 14, int(by - 9), 2)                                           # 쓰러져 다른 기둥에 기댄 널빤지
    for k in range(5): put(posts[2] + 3 + k, int(by - RAIL + 4 + k // 2), WOODD)                          # 부러진 기둥 옆 갈라진 파편
    # 땅: 숲 바닥이 지평선 아래 전체에 이어진다(판 아래·앞·오른쪽으로 계속): 흙 + 이끼 + 풀 + 가는 길
    gr = random.Random(9)
    for Y in range(int(by) - 2, CH):
        t = (Y - by) / max(1, CH - by)
        for X in range(CW):
            base = (int(26 + 14 * t), int(30 + 14 * t), int(44 + 22 * t))
            if gr.random() < .10: base = (base[0] - 5, base[1] + 5, base[2] - 4)
            if gr.random() < .05: base = (base[0] + 8, base[1] + 8, base[2] + 12)
            put(X, Y, base)
    for _ in range(70):                                                 # 풀잎 무더기
        gx, gy = gr.randrange(CW), gr.randrange(int(by), CH)
        for k in range(gr.randrange(2, 5)): put(gx + k % 2, gy - k, (30, 62 - k * 4, 58))
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
    for X in range(int(X0), int(X0 + W + SK * D) + 1):                  # 판의 두께(앞 가장자리 3칸)와 오른쪽 옆면
        for k in range(3):
            if px[X, int(Y0) + 1 + k][3] and int(Y0) + 1 + k < CH and X <= X0 + W: put(X, int(Y0) + 1 + k, (22 - k * 4, 18 - k * 3, 34 - k * 5))
    for Y in range(int(Y0 - SS * D), int(Y0) + 1):
        X = int(X0 + W + SK * (Y0 - Y) / SS) + 1
        for k in range(2): put(X + k, Y + 1, (20, 18, 32))
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
    # 왼쪽 벽 마감: 윗면 뚜껑(두께 6칸, 위에서 보이는 면)과 앞쪽 단면(둥치를 잘라 낸 면)
    CAP, CAPH, CAPD = (78, 70, 118), (104, 94, 148), (40, 34, 66)
    for d in range(0, int(D) + 1):
        X = int(X0 + SK * d); yt = int(Y0 - SS * d - WH)
        for dx in range(0, 7):
            put(X + dx, yt, CAPH if dx < 2 else CAPD if dx > 5 else CAP)
            if dx in (1, 3, 5): put(X + dx, yt - 1 + (dx // 3), CAP if dx != 3 else CAPH)          # 윗면 가장자리가 울퉁불퉁한 가지 자국
    for X in range(int(X0), int(X0) + 7):                                    # 앞쪽 단면: 나이테가 보이는 잘린 면
        for Y in range(int(Y0 - WH), int(Y0) + 1):
            k = (X - int(X0)); c0 = (52, 44, 84) if k < 5 else (30, 26, 52)
            if (Y - int(Y0 - WH)) % 9 == 0 and 0 < k < 6: c0 = (66, 58, 100)    # 나이테 선
            put(X, Y, c0)
    for dx in range(0, 7): put(int(X0) + dx, int(Y0 - WH) - 1, CAPH if dx < 5 else CAP)      # 단면 위 모서리 하이라이트
    # 가구: 부서진 나무 의자·탁자(오른쪽 끝, 의자가 앞)
    def put_sprite(name, x, d):
        s = lib[name]; img.alpha_composite(s, (int(X0 + x + SK * d - s.width / 2), int(Y0 - SS * d - s.height)))
    pass   # 바닥 위 나무 물건(부서진 의자·탁자·널빤지)은 두지 않는다
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
