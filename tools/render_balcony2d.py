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
    for y in range(0, H):
        for x in range(W): px[x, y] = rgb(pal, 'X')
    for _ in range(5): px[rng.randrange(8, W - 8), rng.randrange(6, rail_y - 14)] = rgb(pal, rng.choice('WwWq'))
    # 철창(뒤쪽 한 줄): 위 가로대 y=62, 아래 가로대 y=79. 양 끝은 앞쪽으로 비스듬히 벌어져 화면 밖까지 잘린다. 철창 아래는 전부 땅.
    ML, MR = (112, 114, 128, 255), (82, 84, 98, 255)
    L, Rr, top_y, base_y = 12, W - 12, 62, 79
    def base_at(x):                                        # 아래 가로대(땅 경계)의 높이
        d = max(L - x, x - Rr, 0); return round(base_y + d)
    for x in range(W):                                     # 땅: 의자와 겹치지 않는 따뜻한 어두운 갈색
        for y in range(base_at(x) + 2, H): px[x, y] = (46, 34, 30, 255)
    for y in (base_y + 14, base_y + 30):
        for x in range(W):
            if y > base_at(x): px[x, y] = (30, 22, 22, 255)
    def seg(p0, p1, col):
        (x0, y0), (x1, y1) = p0, p1; n = max(abs(x1 - x0), abs(y1 - y0)) or 1
        for i in range(n + 1): px[round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n)] = col
    seg((L, top_y), (Rr, top_y), ML); seg((L, top_y + 1), (Rr, top_y + 1), MR); seg((L, top_y + 2), (Rr, top_y + 2), MR)
    seg((L, base_y), (Rr, base_y), MR); seg((L, base_y + 1), (Rr, base_y + 1), MR)
    for x in range(L + 4, Rr, 5): seg((x, top_y + 3), (x, base_y - 1), MR); seg((x + 1, top_y + 3), (x + 1, base_y - 1), MR)
    for s, x0, ex in ((-1, L, -1), (1, Rr, W)):            # 꺾인 양 끝: 정면과 같은 굵기(위 2칸, 아래 1칸, 창살 1칸), 깔끔한 45도
        n = abs(ex - x0)
        seg((x0, top_y), (ex, top_y + n), ML); seg((x0, top_y + 1), (ex, top_y + 1 + n), MR); seg((x0, top_y + 2), (ex, top_y + 2 + n), MR)
        seg((x0, base_y), (ex, base_y + n), MR); seg((x0, base_y + 1), (ex, base_y + 1 + n), MR)
        for d in range(4, n, 5):
            xx = x0 + s * d
            for w in (0, 1): seg((xx + w, top_y + d + 3), (xx + w, base_y + d - 1), MR)
    # 쇠 의자와 탁자: 땅 위
    t = lib['iron_table']; c = lib['iron_chair']
    im.alpha_composite(t, (58, 122 - t.height)); im.alpha_composite(c, (26, 118 - c.height))
    # 밤의 색조
    for y in range(H):
        for x in range(W):
            r, g, b, a = px[x, y]; px[x, y] = (int(r * .85), int(g * .92), min(255, int(b * 1.15)), a)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'maps', 'out', '4_balcony_2d.png')
    im.save(out); im.resize((W * 5, H * 5), Image.NEAREST).save(out.replace('.png', '_big.png')); print(out)

if __name__ == '__main__': main()
