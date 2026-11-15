#!/usr/bin/env python3
"""사진(검은 철제 망 등받이 팔걸이 의자, art/ref/iron_chair_ref.jpg)과 같은 의자를 뒤에서 본 모습(하늘/난간 쪽을 향해 놓임)으로 art/objects.txt 에 iron_chair 로 쓴다."""
import re
SC = 1.4                                                 # 크기 배율
W, H = int(22 * SC) + 1, int(28 * SC) + 1
g = [['.'] * W for _ in range(H)]
def px(x, y, c):
    if 0 <= x < W and 0 <= y < H: g[y][x] = c
def line(p, q, c):
    (x0, y0), (x1, y1) = [(a * SC, b * SC) for a, b in (p, q)]; n = int(max(abs(x1 - x0), abs(y1 - y0))) or 1
    for i in range(n + 1): px(round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n), c)
def poly(pts, c):
    for a, b in zip(pts, pts[1:]): line(a, b, c)
# 위에서 내려다보는 원근: 뒤에서 본 의자. 먼 쪽(앞다리, 팔걸이 끝)은 화면 위쪽, 가운데(소실점) 쪽으로 모인다
poly([(6, 22), (6, 8)], 'd'); poly([(15, 22), (15, 8)], 'd')                 # 앞다리(먼 쪽, 어둡게)
poly([(2, 9), (6, 8)], 'm'); poly([(19, 9), (15, 8)], 'm')                   # 팔걸이(앞으로 뻗어 소실점 쪽으로 모임)
poly([(6, 22), (15, 22)], 'd')                                               # 먼 쪽 다리 사이 바닥 그림자 선
for y in range(int(3 * SC), int(15 * SC)):                                  # 망 등받이(가까운 면)
    for x in range(int(4 * SC), int(18 * SC)):
        if (x + y) % 2 == 0: px(x, y, 'm')
poly([(2, 10), (3, 4), (6, 2), (11, 1), (16, 2), (19, 4), (19, 10)], 'l')    # 둥근 등받이 고리
poly([(3, 15), (18, 15)], 'm')                                               # 등받이 아래 가로대
poly([(2, 10), (2, 14)], 'l'); poly([(19, 10), (19, 14)], 'l')
poly([(3, 16), (18, 16)], 'c'); poly([(4, 17), (17, 17)], 'd')               # 앉는 판 가까운 가장자리
poly([(3, 17), (2, 27)], 'l'); poly([(18, 17), (19, 27)], 'l')               # 뒷다리(가까움): 아래로 갈수록 벌어짐
grid = '\n'.join(''.join(r) for r in g)
txt = open('art/objects.txt', encoding='utf-8').read()
blk = '[iron_chair] 사진 속 검은 철제 망 등받이 팔걸이 의자(28x34 사진 트레이스, 3/4 시점, 좌우 반전) | real\n' + grid + '\n\n'
if '[iron_chair]' in txt:
    txt = re.sub(r'\[iron_chair\][^\n]*\n(?:[.\w]+\n)+\n', blk, txt, count=1)
else:
    txt = txt.replace('[iron_table]', blk + '[iron_table]', 1)
open('art/objects.txt', 'w', encoding='utf-8').write(txt)
