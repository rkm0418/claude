#!/usr/bin/env python3
"""쇠 원탁(위에서 내려다본 시점): 타원 상판(윗면+얇은 옆면) + X자 다리.  사용: python3 tools/gen_iron_table.py [상판지름 높이 이름]
기본: 지름 28, 다리 높이 22 -> iron_table.  (아이 키 38칸 기준으로 허리 높이)"""
import re, sys
TOP = int(sys.argv[1]) if len(sys.argv) > 1 else 28
LEG = int(sys.argv[2]) if len(sys.argv) > 2 else 22
NAME = sys.argv[3] if len(sys.argv) > 3 else 'iron_table'
RY = max(2, round(TOP * .17))                      # 윗면 타원의 세로 반지름(위에서 비스듬히 본 정도)
W, H = TOP + 2, 2 * RY + 2 + LEG
g = [['.'] * W for _ in range(H)]
def px(x, y, c):
    if 0 <= x < W and 0 <= y < H: g[y][x] = c
def line(p, q, c, th=1):
    (x0, y0), (x1, y1) = p, q; n = int(max(abs(x1 - x0), abs(y1 - y0))) or 1
    for i in range(n + 1):
        for k in range(th): px(round(x0 + (x1 - x0) * i / n) + k, round(y0 + (y1 - y0) * i / n), c)
cx, cy, rx = (W - 1) / 2, RY, TOP / 2
for y in range(2 * RY + 1):                          # 상판 윗면(타원)
    for x in range(W):
        e = ((x - cx) / rx) ** 2 + ((y - cy) / RY) ** 2
        if e <= 1: px(x, y, 'l' if e < .6 else 'm')
for y in range(2 * RY + 1, 2 * RY + 2 + 1):          # 얇은 옆면: 타원 아래쪽 호를 따라 아래로 1~2칸
    for x in range(W):
        e = ((x - cx) / rx) ** 2 + ((y - 1 - cy) / RY) ** 2
        if e <= 1 and g[y][x] == '.': px(x, y, 'd')
yb = 2 * RY + 2                                       # 다리 시작(상판 바로 밑)
th = 2 if TOP >= 22 else 1
a, b = TOP * .30, TOP * .40
line((cx - a, yb - 1), (cx + b, H - 1), 'm', th); line((cx + a - th + 1, yb - 1), (cx - b, H - 1), 'm', th)   # X자 다리
hy = yb + LEG * .45
for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)): px(round(cx) + dx, round(hy) + dy, 'd')
px(round(cx), round(hy), 'l')
grid = '\n'.join(''.join(r) for r in g)
txt = open('art/objects.txt', encoding='utf-8').read()
blk = '[' + NAME + '] 고풍스러운 쇠 원탁: 타원 상판 + X자 다리(지름 %d, 높이 %d) | real\n' % (TOP, LEG) + grid + '\n\n'
pat = r'\[' + NAME + r'\][^\n]*\n(?:[.\w]+\n)+\n'
txt = re.sub(pat, lambda m: blk, txt, count=1) if re.search(pat, txt) else txt.replace('[balcony_door_ls]', blk + '[balcony_door_ls]', 1)
open('art/objects.txt', 'w', encoding='utf-8').write(txt)
