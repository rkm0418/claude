#!/usr/bin/env python3
"""말랑한 고양이(진짜 고양이, 앉은 자세) 오리지널 캐릭터. 레퍼런스 도트화(art/out/pixelize/cat_*.png)의 비율을 가져옴:
큰 둥근 머리, 작은 몸, 앞발을 모은 앉은 자세, 위로 선 꼬리. 눈 둥근 점(안광/눈썹 없음), 입 일자. 표정 5종.
사용: python3 tools/gen_cutecat.py && python3 tools/variants.py cutecat   (24x30)"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import gen_shadow as G
from gen_shadow import C
from gen_creep import tube
from gen_helpers import tri
G.W, G.H = 26, 30

def cat(expr):
    c = C()
    tube(c, [(17, 28), (22.4, 25.4), (23, 19.5)], 3.2, 2.8, 0, 0, 'o'); c.ell(23, 18.2, 1.7, 1.8, 'q')    # 통통한 꼬리(끝이 둥근 흰색)
    c.line(21.4, 22, 22.4, 24.6, 1, ch='a')
    c.ell(12, 23.8, 6.6, 5.8, 'o'); c.ell(12, 25.6, 3.8, 3.6, 'q')                                          # 둥근 몸과 흰 배
    c.ell(6.2, 25.8, 2.8, 3.4, 'o'); c.ell(17.8, 25.8, 2.8, 3.4, 'o')                                       # 둥근 뒷다리
    c.ell(9.2, 28.5, 2.3, 1.5, 'q'); c.ell(14.8, 28.5, 2.3, 1.5, 'q')                                       # 모은 앞발
    c.ell(5.6, 3.6, 3.3, 3.8, 'o'); c.ell(18.4, 3.6, 3.3, 3.8, 'o'); c.ell(4.8, 1.6, 2.0, 2.0, 'o'); c.ell(19.2, 1.6, 2.0, 2.0, 'o')   # 둥근 귀
    c.ell(5.8, 3.6, 1.5, 1.9, 'i'); c.ell(18.2, 3.6, 1.5, 1.9, 'i')                                         # 귀 안쪽 분홍
    c.ell(12, 12.0, 10.4, 8.4, 'o')                                                                          # 크고 둥근 머리
    c.ell(12, 15.4, 4.2, 2.8, 'q')                                                                          # 하얀 주둥이
    for x, y0 in ((12, 4), (9.2, 5), (14.8, 5)): c.line(x, y0, x, y0 + 2.2, 1, ch='a')                      # 이마 줄무늬
    for sx in (-1, 1):
        for dy in (12.4, 14.6): c.line(12 + sx * 9.2, dy, 12 + sx * 7, dy + .4, 1, ch='a')                # 볼 줄무늬
    for y in (21, 23.4): c.line(6, y, 7.8, y + .6, 1, ch='a'); c.line(18, y, 16.2, y + .6, 1, ch='a')       # 몸 줄무늬
    c.put(12, 13.6, 'p'); c.put(11, 13.6, 'p'); c.put(13, 13.6, 'p')                                        # 코
    c.ell(9.6, 18.6, 3.0, 1.0, 'R'); c.put(11, 19.6, 'y'); c.put(11, 20.6, 'y')                              # 빨간 목줄과 금색 방울(이웃집 고양이 단서)
    if expr == 'A':
        for ex in (6.8, 15.2): c.ell(ex, 11.4, 1.6, 1.7, 'k')
        for x in range(11, 14): c.put(x, 16, 'k')
    if expr == 'B':
        for ex in (6.8, 15.2): c.put(ex - 1, 12, 'k'); c.put(ex, 11, 'k'); c.put(ex + 1, 11, 'k'); c.put(ex + 2, 12, 'k')
        for x in range(11, 14): c.put(x, 16, 'k')
        c.put(12, 17, 'r')
    if expr == 'C':
        for ex in (6.8, 15.2): c.ell(ex, 11.4, 1.6, 1.7, 'k')
        for x in range(11, 14): c.put(x, 16, 'k')
        c.ell(21, 6, 1.1, 1.7, 'c'); c.put(21, 4, 'c')
    if expr == 'D':
        for ex in (5.8, 14.4): c.line(ex, 12, ex + 3, 12, 1, ch='k')
        c.put(12, 16, 'k')
        for x, y in ((21, 1), (22, 1), (23, 1), (22, 2), (21, 3), (22, 3), (23, 3)): c.put(x, y, 'k')
    if expr == 'E':
        for ex in (5.6, 14.4): c.line(ex, 10.6, ex + 3, 12, 1, ch='k') if ex < 10 else c.line(ex + 3, 10.6, ex, 12, 1, ch='k'); c.put(ex + 1, 12, 'k'); c.put(ex + 2, 12, 'k')
        for x in range(11, 14): c.put(x, 16, 'k')
        for x, y in ((20, 3), (21, 3), (20, 4), (22, 4), (21, 5), (22, 5)): c.put(x, y, 'r')
    return c.finish()

def main():
    root = os.path.join(os.path.dirname(__file__), '..', 'art', 'variants')
    notes = {'A': '기본(입 일자)', 'B': '웃음', 'C': '걱정(땀방울, 입 일자)', 'D': '졸림', 'E': '화남(입 일자)'}
    lines = ['# 말랑한 고양이 표정 5종 (tools/gen_cutecat.py 가 생성함)', '']
    for v in 'ABCDE': lines.append(f'[cat_{v}] {notes[v]} | {v}'); lines += cat(v); lines.append('')
    open(os.path.join(root, 'cutecat_pixels.txt'), 'w', encoding='utf-8').write('\n'.join(lines))
if __name__ == '__main__': main()
