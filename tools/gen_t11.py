#!/usr/bin/env python3
"""나무 머리 11번(가시 가지) 수정판: 끝 가지가 더 불규칙, 반짝이 없음, 왼팔은 드문드문하되 이어진 구슬 팔, 오른팔은 정상 팔, 팔 끝 회색 없음.
사용: python3 tools/gen_t11.py && python3 tools/variants.py t11   (시드만 바꾼 4종)"""
import os, sys, math, random
sys.path.insert(0, os.path.dirname(__file__))
import gen_gross  # 48x84
from gen_shadow import C
from gen_creep import tube, chaikin
from gen_treehead import trunk

def branch(c, x, y, ang, L, depth, rng, spread=1.0):
    if depth <= 0 or L < 1.5: return
    k1, k2 = rng.uniform(-.4, .4), rng.uniform(-.4, .4)
    mx, my = x + math.cos(ang + k1) * L * .5, y + math.sin(ang + k1) * L * .5
    ex, ey = mx + math.cos(ang + k2) * L * .5, my + math.sin(ang + k2) * L * .5
    c.line(x, y, mx, my, 2 if depth >= 5 else 1, 1, ch='l'); c.line(mx, my, ex, ey, 1, 1, ch='l')
    if depth == 1:                                   # 끝 가시
        for _ in range(rng.randint(1, 3)):
            a = ang + rng.uniform(-1.2, 1.2); l = rng.uniform(1.5, 4)
            c.line(ex, ey, ex + math.cos(a) * l, ey + math.sin(a) * l, 1, ch='l')
        return
    if depth <= 3 and rng.random() < .3: return    # 중간에 끊긴 가지
    n = rng.choice((1, 2, 2)) if depth > 3 else rng.choice((1, 1, 2))
    for _ in range(n):
        branch(c, ex, ey, ang + rng.uniform(-1, 1) * spread * (1.2 if depth <= 3 else 1.0), L * rng.uniform(.6, 1.0), depth - 1, rng, spread)
    if rng.random() < .15:                           # 몸통에서 곁가지
        branch(c, mx, my, ang + rng.choice((-1, 1)) * rng.uniform(.6, 1.3), L * rng.uniform(.3, .6), depth - 2, rng, spread)

def beaded(c, pts, wmin=0.4, wmax=4.2, period=7):
    P = chaikin(pts, 3)
    for i, (x, y) in enumerate(P):
        w = wmin + (wmax - wmin) * (.5 + .5 * math.sin(i * 6.28 / period))
        c.disc(x, y, w / 2, 's')

def figure(seed):
    c = C(); rng = random.Random(seed)
    tube(c, [(24, 46), (24, 66)], 11, 7, .04); tube(c, [(24, 44), (24, 50)], 7)
    tube(c, [(20, 64), (18, 74), (20, 83)], 4, 2.4); tube(c, [(28, 64), (30, 74), (28, 83)], 4, 2.4)
    beaded(c, [(17, 49), (9, 60), (8, 74)])                                   # 왼팔: 드문드문, 이어짐
    tube(c, [(31, 49), (37, 60), (36, 72)], 3.4, 2.6); c.ell(36, 74.5, 2.3, 3, 's')   # 오른팔: 정상, 끝은 어두운 손
    trunk(c, 5)
    for i in range(3):
        branch(c, 24 + (i - 1) * 2, 34, math.radians(-90 + (i - 1) * rng.uniform(26, 42)), 9, 5, rng, .75)
    return c

def main():
    root = os.path.join(os.path.dirname(__file__), '..', 'art', 'variants')
    lines = ['# 나무 머리 11번 수정판 (tools/gen_t11.py 가 생성함)', '']
    for i, seed in enumerate((11, 12, 13, 14)):
        lines.append(f'[a_{i + 1:02d}] 가시 가지 수정판 시드 {seed} | {i + 1}'); lines += figure(seed).finish(); lines.append('')
    open(os.path.join(root, 't11_pixels.txt'), 'w', encoding='utf-8').write('\n'.join(lines))
if __name__ == '__main__': main()
