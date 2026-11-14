#!/usr/bin/env python3
"""'나무 머리' 시안 12종 (사용자 레퍼런스: 굵은 줄기 다발이 위로 갈라져 퍼지는 카드 로고). 얼굴 없음, 48x84.
사용: python3 tools/gen_treehead.py && python3 tools/variants.py treehead"""
import os, sys, math, random
sys.path.insert(0, os.path.dirname(__file__))
import gen_gross  # G.W, G.H = 48, 84 설정
from gen_shadow import C
from gen_creep import tube
from gen_gross import limbs, wet

def branch(c, x, y, ang, L, depth, seed, mirror=1, spread=36, fork=2, droop=0.0, ch='l', decay=.72):
    r = random.Random(seed * 131 + depth)
    if depth <= 0 or L < 2: return
    ang = ang + droop * (1 if math.cos(ang) >= 0 else -1) * 0.0
    ex, ey = x + math.cos(ang) * L, y + math.sin(ang) * L
    c.line(x, y, ex, ey, 2 if depth >= 5 else 1, 1, ch=ch)
    n = fork if depth > 2 else 2 + r.randint(0, 1)
    for i in range(n):
        off = math.radians(spread * (i - (n - 1) / 2) * r.uniform(.8, 1.25)) * mirror
        a2 = ang + off
        if droop: a2 += droop * math.cos(a2) * -1 * 0 + math.radians(droop) * (1 if math.cos(a2) > 0 else -1)
        branch(c, ex, ey, a2, L * decay * r.uniform(.9, 1.1), depth - 1, seed * 3 + i, mirror, spread, fork, droop, ch, decay)

def body(c, torso_top=46, neck_w=7):
    tube(c, [(24, torso_top), (24, 66)], 11, 7, .06); limbs(c, 74, 7, torso_top + 2, 3)
    tube(c, [(24, torso_top - 2), (24, torso_top + 4)], neck_w)

def trunk(c, n=5, y0=46, y1=34, wid=1.45, twist=0.0, ch='l'):
    for k in range(n):
        off = (k - (n - 1) / 2)
        pts = [(24 + off * wid * 1.4 + math.sin(t * 2.2 + k) * twist, y0 + (y1 - y0) * t) for t in [i / 8 for i in range(9)]]
        for a, b in zip(pts, pts[1:]): c.line(*a, *b, 1, ch=ch)

def crown(c, stems=3, L=11, depth=6, spread=36, fork=2, base=(24, 34), fan=26, mirror_sym=True, seed=1, ch='l', decay=.72, droop=0):
    for i in range(stems):
        off = (i - (stems - 1) / 2) * fan
        branch(c, base[0], base[1], math.radians(-90 + off), L, depth, seed + i if not mirror_sym else seed + abs(i - (stems - 1) // 2),
               (1 if (i - (stems - 1) / 2) >= 0 or not mirror_sym else -1) if mirror_sym else 1, spread, fork, droop, ch, decay)

def t01(): c = C(); body(c); trunk(c); crown(c, 3, 8, 6, 36, 2, seed=1); return c, '대칭 나무 머리: 줄기 다발이 목이 되어 좌우 대칭으로 갈라짐 (로고 기본형)'
def t02(): c = C(); body(c); trunk(c, 7); crown(c, 5, 6, 5, 30, 3, fan=20, seed=2); return c, '빽빽한 가지: 가지가 셋씩 갈라져 머리가 덤불처럼 됨'
def t03(): c = C(); body(c); trunk(c, 5); crown(c, 4, 9, 6, 40, 2, fan=30, mirror_sym=False, seed=3); return c, '비대칭 나무: 가지가 제멋대로 뻗어 한쪽으로 쏠림'
def t04(): c = C(); body(c); trunk(c, 5); crown(c, 3, 8, 6, 36, 2, seed=4, droop=14); return c, '늘어진 가지: 가지가 아래로 휘어 어깨까지 처짐'
def t05(): c = C(); body(c); trunk(c, 5, ch='y'); crown(c, 3, 8, 6, 36, 2, seed=1, ch='y'); return c, '금빛 나무 머리: 로고처럼 금색 선, 몸은 새까맣게'
def t06(): c = C(); body(c); trunk(c, 8, y1=28, wid=1.1); crown(c, 8, 5, 4, 22, 2, base=(24, 28), fan=15, seed=6); return c, '다발 머리: 줄기 여덟 가닥이 빗자루처럼 갈라져 퍼짐'
def t07():
    c = C(); body(c); trunk(c); crown(c, 3, 8, 6, 36, 2, seed=1)
    for sx in (-1, 1):
        pts = chaikin([(24 + sx * 2, 46), (24 + sx * 12, 47), (24 + sx * 17, 56), (24 + sx * 15, 68)])
        for a, b in zip(pts, pts[1:]): c.line(*a, *b, 1, ch='l')
    return c, '뿌리 머리: 나무 머리 아래로 뿌리가 어깨와 팔을 타고 내려옴'
def t08(): c = C(); body(c); trunk(c, 5, y1=38); crown(c, 7, 6, 5, 30, 2, base=(24, 38), fan=24, seed=8, decay=.78); return c, '둥근 수관: 가지가 사방으로 퍼져 둥근 머리를 이룸'
def t09(): c = C(); body(c); trunk(c, 5, y1=30); crown(c, 3, 8, 6, 16, 2, base=(24, 31), fan=12, seed=9, decay=.82); return c, '좁고 긴 나무: 측백나무처럼 길쭉하게 솟음'
def t10(): c = C(); body(c); trunk(c, 5, y1=24, wid=1.45, twist=1.8); crown(c, 3, 6, 5, 36, 2, base=(24, 25), seed=10); return c, '꼬인 목: 줄기 가닥이 서로 꼬이며 길게 올라가 작은 가지로 끝남'
def t11(): c = C(); body(c); trunk(c, 5); crown(c, 4, 8, 5, 58, 2, fan=34, mirror_sym=False, seed=11, decay=.78); return c, '가시 가지: 각이 날카롭게 꺾인 가지가 사방으로 뻗음'
def t12():
    c = C(); body(c); trunk(c, 4, y1=38); crown(c, 2, 8, 5, 34, 2, base=(16, 36), fan=40, seed=12); crown(c, 2, 8, 5, 34, 2, base=(32, 36), fan=40, seed=13)
    c.line(16, 36, 24, 46, 1, ch='l'); c.line(32, 36, 24, 46, 1, ch='l'); return c, '두 그루: 어깨 양쪽에서 나무가 따로 솟아 머리가 둘'

from gen_creep import chaikin
def main():
    root = os.path.join(os.path.dirname(__file__), '..', 'art', 'variants')
    lines = ['# 나무 머리 시안 (tools/gen_treehead.py 가 생성함)', '']
    for i, fn in enumerate([t01, t02, t03, t04, t05, t06, t07, t08, t09, t10, t11, t12]):
        c, desc = fn(); lines.append(f'[{"abc"[i // 4]}_{i + 1:02d}] {desc} | {i + 1}'); lines += wet(c.finish(), i); lines.append('')
    open(os.path.join(root, 'treehead_pixels.txt'), 'w', encoding='utf-8').write('\n'.join(lines))
if __name__ == '__main__': main()
