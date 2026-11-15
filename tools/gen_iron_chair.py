#!/usr/bin/env python3
"""사진(스핀들 등받이 빈티지 의자)을 토대로 쇠 의자 정면을 art/objects.txt 에 iron_chair 로 쓴다."""
import re
W, H = 20, 34
g = [['.'] * W for _ in range(H)]
def px(x, y, c):
    if 0 <= x < W and 0 <= y < H: g[y][x] = c
def rect(x0, y0, x1, y1, c):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1): px(x, y, c)
def outline():
    src = [r[:] for r in g]
    for y in range(H):
        for x in range(W):
            if src[y][x] == '.':
                for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
                    nx, ny = x+dx, y+dy
                    if 0 <= nx < W and 0 <= ny < H and src[ny][nx] not in '.k':
                        g[y][x] = 'k'; break
# 등받이 윗판(살짝 휜 곡선)
rect(3, 1, 16, 3, 'm'); rect(2, 2, 17, 2, 'm'); rect(4, 1, 15, 1, 'c')
px(2, 3, '.'); px(17, 3, '.')
# 양쪽 기둥(마디 장식)
for x in (3, 16):
    rect(x, 4, x, 16, 'm')
    px(x, 7, 'c'); px(x, 10, 'd'); px(x, 11, 'c'); px(x, 12, 'd')
# 살대 4개
for x in (6, 8, 11, 13):
    rect(x, 4, x, 15, 'm'); px(x, 5, 'c')
# 안장 모양 앉는 판
rect(2, 16, 17, 16, 'c'); rect(1, 17, 18, 18, 'm'); rect(2, 19, 17, 19, 'd')
px(1, 18, 'd'); px(18, 18, 'd')
# 뒷다리(안쪽), 앞다리(바깥, 굵은 마디 장식)
for x in (6, 13): rect(x, 20, x, 27, 'd')
for x in (3, 16):
    rect(x, 20, x, 33, 'm')
    for y in (22, 23): px(x, y, 'd')
    px(x, 21, 'c'); px(x, 29, 'd'); px(x, 30, 'c')
# 가로대
rect(4, 26, 15, 26, 'm'); rect(5, 27, 14, 27, 'd')
outline()
grid = '\n'.join(''.join(r) for r in g)
txt = open('art/objects.txt', encoding='utf-8').read()
blk = '[iron_chair] 사진 속 스핀들 의자를 쇠로 옮긴 정면 의자(20x34) | real\n' + grid + '\n\n'
if '[iron_chair]' in txt:
    txt = re.sub(r'\[iron_chair\][^\n]*\n(?:[.\w]+\n)+\n', blk, txt, count=1)
else:
    txt = txt.replace('[iron_table]', blk + '[iron_table]', 1)
open('art/objects.txt', 'w', encoding='utf-8').write(txt)
