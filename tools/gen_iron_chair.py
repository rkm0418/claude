#!/usr/bin/env python3
"""사진(검은 철제 망 등받이 팔걸이 의자, art/ref/iron_chair_ref.jpg)과 같은 의자를 뒤에서 본 모습(하늘/난간 쪽을 향해 놓임)으로 art/objects.txt 에 iron_chair 로 쓴다."""
import re
W, H = 22, 26
g = [['.'] * W for _ in range(H)]
def px(x, y, c):
    if 0 <= x < W and 0 <= y < H: g[y][x] = c
def line(p, q, c):
    (x0, y0), (x1, y1) = p, q; n = int(max(abs(x1 - x0), abs(y1 - y0))) or 1
    for i in range(n + 1): px(round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n), c)
def poly(pts, c):
    for a, b in zip(pts, pts[1:]): line(a, b, c)
for y in range(2, 11):                                   # 망 등받이(속이 비침)
    for x in range(4, 18):
        if (x + y) % 2 == 0: px(x, y, 'm')
poly([(2, 10), (3, 3), (6, 1), (11, 0), (16, 1), (19, 3), (20, 10)], 'l')     # 둥근 등받이 고리(팔걸이로 이어짐)
poly([(3, 11), (18, 11)], 'm')                                                # 등받이 아래 가로대
poly([(2, 10), (2, 13)], 'l'); poly([(20, 10), (20, 13)], 'l')                # 팔걸이 끝
poly([(3, 12), (18, 12)], 'c'); poly([(4, 13), (17, 13)], 'd')                # 앉는 판(뒤에서 얇게)
poly([(6, 14), (6, 21)], 'd'); poly([(15, 14), (15, 21)], 'd')                # 앞다리(멀리, 어둡게)
poly([(3, 12), (3, 25)], 'l'); poly([(18, 12), (18, 25)], 'l')                # 뒷다리(가까이)
grid = '\n'.join(''.join(r) for r in g)
txt = open('art/objects.txt', encoding='utf-8').read()
blk = '[iron_chair] 사진 속 검은 철제 망 등받이 팔걸이 의자(28x34 사진 트레이스, 3/4 시점, 좌우 반전) | real\n' + grid + '\n\n'
if '[iron_chair]' in txt:
    txt = re.sub(r'\[iron_chair\][^\n]*\n(?:[.\w]+\n)+\n', blk, txt, count=1)
else:
    txt = txt.replace('[iron_table]', blk + '[iron_table]', 1)
open('art/objects.txt', 'w', encoding='utf-8').write(txt)
