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
    im = Image.new('RGBA', (W, H), (0, 0, 0, 255)); px = im.load()
    top, rail_y, rail_b, floor_y = 10, 86, 112, 112
    # 하늘: 한 가지 짙은 새벽색(층 없음), 양옆은 뚫려 있음
    for y in range(0, floor_y):
        for x in range(W): px[x, y] = rgb(pal, 'X')
    for _ in range(5): px[rng.randrange(8, W - 8), rng.randrange(6, rail_y - 14)] = rgb(pal, rng.choice('WwWq'))
    # 방지대: 가운데는 정면, 양끝은 뒤쪽으로 꺾여 올라가는 사선(철창이 이어지다 꺾임)
    L, Rr, bend = 14, W - 14, 10
    for x in range(L, Rr):
        for dy in range(2): px[x, rail_y + dy] = rgb(pal, 'l' if dy == 0 else 'm')
        px[x, rail_b - 1] = rgb(pal, 'm')
    for k in range(bend):                                  # 꺾인 부분: 위·아래 가로대가 함께 위로 비스듬히
        for sx, ex in ((L - 1 - k, 1), (Rr + k, 1)):
            px[sx, rail_y - k * 1 // 1 + 0] = rgb(pal, 'l'); px[sx, rail_y - k + 1] = rgb(pal, 'm')
            px[sx, rail_b - 1 - k] = rgb(pal, 'm')
    for x in range(L, Rr, 5):
        for y in range(rail_y + 2, rail_b - 1): px[x, y] = rgb(pal, 'm')
    for k in range(1, bend, 3):                            # 꺾인 부분 창살(점점 짧아짐)
        for sx in (L - 1 - k, Rr + k):
            for y in range(rail_y - k + 2, rail_b - 1 - k): px[sx, y] = rgb(pal, 'm')
    # 바닥: 한 가지 어두운 색 + 가로 이음선만 (깔끔하게)
    for y in range(floor_y, H):
        for x in range(W): px[x, y] = rgb(pal, 'd')
    for y in (floor_y + 6, floor_y + 14):
        for x in range(W): px[x, y] = rgb(pal, 'k')
    # 쇠 의자와 탁자: 오른쪽, 방지대 앞
    t = lib['iron_table']; c = lib['iron_chair']
    im.alpha_composite(t, (62, floor_y + 14 - t.height + 6)); im.alpha_composite(c, (46, floor_y + 14 - c.height + 8))
    # 밤의 색조
    for y in range(H):
        for x in range(W):
            r, g, b, a = px[x, y]; px[x, y] = (int(r * .85), int(g * .92), min(255, int(b * 1.15)), a)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'maps', 'out', '4_balcony_2d.png')
    im.save(out); im.resize((W * 5, H * 5), Image.NEAREST).save(out.replace('.png', '_big.png')); print(out)

if __name__ == '__main__': main()
