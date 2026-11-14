#!/usr/bin/env python3
"""말랑한 곰 캐릭터(오리지널, 초록 후드 옷) 표정 4종. 사용: python3 tools/gen_cutebear.py && python3 tools/variants.py cutebear   (24x32)"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import gen_shadow as G
from gen_shadow import C
G.W, G.H = 24, 32

def rect(c, x0, y0, x1, y1, ch):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1): c.put(x, y, ch)

def bear(expr):
    c = C()
    for sx in (5, 19): c.ell(sx, 4.5, 3.4, 3.2, 'u'); c.ell(sx, 4.8, 1.7, 1.5, 'i')                        # 귀
    c.ell(8.5, 30.3, 3.2, 1.9, 'u'); c.ell(15.5, 30.3, 3.2, 1.9, 'u')                                      # 짧고 둥근 발
    for sx, sgn in ((5.2, -1), (18.8, 1)):                                                                 # 팔: 몸 옆에 겹쳐 둥근 어깨로 이어짐
        c.ell(sx, 23.2, 2.9, 3.9, 'h'); c.ell(sx + sgn * .3, 27, 2.2, 2, 'u')
    c.ell(12, 23.6, 7.4, 7.2, 'h'); c.ell(8.8, 21.5, 2.6, 3.2, 'f')   # 둥근 몸, 하이라이트와 아래 그늘
    c.ell(12, 27.4, 3.4, 1.4, 'z'); c.line(11, 19, 10.4, 22.5, 1, ch='q'); c.line(13, 19, 13.6, 22.5, 1, ch='q')        # 둥근 주머니와 후드 끈
    c.ell(12, 18.6, 5.8, 2.2, 'f')                                                                         # 목 뒤로 말린 후드(각지지 않게 둥글게)
    c.ell(12, 11, 9.6, 8.2, 'u'); c.ell(12, 14, 5.2, 3.6, 'q')                                             # 머리와 주둥이
    for sx in (-1, 1): c.ell(12 + sx * 6.2, 14, 2.1, 1.5, 'i')                                              # 볼터치
    c.put(12, 13, 'b'); c.put(11, 13, 'b'); c.put(13, 13, 'b')                                              # 코
    if expr == 'A':
        for ex in (7, 16): c.put(ex, 11, 'k'); c.put(ex + 1, 11, 'k'); c.put(ex, 12, 'k'); c.put(ex + 1, 12, 'k')
        for x, y in ((10, 15), (11, 16), (12, 15), (13, 16), (14, 15)): c.put(x, y, 'k')
    if expr == 'B':
        for ex in (7, 16): c.put(ex, 12, 'k'); c.put(ex + 1, 11, 'k'); c.put(ex + 2, 12, 'k')
        for x in range(10, 15): c.put(x, 15, 'k')
        for x in range(11, 14): c.put(x, 16, 'r')
    if expr == 'C':
        for ex in (7, 16): c.put(ex, 12, 'k'); c.put(ex + 1, 12, 'k'); c.put(ex, 13, 'k'); c.put(ex + 1, 13, 'k')
        c.line(6, 9, 9, 10, 1, ch='k'); c.line(18, 9, 15, 10, 1, ch='k')
        for x, y in ((10, 16), (11, 15), (12, 16), (13, 15), (14, 16)): c.put(x, y, 'k')
        c.ell(20, 6, 1.2, 1.8, 'c'); c.put(20, 4, 'c')
    if expr == 'D':
        for ex in (6, 15): c.line(ex, 12, ex + 3, 12, 1, ch='k')
        c.put(11, 15, 'k'); c.put(12, 16, 'k'); c.put(13, 15, 'k'); c.ell(12, 16.5, 1, 1, 'r')
        for x, y in ((19, 1), (20, 1), (21, 1), (20, 2), (19, 3), (20, 3), (21, 3)): c.put(x, y, 'w')
    return c

def main():
    root = os.path.join(os.path.dirname(__file__), '..', 'art', 'variants')
    notes = {'A': '기본 표정', 'B': '웃는 표정', 'C': '걱정(땀방울)', 'D': '졸림'}
    lines = ['# 말랑한 곰(초록 후드) 표정 4종 (tools/gen_cutebear.py 가 생성함)', '']
    for v in 'ABCD':
        lines.append(f'[bear_{v}] {notes[v]} | {v}'); lines += bear(v).finish(); lines.append('')
    open(os.path.join(root, 'cutebear_pixels.txt'), 'w', encoding='utf-8').write('\n'.join(lines))
if __name__ == '__main__': main()
