#!/usr/bin/env python3
"""사진(검은 철제 망 등받이 팔걸이 의자, art/ref/iron_chair_ref.jpg)과 같은 의자를 뒤에서 본 모습(하늘/난간 쪽을 향해 놓임)으로 art/objects.txt 에 iron_chair 로 쓴다."""
import re
import sys
SC = float(sys.argv[1]) if len(sys.argv) > 1 else 1.4          # 크기 배율
NAME = sys.argv[2] if len(sys.argv) > 2 else 'iron_chair'                                                 # 크기 배율
W, H = int(30 * SC) + 1, int(28 * SC) + 1
g = [['.'] * W for _ in range(H)]
def px(x, y, c):
    if 0 <= x < W and 0 <= y < H: g[y][x] = c
def line(p, q, c):
    (x0, y0), (x1, y1) = [(a * SC, b * SC) for a, b in (p, q)]; n = int(max(abs(x1 - x0), abs(y1 - y0))) or 1
    for i in range(n + 1): px(round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n), c)
def poly(pts, c):
    for a, b in zip(pts, pts[1:]): line(a, b, c)
# 위에서 내려다보는 원근 + 오른쪽으로 더 돌려 놓음(YAW): 등받이는 좁아 보이고 의자의 오른쪽 옆면이 넓게 보인다. 먼 쪽(앞다리, 팔걸이 끝)은 위쪽·오른쪽으로 크게 밀린다
poly([(13, 22), (11, 9)], 'd'); poly([(27, 21), (27, 8)], 'd')                # 앞다리(먼 쪽, 어둡게)
poly([(5, 10), (11, 9)], 'm'); poly([(18, 10), (27, 8)], 'm')                # 팔걸이(오른쪽은 길게 앞으로 뻗어 보임)
poly([(17, 16), (28, 13)], 'l'); poly([(17, 17), (28, 14)], 'd')             # 앉는 판 오른쪽 옆면(넓게)
for y in range(int(3 * SC), int(15 * SC)):                                  # 망 등받이(가까운 면, 더 좁아짐)
    for x in range(int(6 * SC), int(16 * SC)):
        if (x + y) % 2 == 0: px(x, y, 'm')
poly([(4, 10), (5, 4), (8, 2), (11, 1), (14, 2), (17, 4), (18, 10)], 'l')    # 둥근 등받이 고리
poly([(5, 15), (17, 15)], 'm')                                               # 등받이 아래 가로대
poly([(4, 10), (4, 14)], 'l'); poly([(18, 10), (18, 14)], 'l')
poly([(5, 16), (17, 16)], 'l'); poly([(6, 17), (17, 17)], 'd')               # 앉는 판 가까운 가장자리
poly([(5, 17), (4, 27)], 'l'); poly([(17, 17), (18, 27)], 'l')               # 뒷다리(가까움)
grid = '\n'.join(''.join(r) for r in g)
txt = open('art/objects.txt', encoding='utf-8').read()
blk = '[' + NAME + '] 사진 속 검은 철제 망 등받이 팔걸이 의자(뒤에서 본 모습, 오른쪽으로 살짝 돌림, 배율 %s) | real\n' % SC + grid + '\n\n'
pat = r'\[' + NAME + r'\][^\n]*\n(?:[.\w]+\n)+\n'
if re.search(pat, txt):
    txt = re.sub(pat, lambda m: blk, txt, count=1)
else:
    txt = txt.replace('[iron_table]', blk + '[iron_table]', 1)
open('art/objects.txt', 'w', encoding='utf-8').write(txt)
