#!/usr/bin/env python3
"""말랑한 곰 캐릭터(오리지널, 초록 후드 옷) 표정 4종. 사용: python3 tools/gen_cutebear.py && python3 tools/variants.py cutebear   (24x32)"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import gen_shadow as G
from gen_shadow import C
G.W, G.H = 24, 36

def rect(c, x0, y0, x1, y1, ch):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1): c.put(x, y, ch)

def bear(expr):
    c = C()
    for sx in (5, 19): c.ell(sx, 4.5, 3.4, 3.2, 'u'); c.ell(sx, 4.8, 1.7, 1.5, 'i')                        # 귀
    c.ell(9, 34.6, 2.9, 1.2, 'u'); c.ell(15, 34.6, 2.9, 1.2, 'u')                                           # 발이 바짓단 아래로 살짝 보임
    for x0 in (7, 13):                                                                                     # 평소에 입는 일자 바지: 위아래 폭이 같은 곧은 다리
        rect(c, x0, 27, x0 + 4, 33, 'z'); rect(c, x0 + 4, 27, x0 + 4, 33, 'x'); rect(c, x0, 28, x0, 31, 'h')    # 오른쪽 그늘, 왼쪽 빛
        rect(c, x0, 33, x0 + 4, 33, 'x'); c.put(x0 + 2, 30, 'x')                                            # 바짓단과 무릎 주름
    c.line(12, 27, 12, 33, 1, ch='x')                                                                       # 두 다리 사이
    for sx, sgn in ((5.2, -1), (18.8, 1)):                                                                 # 팔
        c.ell(sx, 22, 2.9, 3.7, 'h'); c.ell(sx + sgn * .3, 25.6, 2.2, 1.9, 'u')
    c.ell(12, 22.2, 7.4, 6.2, 'h'); c.ell(8.8, 20.5, 2.6, 3.0, 'f')                                         # 둥근 후드티 몸과 하이라이트
    c.ell(12, 18.6, 8.2, 2.8, 'f'); c.ell(12, 18.6, 5.4, 1.6, 'z')                                          # 말린 후드와 안쪽 그늘
    for sx in (-1, 1): c.line(12 + sx * 1.6, 20, 12 + sx * 1.9, 23.5, 1, ch='q'); c.put(12 + sx * 1.9, 24.5, 'q')   # 후드 끈
    c.ell(12, 25.2, 4.6, 1.9, 'h'); c.line(8, 24, 16, 24, 1, ch='z')                                        # 앞주머니(몸과 같은 초록, 윗선만 그늘)
    for sx in (5.2, 18.8): c.ell(sx, 24.8, 2.4, .8, 'z')                                                   # 소매 밴드
    rect(c, 7, 27, 17, 27, 'x')                                                                            # 밑단 밴드
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
