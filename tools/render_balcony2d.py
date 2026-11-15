#!/usr/bin/env python3
"""베란다 바깥 2D(정면, 위를 올려다보는 구도) - 사용자 스케치: 양옆 벽, 위쪽 하늘(드문 별), 쇠창살 방지대, 바닥 사다리꼴, 오른쪽에 쇠 의자와 탁자.
사용: python3 tools/render_balcony2d.py  -> maps/out/4_balcony_2d.png"""
import os, random, sys
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
    for y in range(0, floor_y):
        for x in range(W): px[x, y] = rgb(pal, 'X')
    for _ in range(5): px[rng.randrange(8, W - 8), rng.randrange(6, rail_y - 14)] = rgb(pal, rng.choice('WwWq'))
    # 바닥: 의자(밝은 회색 선)와 겹치지 않는 따뜻한 어두운 갈색, 가로 이음선만
    for y in range(floor_y, H):
        for x in range(W): px[x, y] = (46, 34, 30, 255)
    for y in (floor_y + 14, floor_y + 30):
        for x in range(W): px[x, y] = (30, 22, 22, 255)
    ML, MR = (112, 114, 128, 255), (82, 84, 98, 255)    # 철창 색(밝은 줄/보통 줄)
    def seg(p0, p1, col):
        (x0, y0), (x1, y1) = p0, p1; n = max(abs(x1 - x0), abs(y1 - y0)) or 1
        for i in range(n + 1): px[round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n)] = col
    L, Rr = 26, W - 26                                     # 가운데 정면 구간 [L, Rr], 양옆은 앞쪽으로 꺾여 화면 밖까지
    ft, fb = H - 30, H - 5                                 # 앞쪽 철창의 윗줄/아랫줄
    def rails():
        seg((L, rail_y), (Rr, rail_y), ML); seg((L, rail_y + 1), (Rr, rail_y + 1), MR); seg((L, floor_y - 1), (Rr, floor_y - 1), MR)
        for x in range(L, Rr + 1, 5): seg((x, rail_y + 2), (x, floor_y - 2), MR)
        for s, ex in ((-1, -1), (1, W)):                   # 왼쪽(-1)/오른쪽(1) 꺾인 철창
            x0 = L if s < 0 else Rr
            seg((x0, rail_y), (ex, ft), ML); seg((x0, floor_y - 1), (ex, fb), MR)
            for d in range(5, 28, 5):
                xx = x0 + s * d; t = d / abs(ex - x0)
                y0 = round(rail_y + (ft - rail_y) * t) + 1; y1 = round(floor_y - 1 + (fb - floor_y + 1) * t)
                seg((xx, y0), (xx, y1), MR)
    rails()
    # 쇠 의자와 탁자: 바닥 위
    t = lib['iron_table']; c = lib['iron_chair']
    im.alpha_composite(t, (60, 104 - t.height)); im.alpha_composite(c, (30, 104 - c.height))
    # 정면(보는 쪽) 철창: 가로로 늘려 사각 공간을 닫는다
    seg((0, ft), (W - 1, ft), ML); seg((0, ft + 1), (W - 1, ft + 1), MR); seg((0, fb), (W - 1, fb), MR)
    for x in range(2, W, 5): seg((x, ft + 2), (x, fb - 1), MR)
    # 밤의 색조
    for y in range(H):
        for x in range(W):
            r, g, b, a = px[x, y]; px[x, y] = (int(r * .85), int(g * .92), min(255, int(b * 1.15)), a)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'maps', 'out', '4_balcony_2d.png')
    im.save(out); im.resize((W * 5, H * 5), Image.NEAREST).save(out.replace('.png', '_big.png')); print(out)

if __name__ == '__main__': main()
