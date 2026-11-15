#!/usr/bin/env python3
"""art/ref/iron_chair_ref.jpg(검은 철제 망 등받이 팔걸이 의자 사진)를 그대로 도트로 옮겨 좌우 반전해 art/objects.txt 에 iron_chair 로 쓴다."""
import re
import numpy as np
from PIL import Image
a = np.array(Image.open('art/ref/iron_chair_ref.jpg').convert('L')).astype(float)
ys, xs = np.where(a < 110)
a = (a[ys.min():ys.max() + 1, xs.min():xs.max() + 1] < 110).astype(float)
W, H = 28, 34
im = Image.fromarray((a * 255).astype('uint8')).resize((W, H), Image.BOX)
cov = np.array(im) / 255.0
g = [['.'] * W for _ in range(H)]
for y in range(H):
    for x in range(W):
        v = cov[y, x]
        if v > .45: g[y][x] = 'l'
        elif v > .17: g[y][x] = 'd'
for y in range(3, 12):                                   # 속이 비치는 망 등받이(사진에서 밝게 날아간 부분)
    for x in range(14, 26 - (y - 3) // 4):
        if g[y][x] == '.' and (x + y) % 2 == 0: g[y][x] = 'm'
g[:] = [r[::-1] for r in g]
grid = '\n'.join(''.join(r) for r in g)
txt = open('art/objects.txt', encoding='utf-8').read()
blk = '[iron_chair] 사진 속 검은 철제 망 등받이 팔걸이 의자(28x34 사진 트레이스, 3/4 시점, 좌우 반전) | real\n' + grid + '\n\n'
if '[iron_chair]' in txt:
    txt = re.sub(r'\[iron_chair\][^\n]*\n(?:[.\w]+\n)+\n', blk, txt, count=1)
else:
    txt = txt.replace('[iron_table]', blk + '[iron_table]', 1)
open('art/objects.txt', 'w', encoding='utf-8').write(txt)
