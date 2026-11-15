#!/usr/bin/env python3
"""사진(스핀들 등받이 빈티지 의자)을 토대로 쇠 의자 정면을 art/objects.txt 에 iron_chair 로 쓴다."""
import re
W, H = 18, 32
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
# 사진: 검은 철제 팔걸이 의자. 뒤에서 본 모습(난간 쪽을 향해 앉음)
W2 = 18
for x in range(4, 14): px(x, 0, 'l')                      # 등받이 고리 윗줄
px(3, 1, 'm'); px(14, 1, 'm'); px(2, 2, 'm'); px(15, 2, 'm')
for y in range(3, 12):                                    # 고리 양쪽(팔걸이로 이어짐)
    px(2, y, 'm'); px(15, y, 'm')
for y in range(2, 11):                                    # 망(그물) 등받이: 마름모 점
    for x in range(3, 15):
        if (x + y) % 2 == 0: px(x, y, 'd')
for x in range(3, 15): px(x, 11, 'm')                     # 등받이 아래 가로대
px(1, 12, 'm'); px(16, 12, 'm'); px(1, 13, 'm'); px(16, 13, 'm')   # 팔걸이 끝
for x in range(2, 16): px(x, 14, 'c')                     # 앉는 판(뒤에서 얇게)
for x in range(3, 15): px(x, 15, 'd')
for y in range(15, 31): px(3, y, 'm'); px(14, y, 'm')     # 뒷다리(가까움, 길게)
for y in range(15, 27): px(6, y, 'd'); px(11, y, 'd')     # 앞다리(멀리, 짧게)
px(3, 16, 'c'); px(14, 16, 'c')
grid = '\n'.join(''.join(r) for r in g)
txt = open('art/objects.txt', encoding='utf-8').read()
blk = '[iron_chair] 사진 속 스핀들 의자를 쇠로 옮긴 정면 의자(20x34) | real\n' + grid + '\n\n'
if '[iron_chair]' in txt:
    txt = re.sub(r'\[iron_chair\][^\n]*\n(?:[.\w]+\n)+\n', blk, txt, count=1)
else:
    txt = txt.replace('[iron_table]', blk + '[iron_table]', 1)
open('art/objects.txt', 'w', encoding='utf-8').write(txt)
