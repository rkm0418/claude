#!/usr/bin/env python3
"""주인공 5차: 최신 레퍼런스의 머리 스타일(가운데 가르마 둥근 단발)만 검은 머리로. 옷은 평상복 시안(gen_child.py), 얼굴 없음, 볼터치 없음.
사용: python3 tools/gen_child5.py && python3 tools/variants.py child5   (24x38)"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import gen_child as K
from gen_shadow import C

def hair_black(c):
    c.ell(12, 8.2, 10.4, 7.8, 's')
    for y in range(18):
        for x in range(24):
            if c.g[y][x] != 's': continue
            lim = 13.0 if (x < 4.6 or x > 19.4) else 10.6 - abs(x - 12) * 0.05
            if y > lim: c.g[y][x] = K.SKIN
    for y in range(2, 11):                                                                                 # 가운데 가르마
        half = 0.4 + (y - 2) * 0.22
        for x in range(24):
            if abs(x - 12) <= half and c.g[y][x] == 's': c.g[y][x] = K.SKIN
    for x0, y0, x1, y1 in ((7, 3.4, 5, 8.6), (9.4, 3.0, 8.0, 7.6), (15, 3.6, 16.6, 7.8), (17.6, 4.4, 19, 8.4)): c.line(x0, y0, x1, y1, 1, ch='d')   # 결(옅은 선)
    for x, y in ((6, 4), (7, 3), (17, 4)): c.put(x, y, 'm')                                                                                      # 윤기

def build(shirt, shorts, hands_covered=False):
    c = C(); K.base(c, shirt, shorts, sleeves_over_hands=hands_covered); K.head(c, blush=False); hair_black(c); return c

def A():
    c = build('c', 'h'); c.line(8.4, 35.4, 10.4, 35.4, 1, ch='W'); c.put(9.4, 34.6, 'W'); c.put(9.4, 36.2, 'W')
    c.ell(9.2, 37.4, 2.4, .9, 'p'); c.ell(14.8, 37.2, 1.8, .8, K.SKIN); return c.finish()
def B():
    c = build('t', 'd'); c.ell(9.2, 37.2, 2.0, .9, 'k'); c.ell(14.8, 37.2, 2.0, .9, 'k'); return c.finish()
def Cc():
    c = build('y', 'a'); c.ell(9.2, 36.0, 1.9, 1.2, 'W'); c.ell(14.8, 35.2, 1.9, 2.2, 'W'); c.ell(9.2, 37.3, 2.0, .8, 'd'); c.ell(14.8, 37.3, 2.0, .8, 'd'); return c.finish()
def D():
    c = build('l', 'd', True)
    for sgn in (-1, 1): c.ell(12 + sgn * 7.6, 30.4, 1.9, 1.7, 'l')
    c.ell(9.2, 37.2, 1.8, .9, K.SKIN); c.ell(14.8, 37.2, 1.8, .9, K.SKIN); return c.finish()

def main():
    root = os.path.join(os.path.dirname(__file__), '..', 'art', 'variants')
    notes = {'A': '하늘색 긴소매, 올리브 반바지, 무릎 밴드, 슬리퍼 한 짝', 'B': '민트 후드티, 검은 반바지, 운동화', 'C': '노란 긴소매, 한쪽만 내려간 양말', 'D': '손을 덮은 큰 회색 후드, 맨발'}
    lines = ['# 주인공 5차 시안: 가운데 가르마 검은 단발 + 얼굴 없음 (tools/gen_child5.py 가 생성함)', '']
    for v, fn in zip('ABCD', (A, B, Cc, D)): lines.append(f'[child_{v}] {notes[v]} | {v}'); lines += fn(); lines.append('')
    open(os.path.join(root, 'child5_pixels.txt'), 'w', encoding='utf-8').write('\n'.join(lines))
if __name__ == '__main__': main()
