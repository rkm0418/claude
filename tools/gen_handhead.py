#!/usr/bin/env python3
"""'머리가 손 모양' 시안 12종: 머리 자리에 손(손바닥+긴 손가락)이 얼굴 없이 달린 형태.
사용: python3 tools/gen_handhead.py && python3 tools/variants.py handhead"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from gen_shadow import C
from gen_creep import tube
from gen_hand import fing, palm

def body(c, neck=(16, 14), top=26, hips=40, lean=0):
    tube(c, [(neck[0], neck[1]), (16 + lean, top)], 2.8)
    tube(c, [(16 + lean, top), (16, hips)], 7, 4, .08)
    tube(c, [(14, hips), (12, 48), (14, 55)], 2.4, 1.6); tube(c, [(18, hips), (20, 48), (18, 55)], 2.4, 1.6)
    for sx in (-1, 1):
        X = 16 + sx * 4
        tube(c, [(X, top + 2), (X + sx * 4, 40), (X + sx * 3, 50)], 2.2, 1.3, .12, sx); fing(c, X + sx * 3, 50, 90, 4, 5, 36, seed=sx + 3)

def hand_head(c, x, y, rx, ry, ang, n, L, spread, curl=0, seed=1):
    palm(c, x, y, rx, ry); fing(c, x, y - 1 if ang > 180 else y + 1, ang, n, L, spread, curl, seed)

def h01():
    c = C(); body(c, (17, 15), lean=1); hand_head(c, 16, 12, 4.4, 3.4, 232, 5, 13, 70, seed=1)
    return c, '기울어진 손 머리: 손바닥이 머리, 손가락이 왼쪽 위로 뻗음 (원본 03번 형태)'
def h02():
    c = C(); body(c); hand_head(c, 16, 14, 4.6, 4, 270, 5, 13, 100, seed=2)
    return c, '펼친 손 머리: 손바닥이 머리, 손가락 다섯이 위로 곧게 펼쳐짐'
def h03():
    c = C(); body(c, (16, 8)); hand_head(c, 16, 6, 4.4, 4, 90, 7, 16, 130, curl=-6, seed=3)
    return c, '늘어진 손 머리: 손가락이 머리카락처럼 어깨 아래로 드리움'
def h04():
    c = C(); body(c); palm(c, 16, 14, 5.2, 5)
    for x in (13, 15, 17, 19): c.line(x, 10, x, 12, 1, ch='k')
    for y in (15, 18): c.line(12, y, 20, y, 1, ch='k')
    c.ell(21, 16, 2, 3, 'l')
    return c, '주먹 머리: 쥔 주먹이 머리, 마디와 엄지가 보임'
def h05():
    c = C(); body(c); hand_head(c, 16, 15, 4, 3.4, 270, 11, 13, 170, seed=5)
    return c, '부채 머리: 손가락 열한 개가 공작처럼 펼쳐짐'
def h06():
    c = C(); body(c, (16, 9), top=26); c.line(16, 9, 16, 26, 1.8, ch='s'); hand_head(c, 16, 9, 3.6, 3, 270, 5, 9, 90, seed=6)
    return c, '가는 손목 목: 가는 목 위에 작은 손 머리가 얹힘'
def h07():
    c = C(); body(c)
    hand_head(c, 12, 14, 3.4, 3.6, 255, 4, 12, 50, seed=7); hand_head(c, 20, 14, 3.4, 3.6, 285, 4, 12, 50, seed=8)
    return c, '두 손 머리: 손 둘이 V자로 맞붙어 머리를 이룸'
def h08():
    c = C(); body(c, (16, 18), top=26); tube(c, [(16, 24), (22, 18), (26, 15)], 2.8)
    hand_head(c, 26, 14, 3.6, 3.4, 95, 5, 15, 60, seed=9)
    return c, '꺾인 손 머리: 목이 어깨로 꺾여 손가락이 가슴 앞으로 늘어짐'
def h09():
    c = C(); body(c); hand_head(c, 16, 15, 4.2, 3.4, 270, 6, 13, 110, curl=26, seed=10)
    return c, '말린 손가락 머리: 손가락 끝이 안쪽으로 말려 왕관처럼 보임'
def h10():
    c = C(); body(c, (16, 6)); hand_head(c, 16, 5, 3.6, 3.4, 90, 6, 30, 70, curl=-4, seed=11)
    return c, '긴 손가락 장막: 손가락이 허리까지 내려와 몸 앞을 덮음'
def h11():
    c = C(); body(c, (16, 16)); hand_head(c, 16, 15, 4.6, 3.6, 270, 5, 9, 100, seed=12); hand_head(c, 16, 6, 3, 2.6, 270, 5, 6, 90, seed=13)
    return c, '겹친 손: 손 위에 작은 손이 또 돋아남'
def h12():
    c = C(); body(c); hand_head(c, 16, 14, 4.6, 4, 270, 3, 18, 40, curl=0, seed=14)
    return c, '세 손가락: 굵고 긴 손가락 셋만 곧게 솟음'

def main():
    root = os.path.join(os.path.dirname(__file__), '..', 'art', 'variants')
    lines = ['# 손 머리 시안 (tools/gen_handhead.py 가 생성함)', '']
    for i, fn in enumerate([h01, h02, h03, h04, h05, h06, h07, h08, h09, h10, h11, h12]):
        c, desc = fn(); lines.append(f'[{"abc"[i // 4]}_{i + 1:02d}] {desc} | {i + 1}'); lines += c.finish(); lines.append('')
    open(os.path.join(root, 'handhead_pixels.txt'), 'w', encoding='utf-8').write('\n'.join(lines))
if __name__ == '__main__': main()
