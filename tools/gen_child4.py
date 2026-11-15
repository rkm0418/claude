#!/usr/bin/env python3
"""주인공 4차: 새 레퍼런스(베이지 회색 가운데 가르마 단발, 큰 분홍 볼, 짙은 회색 교복 재킷과 주황 넥타이). 얼굴 없음 / 얼굴(웃음) 두 가지.
사용: python3 tools/gen_child4.py && python3 tools/variants.py child4   (24x38)"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import gen_shadow as G
from gen_shadow import C
from gen_creep import tube
import gen_child as K
G.W, G.H = 24, 38

def uniform(c):
    c.ell(9, 33.6, 2.6, 3.4, 'd'); c.ell(15, 33.6, 2.6, 3.4, 'd'); c.ell(9, 37.2, 2.4, 1.0, 'k'); c.ell(15, 37.2, 2.4, 1.0, 'k')    # 바지와 구두
    for sgn in (-1, 1):
        tube(c, [(12 + sgn * 5.6, 22.8), (12 + sgn * 7.0, 29.4)], 3.0, 3.0, 0, 0, 'm'); c.ell(12 + sgn * 7.2, 31.0, 1.5, 1.6, K.SKIN)   # 재킷 소매와 손
    c.ell(12, 26.6, 6.6, 5.8, 'm'); c.ell(12, 20.8, 2.6, 1.3, K.SKIN)                                         # 재킷 몸통과 목
    for y in range(21, 27):                                                                                # 흰 셔츠 V와 넥타이
        half = 2.4 - (y - 21) * .4
        for x in range(int(12 - half + .5), int(12 + half + .5) + 1): c.put(x, y, 'W')
    c.put(12, 22, 'o'); c.put(12, 23, 'o'); c.put(11, 24, 'o'); c.put(12, 24, 'o'); c.put(12, 25, 'o'); c.put(12, 26, 'o')
    c.line(9.4, 22, 11.4, 27.6, 1, ch='d'); c.line(14.6, 22, 12.6, 27.6, 1, ch='d')                         # 옷깃(라펠)
    c.put(11, 29, 'y')                                                                                     # 단추

def hair(c):
    c.ell(12, 8.2, 10.4, 7.8, 'w')
    for y in range(18):
        for x in range(24):
            if c.g[y][x] != 'w': continue
            lim = 13.0 if (x < 4.6 or x > 19.4) else 10.6 - abs(x - 12) * 0.05
            if y > lim: c.g[y][x] = K.SKIN
    for y in range(2, 11):                                                                                 # 가운데 가르마: 위로 올라가는 살색 틈
        half = 0.4 + (y - 2) * 0.22
        for x in range(24):
            if abs(x - 12) <= half and c.g[y][x] == 'w': c.g[y][x] = K.SKIN
    for x0, y0, x1, y1 in ((7, 3.4, 5, 8.6), (9.4, 3.0, 8.0, 7.6), (15, 3.6, 16.6, 7.8), (17.6, 4.4, 19, 8.4)): c.line(x0, y0, x1, y1, 1, ch='l')

def person(face):
    c = C(); uniform(c); K.head(c, blush=False); hair(c)
    for sx in (-1, 1): c.ell(12 + sx * 6.4, 15.8, 2.8, 2.0, 'i')                                           # 큰 분홍 볼
    if face:                                                                                               # 얼굴 있는 버전: 감은 웃는 눈 + 큰 웃음
        for ex in (8.6, 15.4): c.put(ex - 1, 13.4, 'k'); c.put(ex, 12.6, 'k'); c.put(ex + 1, 13.4, 'k')
        c.put(12, 14.6, 'a'); c.ell(12, 17.2, 2.4, 1.3, 'k'); c.put(12, 17.6, 'r'); c.put(11, 17.6, 'r'); c.put(13, 17.6, 'r')
    return c.finish()

def main():
    root = os.path.join(os.path.dirname(__file__), '..', 'art', 'variants')
    lines = ['# 주인공 4차 시안 (tools/gen_child4.py 가 생성함)', '', '[child_A] 얼굴 없음 + 큰 분홍 볼, 베이지 가운데 가르마, 교복 재킷과 주황 넥타이 | A']
    lines += person(False) + ['', '[child_B] 얼굴 있음(웃는 눈, 큰 웃음) + 같은 머리와 교복 | B'] + person(True) + ['']
    open(os.path.join(root, 'child4_pixels.txt'), 'w', encoding='utf-8').write('\n'.join(lines))
if __name__ == '__main__': main()
