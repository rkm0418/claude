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
    # 하늘: 위는 아주 깊은 남색, 아래(지평선 쪽)는 약간 밝게
    for y in range(top, rail_y):
        t = (y - top) / (rail_y - top); ch = 'X' if t < .9 else 'D'
        for x in range(6, W - 6): px[x, y] = rgb(pal, ch)
    for _ in range(5): px[rng.randrange(10, W - 10), rng.randrange(top + 2, rail_y - 14)] = rgb(pal, rng.choice('WwWq'))
    # 천장(위의 얇은 띠, 스케치의 비스듬한 윗선)
    for x in range(W):
        yy = 6 + int((x / W) * -3)
        for y in range(0, yy + top - 6): px[x, y] = rgb(pal, 's')
    # 양옆 벽
    for y in range(H):
        for x in range(0, 6): px[x, y] = rgb(pal, 'd' if (x + y) % 11 else 'm')
        for x in range(W - 6, W): px[x, y] = rgb(pal, 'd' if (x * 3 + y) % 13 else 'm')
    for y in range(rail_y, rail_b - 1):                      # 창살 뒤로도 하늘이 이어진다
        for x in range(6, W - 6): px[x, y] = rgb(pal, 'D')
    # 방지대: 윗 가로대, 쇠창살, 아래 가로대. 양끝은 비스듬히 벽에 붙는다
    for x in range(6, W - 6):
        for dy in range(2): px[x, rail_y + dy] = rgb(pal, 'l' if dy == 0 else 'm')
        px[x, rail_b - 1] = rgb(pal, 'm')
    for x in range(10, W - 8, 5):
        for y in range(rail_y + 2, rail_b - 1): px[x, y] = rgb(pal, 'm'); 
    for k in range(6):                                     # 난간 끝이 벽으로 꺾이는 사선
        px[5 - min(k, 5), rail_y + 6 - k] = rgb(pal, 'm'); px[W - 6 + min(k, 5), rail_y + 6 - k] = rgb(pal, 'm')
    # 바닥: 사다리꼴(앞으로 올수록 넓음), 가로 이음선
    for y in range(floor_y, H):
        t = (y - floor_y) / (H - floor_y); inset = int(8 * (1 - t))
        for x in range(inset, W - inset):
            px[x, y] = rgb(pal, 'd') if (y * 7 + x * 3) % 17 else rgb(pal, 'm')
    for y in (floor_y + 3, floor_y + 8, floor_y + 15):
        for x in range(0, W): px[x, y] = rgb(pal, 'k')
    # 쇠 의자와 탁자: 오른쪽, 방지대 앞
    t = lib['iron_table']; c = lib['iron_chair']
    im.alpha_composite(t, (62, floor_y + 14 - t.height + 6)); im.alpha_composite(c, (44, floor_y + 14 - c.height + 8))
    # 밤의 색조
    for y in range(H):
        for x in range(W):
            r, g, b, a = px[x, y]; px[x, y] = (int(r * .85), int(g * .92), min(255, int(b * 1.15)), a)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'maps', 'out', '4_balcony_2d.png')
    im.save(out); im.resize((W * 5, H * 5), Image.NEAREST).save(out.replace('.png', '_big.png')); print(out)

if __name__ == '__main__': main()
