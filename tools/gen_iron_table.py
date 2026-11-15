#!/usr/bin/env python3
"""쇠 원탁(위에서 내려다보는 시점): 얇은 상판 + X자 다리. art/objects.txt 의 iron_table 을 다시 쓴다."""
import re
SC = 1.4
LEG = 20                                                 # 다리 끝 높이(낮출수록 탁자가 낮아짐)
W, H = int(30 * SC) + 1, int((LEG + 1) * SC) + 1
g = [['.'] * W for _ in range(H)]
def px(x, y, c):
    if 0 <= x < W and 0 <= y < H: g[y][x] = c
def line(p, q, c, ox=0):
    (x0, y0), (x1, y1) = [(a * SC, b * SC) for a, b in (p, q)]; n = int(max(abs(x1 - x0), abs(y1 - y0))) or 1
    for i in range(n + 1): px(round(x0 + (x1 - x0) * i / n) + ox, round(y0 + (y1 - y0) * i / n), c)
# 상판: 타원 윗면 3줄 + 얇은 옆면 1줄 (가로 폭만 배율, 두께는 그대로)
w0, w1, w2 = [int(v * SC) for v in (5, 2, 1)]
for y, (a_, b_) in enumerate([(int(5 * SC), int(24 * SC)), (int(2 * SC), int(27 * SC)), (int(1 * SC), int(28 * SC))]):
    for x in range(a_, b_ + 1): px(x, y, 'c' if y == 0 else 'l' if y == 1 else 'm')
for x in range(int(2 * SC), int(28 * SC)): px(x, 3, 'd')
for x in (int(4 * SC), int(25 * SC)): px(x, 3, 'k')
# 다리: 가늘고 긴 X자(상판 아래 양끝에서 가운데에서 엇갈려 반대쪽 바닥으로) + 교차부 작은 고리
for ox in (0, 1):                                          # 다리를 2칸 굵기로
    line((8, 4 / SC), (24, LEG), 'm', ox); line((21, 4 / SC), (5, LEG), 'm', ox)   # 상판 바로 밑(4번째 줄)에서 시작
for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)): px(int(12 * SC) + dx, int(12 * SC) + dy, 'd')
px(int(12 * SC), int(12 * SC), 'l')
grid = '\n'.join(''.join(r) for r in g)
txt = open('art/objects.txt', encoding='utf-8').read()
blk = '[iron_table] 고풍스러운 쇠 원탁: 얇은 상판 + X자 다리(42x30) | real\n' + grid + '\n\n'
txt = re.sub(r'\[iron_table\][^\n]*\n(?:[.\w]+\n)+\n', blk, txt, count=1)
open('art/objects.txt', 'w', encoding='utf-8').write(txt)
