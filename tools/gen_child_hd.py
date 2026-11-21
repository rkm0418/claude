#!/usr/bin/env python3
"""주인공 고해상도판: 기존 8방향 도트(24x42)를 같은 모양 그대로 4배 촘촘한 도트(56x96, 게임 크기 14x24 × 4)로 부드럽게 만든다.
  1) Scale2x(EPX)를 두 번 — 계단 모서리를 둥글게 다듬어 4배 크기로(96x168)  2) 게임 크기 × 4 로 줄이고 알파는 다시 또렷하게(도트 느낌 유지)
  3) 걷기 네 장 사이 사이에 중간 자세를 섞어 만든 한 장씩을 더해 걷기를 8장으로(더 부드러운 걸음)
출력: art/out/sprites/child_hd/child_<방향>_<idle|w1..w4|m1..m4>.png   사용: python3 tools/gen_child_hd.py"""
import os
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.join(HERE, '..', 'art', 'out', 'sprites', 'child8'); OUT = os.path.join(HERE, '..', 'art', 'out', 'sprites', 'child_hd')
K = 4; GW, GH = 14, 24; SIZE = (GW * K, GH * K)
DIRS = ['d', 'dr', 'r', 'ur', 'u', 'ul', 'l', 'dl']; FR = ['idle', 'w1', 'w2', 'w3', 'w4']

def scale2x(a):
    h, w = a.shape[:2]; p = np.pad(a, ((1, 1), (1, 1), (0, 0)), mode='edge')
    P = p[1:-1, 1:-1]; A = p[:-2, 1:-1]; B = p[1:-1, 2:]; C = p[1:-1, :-2]; D = p[2:, 1:-1]
    eq = lambda x, y: np.all(x == y, axis=-1)
    o = np.repeat(np.repeat(P, 2, 0), 2, 1).copy()
    m1 = eq(C, A) & ~eq(C, D) & ~eq(A, B); m2 = eq(A, B) & ~eq(A, C) & ~eq(B, D); m3 = eq(D, C) & ~eq(D, B) & ~eq(C, A); m4 = eq(B, D) & ~eq(B, A) & ~eq(D, C)
    for m, (dy, dx), src in ((m1, (0, 0), A), (m2, (0, 1), B), (m3, (1, 0), C), (m4, (1, 1), D)):
        ys, xs = np.nonzero(m); o[ys * 2 + dy, xs * 2 + dx] = src[ys, xs]
    return o

def hd(im):
    a = np.array(im.convert('RGBA')); a = scale2x(scale2x(a)); big = Image.fromarray(a, 'RGBA')
    small = big.convert('RGBa').resize(SIZE, Image.LANCZOS).convert('RGBA'); s = np.array(small); s[..., 3] = np.where(s[..., 3] >= 128, 255, 0); return Image.fromarray(s, 'RGBA')

def mix(a, b):
    """두 걷기 자세의 중간 자세: 알파를 평균해 문턱을 넘는 곳만 남기고 색은 가까운 쪽에서 가져온다."""
    A, B = np.array(a).astype(float), np.array(b).astype(float); al = (A[..., 3] + B[..., 3]) / 2
    col = np.where((A[..., 3] >= B[..., 3])[..., None], A[..., :3], B[..., :3]); o = np.dstack([col, np.where(al >= 128, 255, 0)]).astype(np.uint8); return Image.fromarray(o, 'RGBA')

def build():
    os.makedirs(OUT, exist_ok=True); res = {}
    for d in DIRS:
        f = {k: hd(Image.open(os.path.join(SRC, f'child_{d}_{k}.png'))) for k in FR}
        for i, (p, q) in enumerate((('w1', 'w2'), ('w2', 'w3'), ('w3', 'w4'), ('w4', 'w1'))): f[f'm{i + 1}'] = mix(f[p], f[q])
        for k, im in f.items(): im.save(os.path.join(OUT, f'child_{d}_{k}.png'))
        res[d] = f
    return res

if __name__ == '__main__':
    r = build(); S = 3; names = ['idle', 'w1', 'm1', 'w2', 'm2', 'w3', 'm3', 'w4', 'm4']
    sheet = Image.new('RGBA', (len(names) * (SIZE[0] + 6) * S // 2 + 8, 3 * (SIZE[1] + 6) * S // 2 + 8), (44, 48, 64, 255))
    for row, d in enumerate(('d', 'r', 'u')):
        for c, k in enumerate(names): sheet.alpha_composite(r[d][k].resize((SIZE[0] * S // 2, SIZE[1] * S // 2), Image.NEAREST), (4 + c * (SIZE[0] + 6) * S // 2, 4 + row * (SIZE[1] + 6) * S // 2))
    sheet.save(os.path.join(HERE, '..', 'maps', 'out', 'child_hd_sheet.png')); print('child_hd', len(DIRS) * 9)
