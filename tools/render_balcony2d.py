#!/usr/bin/env python3
"""베란다 바깥 2D(정면, 위를 올려다보는 구도) - 사용자 스케치: 양옆 벽, 위쪽 하늘(드문 별), 쇠창살 방지대, 바닥 사다리꼴, 오른쪽에 쇠 의자와 탁자.
사용: python3 tools/render_balcony2d.py  -> maps/out/4_balcony_2d.png"""
import math, os, random, sys
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render, render_maps as R

W, H = 96, 136
def rgb(pal, ch): return pal[ch][:3] + (255,) if len(pal[ch]) >= 3 else pal[ch]

def main():
    pal = render.load_palette(); lib = R.load_library(); rng = random.Random(8)
    im = Image.new('RGBA', (W, H), (0, 0, 0, 255)); _px = im.load()
    class _P:
        def __getitem__(s, k): return _px[k]
        def __setitem__(s, k, v):
            if 0 <= k[0] < W and 0 <= k[1] < H: _px[k] = v
    px = _P()
    top, rail_y, rail_b, floor_y = 10, 62, 88, 88
    # 하늘: 한 가지 짙은 새벽색(층 없음), 양옆은 뚫려 있음
    for y in range(0, H):
        for x in range(W): px[x, y] = rgb(pal, 'X')
    for _ in range(5): px[rng.randrange(8, W - 8), rng.randrange(6, rail_y - 14)] = rgb(pal, rng.choice('WwWq'))
    # 철창(뒤쪽 한 줄): 위 가로대 y=62, 아래 가로대 y=79. 양 끝은 앞쪽으로 비스듬히 벌어져 화면 밖까지 잘린다. 철창 아래는 전부 땅.
    ML, MR = (112, 114, 128, 255), (82, 84, 98, 255)
    L, Rr, top_y, base_y = 12, W - 12, 62, 79
    TT, TB, TW = 2, 1, 1                                   # 철창 두께: 윗줄, 아랫줄, 창살(칸)
    ST, SB = 3, 2                                                 # 양옆 꺾인 부분 윗줄만 한 칸 더 굵게
    def base_at(x):                                        # 아래 가로대(땅 경계)의 높이
        d = max(L - x, x - Rr, 0); return round(base_y + d)
    # 나무판자 바닥(원근법): 소실점 (VX, VY)로 모이는 판자 이음선, 가까울수록 판이 커진다
    PL = [(78, 52, 35), (70, 47, 32), (84, 57, 38)]
    VX, VY, G, BW = W / 2, 20.0, 1.18, 8.0
    for x in range(W):
        for y in range(base_at(x) + (SB if (x < L or x > Rr) else TB), H):
            t = (y - VY) / (base_y - VY)                       # 1 = 안쪽 끝(철창 아래), 클수록 가깝다
            xb = VX + (x + .5 - VX) / t; u = math.floor(xb / BW)  # 안쪽 끝 기준 가로 위치 → 판 번호
            k = math.log(t) / math.log(G); r = math.floor(k)    # 앞뒤 방향 줄 번호
            rowh = (base_y - VY) * t * math.log(G)              # 이 줄의 화면 높이
            c = PL[(u * 5 + r * 2) % 3]
            if ((xb - u * BW) * t < 1.0): c = (34, 22, 16)       # 판 사이 세로 이음(소실점으로 모임)
            elif (k - r) * rowh < 1.0 and (u + r) % 3: c = (34, 22, 16)   # 판 끝 가로 이음(판마다 어긋남)
            elif (x * 5 + y * 3) % 17 == 0: c = (92, 63, 42)     # 나뭇결 점
            px[x, y] = c + (255,)
    def seg(p0, p1, col):
        (x0, y0), (x1, y1) = p0, p1; n = max(abs(x1 - x0), abs(y1 - y0)) or 1
        for i in range(n + 1): px[round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n)] = col
    def band(p0, p1, th, col0, col=MR, dy=0):             # 두께 th칸의 선(가로/45도 공통)
        for k in range(th): seg((p0[0], p0[1] + dy + k), (p1[0], p1[1] + dy + k), col0 if k == 0 else col)
    band((L, top_y), (Rr, top_y), TT, ML); band((L, base_y), (Rr, base_y), TB, MR)
    for x in range(L + 4, Rr, 5):
        for w in range(TW): seg((x + w, top_y + TT), (x + w, base_y - 1), MR)
    for x in (L, Rr - TW + 1):                             # 정면과 양옆이 만나는 곳에도 창살 하나
        for w in range(TW): seg((x + w, top_y + TT), (x + w, base_y - 1), MR)
    for s, x0, ex in ((-1, L, -1), (1, Rr, W)):            # 꺾인 양 끝: 정면과 같은 굵기, 깔끔한 45도
        n = abs(ex - x0)
        band((x0, top_y), (ex, top_y + n), ST, ML); band((x0, base_y), (ex, base_y + n), SB, MR)
        for d in range(4, n, 5):
            xx = x0 + s * d
            for w in range(TW): seg((xx + w, top_y + d + ST), (xx + w, base_y + d - 1), MR)
    # 쇠 의자와 탁자: 땅 위
    t = lib['iron_table']; c = lib['iron_chair']
    t = t.resize((t.width * 3 // 2 * 1, t.height * 3 // 2), Image.NEAREST)
    im.alpha_composite(t, (56, 124 - t.height)); im.alpha_composite(c, (30, 118 - c.height))
    # 밤의 색조
    for y in range(H):
        for x in range(W):
            r, g, b, a = px[x, y]; px[x, y] = (int(r * .85), int(g * .92), min(255, int(b * 1.15)), a)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'maps', 'out', '4_balcony_2d.png')
    im.save(out); im.resize((W * 5, H * 5), Image.NEAREST).save(out.replace('.png', '_big.png')); print(out)

if __name__ == '__main__': main()
