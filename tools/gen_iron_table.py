#!/usr/bin/env python3
"""쇠 원탁(위에서 내려다보는 시점): 얇은 상판 + 가늘고 긴 다리. art/objects.txt 의 iron_table 을 다시 쓴다."""
import re
W, H = 30, 30
g = [['.'] * W for _ in range(H)]
def px(x, y, c):
    if 0 <= x < W and 0 <= y < H: g[y][x] = c
def line(p, q, c):
    (x0, y0), (x1, y1) = p, q; n = int(max(abs(x1 - x0), abs(y1 - y0))) or 1
    for i in range(n + 1): px(round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n), c)
# 상판: 타원 윗면 3줄 + 얇은 옆면 1줄
for y, (a, b) in enumerate([(5, 24), (2, 27), (1, 28)]):
    for x in range(a, b + 1): px(x, y, 'c' if y == 0 else 'l' if y == 1 else 'm')
for x in range(2, 28): px(x, 3, 'd')
for x in (4, 25): px(x, 3, 'k')
# 다리: 가늘고 긴 1칸 선(바깥으로 살짝 벌어짐) + 안쪽 다리 + 가는 링 받침
line((6, 4), (3, 29), 'm'); line((23, 4), (26, 29), 'm')
line((11, 4), (11, 24), 'd'); line((18, 4), (18, 24), 'd')
for x in range(5, 25): px(x, 17, 'd')
grid = '\n'.join(''.join(r) for r in g)
txt = open('art/objects.txt', encoding='utf-8').read()
blk = '[iron_table] 고풍스러운 쇠 원탁: 얇은 상판 + 가늘고 긴 다리(30x30) | real\n' + grid + '\n\n'
txt = re.sub(r'\[iron_table\][^\n]*\n(?:[.\w]+\n)+\n', blk, txt, count=1)
open('art/objects.txt', 'w', encoding='utf-8').write(txt)
